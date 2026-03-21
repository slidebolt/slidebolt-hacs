"""Slidebolt camera platform."""

from __future__ import annotations

import aiohttp

from homeassistant.components.camera import Camera, CameraEntityFeature

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("camera", async_add_entities)


class SlideboltCamera(SlideboltBaseEntity, Camera):

    def __init__(self, bridge, unique_id: str) -> None:
        SlideboltBaseEntity.__init__(self, bridge, unique_id)
        Camera.__init__(self)

    @property
    def is_streaming(self) -> bool:
        return bool(self._state.get("is_streaming", False))

    @property
    def is_recording(self) -> bool:
        return bool(self._state.get("is_recording", False))

    @property
    def motion_detection_enabled(self) -> bool:
        return bool(self._state.get("motion_detection_enabled", False))

    @property
    def supported_features(self) -> CameraEntityFeature:
        return CameraEntityFeature(self._state.get("supported_features", 0))

    async def stream_source(self) -> str | None:
        return self._state.get("stream_source")

    async def async_camera_image(self, width=None, height=None) -> bytes | None:
        url = self._state.get("snapshot_url")
        if not url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception:
            pass
        return None

    async def async_turn_on(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", {})

    async def async_turn_off(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", {})

    async def async_enable_motion_detection(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "enable_motion_detection", {})

    async def async_disable_motion_detection(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "disable_motion_detection", {})

    async def async_perform_ptz(self, movement: str, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "ptz", {"movement": movement, **kwargs})
