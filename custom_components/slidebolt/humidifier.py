"""Slidebolt humidifier platform."""

from __future__ import annotations

from homeassistant.components.humidifier import HumidifierEntity, HumidifierEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("humidifier", async_add_entities)


class SlideboltHumidifier(SlideboltBaseEntity, HumidifierEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def target_humidity(self) -> int | None:
        return self._state.get("target_humidity")

    @property
    def current_humidity(self) -> int | None:
        return self._state.get("current_humidity")

    @property
    def min_humidity(self) -> int:
        return self._state.get("min_humidity", 0)

    @property
    def max_humidity(self) -> int:
        return self._state.get("max_humidity", 100)

    @property
    def mode(self) -> str | None:
        return self._state.get("mode")

    @property
    def available_modes(self) -> list[str] | None:
        return self._state.get("available_modes")

    @property
    def supported_features(self) -> HumidifierEntityFeature:
        return HumidifierEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", kwargs)

    async def async_set_humidity(self, humidity: int) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_humidity", {"humidity": humidity})

    async def async_set_mode(self, mode: str) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_mode", {"mode": mode})
