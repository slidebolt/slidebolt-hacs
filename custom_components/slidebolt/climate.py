"""Slidebolt climate platform."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("climate", async_add_entities)


class SlideboltClimate(SlideboltBaseEntity, ClimateEntity):

    @property
    def hvac_mode(self) -> HVACMode | None:
        mode = self._state.get("hvac_mode")
        return HVACMode(mode) if mode else None

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [HVACMode(m) for m in self._state.get("hvac_modes", [])]

    @property
    def current_temperature(self) -> float | None:
        return self._state.get("current_temperature")

    @property
    def target_temperature(self) -> float | None:
        return self._state.get("target_temperature")

    @property
    def temperature_unit(self) -> str:
        return self._state.get("temperature_unit", "°C")

    @property
    def target_temperature_step(self) -> float | None:
        return self._state.get("target_temperature_step")

    @property
    def min_temp(self) -> float | None:
        return self._state.get("min_temp")

    @property
    def max_temp(self) -> float | None:
        return self._state.get("max_temp")

    @property
    def supported_features(self) -> ClimateEntityFeature:
        return ClimateEntityFeature(self._state.get("supported_features", 0))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_hvac_mode", {"hvac_mode": str(hvac_mode)})

    async def async_set_temperature(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_temperature", kwargs)
