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
from .coordinator import BabyBuddyCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the babybuddy component."""

    coordinator = BabyBuddyCoordinator(hass, config_entry)
    await coordinator.async_setup_coordinator()
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
        hass.services.async_remove(DOMAIN, ATTR_ACTION_ADD_CHILD)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""

    LOGGER.debug(f"Migrating from ConfigFlow version {config_entry.version}.")

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_PATH] = DEFAULT_PATH

        hass.config_entries.async_update_entry(
            config_entry, version=CONFIG_FLOW_VERSION, data=new
        )

    LOGGER.info(
        f"Migration to ConfigFlow version {config_entry.version} successful.",
    )

    return True
