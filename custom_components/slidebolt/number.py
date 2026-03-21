"""Slidebolt number platform."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("number", async_add_entities)


class SlideboltNumber(SlideboltBaseEntity, NumberEntity):

    @property
    def native_value(self) -> float | None:
        return self._state.get("native_value")

    @property
    def native_min_value(self) -> float | None:
        return self._state.get("native_min_value")

    @property
    def native_max_value(self) -> float | None:
        return self._state.get("native_max_value")

    @property
    def native_step(self) -> float | None:
        return self._state.get("native_step")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._state.get("native_unit_of_measurement")

    @property
    def mode(self) -> str | None:
        return self._state.get("mode")

    async def async_set_native_value(self, value: float) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_native_value", {"value": value})
