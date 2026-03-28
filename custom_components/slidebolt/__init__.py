"""Slidebolt integration."""

from __future__ import annotations

import logging
import uuid

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .bridge import SlideboltBridge
from .const import CONF_CLIENT_ID, CONF_HOST, CONF_PORT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Slidebolt from a config entry."""
    client_id = entry.data.get(CONF_CLIENT_ID)
    if not client_id:
        client_id = str(uuid.uuid4())
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_CLIENT_ID: client_id},
        )

    bridge = SlideboltBridge(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        client_id,
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = bridge

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await bridge.async_start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Slidebolt config entry."""
    bridge: SlideboltBridge = hass.data[DOMAIN].pop(entry.entry_id)
    await bridge.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
