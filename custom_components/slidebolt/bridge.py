"""Transport-neutral authenticated Slidebolt bridge."""

from __future__ import annotations

import asyncio
import json
import logging

import aiohttp
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_ENTITY_ADDED, SIGNAL_ENTITY_REMOVED, SIGNAL_ENTITY_UPDATED

_LOGGER = logging.getLogger(__name__)

WS_PATH = "/api/slidebolt/ws"


class SlideboltBridge:
    """Maintain an authenticated contract session with the Slidebolt plugin."""

    def __init__(self, hass) -> None:
        self.hass = hass
        self.config = {}
        self.mode = "server"
        self.url = None
        self.access_token = None
        self.session = aiohttp.ClientSession()
        self.ws = None
        self.listen_task = None
        self.entities = {}
        self.request_id = 1
        self.pending_results = {}
        self.platform_adders = {}
        self.entity_objects = {}
        self.ws_lock = asyncio.Lock()
        self.last_message_type = None
        self.last_error = None

    async def async_configure(self, mode: str = "client", url: str | None = None, access_token: str | None = None) -> None:
        self.mode = mode
        self.url = url
        self.access_token = access_token
        if self.listen_task:
            self.listen_task.cancel()
            self.listen_task = None
        await self._close_ws()
        if mode == "client":
            self.listen_task = self.hass.async_create_task(self._async_run_client())

    async def async_register_platform(self, platform: str, async_add_entities) -> None:
        self.platform_adders[platform] = async_add_entities
        current = [
            self._build_entity(payload)
            for payload in self.entities.values()
            if payload["platform"] == platform and payload["unique_id"] not in self.entity_objects
        ]
        if current:
            for entity in current:
                self.entity_objects[entity.unique_id] = entity
            async_add_entities(current)
            for entity in current:
                async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, entity.unique_id)

    def _build_entity(self, payload):
        platform = payload["platform"]
        if platform == "light":
            from .light import SlideboltLightEntity

            return SlideboltLightEntity(self, payload["unique_id"])
        if platform == "switch":
            from .switch import SlideboltSwitchEntity

            return SlideboltSwitchEntity(self, payload["unique_id"])
        if platform == "sensor":
            from .sensor import SlideboltSensorEntity

            return SlideboltSensorEntity(self, payload["unique_id"])
        if platform == "binary_sensor":
            from .binary_sensor import SlideboltBinarySensorEntity

            return SlideboltBinarySensorEntity(self, payload["unique_id"])
        if platform == "button":
            from .button import SlideboltButtonEntity

            return SlideboltButtonEntity(self, payload["unique_id"])
        if platform == "number":
            from .number import SlideboltNumberEntity

            return SlideboltNumberEntity(self, payload["unique_id"])
        if platform == "select":
            from .select import SlideboltSelectEntity

            return SlideboltSelectEntity(self, payload["unique_id"])
        if platform == "text":
            from .text import SlideboltTextEntity

            return SlideboltTextEntity(self, payload["unique_id"])
        if platform == "lock":
            from .lock import SlideboltLockEntity

            return SlideboltLockEntity(self, payload["unique_id"])
        if platform == "cover":
            from .cover import SlideboltCoverEntity

            return SlideboltCoverEntity(self, payload["unique_id"])
        if platform == "fan":
            from .fan import SlideboltFanEntity

            return SlideboltFanEntity(self, payload["unique_id"])
        if platform == "climate":
            from .climate import SlideboltClimateEntity

            return SlideboltClimateEntity(self, payload["unique_id"])
        raise ValueError(f"unsupported platform {platform}")

    async def _async_run_client(self) -> None:
        if not self.url or not self.access_token:
            return
        while True:
            try:
                ws = await self.session.ws_connect(self.url)
                if not await self._authenticate_client(ws):
                    await ws.close()
                    await asyncio.sleep(1)
                    continue
                await self._set_active_ws(ws)
                async for message in ws:
                    if message.type != aiohttp.WSMsgType.TEXT:
                        continue
                    payload = json.loads(message.data)
                    await self._handle_message(payload)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # pragma: no cover - local integration path
                self.last_error = str(err)
                _LOGGER.exception("Slidebolt bridge client connection failed: %s", err)
            finally:
                await self._close_ws()
            await asyncio.sleep(1)

    async def _authenticate_client(self, ws) -> bool:
        msg = await ws.receive_json()
        if msg.get("type") != "auth_required":
            return False
        await ws.send_json({"type": "auth", "access_token": self.access_token})
        msg = await ws.receive_json()
        return msg.get("type") == "auth_ok"

    async def async_accept_server_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_json({"type": "auth_required"})
        auth = await ws.receive_json()
        if auth.get("type") != "auth":
            await ws.send_json({"type": "auth_invalid", "message": "auth required"})
            await ws.close()
            return ws
        if not self._validate_access_token(auth.get("access_token", "")):
            await ws.send_json({"type": "auth_invalid", "message": "invalid token"})
            await ws.close()
            return ws
        await ws.send_json({"type": "auth_ok"})
        await self._set_active_ws(ws)
        try:
            async for message in ws:
                if message.type != aiohttp.WSMsgType.TEXT:
                    continue
                payload = json.loads(message.data)
                await self._handle_message(payload)
        finally:
            await self._clear_ws(ws)
        return ws

    def _validate_access_token(self, token: str) -> bool:
        refresh_token = self.hass.auth.async_validate_access_token(token)
        return refresh_token is not None

    async def _set_active_ws(self, ws) -> None:
        async with self.ws_lock:
            if self.ws is not None and self.ws is not ws:
                await self.ws.close()
            self.ws = ws

    async def _clear_ws(self, ws) -> None:
        async with self.ws_lock:
            if self.ws is ws:
                self.ws = None

    async def _handle_message(self, payload):
        msg_type = payload.get("type")
        self.last_message_type = msg_type
        if msg_type in ("auth_required", "auth", "auth_ok", "auth_invalid"):
            return
        if msg_type == "hello":
            return
        if msg_type == "ping":
            await self._send_json({"type": "pong"})
            return
        if msg_type == "snapshot":
            snapshot = payload.get("snapshot") or {}
            devices = snapshot.get("devices") or []
            next_entities = {}
            for device in devices:
                for entity in device.get("entities") or []:
                    next_entities[entity["unique_id"]] = entity
            prev_entities = self.entities
            removed = set(prev_entities) - set(next_entities)
            self.entities = next_entities
            for unique_id in removed:
                await self._remove_entity(unique_id, prev_entities.get(unique_id))
                async_dispatcher_send(self.hass, SIGNAL_ENTITY_REMOVED, unique_id)
            if self.mode == "server":
                for entity in next_entities.values():
                    self._sync_state(entity)
            await self._add_new_entities()
            async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, None)
            return
        if msg_type in ("entity_added", "entity_updated"):
            entity = payload["entity"]
            is_new = entity["unique_id"] not in self.entities
            self.entities[entity["unique_id"]] = entity
            if self.mode == "server":
                self._sync_state(entity)
            if is_new:
                await self._add_new_entities()
                await self._reconcile_entity_id(entity)
                async_dispatcher_send(self.hass, SIGNAL_ENTITY_ADDED, entity["unique_id"])
            async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, entity["unique_id"])
            return
        if msg_type == "entity_removed":
            unique_id = payload["entity_unique_id"]
            removed_entity = self.entities.pop(unique_id, None)
            await self._remove_entity(unique_id, removed_entity)
            async_dispatcher_send(self.hass, SIGNAL_ENTITY_REMOVED, unique_id)
            return
        if msg_type == "command_result":
            request_id = payload.get("request_id")
            fut = self.pending_results.pop(request_id, None)
            if fut and not fut.done():
                fut.set_result(payload)

    async def _add_new_entities(self) -> None:
        grouped = {}
        for payload in self.entities.values():
            unique_id = payload["unique_id"]
            if unique_id in self.entity_objects:
                continue
            grouped.setdefault(payload["platform"], []).append(payload)
        for platform, payloads in grouped.items():
            adder = self.platform_adders.get(platform)
            if adder is None:
                continue
            entities = []
            for payload in payloads:
                entity = self._build_entity(payload)
                self.entity_objects[payload["unique_id"]] = entity
                entities.append(entity)
            if entities:
                try:
                    self.hass.add_job(adder, entities)
                except Exception as err:
                    self.last_error = str(err)
                    raise
                await asyncio.sleep(0.1)
                for payload in payloads:
                    async_dispatcher_send(self.hass, SIGNAL_ENTITY_UPDATED, payload["unique_id"])
                    await self._reconcile_entity_id(payload)

    async def async_send_command(self, unique_id: str, command: str, params: dict | None = None) -> dict:
        if self.ws is None:
            raise RuntimeError("bridge is not connected")
        request_id = f"cmd-{self.request_id}"
        self.request_id += 1
        future = self.hass.loop.create_future()
        self.pending_results[request_id] = future
        await self._send_json(
            {
                "type": "command",
                "request_id": request_id,
                "entity_unique_id": unique_id,
                "command": command,
                "params": params or {},
            }
        )
        return await asyncio.wait_for(future, timeout=5)

    async def _send_json(self, payload: dict) -> None:
        async with self.ws_lock:
            if self.ws is None:
                raise RuntimeError("bridge is not connected")
            await self.ws.send_json(payload)

    async def _close_ws(self) -> None:
        async with self.ws_lock:
            if self.ws is not None:
                await self.ws.close()
                self.ws = None

    def payload(self, unique_id: str):
        return self.entities[unique_id]

    async def async_handle_service_event(self, event) -> None:
        if self.mode != "server":
            return
        data = event.data or {}
        domain = data.get("domain")
        service = data.get("service")
        service_data = data.get("service_data") or {}
        entity_id = service_data.get("entity_id")
        if isinstance(entity_id, list):
            entity_ids = entity_id
        elif entity_id:
            entity_ids = [entity_id]
        else:
            return
        for payload in self.entities.values():
            if payload.get("entity_id") not in entity_ids:
                continue
            params = {}
            if domain == "light":
                if "brightness" in service_data:
                    params["brightness"] = round((service_data["brightness"] / 255) * 100)
                if "rgb_color" in service_data:
                    params["rgb"] = list(service_data["rgb_color"])
                if "color_temp_kelvin" in service_data:
                    params["temperature"] = service_data["color_temp_kelvin"]
            elif domain == "number" and "value" in service_data:
                params["value"] = service_data["value"]
            elif domain == "select" and "option" in service_data:
                params["option"] = service_data["option"]
            elif domain == "text" and "value" in service_data:
                params["value"] = service_data["value"]
            elif domain == "cover":
                if "position" in service_data:
                    params["position"] = service_data["position"]
            elif domain == "fan":
                if "percentage" in service_data:
                    params["percentage"] = service_data["percentage"]
            elif domain == "climate":
                if "temperature" in service_data:
                    params["temperature"] = service_data["temperature"]
                if "hvac_mode" in service_data:
                    params["hvac_mode"] = service_data["hvac_mode"]
            await self.async_send_command(payload["unique_id"], service, params)

    async def _reconcile_entity_id(self, payload: dict) -> None:
        desired_entity_id = payload.get("entity_id")
        if not desired_entity_id:
            return
        registry = er.async_get(self.hass)
        for _ in range(20):
            entity_id = registry.async_get_entity_id(payload["platform"], "slidebolt", payload["unique_id"])
            if entity_id is None:
                await asyncio.sleep(0.1)
                continue
            if entity_id != desired_entity_id:
                existing = registry.async_get(desired_entity_id)
                if existing is not None:
                    # If HA already converged to the desired ID, don't treat
                    # re-registration as fatal during reconnect/replay.
                    return
                try:
                    registry.async_update_entity(entity_id, new_entity_id=desired_entity_id)
                except ValueError:
                    # HA can race entity registration during reconnect/replay.
                    # If the desired ID has already been claimed, treat that
                    # as converged instead of crashing the bridge session.
                    if registry.async_get(desired_entity_id) is not None:
                        return
                    raise
            return

    async def _remove_entity(self, unique_id: str, payload: dict | None = None) -> None:
        if payload is None:
            payload = self.entities.get(unique_id)
        platform = None
        entity_id = None
        if payload is not None:
            platform = payload.get("platform")
            entity_id = payload.get("entity_id")
        entity = self.entity_objects.pop(unique_id, None)
        if entity is not None and getattr(entity, "hass", None) is not None:
            await entity.async_remove()
        if entity_id and self.mode == "server":
            self.hass.states.async_remove(entity_id)
        if not platform:
            return
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id(platform, "slidebolt", unique_id)
        if entity_id is not None:
            registry.async_remove(entity_id)

    def _sync_state(self, payload: dict) -> None:
        entity_id = payload.get("entity_id")
        platform = payload.get("platform")
        state = payload.get("state") or {}
        attributes = dict(payload.get("attributes") or {})
        attributes.setdefault("friendly_name", payload.get("name"))
        if platform == "light":
            ha_state = "on" if state.get("on") else "off"
            brightness = state.get("brightness")
            if brightness is not None:
                attributes["brightness"] = max(0, min(255, round((int(brightness) / 100) * 255)))
            rgb = state.get("rgb")
            if rgb:
                attributes["rgb_color"] = list(rgb)
            temperature = state.get("temperature")
            if temperature is not None:
                attributes["color_temp_kelvin"] = temperature
        elif platform == "switch":
            ha_state = "on" if state.get("on") else "off"
        elif platform == "binary_sensor":
            ha_state = "on" if state.get("on") else "off"
        elif platform == "sensor":
            ha_state = state.get("value")
        elif platform == "number":
            ha_state = state.get("value")
            attributes["min"] = payload.get("attributes", {}).get("min", 0)
            attributes["max"] = payload.get("attributes", {}).get("max", 100)
            attributes["step"] = payload.get("attributes", {}).get("step", 1)
            if "unit" in payload.get("attributes", {}):
                attributes["unit_of_measurement"] = payload.get("attributes", {}).get("unit")
            if "device_class" in payload.get("attributes", {}):
                attributes["device_class"] = payload.get("attributes", {}).get("device_class")
        elif platform == "select":
            ha_state = state.get("option")
            attributes["options"] = payload.get("attributes", {}).get("options", [])
        elif platform == "text":
            ha_state = state.get("value")
            if "min" in payload.get("attributes", {}):
                attributes["min"] = payload.get("attributes", {}).get("min")
            if "max" in payload.get("attributes", {}):
                attributes["max"] = payload.get("attributes", {}).get("max")
            if "pattern" in payload.get("attributes", {}):
                attributes["pattern"] = payload.get("attributes", {}).get("pattern")
            if "mode" in payload.get("attributes", {}):
                attributes["mode"] = payload.get("attributes", {}).get("mode")
        elif platform == "button":
            ha_state = state.get("presses", 0)
        elif platform == "lock":
            ha_state = "locked" if state.get("locked") else "unlocked"
        elif platform == "cover":
            position = state.get("position", 0)
            ha_state = "open" if position > 0 else "closed"
            attributes["current_position"] = position
        elif platform == "fan":
            ha_state = "on" if state.get("on") else "off"
            if "percentage" in state:
                attributes["percentage"] = state.get("percentage")
        elif platform == "climate":
            ha_state = state.get("hvac_mode", "off")
            if "temperature" in state:
                attributes["temperature"] = state.get("temperature")
        else:
            return
        if entity_id:
            self.hass.states.async_set(entity_id, ha_state, attributes)


class SlideboltBridgeView(HomeAssistantView):
    """WS endpoint for plugin -> HA mode."""

    url = WS_PATH
    name = "api:slidebolt:ws"
    requires_auth = False

    def __init__(self, bridge: SlideboltBridge) -> None:
        self.bridge = bridge

    async def get(self, request: web.Request) -> web.StreamResponse:
        return await self.bridge.async_accept_server_ws(request)
