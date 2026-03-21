"""Slidebolt fan platform."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("fan", async_add_entities)


class SlideboltFan(SlideboltBaseEntity, FanEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def percentage(self) -> int | None:
        return self._state.get("percentage")

    @property
    def supported_features(self) -> FanEntityFeature:
        return FanEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", kwargs)

    async def async_set_percentage(self, percentage: int) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_percentage", {"percentage": percentage})
