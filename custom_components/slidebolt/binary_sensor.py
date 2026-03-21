"""Slidebolt binary sensor platform."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("binary_sensor", async_add_entities)


class SlideboltBinarySensor(SlideboltBaseEntity, BinarySensorEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def device_class(self) -> str | None:
        return self._state.get("device_class")
