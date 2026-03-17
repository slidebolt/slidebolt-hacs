"""Slidebolt text platform."""

from __future__ import annotations

from homeassistant.components.text import TextEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("text", async_add_entities)


class SlideboltTextEntity(SlideboltBaseEntity, TextEntity):
    _attr_has_entity_name = True

    @property
    def native_value(self):
        value = self.payload.get("state", {}).get("value")
        if value in (None, ""):
            return None
        return value

    @property
    def native_min(self):
        return self.payload.get("attributes", {}).get("min", 0)

    @property
    def native_max(self):
        return self.payload.get("attributes", {}).get("max", 255)

    @property
    def pattern(self):
        return self.payload.get("attributes", {}).get("pattern")

    @property
    def mode(self):
        return self.payload.get("attributes", {}).get("mode", "text")

    async def async_set_value(self, value: str) -> None:
        await self.bridge.async_send_command(self.unique_id, "set_value", {"value": value})
