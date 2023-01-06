"""Constants for the babybuddy integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

import homeassistant.util.dt as dt_util
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import ATTR_TIME, UnitOfTime

DOMAIN: Final = "babybuddy"

CONF_FEEDING_UNIT: Final = "feedings"
CONF_WEIGHT_UNIT: Final = "weight"

DEFAULT_NAME: Final = "Baby Buddy"
DEFAULT_PORT: Final = 8000
DEFAULT_PATH: Final = ""
DEFAULT_SCAN_INTERVAL: Final = 60

CONFIG_FLOW_VERSION: Final = 2

ATTR_ACTIVE: Final = "active"
ATTR_AMOUNT: Final = "amount"
ATTR_BIRTH_DATE: Final = "birth_date"
ATTR_BMI: Final = "bmi"
ATTR_CHANGES: Final = "changes"
ATTR_CHILD: Final = "child"
ATTR_CHILDREN: Final = "children"
ATTR_COLOR: Final = "color"
ATTR_COUNT: Final = "count"
ATTR_DESCRIPTIVE: Final = "descriptive"
ATTR_DURATION: Final = "duration"
ATTR_END: Final = "end"
ATTR_FEEDINGS: Final = "feedings"
ATTR_FIRST_NAME: Final = "first_name"
ATTR_HEAD_CIRCUMFERENCE_DASH: Final = "head-circumference"
ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE: Final = "head_circumference"
ATTR_HEIGHT: Final = "height"
ATTR_LAST_NAME: Final = "last_name"
ATTR_METHOD: Final = "method"
ATTR_MILESTONE: Final = "milestone"
ATTR_NOTE: Final = "note"
ATTR_NOTES: Final = "notes"
ATTR_PICTURE: Final = "picture"
ATTR_PUMPING: Final = "pumping"
ATTR_RESULTS: Final = "results"
ATTR_SLEEP: Final = "sleep"
ATTR_SLUG: Final = "slug"
ATTR_SOLID: Final = "solid"
ATTR_START: Final = "start"
ATTR_TIMER: Final = "timer"
ATTR_TIMERS: Final = "timers"
ATTR_TUMMY_TIMES: Final = "tummy-times"
ATTR_TYPE: Final = "type"
ATTR_WEIGHT: Final = "weight"
ATTR_WET: Final = "wet"

DEFAULT_DIAPER_TYPE: Final = ATTR_WET
DIAPER_COLOR: Final = "diaper_color"
DIAPER_COLORS: Final = ["Black", "Brown", "Green", "Yellow"]
DIAPER_TYPE: Final = "change_type"
DIAPER_TYPES: Final = ["Wet", "Solid", "Wet and Solid"]
FEEDING_METHOD: Final = "feeding_method"
FEEDING_METHODS: Final = [
    "Bottle",
    "Left breast",
    "Right breast",
    "Both breasts",
    "Parent fed",
    "Self fed",
]
FEEDING_TYPE: Final = "feeding_type"
FEEDING_TYPES: Final = ["Breast milk", "Formula", "Fortified breast milk", "Solid food"]

ERROR_CHILD_SENSOR_SELECT: Final = (
    "Babybuddy child sensor should be selected - ignoring"
)


@dataclass
class BabyBuddyEntityDescription(SensorEntityDescription, SwitchEntityDescription):
    """Describe Baby Buddy sensor entity."""

    state_key: Callable[[dict], int] | str = ""


SENSOR_TYPES: tuple[BabyBuddyEntityDescription, ...] = (
    BabyBuddyEntityDescription(
        icon="mdi:scale-bathroom",
        key=ATTR_BMI,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_BMI,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:paper-roll-outline",
        key=ATTR_CHANGES,
        state_key=ATTR_TIME,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:baby-bottle-outline",
        key=ATTR_FEEDINGS,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_AMOUNT,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:head-outline",
        key=ATTR_HEAD_CIRCUMFERENCE_DASH,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:human-male-height",
        key=ATTR_HEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_HEIGHT,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:note-multiple-outline",
        key=ATTR_NOTES,
        state_key=ATTR_TIME,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:mother-nurse",
        key=ATTR_PUMPING,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_AMOUNT,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:sleep",
        key=ATTR_SLEEP,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=lambda value: int(
            dt_util.parse_duration(value[ATTR_DURATION]).total_seconds() / 60
        ),
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer",
        key=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=SensorDeviceClass.TEMPERATURE,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:timer-sand",
        key=ATTR_TIMERS,
        state_key=ATTR_START,
    ),
    BabyBuddyEntityDescription(
        icon="mdi:baby",
        key=ATTR_TUMMY_TIMES,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=lambda value: int(
            dt_util.parse_duration(value[ATTR_DURATION]).total_seconds() / 60
        ),
    ),
    BabyBuddyEntityDescription(
        icon="mdi:scale-bathroom",
        key=ATTR_WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_WEIGHT,
    ),
)


@dataclass
class BabyBuddySelectDescription(SelectEntityDescription):
    """Describe Baby Buddy select entity."""


SELECTOR_TYPES: tuple[BabyBuddySelectDescription, ...] = (
    BabyBuddySelectDescription(
        icon="mdi:paper-roll-outline",
        key=DIAPER_COLOR,
        name=f"{DEFAULT_NAME} Diaper color",
        options=DIAPER_COLORS,
    ),
    BabyBuddySelectDescription(
        icon="mdi:paper-roll-outline",
        key=DIAPER_TYPE,
        name=f"{DEFAULT_NAME} Diaper type",
        options=DIAPER_TYPES,
    ),
    BabyBuddySelectDescription(
        icon="mdi:baby-bottle-outline",
        key=FEEDING_METHOD,
        name=f"{DEFAULT_NAME} Feeding method",
        options=FEEDING_METHODS,
    ),
    BabyBuddySelectDescription(
        icon="mdi:baby-bottle-outline",
        key=FEEDING_TYPE,
        name=f"{DEFAULT_NAME} Feeding type",
        options=FEEDING_TYPES,
    ),
)

PLATFORMS: Final = ["sensor", "select", "switch"]
