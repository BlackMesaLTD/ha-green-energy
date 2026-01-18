"""Config flow for Green Energy integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    GreenEnergyApiClient,
    InvalidPairingCode,
    CannotConnect,
)
from .const import (
    DOMAIN,
    CONF_PAIRING_CODE,
    CONF_TOKEN,
    CONF_INSTANCE_ID,
    CONF_USER_EMAIL,
    CONF_API_URL,
    CONF_SOLAR_ENTITY,
    CONF_BATTERY_ENTITY,
    CONF_GRID_ENTITY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    DEFAULT_API_URL,
)

_LOGGER = logging.getLogger(__name__)


class GreenEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Green Energy."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._token: str | None = None
        self._instance_id: str | None = None
        self._user_email: str | None = None
        self._api_url: str = DEFAULT_API_URL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - pairing code entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            pairing_code = user_input[CONF_PAIRING_CODE].strip()
            self._api_url = user_input.get(CONF_API_URL, DEFAULT_API_URL).rstrip("/")

            api = GreenEnergyApiClient(
                session=async_get_clientsession(self.hass),
                api_url=self._api_url,
            )

            try:
                result = await api.async_pair(pairing_code)

                self._token = result["api_token"]
                self._instance_id = result["instance_id"]
                self._user_email = result.get("user_email", "Unknown")

                # Check if this instance is already configured
                await self.async_set_unique_id(self._instance_id)
                self._abort_if_unique_id_configured()

                return await self.async_step_entities()

            except InvalidPairingCode:
                errors["base"] = "invalid_code"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during pairing")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PAIRING_CODE): str,
                    vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "pairing_url": f"{DEFAULT_API_URL}/dashboard/settings?tab=connections&conn=home-assistant"
            },
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle entity selection step."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Green Energy ({self._user_email})",
                data={
                    CONF_TOKEN: self._token,
                    CONF_INSTANCE_ID: self._instance_id,
                    CONF_USER_EMAIL: self._user_email,
                    CONF_API_URL: self._api_url,
                },
                options={
                    CONF_SOLAR_ENTITY: user_input.get(CONF_SOLAR_ENTITY),
                    CONF_BATTERY_ENTITY: user_input.get(CONF_BATTERY_ENTITY),
                    CONF_GRID_ENTITY: user_input.get(CONF_GRID_ENTITY),
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                },
            )

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SOLAR_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(CONF_BATTERY_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["battery", "power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(CONF_GRID_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return GreenEnergyOptionsFlow(config_entry)


class GreenEnergyOptionsFlow(OptionsFlow):
    """Handle options flow for Green Energy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SOLAR_ENTITY,
                        default=options.get(CONF_SOLAR_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(
                        CONF_BATTERY_ENTITY,
                        default=options.get(CONF_BATTERY_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["battery", "power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(
                        CONF_GRID_ENTITY,
                        default=options.get(CONF_GRID_ENTITY),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class=["power", "energy"],
                            multiple=False,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
        )
