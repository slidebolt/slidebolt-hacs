"""Slidebolt cover platform."""

from __future__ import annotations

from homeassistant.components.cover import CoverEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("cover", async_add_entities)


class SlideboltCoverEntity(SlideboltBaseEntity, CoverEntity):
    _attr_has_entity_name = True

    @property
    def current_cover_position(self):
        return self.payload.get("state", {}).get("position", 0)

    @property
    def is_closed(self):
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "open_cover", {})

    async def async_close_cover(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "close_cover", {})

    async def async_set_cover_position(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "set_cover_position", {"position": kwargs["position"]})
