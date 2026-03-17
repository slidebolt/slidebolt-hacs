"""Slidebolt lock platform."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity

from .entity_base import SlideboltBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await hass.data["slidebolt"].async_register_platform("lock", async_add_entities)


class SlideboltLockEntity(SlideboltBaseEntity, LockEntity):
    _attr_has_entity_name = True

    @property
    def is_locked(self):
        return bool(self.payload.get("state", {}).get("locked", False))

    async def async_lock(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "lock", {})

    async def async_unlock(self, **kwargs):
        await self.bridge.async_send_command(self.unique_id, "unlock", {})
