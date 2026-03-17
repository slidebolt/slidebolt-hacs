"""Slidebolt sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("sensor", async_add_entities)


class SlideboltSensorEntity(SlideboltBaseEntity, SensorEntity):
    _attr_has_entity_name = True

    @property
    def native_value(self):
        return self.payload.get("state", {}).get("value")

    @property
    def native_unit_of_measurement(self):
        return self.payload.get("attributes", {}).get("unit")

    @property
    def device_class(self):
        raw = self.payload.get("attributes", {}).get("device_class")
        if not raw:
            return None
        try:
            return SensorDeviceClass(raw)
        except ValueError:
            return raw
