"""Slidebolt media player platform."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("media_player", async_add_entities)


class SlideboltMediaPlayer(SlideboltBaseEntity, MediaPlayerEntity):

    @property
    def state(self) -> MediaPlayerState | None:
        s = self._state.get("state")
        return MediaPlayerState(s) if s else None

    @property
    def volume_level(self) -> float | None:
        return self._state.get("volume_level")

    @property
    def is_volume_muted(self) -> bool | None:
        return self._state.get("is_volume_muted")

    @property
    def media_title(self) -> str | None:
        return self._state.get("media_title")

    @property
    def media_artist(self) -> str | None:
        return self._state.get("media_artist")

    @property
    def media_duration(self) -> int | None:
        return self._state.get("media_duration")

    @property
    def media_position(self) -> int | None:
        return self._state.get("media_position")

    @property
    def source(self) -> str | None:
        return self._state.get("source")

    @property
    def source_list(self) -> list[str] | None:
        return self._state.get("source_list")

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return MediaPlayerEntityFeature(self._state.get("supported_features", 0))

    async def async_turn_on(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_on", {})

    async def async_turn_off(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "turn_off", {})

    async def async_media_play(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "media_play", {})

    async def async_media_pause(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "media_pause", {})

    async def async_media_stop(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "media_stop", {})

    async def async_media_next_track(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "media_next_track", {})

    async def async_media_previous_track(self) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "media_previous_track", {})

    async def async_set_volume_level(self, volume: float) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "set_volume_level", {"volume_level": volume})

    async def async_mute_volume(self, mute: bool) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "mute_volume", {"is_volume_muted": mute})

    async def async_select_source(self, source: str) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "select_source", {"source": source})
