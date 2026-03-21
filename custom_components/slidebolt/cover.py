"""Slidebolt cover platform."""

from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("cover", async_add_entities)


class SlideboltCover(SlideboltBaseEntity, CoverEntity):

    @property
    def supported_features(self) -> CoverEntityFeature:
        return CoverEntityFeature(self._state.get("supported_features", 0))

    @property
    def current_cover_position(self) -> int | None:
        return self._state.get("current_position")

    @property
    def is_closed(self) -> bool | None:
        state = self._state.get("state")
        if state is not None:
            return state == "closed"
        pos = self.current_cover_position
        if pos is not None:
            return pos == 0
        return None

    @property
    def is_opening(self) -> bool:
        return self._state.get("state") == "opening"

    @property
    def is_closing(self) -> bool:
        return self._state.get("state") == "closing"

    async def async_open_cover(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "open_cover", kwargs)

    async def async_close_cover(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "close_cover", kwargs)

    async def async_set_cover_position(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_cover_position", kwargs)

    async def async_stop_cover(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "stop_cover", kwargs)
