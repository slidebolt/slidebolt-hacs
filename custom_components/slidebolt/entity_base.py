"""Base entity helpers for Slidebolt."""

from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import SIGNAL_ENTITY_UPDATED


class SlideboltBaseEntity(Entity):
    """Shared entity wrapper around plugin-owned payloads."""

    _attr_should_poll = False

    def __init__(self, bridge, unique_id: str) -> None:
        self.bridge = bridge
        self.unique_id = unique_id
        self._attr_unique_id = unique_id
        entity_id = bridge.payload(unique_id).get("entity_id")
        self._attr_entity_id = entity_id
        if entity_id and "." in entity_id:
            self._attr_suggested_object_id = entity_id.split(".", 1)[1]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ENTITY_UPDATED,
                self._handle_update_signal,
            )
        )
        self.async_schedule_update_ha_state(True)

    @property
    def payload(self):
        return self.bridge.payload(self.unique_id)

    @property
    def available(self) -> bool:
        return bool(self.payload.get("available", True))

    @property
    def name(self):
        return self.payload.get("name")

    def _handle_update_signal(self, changed_unique_id):
        if changed_unique_id is None or changed_unique_id == self.unique_id:
            self.schedule_update_ha_state()
