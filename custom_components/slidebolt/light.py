"""Slidebolt light platform."""

from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("light", async_add_entities)


class SlideboltLight(SlideboltBaseEntity, LightEntity):

    @property
    def is_on(self) -> bool:
        return bool(self._state.get("is_on", False))

    @property
    def brightness(self) -> int | None:
        return self._state.get("brightness")

    @property
    def color_mode(self) -> ColorMode | None:
        mode = self._state.get("color_mode")
        return ColorMode(mode) if mode else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        rgb = self._state.get("rgb_color")
        return tuple(rgb) if rgb else None

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._state.get("color_temp_kelvin")

    @property
    def min_color_temp_kelvin(self) -> int | None:
        return self._state.get("min_color_temp_kelvin")

    @property
    def max_color_temp_kelvin(self) -> int | None:
        return self._state.get("max_color_temp_kelvin")

    @property
    def supported_color_modes(self) -> set[ColorMode] | None:
        modes = self._state.get("supported_color_modes")
        if modes is None:
            return None
        return {ColorMode(m) for m in modes}

    @property
    def supported_features(self) -> LightEntityFeature:
        return LightEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", kwargs)
