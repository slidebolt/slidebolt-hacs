"""Slidebolt remote platform."""

from __future__ import annotations

from homeassistant.components.remote import RemoteEntity, RemoteEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("remote", async_add_entities)


class SlideboltRemote(SlideboltBaseEntity, RemoteEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def activity_list(self) -> list[str] | None:
        return self._state.get("activity_list")

    @property
    def current_activity(self) -> str | None:
        return self._state.get("current_activity")

    @property
    def supported_features(self) -> RemoteEntityFeature:
        return RemoteEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", kwargs)

    async def async_send_command(self, command: list[str], **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "send_command", {"command": command, **kwargs})
