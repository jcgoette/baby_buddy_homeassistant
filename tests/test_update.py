"""Test the babybuddy server update entity."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from aiohttp.client_exceptions import ClientError
import pytest

from custom_components.babybuddy.client import BabyBuddyClient
from custom_components.babybuddy.const import ATTR_VERSION, DOMAIN
from custom_components.babybuddy.coordinator import get_server_device_identifier
from homeassistant import config_entries
from homeassistant.components.update import (
    ATTR_INSTALLED_VERSION,
    ATTR_LATEST_VERSION,
    ATTR_RELEASE_URL,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import MOCK_CONFIG

UPDATE_ENTITY_ID = "update.baby_buddy_server"

_original_async_get = BabyBuddyClient.async_get
_original_async_connect = BabyBuddyClient.async_connect


def _patch_server_version(response: dict[str, Any] | Exception | None):
    """Make the client see a server whose /api/version returns ``response``.

    ``None`` simulates a server without the endpoint (stock Baby Buddy).
    Every other request still goes to the live test server.
    """

    async def async_connect(self: BabyBuddyClient) -> None:
        await _original_async_connect(self)
        if response is None:
            self.endpoints.pop(ATTR_VERSION, None)
        else:
            self.endpoints[ATTR_VERSION] = f"{self.url}/api/version"

    async def async_get(self: BabyBuddyClient, endpoint=None, entry=None):
        if endpoint == ATTR_VERSION:
            if isinstance(response, Exception):
                raise response
            return response
        return await _original_async_get(self, endpoint, entry)

    return (
        patch.object(BabyBuddyClient, "async_connect", async_connect),
        patch.object(BabyBuddyClient, "async_get", async_get),
    )


@pytest.mark.parametrize(
    ("response", "state", "installed", "latest", "release_url"),
    [
        (
            {
                "version": "2.10.1",
                "latest_version": "2.11.0",
                "release_url": "https://example.test/notes",
            },
            STATE_ON,
            "2.10.1",
            "2.11.0",
            "https://example.test/notes",
        ),
        (
            # Older servers may omit release_url; build it from the tag.
            {"version": "2.10.1", "latest_version": "2.11.0"},
            STATE_ON,
            "2.10.1",
            "2.11.0",
            "https://github.com/babybuddy/babybuddy/releases/tag/v2.11.0",
        ),
        (
            {"version": "2.11.0", "latest_version": "2.11.0", "release_url": None},
            STATE_OFF,
            "2.11.0",
            "2.11.0",
            "https://github.com/babybuddy/babybuddy/releases/tag/v2.11.0",
        ),
        (
            {"version": "2.11.0", "latest_version": "disabled", "release_url": None},
            STATE_UNKNOWN,
            "2.11.0",
            None,
            None,
        ),
        (
            {"version": "2.11.0", "latest_version": "unknown", "release_url": None},
            STATE_UNKNOWN,
            "2.11.0",
            None,
            None,
        ),
    ],
)
async def test_update_entity_states(
    hass: HomeAssistant,
    setup_baby_buddy_entry_live,
    response,
    state,
    installed,
    latest,
    release_url,
) -> None:
    """The entity mirrors what the server reports, like Frigate's."""
    # The fixture already set up the entry against the live server; reload
    # it with the version response patched.
    entry = setup_baby_buddy_entry_live
    connect_patch, get_patch = _patch_server_version(response)
    with connect_patch, get_patch:
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    entity = hass.states.get(UPDATE_ENTITY_ID)
    assert entity is not None
    assert entity.state == state
    assert entity.attributes[ATTR_INSTALLED_VERSION] == installed
    assert entity.attributes[ATTR_LATEST_VERSION] == latest
    assert entity.attributes[ATTR_RELEASE_URL] == release_url

    device = dr.async_get(hass).async_get_device(
        identifiers={get_server_device_identifier(entry)}
    )
    assert device is not None
    assert device.name == "Baby Buddy"
    assert device.sw_version == installed


async def test_no_entity_without_version_endpoint(hass: HomeAssistant) -> None:
    """A stock server (no /api/version) gets no update entity."""
    connect_patch, get_patch = _patch_server_version(None)
    with connect_patch, get_patch:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
        await hass.async_block_till_done()

    assert result["result"].state is ConfigEntryState.LOADED
    assert hass.states.get(UPDATE_ENTITY_ID) is None


async def test_version_request_failure(
    hass: HomeAssistant, setup_baby_buddy_entry_live
) -> None:
    """A failed version read makes the entity unavailable, not the entry."""
    entry = setup_baby_buddy_entry_live
    connect_patch, get_patch = _patch_server_version(ClientError("boom"))
    with connect_patch, get_patch:
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    entity = hass.states.get(UPDATE_ENTITY_ID)
    assert entity is not None
    assert entity.state == STATE_UNAVAILABLE


async def test_server_device_is_not_treated_as_child(
    hass: HomeAssistant, setup_baby_buddy_entry_live
) -> None:
    """Child bookkeeping must not count or delete the server device."""
    entry = setup_baby_buddy_entry_live
    connect_patch, get_patch = _patch_server_version(
        {"version": "2.11.0", "latest_version": "2.11.0", "release_url": None}
    )
    with connect_patch, get_patch:
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = entry.runtime_data.coordinator
        server_id = get_server_device_identifier(entry)[1]
        assert server_id not in coordinator.child_ids

        # Simulate a child removal pass; the server device must survive.
        await coordinator.async_remove_deleted_children()
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    registry = dr.async_get(hass)
    assert registry.async_get_device(identifiers={(DOMAIN, server_id)}) is not None
    assert server_id not in coordinator.child_ids


async def test_live_server(hass: HomeAssistant, setup_baby_buddy_entry_live) -> None:
    """Against the real test server: entity exists iff the server has the endpoint."""
    entry = setup_baby_buddy_entry_live
    await hass.async_block_till_done()
    has_endpoint = ATTR_VERSION in entry.runtime_data.coordinator.client.endpoints
    entity = hass.states.get(UPDATE_ENTITY_ID)
    if not has_endpoint:
        assert entity is None
        return
    assert entity is not None
    assert entity.attributes[ATTR_INSTALLED_VERSION]
