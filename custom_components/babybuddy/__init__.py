"""The babybuddy sensor integration."""  # pylint: disable=logging-fstring-interpolation
from __future__ import annotations

import logging
from asyncio import TimeoutError as AsyncIOTimeoutError
from datetime import timedelta
from http import HTTPStatus
from typing import Any

import homeassistant.util.dt as dt_util
import voluptuous as vol
from aiohttp.client_exceptions import ClientError, ClientResponseError
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
from homeassistant.helpers.device_registry import (
    DeviceRegistry,
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import BabyBuddyClient
from .const import (
    ATTR_BIRTH_DATE,
    ATTR_CHILDREN,
    ATTR_COUNT,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_RESULTS,
    CONFIG_FLOW_VERSION,
    DEFAULT_PATH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SENSOR_TYPES,
)
from .errors import AuthorizationError, ConnectError

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BIRTH_DATE, default=dt_util.now().date()): cv.date,
        vol.Required(ATTR_FIRST_NAME): cv.string,
        vol.Required(ATTR_LAST_NAME): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the babybuddy component."""

    coordinator = BabyBuddyCoordinator(hass, config_entry)
    await coordinator.async_setup()
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload babybuddy entry from config_entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "add_child")

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    _LOGGER.debug(f"Migrating from ConfigFlow version {config_entry.version}.")

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_PATH] = DEFAULT_PATH

        config_entry.version = CONFIG_FLOW_VERSION
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info(
        f"Migration to ConfigFlow version {config_entry.version} successful.",
    )

    return True


class BabyBuddyCoordinator(DataUpdateCoordinator):
    """Coordinate retrieving and updating data from babybuddy."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the BabyBuddyData object."""
        _LOGGER.debug("Initializing BabyBuddyCoordinator")
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self.async_update,
            update_interval=timedelta(
                seconds=config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self.client: BabyBuddyClient = BabyBuddyClient(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_PORT],
            config_entry.data[CONF_PATH],
            config_entry.data[CONF_API_KEY],
            hass.helpers.aiohttp_client.async_get_clientsession(),
        )
        self.device_registry: DeviceRegistry = async_get(self.hass)
        self.child_ids: list[str] = []

    async def async_set_children_from_db(self) -> None:
        """Set child_ids from HA database."""
        self.child_ids = [
            next(iter(device.identifiers))[1]
            for device in async_entries_for_config_entry(
                self.device_registry, self.config_entry.entry_id
            )
        ]

    async def async_setup(self) -> None:
        """Set up babybuddy."""

        try:
            await self.client.async_connect()
        except AuthorizationError as err:
            raise ConfigEntryAuthFailed from err
        except ConnectError as err:
            raise ConfigEntryNotReady(err) from err

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
            DOMAIN, "add_child", async_add_child, schema=SERVICE_ADD_CHILD_SCHEMA
        )

        self.config_entry.async_on_unload(
            self.config_entry.add_update_listener(options_updated_listener)
        )

    async def async_remove_deleted_children(self) -> None:
        """Remove child device if child is removed from babybuddy."""
        for device in async_entries_for_config_entry(
            self.device_registry, self.config_entry.entry_id
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
        except ClientResponseError as err:
            if err.status == HTTPStatus.FORBIDDEN:
                raise ConfigEntryAuthFailed from err
        except (AsyncIOTimeoutError, ClientError) as err:
            raise UpdateFailed(err) from err

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
                except ClientResponseError as err:
                    _LOGGER.debug(
                        f"No {endpoint} found for {child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}. Skipping"
                    )
                    continue
                except (AsyncIOTimeoutError, ClientError) as err:
                    _LOGGER.error(err)
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
