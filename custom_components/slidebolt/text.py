"""Slidebolt text platform."""

from __future__ import annotations

from homeassistant.components.text import TextEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("text", async_add_entities)


class SlideboltText(SlideboltBaseEntity, TextEntity):

    @property
    def native_value(self) -> str | None:
        return self._state.get("native_value")

    @property
    def native_min(self) -> int:
        return self._state.get("native_min", 0)

    @property
    def native_max(self) -> int:
        return self._state.get("native_max", 255)

    @property
    def pattern(self) -> str | None:
        return self._state.get("pattern")

    @property
    def mode(self) -> str | None:
        return self._state.get("mode")

    async def async_set_value(self, value: str) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_value", {"value": value})
