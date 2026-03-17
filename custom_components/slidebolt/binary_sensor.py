"""Slidebolt binary sensor platform."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("binary_sensor", async_add_entities)


class SlideboltBinarySensorEntity(SlideboltBaseEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    @property
    def is_on(self):
        return bool(self.payload.get("state", {}).get("on", False))

    @property
    def device_class(self):
        raw = self.payload.get("attributes", {}).get("device_class")
        if not raw:
            return None
        try:
            return BinarySensorDeviceClass(raw)
        except ValueError:
            return raw
