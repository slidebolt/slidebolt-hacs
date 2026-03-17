"""Slidebolt button platform."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("button", async_add_entities)


class SlideboltButtonEntity(SlideboltBaseEntity, ButtonEntity):
    _attr_has_entity_name = True

    async def async_press(self) -> None:
        await self.bridge.async_send_command(self.unique_id, "press", {})
