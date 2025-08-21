"""Initialization for babybuddy integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PATH
from homeassistant.core import HomeAssistant

from .const import (
    ATTR_ACTION_ADD_CHILD,
    CONFIG_FLOW_VERSION,
    DEFAULT_PATH,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator, BabyBuddyData

# async_setup is for the initial setup of the integration itself


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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload babybuddy entry from entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, ATTR_ACTION_ADD_CHILD)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    LOGGER.debug(f"Migrating from ConfigFlow version {entry.version}.")

    if entry.version == 1:
        new = {**entry.data}
        new[CONF_PATH] = DEFAULT_PATH

        hass.config_entries.async_update_entry(
            entry, version=CONFIG_FLOW_VERSION, data=new
        )

    LOGGER.info(
        f"Migration to ConfigFlow version {entry.version} successful.",
    )

    return True
