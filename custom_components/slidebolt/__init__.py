"""Slidebolt custom integration."""

from __future__ import annotations

from homeassistant.helpers.discovery import async_load_platform

from .bridge import SlideboltBridge, SlideboltBridgeView
from .const import DOMAIN, PLATFORMS, SERVICE_CONFIGURE


async def async_setup(hass, config):
    """Set up the Slidebolt integration from YAML."""
    bridge = SlideboltBridge(hass)
    bridge.config = config
    hass.data[DOMAIN] = bridge
    hass.http.register_view(SlideboltBridgeView(bridge))
    hass.bus.async_listen("call_service", bridge.async_handle_service_event)

    async def handle_configure(call):
        await bridge.async_configure(
            mode=call.data.get("mode", "client"),
            url=call.data.get("url"),
            access_token=call.data.get("access_token"),
        )

    hass.services.async_register(DOMAIN, SERVICE_CONFIGURE, handle_configure)

    for platform in PLATFORMS:
        hass.async_create_task(async_load_platform(hass, platform, DOMAIN, {}, config))

    return True


async def async_setup_entry(hass, entry):
    """Set up Slidebolt from a config entry."""
    return True


async def async_unload_entry(hass, entry):
    """Unload Slidebolt config entry."""
    return True
