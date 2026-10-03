"""Test Baby Buddy stable unique id helpers."""

from custom_components.babybuddy.const import ATTR_TIMER
from custom_components.babybuddy.unique_id import (
    build_entity_unique_id,
    build_entry_unique_id,
    parse_child_id_from_unique_id,
    parse_endpoint_from_unique_id,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PATH, CONF_PORT


def test_entry_unique_id_ignores_api_key() -> None:
    """Rotating the API key should not create a new config entry identity."""

    first = {
        CONF_HOST: "http://baby.local",
        CONF_PORT: 8000,
        CONF_PATH: "/bb",
        CONF_API_KEY: "old-token",
    }
    second = {**first, CONF_API_KEY: "new-token"}

    assert build_entry_unique_id(first) == build_entry_unique_id(second)


def test_entity_unique_ids_ignore_api_key_and_remain_parseable() -> None:
    """Entity ids should stay stable across API key rotation."""

    first = {
        CONF_HOST: "http://baby.local",
        CONF_PORT: 8000,
        CONF_PATH: "/bb",
        CONF_API_KEY: "old-token",
    }
    second = {**first, CONF_API_KEY: "new-token"}

    old_data_sensor = build_entity_unique_id(first, 12, "head-circumference")
    new_data_sensor = build_entity_unique_id(second, 12, "head-circumference")
    timer = build_entity_unique_id(second, 12, ATTR_TIMER)

    assert old_data_sensor == new_data_sensor
    assert parse_child_id_from_unique_id(new_data_sensor) == 12
    assert parse_endpoint_from_unique_id(new_data_sensor) == "head-circumference"
    assert parse_endpoint_from_unique_id(timer) == ATTR_TIMER


def test_old_api_key_unique_ids_still_parse_for_service_targets() -> None:
    """Legacy registry entries should keep resolving service target child ids."""

    assert parse_child_id_from_unique_id("oldtoken-34") == 34
    assert parse_child_id_from_unique_id("oldtoken-34-timer") == 34
    assert parse_endpoint_from_unique_id("oldtoken-34-head-circumference") == "head-circumference"
