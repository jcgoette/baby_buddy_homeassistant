"""Platform for babybuddy binary switch integration."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_NAME, CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .client import get_datetime_from_time
from .const import (
    ATTR_ACTION_ADD_FEEDING,
    ATTR_ACTION_ADD_PUMPING,
    ATTR_ACTION_ADD_SLEEP,
    ATTR_ACTION_ADD_TUMMY_TIME,
    ATTR_AMOUNT,
    ATTR_CHILD,
    ATTR_END,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_ICON_TIMER_SAND,
    ATTR_LAST_NAME,
    ATTR_METHOD,
    ATTR_MILESTONE,
    ATTR_NAP,
    ATTR_NOTES,
    ATTR_PUMPING,
    ATTR_SLEEP,
    ATTR_START,
    ATTR_TAGS,
    ATTR_TIMER,
    ATTR_TIMERS,
    ATTR_TUMMY_TIMES,
    ATTR_TYPE,
    DOMAIN,
    FEEDING_METHODS,
    FEEDING_TYPES,
    LOGGER,
)
from .coordinator import BabyBuddyCoordinator
from .errors import ValidationError

COMMON_FIELDS: dict[vol.Optional | vol.Exclusive, Any] = {
    vol.Exclusive(ATTR_TIMER, group_of_exclusion="timer_or_start"): cv.boolean,
    vol.Exclusive(ATTR_START, group_of_exclusion="timer_or_start"): vol.Any(
        cv.datetime, cv.time
    ),
    vol.Optional(ATTR_END): vol.Any(cv.datetime, cv.time),
    vol.Optional(ATTR_TAGS): vol.All(cv.ensure_list, [str]),
}


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy switches."""
    coordinator: BabyBuddyCoordinator = entry.runtime_data
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update the status of entities."""
        update_items(coordinator, tracked, async_add_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "start_timer",
        {
            vol.Optional(ATTR_START): vol.Any(cv.datetime, cv.time),
            vol.Optional(ATTR_NAME): cv.string,
        },
        "async_start_timer",
    )

    platform.async_register_entity_service(
        ATTR_ACTION_ADD_FEEDING,
        {
            **COMMON_FIELDS,
            vol.Required(ATTR_TYPE): vol.In(FEEDING_TYPES),
            vol.Required(ATTR_METHOD): vol.In(FEEDING_METHODS),
            vol.Optional(ATTR_AMOUNT): cv.positive_float,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        f"async_{ATTR_ACTION_ADD_FEEDING}",
    )
    platform.async_register_entity_service(
        ATTR_ACTION_ADD_PUMPING,
        {
            **COMMON_FIELDS,
            vol.Required(ATTR_AMOUNT): cv.positive_float,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        f"async_{ATTR_ACTION_ADD_PUMPING}",
    )
    platform.async_register_entity_service(
        ATTR_ACTION_ADD_SLEEP,
        {
            **COMMON_FIELDS,
            vol.Optional(ATTR_NAP): cv.boolean,
            vol.Optional(ATTR_NOTES): cv.string,
        },
        f"async_{ATTR_ACTION_ADD_SLEEP}",
    )
    platform.async_register_entity_service(
        ATTR_ACTION_ADD_TUMMY_TIME,
        {
            **COMMON_FIELDS,
            vol.Optional(ATTR_MILESTONE): cv.string,
        },
        f"async_{ATTR_ACTION_ADD_TUMMY_TIME}",
    )


@callback
def update_items(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add timer switches to new child."""
    new_entities = []
    if coordinator.data:
        for child in coordinator.data[0]:
            if child[ATTR_ID] not in tracked:
                tracked[child[ATTR_ID]] = BabyBuddyChildTimerSwitch(coordinator, child)
                new_entities.append(tracked[child[ATTR_ID]])
        if new_entities:
            async_add_entities(new_entities)


class BabyBuddyChildTimerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a babybuddy timer switch."""

    coordinator: BabyBuddyCoordinator

    def __init__(
        self,
        coordinator: BabyBuddyCoordinator,
        child: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.child = child
        self._attr_name = (
            f"{self.child[ATTR_FIRST_NAME]} {self.child[ATTR_LAST_NAME]} {ATTR_TIMER}"
        )
        self._attr_unique_id = (
            f"{self.coordinator.entry.data[CONF_API_KEY]}-{child[ATTR_ID]}-{ATTR_TIMER}"
        )
        self._attr_icon = ATTR_ICON_TIMER_SAND
        self._attr_device_info = {
            "identifiers": {(DOMAIN, child[ATTR_ID])},
            "name": f"{child[ATTR_FIRST_NAME]} {child[ATTR_LAST_NAME]}",
        }

    @property
    def is_on(self) -> bool:
        """Return entity state."""
        if self.child[ATTR_ID] in self.coordinator.data[1]:
            timer_data = self.coordinator.data[1][self.child[ATTR_ID]][ATTR_TIMERS]
            # In Babybuddy 2.0 'active' is not in the JSON response, so return
            # True if any timers are returned, as only active timers are
            # returned.
            return timer_data.get("active", len(timer_data) > 0)
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for babybuddy."""
        attrs: dict[str, Any] = {}
        if self.is_on:
            attrs = self.coordinator.data[1][self.child[ATTR_ID]].get(ATTR_TIMERS)
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start a new timer."""
        await self.async_start_timer()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Delete active timer."""
        timer_id = self.extra_state_attributes[ATTR_ID]
        await self.coordinator.client.async_delete(ATTR_TIMERS, timer_id)
        await self.coordinator.async_request_refresh()

    async def async_start_timer(
        self, start: datetime | time | None = None, name: str | None = None
    ) -> None:
        """Start a new timer for child."""
        data: dict[str, Any] = {ATTR_CHILD: self.child[ATTR_ID]}
        try:
            data[ATTR_START] = get_datetime_from_time(start or dt_util.now())
        except ValidationError as error:
            LOGGER.error(error)
            return
        if name:
            data[ATTR_NAME] = name

        await self.coordinator.client.async_post(ATTR_TIMERS, data)
        await self.coordinator.async_request_refresh()

    async def async_add_feeding(
        self,
        type: str,  # pylint: disable=redefined-builtin
        method: str,
        timer: bool | None = None,
        start: datetime | time | None = None,
        end: datetime | time | None = None,
        amount: int | None = None,
        notes: str | None = None,
        tags: str | None = None,
    ) -> None:
        """Add a feeding entry."""
        try:
            data = self.set_common_fields(timer, start, end, tags)
        except ValidationError as error:
            LOGGER.error(error)
            return

        data.update(
            {
                ATTR_TYPE: type.lower(),
                ATTR_METHOD: method.lower(),
            }
        )

        if amount:
            data[ATTR_AMOUNT] = amount
        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_FEEDINGS, data)
        await self.coordinator.async_request_refresh()

    async def async_add_pumping(
        self,
        amount: int,
        timer: bool | None = None,
        start: datetime | time | None = None,
        end: datetime | time | None = None,
        notes: str | None = None,
        tags: str | None = None,
    ) -> None:
        """Add a pumping entry."""
        try:
            data = self.set_common_fields(timer, start, end, tags)
        except ValidationError as error:
            LOGGER.error(error)
            return

        data[ATTR_AMOUNT] = amount

        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_PUMPING, data)
        await self.coordinator.async_request_refresh()

    async def async_add_sleep(
        self,
        timer: bool | None = None,
        start: datetime | time | None = None,
        end: datetime | time | None = None,
        nap: bool | None = None,
        notes: str | None = None,
        tags: str | None = None,
    ) -> None:
        """Add a sleep entry."""
        try:
            data = self.set_common_fields(timer, start, end, tags)
        except ValidationError as error:
            LOGGER.error(error)
            return

        if nap is not None:
            data[ATTR_NAP] = nap
        if notes:
            data[ATTR_NOTES] = notes

        await self.coordinator.client.async_post(ATTR_SLEEP, data)
        await self.coordinator.async_request_refresh()

    async def async_add_tummy_time(
        self,
        timer: bool | None = None,
        start: datetime | time | None = None,
        end: datetime | time | None = None,
        milestone: str | None = None,
        tags: str | None = None,
    ) -> None:
        """Add a tummy time entry."""
        try:
            data = self.set_common_fields(timer, start, end, tags)
        except ValidationError as error:
            LOGGER.error(error)
            return
        if milestone:
            data[ATTR_MILESTONE] = milestone

        await self.coordinator.client.async_post(ATTR_TUMMY_TIMES, data)
        await self.coordinator.async_request_refresh()

    def set_common_fields(
        self,
        timer: bool | None = None,
        start: datetime | time | None = None,
        end: datetime | time | None = None,
        tags: str | None = None,
    ) -> dict[str, Any]:
        """Set data common fields."""
        data: dict[str, Any] = {}
        if timer:
            if not self.is_on:
                raise ValidationError(
                    "Timer not found or stopped. Timer must be active."
                )
            data[ATTR_TIMER] = self.extra_state_attributes[ATTR_ID]
        else:
            data[ATTR_CHILD] = self.child[ATTR_ID]
            data[ATTR_START] = get_datetime_from_time(start or dt_util.now())
            data[ATTR_END] = get_datetime_from_time(end or dt_util.now())
        if tags:
            data[ATTR_TAGS] = tags
        return data
