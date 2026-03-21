"""Config flow for Slidebolt."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow

from .const import DEFAULT_PORT, DOMAIN
from .bridge import async_hello

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="127.0.0.1"): str,
        vol.Required("port", default=DEFAULT_PORT): int,
    }
)


class SlideboltConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for connecting to a Slidebolt server."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._discovered_host: str | None = None
        self._discovered_port: int | None = None

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle zeroconf discovery."""
        host = str(discovery_info.ip_address)
        port = discovery_info.port or DEFAULT_PORT

        # Use the stable hardware-derived ID from the TXT record so HA updates
        # the existing config entry (with the new port) rather than creating a
        # duplicate when the service restarts on a different port.
        unique_id = discovery_info.properties.get("id") or f"{host}:{port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(
            updates={"host": host, "port": port},
            reload_on_update=True,
        )

        self._discovered_host = host
        self._discovered_port = port

        self.context["title_placeholders"] = {"host": host, "port": str(port)}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        """Confirm zeroconf discovery."""
        errors = {}

        if user_input is not None:
            host = self._discovered_host
            port = self._discovered_port
            try:
                has_token = await async_hello(host, port)
            except Exception:
                _LOGGER.exception("Failed to connect to discovered Slidebolt server")
                errors["base"] = "cannot_connect"
            else:
                if not has_token:
                    errors["base"] = "no_token"
                else:
                    return self.async_create_entry(
                        title="Slidebolt",
                        data={"host": host, "port": port},
                    )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "host": self._discovered_host,
                "port": str(self._discovered_port),
            },
            errors=errors,
        )

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        errors = {}

        if user_input is not None:
            host = user_input["host"]
            port = user_input["port"]

            # Prevent duplicate entries
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            try:
                has_token = await async_hello(host, port)
            except Exception:
                _LOGGER.exception("Failed to connect to Slidebolt server")
                errors["base"] = "cannot_connect"
            else:
                if not has_token:
                    errors["base"] = "no_token"
                else:
                    return self.async_create_entry(
                        title="Slidebolt",
                        data={"host": host, "port": port},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
