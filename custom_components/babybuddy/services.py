"""Services for the babybuddy integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ACTION_ADD_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_CHILDREN,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    DOMAIN,
)
from .coordinator import BabyBuddyCoordinator

SERVICE_ADD_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BIRTH_DATE, default=dt_util.now().date()): cv.date,
        vol.Required(ATTR_FIRST_NAME): cv.string,
        vol.Required(ATTR_LAST_NAME): cv.string,
    }
)


async def async_add_child(call: ServiceCall) -> None:
    """Add new child."""
    for entry in call.hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )

    data = {
        ATTR_FIRST_NAME: call.data[ATTR_FIRST_NAME],
        ATTR_LAST_NAME: call.data[ATTR_LAST_NAME],
        ATTR_BIRTH_DATE: call.data[ATTR_BIRTH_DATE],
    }

    coordinator: BabyBuddyCoordinator = entry.runtime_data

    await coordinator.client.async_post(ATTR_CHILDREN, data)
    await coordinator.async_request_refresh()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the babybuddy integration."""

    hass.services.async_register(
        DOMAIN,
        ATTR_ACTION_ADD_CHILD,
        async_add_child,
        SERVICE_ADD_CHILD_SCHEMA,
    )
