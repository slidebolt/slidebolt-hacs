"""Slidebolt lock platform."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity

from .const import DOMAIN
from .entity_base import SlideboltBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    bridge = hass.data[DOMAIN][entry.entry_id]
    await bridge.async_register_platform("lock", async_add_entities)


class SlideboltLock(SlideboltBaseEntity, LockEntity):

    @property
    def is_locked(self) -> bool | None:
        return self._state.get("is_locked")

    @property
    def is_locking(self) -> bool:
        return bool(self._state.get("is_locking", False))

    @property
    def is_unlocking(self) -> bool:
        return bool(self._state.get("is_unlocking", False))

    async def async_lock(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "lock", kwargs)

    async def async_unlock(self, **kwargs) -> None:
        await self.bridge.async_send_command(self._attr_unique_id, "unlock", kwargs)
