"""Config flow for babybuddy integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    TEMPERATURE,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .client import BabyBuddyClient
from .const import (
    CONF_FEEDING_UNIT,
    CONF_WEIGHT_UNIT,
    CONFIG_FLOW_VERSION,
    DEFAULT_NAME,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .errors import AuthorizationError, ConnectError

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class BabyBuddyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle babybuddy config flow."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BabyBuddyOptionsFlowHandler:
        """Get the options flow for this handler."""
        return BabyBuddyOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initiate config flow."""
        self._reauth_unique_id = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                client: BabyBuddyClient = BabyBuddyClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_PATH],
                    user_input[CONF_API_KEY],
                    self.hass.helpers.aiohttp_client.async_get_clientsession(),
                )
                await client.async_connect()
            except AuthorizationError:
                errors["api_key"] = "invalid_auth"
            except ConnectError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_unique_id = self.context["unique_id"]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        errors = {}
        existing_entry = await self.async_set_unique_id(self._reauth_unique_id)
        if user_input is not None and existing_entry is not None:
            user_input[CONF_HOST] = existing_entry.data[CONF_HOST]
            user_input[CONF_PORT] = existing_entry.data[CONF_PORT]
            user_input[CONF_PATH] = existing_entry.data[CONF_PATH]
            try:
                client: BabyBuddyClient = BabyBuddyClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_PATH],
                    user_input[CONF_API_KEY],
                    self.hass.helpers.aiohttp_client.async_get_clientsession(),
                )
                await client.async_connect()
            except ConnectError:
                errors["base"] = "cannot_connect"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    existing_entry,
                    data={**existing_entry.data, **user_input},
                )
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


@dataclass
class BabyBuddyOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle babybuddy options."""

    config_entry: config_entries.ConfigEntry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage babybuddy options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                TEMPERATURE,
                default=self.config_entry.options.get(TEMPERATURE, None),
            ): vol.In([UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT]),
            vol.Optional(
                CONF_WEIGHT_UNIT,
                default=self.config_entry.options.get(CONF_WEIGHT_UNIT, None),
            ): vol.In([UnitOfMass.KILOGRAMS, UnitOfMass.POUNDS, UnitOfMass.OUNCES]),
            vol.Optional(
                CONF_FEEDING_UNIT,
                default=self.config_entry.options.get(CONF_FEEDING_UNIT, None),
            ): vol.In([UnitOfVolume.MILLILITERS, UnitOfVolume.FLUID_OUNCES]),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): int,
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
