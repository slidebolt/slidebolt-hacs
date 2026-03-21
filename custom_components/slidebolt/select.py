"""Slidebolt select platform."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("select", async_add_entities)


class SlideboltSelect(SlideboltBaseEntity, SelectEntity):

    @property
    def current_option(self) -> str | None:
        return self._state.get("current_option")

    @property
    def options(self) -> list[str]:
        return self._state.get("options", [])

    async def async_select_option(self, option: str) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "select_option", {"option": option})
