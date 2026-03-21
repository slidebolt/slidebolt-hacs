"""Slidebolt event platform."""

from __future__ import annotations

from homeassistant.components.event import EventEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("event", async_add_entities)


class SlideboltEvent(SlideboltBaseEntity, EventEntity):

    @property
    def event_types(self) -> list[str]:
        return self._state.get("event_types", [])

    @property
    def device_class(self) -> str | None:
        return self._state.get("device_class")

    def trigger_event(self, event_type: str, event_attributes: dict | None = None) -> None:
        """Called by the bridge when an event fires."""
        self._trigger_event(event_type, event_attributes or {})
        self.schedule_update_ha_state()
