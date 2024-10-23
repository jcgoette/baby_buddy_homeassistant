"""Constants for babybuddy integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Final

from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import ATTR_TIME, UnitOfTime
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "babybuddy"

CONF_FEEDING_UNIT: Final = "feedings"
CONF_WEIGHT_UNIT: Final = "weight"

DEFAULT_NAME: Final = "Baby Buddy"
DEFAULT_PORT: Final = 8000
DEFAULT_PATH: Final = ""
DEFAULT_SCAN_INTERVAL: Final = 60

CONFIG_FLOW_VERSION: Final = 2

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
        key=FEEDING_METHOD,
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
