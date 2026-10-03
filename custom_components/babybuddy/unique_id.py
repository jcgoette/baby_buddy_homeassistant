"""Stable unique id helpers for Baby Buddy entities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.const import CONF_HOST, CONF_PATH, CONF_PORT

from .const import DEFAULT_PATH, DEFAULT_PORT

_UNIQUE_ID_SEPARATOR = "|"
_UNIQUE_ID_PREFIX = "babybuddy"


def build_entry_unique_id(data: Mapping[str, Any]) -> str:
    """Build a config-entry identity that survives API key rotation."""
    host = str(data[CONF_HOST]).rstrip("/")
    port = data.get(CONF_PORT, DEFAULT_PORT)
    path = str(data.get(CONF_PATH, DEFAULT_PATH) or DEFAULT_PATH).strip("/")
    path_suffix = f"/{path}" if path else ""
    return f"{host}:{port}{path_suffix}"


def build_entity_unique_id(
    config_data: Mapping[str, Any],
    child_id: int | str | None = None,
    endpoint: str | None = None,
) -> str:
    """Build an entity unique id that does not include the API key."""
    parts = [_UNIQUE_ID_PREFIX, build_entry_unique_id(config_data)]
    if child_id is not None:
        parts.append(str(child_id))
    if endpoint is not None:
        parts.append(endpoint)
    return _UNIQUE_ID_SEPARATOR.join(parts)


def parse_child_id_from_unique_id(unique_id: str) -> int:
    """Return a child id from current or legacy entity unique ids."""
    if unique_id.startswith(f"{_UNIQUE_ID_PREFIX}{_UNIQUE_ID_SEPARATOR}"):
        parts = unique_id.split(_UNIQUE_ID_SEPARATOR)
        return int(parts[2])

    return int(unique_id.split("-", 2)[1])


def parse_endpoint_from_unique_id(unique_id: str) -> str | None:
    """Return an endpoint suffix from current or legacy entity unique ids."""
    if unique_id.startswith(f"{_UNIQUE_ID_PREFIX}{_UNIQUE_ID_SEPARATOR}"):
        parts = unique_id.split(_UNIQUE_ID_SEPARATOR, 3)
        return parts[3] if len(parts) > 3 else None

    parts = unique_id.split("-", 2)
    return parts[2] if len(parts) > 2 else None


def migrate_legacy_entity_unique_id(
    config_data: Mapping[str, Any], unique_id: str
) -> str | None:
    """Convert an API-key-prefixed entity unique id to the stable format."""
    if unique_id.startswith(f"{_UNIQUE_ID_PREFIX}{_UNIQUE_ID_SEPARATOR}"):
        return None

    parts = unique_id.split("-", 2)
    if len(parts) < 2:
        return None

    if parts[1].isdigit():
        endpoint = parts[2] if len(parts) > 2 else None
        return build_entity_unique_id(config_data, parts[1], endpoint)

    return build_entity_unique_id(config_data, endpoint=parts[1])
