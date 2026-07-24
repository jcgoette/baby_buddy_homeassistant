"""Diagnostics support for Baby Buddy."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import ATTR_LAST_NAME, ATTR_SLUG
from .coordinator import BabyBuddyConfigEntry

# Define the sensitive keys that should be scrubbed from the output
TO_REDACT = [
    ATTR_LAST_NAME,
    ATTR_SLUG,
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BabyBuddyConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "config_entry": {
            "created_at": entry.created_at,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
            "unique_id": entry.unique_id,
            "version": entry.version,
        },
        "coordinator_data": async_redact_data(list(coordinator.data), TO_REDACT)
        if coordinator
        else None,
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: BabyBuddyConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "config_entry": {
            "created_at": entry.created_at,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
            "unique_id": entry.unique_id,
            "version": entry.version,
        },
        "device": {
            "created_at": device.created_at,
            "id": device.id,
            "identifiers": list(device.identifiers),
            "name": async_redact_data(device.name, TO_REDACT),
        },
        "coordinator_data": async_redact_data(list(coordinator.data), TO_REDACT)
        if coordinator
        else None,
    }
