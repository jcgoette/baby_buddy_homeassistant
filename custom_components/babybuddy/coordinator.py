"""Initialization for babybuddy integration."""

from __future__ import annotations

from asyncio import TimeoutError as AsyncIOTimeoutError
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from aiohttp.client_exceptions import ClientError, ClientResponseError
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ID,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .client import BabyBuddyClient
from .const import (
    ATTR_ACTION_ADD_CHILD,
    ATTR_BIRTH_DATE,
    ATTR_CHILDREN,
    ATTR_COUNT,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_RESULTS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
    SENSOR_TYPES,
)
from .errors import AuthorizationError, ConnectError

SERVICE_ADD_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BIRTH_DATE, default=dt_util.now().date()): cv.date,
        vol.Required(ATTR_FIRST_NAME): cv.string,
        vol.Required(ATTR_LAST_NAME): cv.string,
    }
)


class BabyBuddyCoordinator(DataUpdateCoordinator):
    """Coordinate retrieving and updating data from babybuddy."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the BabyBuddyData object."""
        LOGGER.debug("Initializing BabyBuddyCoordinator")
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            setup_method=self.async_setup_coordinator,
            update_method=self.async_update,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.hass = hass
        self.entry: ConfigEntry = entry
        self.client: BabyBuddyClient = BabyBuddyClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_PATH],
            entry.data[CONF_API_KEY],
            async_get_clientsession(self.hass),
        )
        self.device_registry: dr.DeviceRegistry = dr.async_get(self.hass)
        self.child_ids: list[str] = []

    async def async_set_children_from_db(self) -> None:
        """Set child_ids from HA database."""
        self.child_ids = [
            next(iter(device.identifiers))[1]
            for device in dr.async_entries_for_config_entry(
                self.device_registry, self.entry.entry_id
            )
        ]

    async def async_setup_coordinator(self) -> None:
        """Set up babybuddy."""

        try:
            await self.client.async_connect()
        except AuthorizationError as error:
            raise ConfigEntryAuthFailed from error
        except ConnectError as error:
            raise ConfigEntryNotReady(error) from error

        await self.async_set_children_from_db()

        async def async_add_child(call: ServiceCall) -> None:
            """Add new child."""
            data = {
                ATTR_FIRST_NAME: call.data[ATTR_FIRST_NAME],
                ATTR_LAST_NAME: call.data[ATTR_LAST_NAME],
                ATTR_BIRTH_DATE: call.data[ATTR_BIRTH_DATE],
            }
            await self.client.async_post(ATTR_CHILDREN, data)
            await self.async_request_refresh()

        self.hass.services.async_register(
            DOMAIN,
            ATTR_ACTION_ADD_CHILD,
            async_add_child,
            schema=SERVICE_ADD_CHILD_SCHEMA,
        )

        self.entry.async_on_unload(
            self.entry.add_update_listener(options_updated_listener)
        )

    async def async_remove_deleted_children(self) -> None:
        """Remove child device if child is removed from babybuddy."""
        for device in dr.async_entries_for_config_entry(
            self.device_registry, self.entry.entry_id
        ):
            if next(iter(device.identifiers))[1] not in self.child_ids:
                self.device_registry.async_remove_device(device.id)

    async def async_update(
        self,
    ) -> tuple[list[dict[str, str]], dict[int, dict[str, dict[str, str]]]]:
        """Update babybuddy data."""
        children_list: dict[str, Any] = {}
        child_data: dict[int, dict[str, dict[str, str]]] = {}

        try:
            children_list = await self.client.async_get(ATTR_CHILDREN)
        except ClientResponseError as error:
            if error.status == HTTPStatus.FORBIDDEN:
                raise ConfigEntryAuthFailed from error
        except (AsyncIOTimeoutError, ClientError) as error:
            raise UpdateFailed(error) from error

        if children_list[ATTR_COUNT] < len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[ATTR_RESULTS]]
            await self.async_remove_deleted_children()
        if children_list[ATTR_COUNT] == 0:
            raise UpdateFailed("No children found. Please add at least one child.")
        if children_list[ATTR_COUNT] > len(self.child_ids):
            self.child_ids = [child[ATTR_ID] for child in children_list[ATTR_RESULTS]]

        for child in children_list[ATTR_RESULTS]:
            child_data.setdefault(child[ATTR_ID], {})
            for endpoint in SENSOR_TYPES:
                endpoint_data: dict = {}
                try:
                    endpoint_data = await self.client.async_get(
                        endpoint.key, f"?child={child[ATTR_ID]}&limit=1"
                    )
                except ClientResponseError as error:
                    LOGGER.debug(
                        f"No {endpoint} found for {child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}. Skipping. error: {error}.)"
                    )
                    continue
                except (AsyncIOTimeoutError, ClientError) as error:
                    LOGGER.error(error)
                    continue
                data: list[dict[str, str]] = endpoint_data[ATTR_RESULTS]
                child_data[child[ATTR_ID]][endpoint.key] = data[0] if data else {}

        return (children_list[ATTR_RESULTS], child_data)


async def options_updated_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    hass.data[DOMAIN][entry.entry_id].update_interval = timedelta(
        seconds=entry.options[CONF_SCAN_INTERVAL]
    )
    await hass.data[DOMAIN][entry.entry_id].async_request_refresh()
