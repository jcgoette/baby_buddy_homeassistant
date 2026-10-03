"""Initialization for babybuddy integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PATH
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONFIG_FLOW_VERSION, DEFAULT_PATH, LOGGER, PLATFORMS
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator, BabyBuddyData
from .services import async_setup_services
from .unique_id import build_entry_unique_id, migrate_legacy_entity_unique_id


# async_setup is for the initial setup of the integration itself
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up babybuddy."""
    async_setup_services(hass)
    return True


# async_setup_entry handles the setup of individual configuration
# entries created by users via the UI (i.e., Config Entry)
async def async_setup_entry(hass: HomeAssistant, entry: BabyBuddyConfigEntry) -> bool:
    """Set up the babybuddy component."""

    coordinator = BabyBuddyCoordinator(hass, entry)
    entry.runtime_data = BabyBuddyData(coordinator=coordinator, entities={})

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BabyBuddyConfigEntry) -> bool:
    """Unload babybuddy config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    LOGGER.debug(f"Migrating from ConfigFlow version {entry.version}.")

    migration_data = entry.data
    if entry.version == 1:
        migration_data = {**entry.data}
        migration_data[CONF_PATH] = DEFAULT_PATH

        hass.config_entries.async_update_entry(
            entry, version=2, data=migration_data
        )

    if entry.version < CONFIG_FLOW_VERSION:
        entity_registry = er.async_get(hass)
        for entity_entry in er.async_entries_for_config_entry(
            entity_registry, entry.entry_id
        ):
            new_unique_id = migrate_legacy_entity_unique_id(
                migration_data, entity_entry.unique_id
            )
            if new_unique_id is not None:
                entity_registry.async_update_entity(
                    entity_entry.entity_id, new_unique_id=new_unique_id
                )

        hass.config_entries.async_update_entry(
            entry,
            version=CONFIG_FLOW_VERSION,
            unique_id=build_entry_unique_id(migration_data),
        )

    LOGGER.info(
        f"Migration to ConfigFlow version {entry.version} successful.",
    )

    return True
