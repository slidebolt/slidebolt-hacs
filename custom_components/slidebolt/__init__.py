"""Slidebolt integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .bridge import SlideboltBridge
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Slidebolt from a config entry."""
    bridge = SlideboltBridge(hass, entry.data["host"], entry.data["port"])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = bridge

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await bridge.async_start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Slidebolt config entry."""
    bridge: SlideboltBridge = hass.data[DOMAIN].pop(entry.entry_id)
    await bridge.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
