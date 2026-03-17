"""Slidebolt climate platform."""

from __future__ import annotations

from homeassistant.components.climate import ATTR_TEMPERATURE, ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("climate", async_add_entities)


class SlideboltClimateEntity(SlideboltBaseEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def _temperature_attrs(self):
        return self.payload.get("attributes", {})

    @property
    def hvac_mode(self):
        mode = self.payload.get("state", {}).get("hvac_mode", "off")
        try:
            return HVACMode(mode)
        except ValueError:
            return HVACMode.OFF

    @property
    def target_temperature(self):
        return self.payload.get("state", {}).get("temperature")

    @property
    def temperature_unit(self):
        raw = self._temperature_attrs.get("temperature_unit")
        if raw is None:
            raw = self.payload.get("state", {}).get("temperature_unit")
        if raw == "F":
            return UnitOfTemperature.FAHRENHEIT
        if raw == "C":
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.CELSIUS

    @property
    def target_temperature_step(self):
        return 1

    @property
    def precision(self):
        return 1.0

    @property
    def min_temp(self):
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return 41
        return 5

    @property
    def max_temp(self):
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return 95
        return 35

    async def async_set_hvac_mode(self, hvac_mode):
        await self.bridge.async_send_command(self.unique_id, "set_hvac_mode", {"hvac_mode": str(hvac_mode)})

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            await self.bridge.async_send_command(
                self.unique_id,
                "set_temperature",
                {"temperature": round(kwargs[ATTR_TEMPERATURE])},
            )
