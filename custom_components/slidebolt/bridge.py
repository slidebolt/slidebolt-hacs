"""WebSocket client for Slidebolt server."""

from __future__ import annotations

import asyncio
import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import CONF_CLIENT_ID, SIGNAL_ENTITY_ADDED, SIGNAL_ENTITY_REMOVED, SIGNAL_ENTITY_UPDATED

_LOGGER = logging.getLogger(__name__)


async def async_hello(host: str, port: int, client_id: str) -> tuple[bool, str]:
    """Test connection and validate the Slidebolt hello handshake.

    Returns (auth_required, server_id). Raises on connection failure.
    """
    url = f"ws://{host}:{port}/ws"
    session = aiohttp.ClientSession()
    try:
        ws = await session.ws_connect(url, timeout=10)
        try:
            await ws.send_json({"type": "hello", CONF_CLIENT_ID: client_id})
            msg = await asyncio.wait_for(ws.receive_json(), timeout=10)
            if msg.get("type") != "hello":
                raise ConnectionError(f"Unexpected response: {msg}")
            return bool(msg.get("auth", False)), msg.get("server_id", "")
        finally:
            await ws.close()
    finally:
        await session.close()


class SlideboltBridge:
    """Manages the WebSocket connection to a Slidebolt server."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, client_id: str) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.client_id = client_id
        self.entities: dict[str, dict] = {}
        self._platform_callbacks: dict[str, callable] = {}
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._task: asyncio.Task | None = None
        self._request_id = 0
        self._pending: dict[str, asyncio.Future] = {}
        self._stop = asyncio.Event()

    def payload(self, unique_id: str) -> dict:
        """Get the current payload for an entity."""
        return self.entities.get(unique_id, {})

    async def async_register_platform(self, platform: str, async_add_entities: callable) -> None:
        """Register a platform's add_entities callback."""
        self._platform_callbacks[platform] = async_add_entities

    async def async_start(self) -> None:
        """Start the WebSocket connection loop."""
        self._stop.clear()
        self._task = self.hass.async_create_task(self._run())

    async def async_stop(self) -> None:
        """Stop the WebSocket connection."""
        self._stop.set()
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            self._task = None
        if self._session:
            await self._session.close()
            self._session = None

    async def async_send_command(self, unique_id: str, command: str, params: dict) -> dict | None:
        """Send a command to the server and wait for the result."""
        if not self._ws or self._ws.closed:
            _LOGGER.warning("Cannot send command, not connected")
            return None

        self._request_id += 1
        cmd_id = f"cmd-{self._request_id}"

        entity = self.entities.get(unique_id, {})
        msg = {
            "type": "command",
            "id": cmd_id,
            "entity_id": entity.get("entity_id", unique_id),
            "command": command,
            "params": params,
        }

        future = self.hass.loop.create_future()
        self._pending[cmd_id] = future

        try:
            await self._ws.send_json(msg)
            return await asyncio.wait_for(future, timeout=5)
        except asyncio.TimeoutError:
            _LOGGER.warning("Command %s timed out", cmd_id)
            return None
        finally:
            self._pending.pop(cmd_id, None)

    async def _run(self) -> None:
        """Connection loop with reconnect."""
        while not self._stop.is_set():
            try:
                await self._connect()
            except Exception:
                _LOGGER.exception("Connection failed")
            if not self._stop.is_set():
                _LOGGER.info("Reconnecting in 5 seconds...")
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=5)
                except asyncio.TimeoutError:
                    pass

    async def _connect(self) -> None:
        """Establish connection and run message loop."""
        url = f"ws://{self.host}:{self.port}/ws"
        self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(url)
            _LOGGER.info("Connected to %s", url)

            # Hello handshake
            await self._ws.send_json({"type": "hello", CONF_CLIENT_ID: self.client_id})
            hello = await asyncio.wait_for(self._ws.receive_json(), timeout=10)
            if hello.get("type") != "hello" or not hello.get("auth"):
                _LOGGER.error("Server handshake failed: %s", hello)
                return

            # Message loop
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.json())
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
        finally:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            if self._session:
                await self._session.close()
                self._session = None

    async def _handle_message(self, msg: dict) -> None:
        """Route an inbound message."""
        msg_type = msg.get("type")

        if msg_type == "snapshot":
            await self._handle_snapshot(msg)
        elif msg_type == "entity_added":
            await self._handle_entity_added(msg.get("entity", {}))
        elif msg_type == "entity_updated":
            self._handle_entity_updated(msg.get("entity", {}))
        elif msg_type == "entity_removed":
            self._handle_entity_removed(msg.get("entity_id", ""), msg.get("unique_id", ""))
        elif msg_type == "command_result":
            self._handle_command_result(msg)
        elif msg_type == "pong":
            pass
        else:
            _LOGGER.debug("Unknown message type: %s", msg_type)

    async def _handle_snapshot(self, msg: dict) -> None:
        """Process a full entity snapshot."""
        snapshot = msg.get("snapshot", {})
        devices = snapshot.get("devices", [])

        for device in devices:
            for entity in device.get("entities", []):
                unique_id = entity.get("unique_id")
                if not unique_id:
                    continue
                is_new = unique_id not in self.entities
                self.entities[unique_id] = entity
                if is_new:
                    await self._add_entity(entity)
                else:
                    async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, unique_id)

    async def _handle_entity_added(self, entity: dict) -> None:
        """Process a new entity."""
        unique_id = entity.get("unique_id")
        if not unique_id:
            return
        self.entities[unique_id] = entity
        await self._add_entity(entity)

    def _handle_entity_updated(self, entity: dict) -> None:
        """Process an entity state update."""
        unique_id = entity.get("unique_id")
        if not unique_id:
            return
        self.entities[unique_id] = entity
        async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, unique_id)

    def _handle_entity_removed(self, entity_id: str, unique_id: str) -> None:
        """Process an entity removal."""
        if unique_id:
            self.entities.pop(unique_id, None)
        async_dispatcher_send(self.hass, SIGNAL_ENTITY_REMOVED, unique_id or entity_id)

    def _handle_command_result(self, msg: dict) -> None:
        """Resolve a pending command future."""
        cmd_id = msg.get("id")
        future = self._pending.get(cmd_id)
        if future and not future.done():
            future.set_result(msg)

    async def _add_entity(self, entity: dict) -> None:
        """Add an entity via its platform callback."""
        platform = entity.get("platform")
        callback = self._platform_callbacks.get(platform)
        if callback:
            from .entity_base import SlideboltBaseEntity, create_platform_entity

            ha_entity = create_platform_entity(platform, self, entity["unique_id"])
            if ha_entity:
                callback([ha_entity])
                async_dispatcher_send(self.hass, SIGNAL_ENTITY_ADDED, entity["unique_id"])
        else:
            _LOGGER.debug("No platform callback for %s (may not be loaded yet)", platform)
