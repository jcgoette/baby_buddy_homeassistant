"""Constants for babybuddy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Final

from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import ATTR_TIME, UnitOfTime
import homeassistant.util.dt as dt_util

LOGGER = logging.getLogger(__package__)

DOMAIN: Final[str] = "babybuddy"

CONF_FEEDING_UNIT: Final[str] = "feedings"
CONF_WEIGHT_UNIT: Final[str] = "weight"

DEFAULT_NAME: Final[str] = "Baby Buddy"
DEFAULT_PORT: Final[int] = 8000
DEFAULT_PATH: Final[str] = ""
DEFAULT_SCAN_INTERVAL: Final[int] = 60

CONFIG_FLOW_VERSION: Final[int] = 2

ATTR_AMOUNT: Final[str] = "amount"
ATTR_BABYBUDDY_CHILD: Final[str] = "babybuddy_child"
ATTR_BIRTH_DATE: Final[str] = "birth_date"
ATTR_BMI: Final[str] = "bmi"
ATTR_CHANGES: Final[str] = "changes"
ATTR_CHILD: Final[str] = "child"
ATTR_CHILDREN: Final[str] = "children"
ATTR_COLOR: Final[str] = "color"
ATTR_COUNT: Final[str] = "count"
ATTR_DESCRIPTIVE: Final[str] = "descriptive"
ATTR_DURATION: Final[str] = "duration"
ATTR_END: Final[str] = "end"
ATTR_FEEDINGS: Final[str] = "feedings"
ATTR_FIRST_NAME: Final[str] = "first_name"
ATTR_HEAD_CIRCUMFERENCE_DASH: Final[str] = "head-circumference"
ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE: Final[str] = "head_circumference"
ATTR_HEIGHT: Final[str] = "height"
ATTR_LAST_NAME: Final[str] = "last_name"
ATTR_METHOD: Final[str] = "method"
ATTR_MILESTONE: Final[str] = "milestone"
ATTR_NAP: Final[str] = "nap"
ATTR_NOTE: Final[str] = "note"
ATTR_NOTES: Final[str] = "notes"
ATTR_PICTURE: Final[str] = "picture"
ATTR_PUMPING: Final[str] = "pumping"
ATTR_RESULTS: Final[str] = "results"
ATTR_SLEEP: Final[str] = "sleep"
ATTR_SLUG: Final[str] = "slug"
ATTR_SOLID: Final[str] = "solid"
ATTR_START: Final[str] = "start"
ATTR_TAGS: Final[str] = "tags"
ATTR_TIMER: Final[str] = "timer"
ATTR_TIMERS: Final[str] = "timers"
ATTR_TUMMY_TIMES: Final[str] = "tummy-times"
ATTR_TYPE: Final[str] = "type"
ATTR_WEIGHT: Final[str] = "weight"
ATTR_WET: Final[str] = "wet"

ATTR_ICON_BABY_BOTTLE: Final[str] = "mdi:baby-bottle-outline"
ATTR_ICON_BABY: Final[str] = "mdi:baby"
ATTR_ICON_CHILD_SENSOR: Final[str] = "mdi:baby-face-outline"
ATTR_ICON_HEAD: Final[str] = "mdi:head-outline"
ATTR_ICON_HEIGHT: Final[str] = "mdi:human-male-height"
ATTR_ICON_MOTHER_NURSE: Final[str] = "mdi:mother-nurse"
ATTR_ICON_NOTE: Final[str] = "mdi:note-multiple-outline"
ATTR_ICON_PAPER_ROLL: Final[str] = "mdi:paper-roll-outline"
ATTR_ICON_SCALE: Final[str] = "mdi:scale-bathroom"
ATTR_ICON_SLEEP: Final[str] = "mdi:sleep"
ATTR_ICON_THERMOMETER: Final[str] = "mdi:thermometer"
ATTR_ICON_TIMER_SAND: Final[str] = "mdi:timer-sand"

ATTR_ACTION_ADD_BMI: Final[str] = "add_bmi"
ATTR_ACTION_ADD_CHILD: Final[str] = "add_child"
ATTR_ACTION_ADD_DIAPER_CHANGE: Final[str] = "add_diaper_change"
ATTR_ACTION_ADD_FEEDING: Final[str] = "add_feeding"
ATTR_ACTION_ADD_HEAD_CIRCUMFERENCE: Final[str] = "add_head_circumference"
ATTR_ACTION_ADD_HEIGHT: Final[str] = "add_height"
ATTR_ACTION_ADD_NOTE: Final[str] = "add_note"
ATTR_ACTION_ADD_PUMPING: Final[str] = "add_pumping"
ATTR_ACTION_ADD_SLEEP: Final[str] = "add_sleep"
ATTR_ACTION_ADD_TEMPERATURE: Final[str] = "add_temperature"
ATTR_ACTION_ADD_TUMMY_TIME: Final[str] = "add_tummy_time"
ATTR_ACTION_ADD_WEIGHT: Final[str] = "add_weight"
ATTR_ACTION_DELETE_LAST_ENTRY: Final[str] = "delete_last_entry"

DEFAULT_DIAPER_TYPE: Final = ATTR_WET
DIAPER_COLOR: Final[str] = "diaper_color"
DIAPER_COLORS: Final = ["Black", "Brown", "Green", "Yellow"]
DIAPER_TYPE: Final[str] = "change_type"
DIAPER_TYPES: Final = ["Wet", "Solid", "Wet and Solid"]
FEEDING_METHODS: Final = [
    "Bottle",
    "Left breast",
    "Right breast",
    "Both breasts",
    "Parent fed",
    "Self fed",
]
FEEDING_TYPE: Final[str] = "feeding_type"
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
        icon=ATTR_ICON_SCALE,
        key=ATTR_BMI,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_BMI,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon=ATTR_ICON_PAPER_ROLL,
        key=ATTR_CHANGES,
        state_key=ATTR_TIME,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_BABY_BOTTLE,
        key=ATTR_FEEDINGS,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_AMOUNT,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_HEAD,
        key=ATTR_HEAD_CIRCUMFERENCE_DASH,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_HEAD_CIRCUMFERENCE_UNDERSCORE,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_HEIGHT,
        key=ATTR_HEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_HEIGHT,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon=ATTR_ICON_NOTE,
        key=ATTR_NOTES,
        state_key=ATTR_TIME,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_MOTHER_NURSE,
        key=ATTR_PUMPING,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=ATTR_AMOUNT,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_SLEEP,
        key=ATTR_SLEEP,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=lambda value: int(
            dt_util.parse_duration(value[ATTR_DURATION]).total_seconds() / 60
        ),
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TEMPERATURE,
        icon=ATTR_ICON_THERMOMETER,
        key=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=SensorDeviceClass.TEMPERATURE,
    ),
    BabyBuddyEntityDescription(
        device_class=SensorDeviceClass.TIMESTAMP,
        icon=ATTR_ICON_TIMER_SAND,
        key=ATTR_TIMERS,
        state_key=ATTR_START,
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_BABY,
        key=ATTR_TUMMY_TIMES,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        state_key=lambda value: int(
            dt_util.parse_duration(value[ATTR_DURATION]).total_seconds() / 60
        ),
    ),
    BabyBuddyEntityDescription(
        icon=ATTR_ICON_SCALE,
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
        icon=ATTR_ICON_PAPER_ROLL,
        key=DIAPER_COLOR,
        name=f"{DEFAULT_NAME} Diaper color",
        options=DIAPER_COLORS,
    ),
    BabyBuddySelectDescription(
        icon=ATTR_ICON_PAPER_ROLL,
        key=DIAPER_TYPE,
        name=f"{DEFAULT_NAME} Diaper type",
        options=DIAPER_TYPES,
    ),
    BabyBuddySelectDescription(
        icon=ATTR_ICON_BABY_BOTTLE,
        key="feeding_method",
        name=f"{DEFAULT_NAME} Feeding method",
        options=FEEDING_METHODS,
    ),
    BabyBuddySelectDescription(
        icon=ATTR_ICON_BABY_BOTTLE,
        key=FEEDING_TYPE,
        name=f"{DEFAULT_NAME} Feeding type",
        options=FEEDING_TYPES,
    ),
)

PLATFORMS: Final = ["sensor", "select", "switch"]
