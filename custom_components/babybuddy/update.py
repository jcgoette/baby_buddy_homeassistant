"""Update platform for babybuddy integration.

Like the Frigate integration, the server reports both its own version and the
latest release (``/api/version``); this entity only displays them. Servers
without that endpoint get no update entity.
"""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PATH, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LATEST_VERSION,
    ATTR_RELEASE_URL,
    ATTR_VERSION,
    BABY_BUDDY_RELEASE_TAG_URL,
    DEFAULT_NAME,
    LATEST_VERSION_NOT_AVAILABLE,
    LOGGER,
)
from .coordinator import (
    BabyBuddyConfigEntry,
    BabyBuddyVersionCoordinator,
    get_server_device_identifier,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy server update entity."""
    client = entry.runtime_data.coordinator.client
    if ATTR_VERSION not in client.endpoints:
        LOGGER.info(
            "This Baby Buddy server does not report its version (no /api/version"
            " endpoint); no update entity is created"
        )
        return

    coordinator = BabyBuddyVersionCoordinator(hass, entry, client)
    await coordinator.async_refresh()
    async_add_entities([BabyBuddyServerUpdate(coordinator, entry)])


class BabyBuddyServerUpdate(
    CoordinatorEntity[BabyBuddyVersionCoordinator], UpdateEntity
):
    """Baby Buddy server version (informational, cannot install)."""

    _attr_has_entity_name = True
    _attr_name = "Server"
    _attr_title = DEFAULT_NAME

    def __init__(
        self, coordinator: BabyBuddyVersionCoordinator, entry: BabyBuddyConfigEntry
    ) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_API_KEY]}-update"
        self._attr_device_info = DeviceInfo(
            identifiers={get_server_device_identifier(entry)},
            name=DEFAULT_NAME,
            manufacturer=DEFAULT_NAME,
            model="Server",
            configuration_url=f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}{entry.data[CONF_PATH]}/",
            sw_version=self.installed_version,
        )

    @property
    def installed_version(self) -> str | None:
        """Version the server is running."""
        if not self.coordinator.data:
            return None
        version = self.coordinator.data.get(ATTR_VERSION)
        return str(version) if version else None

    @property
    def latest_version(self) -> str | None:
        """Latest released version, as checked by the server."""
        if not self.coordinator.data:
            return None
        version = self.coordinator.data.get(ATTR_LATEST_VERSION)
        if not version or version in LATEST_VERSION_NOT_AVAILABLE:
            return None
        return str(version)

    @property
    def release_url(self) -> str | None:
        """URL of the latest release's notes."""
        if (version := self.latest_version) is None:
            return None
        return self.coordinator.data.get(
            ATTR_RELEASE_URL
        ) or BABY_BUDDY_RELEASE_TAG_URL.format(version=version)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Keep the server device's software version current."""
        version = self.installed_version
        if (
            version is not None
            and self.device_entry is not None
            and self.device_entry.sw_version != version
        ):
            dr.async_get(self.hass).async_update_device(
                self.device_entry.id, sw_version=version
            )
        super()._handle_coordinator_update()
