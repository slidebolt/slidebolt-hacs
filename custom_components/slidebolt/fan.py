"""Slidebolt fan platform."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("fan", async_add_entities)


class SlideboltFanEntity(SlideboltBaseEntity, FanEntity):
    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.SET_SPEED

    @property
    def is_on(self):
        return bool(self.payload.get("state", {}).get("on", False))

    @property
    def percentage(self):
        return self.payload.get("state", {}).get("percentage")

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        params = {}
        if percentage is not None:
            params["percentage"] = percentage
        await self.bridge.async_send_command(self.unique_id, "turn_on", params)

    async def async_turn_off(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "turn_off", {})

    async def async_set_percentage(self, percentage: int):
        await self.bridge.async_send_command(self.unique_id, "set_percentage", {"percentage": percentage})
