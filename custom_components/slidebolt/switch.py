"""Slidebolt switch platform."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("switch", async_add_entities)


class SlideboltSwitchEntity(SlideboltBaseEntity, SwitchEntity):
    _attr_has_entity_name = True

    @property
    def is_on(self):
        return bool(self.payload.get("state", {}).get("on", False))

    async def async_turn_on(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "turn_on", {})

    async def async_turn_off(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "turn_off", {})
