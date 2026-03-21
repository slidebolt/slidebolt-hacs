"""Slidebolt valve platform."""

from __future__ import annotations

from homeassistant.components.valve import ValveEntity, ValveEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("valve", async_add_entities)


class SlideboltValve(SlideboltBaseEntity, ValveEntity):

    @property
    def reports_position(self) -> bool:
        return bool(self._state.get("reports_position", False))

    @property
    def is_closed(self) -> bool | None:
        state = self._state.get("state")
        if state is not None:
            return state == "closed"
        return None

    @property
    def current_valve_position(self) -> int | None:
        return self._state.get("current_valve_position")

    @property
    def is_opening(self) -> bool:
        return self._state.get("state") == "opening"

    @property
    def is_closing(self) -> bool:
        return self._state.get("state") == "closing"

    @property
    def supported_features(self) -> ValveEntityFeature:
        return ValveEntityFeature(self._state.get("supported_features", 0))

    async def async_open_valve(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "open_valve", kwargs)

    async def async_close_valve(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "close_valve", kwargs)

    async def async_set_valve_position(self, position: int) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_valve_position", {"position": position})
