"""Slidebolt button platform."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("button", async_add_entities)


class SlideboltButton(SlideboltBaseEntity, ButtonEntity):

    @property
    def device_class(self) -> str | None:
        return self._state.get("device_class")

    async def async_press(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "press", {})
