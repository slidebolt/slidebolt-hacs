"""Slidebolt sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("sensor", async_add_entities)


class SlideboltSensor(SlideboltBaseEntity, SensorEntity):

    @property
    def native_value(self):
        return self._state.get("native_value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._state.get("native_unit_of_measurement")

    @property
    def device_class(self) -> str | None:
        return self._state.get("device_class")

    @property
    def state_class(self) -> str | None:
        return self._state.get("state_class")
