"""Slidebolt light platform."""

from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Slidebolt light platform."""
    await hass.data["slidebolt"].async_register_platform("light", async_add_entities)


class SlideboltLightEntity(SlideboltBaseEntity, LightEntity):
    """HA light rendered from plugin-owned contract data."""

    _attr_has_entity_name = True
    _attr_min_color_temp_kelvin = 2000
    _attr_max_color_temp_kelvin = 6535

    @property
    def is_on(self):
        return bool(self.payload.get("state", {}).get("on", False))

    @property
    def brightness(self):
        brightness = self.payload.get("state", {}).get("brightness")
        if brightness is None:
            return None
        return max(0, min(255, round((int(brightness) / 100) * 255)))

    @property
    def rgb_color(self):
        rgb = self.payload.get("state", {}).get("rgb")
        if not rgb:
            return None
        return tuple(rgb)

    @property
    def color_temp_kelvin(self):
        return self.payload.get("state", {}).get("temperature")

    @property
    def supported_color_modes(self):
        features = self.payload.get("features", {})
        modes = set()
        if features.get("rgb"):
            modes.add(ColorMode.RGB)
        if features.get("temperature"):
            modes.add(ColorMode.COLOR_TEMP)
        if not modes and features.get("brightness"):
            modes.add(ColorMode.BRIGHTNESS)
        if not modes:
            modes.add(ColorMode.ONOFF)
        return modes

    @property
    def color_mode(self):
        state = self.payload.get("state", {})
        if state.get("rgb"):
            return ColorMode.RGB
        if state.get("temperature"):
            return ColorMode.COLOR_TEMP
        if self.payload.get("features", {}).get("brightness"):
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    async def async_turn_on(self, **kwargs):
        params = {}
        if "brightness" in kwargs:
            params["brightness"] = round((kwargs["brightness"] / 255) * 100)
        if "rgb_color" in kwargs:
            params["rgb"] = list(kwargs["rgb_color"])
        if "color_temp_kelvin" in kwargs:
            params["temperature"] = kwargs["color_temp_kelvin"]
        await self.bridge.async_send_command(self.unique_id, "turn_on", params)

    async def async_turn_off(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "turn_off", {})
