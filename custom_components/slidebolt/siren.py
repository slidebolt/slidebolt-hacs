"""Slidebolt siren platform."""

from __future__ import annotations

from homeassistant.components.siren import SirenEntity, SirenEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("siren", async_add_entities)


class SlideboltSiren(SlideboltBaseEntity, SirenEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def available_tones(self) -> list[str] | None:
        return self._state.get("available_tones")

    @property
    def supported_features(self) -> SirenEntityFeature:
        return SirenEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", kwargs)
