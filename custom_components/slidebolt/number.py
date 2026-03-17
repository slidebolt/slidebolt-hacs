"""Slidebolt number platform."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("number", async_add_entities)


class SlideboltNumberEntity(SlideboltBaseEntity, NumberEntity):
    _attr_has_entity_name = True

    @property
    def native_value(self):
        return self.payload.get("state", {}).get("value")

    @property
    def native_min_value(self):
        return self.payload.get("attributes", {}).get("min", 0)

    @property
    def native_max_value(self):
        return self.payload.get("attributes", {}).get("max", 100)

    @property
    def native_step(self):
        return self.payload.get("attributes", {}).get("step", 1)

    @property
    def native_unit_of_measurement(self):
        return self.payload.get("attributes", {}).get("unit")

    @property
    def device_class(self):
        raw = self.payload.get("attributes", {}).get("device_class")
        if not raw:
            return None
        try:
            return NumberDeviceClass(raw)
        except ValueError:
            return raw

    async def async_set_native_value(self, value: float) -> None:
        await self.bridge.async_send_command(self.unique_id, "set_value", {"value": value})
