"""Config flow for Slidebolt."""

from __future__ import annotations

import logging
import uuid

import voluptuous as vol

from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow

from .const import CONF_CLIENT_ID, CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN
from .bridge import async_hello

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="127.0.0.1"): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class SlideboltConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for connecting to a Slidebolt server."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._discovered_host: str | None = None
        self._discovered_port: int | None = None
        self._client_id: str = str(uuid.uuid4())

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
                auth_ok, _server_id = await async_hello(host, port, self._client_id)
            except Exception:
                _LOGGER.exception("Failed to connect to discovered Slidebolt server")
                errors["base"] = "cannot_connect"
            else:
                if not auth_ok:
                    errors["base"] = "invalid_auth"
                else:
                    return self.async_create_entry(
                        title="Slidebolt",
                        data={CONF_HOST: host, CONF_PORT: port, CONF_CLIENT_ID: self._client_id},
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
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                auth_ok, server_id = await async_hello(host, port, self._client_id)
            except Exception:
                _LOGGER.exception("Failed to connect to Slidebolt server")
                errors["base"] = "cannot_connect"
            else:
                if not auth_ok:
                    errors["base"] = "invalid_auth"
                else:
                    # Use the same server_id that zeroconf uses so both flows
                    # resolve to a single config entry.
                    unique_id = server_id or f"{host}:{port}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Slidebolt",
                        data={CONF_HOST: host, CONF_PORT: port, CONF_CLIENT_ID: self._client_id},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Allow the user to edit host/port of an existing entry."""
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            client_id = entry.data.get(CONF_CLIENT_ID, str(uuid.uuid4()))

            try:
                auth_ok, server_id = await async_hello(host, port, client_id)
            except Exception:
                _LOGGER.exception("Failed to connect to Slidebolt server")
                errors["base"] = "cannot_connect"
            else:
                if not auth_ok:
                    errors["base"] = "invalid_auth"
                else:
                    if server_id:
                        await self.async_set_unique_id(server_id)
                    return self.async_update_reload_and_abort(
                        entry,
                        data={CONF_HOST: host, CONF_PORT: port, CONF_CLIENT_ID: client_id},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST, "127.0.0.1")): str,
                vol.Required(CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )
