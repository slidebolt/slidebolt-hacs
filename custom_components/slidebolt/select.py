"""Slidebolt select platform."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("select", async_add_entities)


class SlideboltSelectEntity(SlideboltBaseEntity, SelectEntity):
    _attr_has_entity_name = True

    @property
    def current_option(self):
        return self.payload.get("state", {}).get("option")

    @property
    def options(self):
        return self.payload.get("attributes", {}).get("options", [])

    async def async_select_option(self, option: str) -> None:
        await self.bridge.async_send_command(self.unique_id, "select_option", {"option": option})
