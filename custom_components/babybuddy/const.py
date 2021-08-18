"""Constants for the babybuddy integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Final

from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntityDescription,
)
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_TIME,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    MASS_KILOGRAMS,
    TEMP_CELSIUS,
    TIME_MINUTES,
    VOLUME_MILLILITERS,
)
from homeassistant.helpers.config_validation import time_period_str

DOMAIN: Final = "babybuddy"

CONF_WEIGHT_UNIT: Final = "weight"
CONF_TEMPERATURE_UNIT: Final = "temperature"
CONF_FEEDING_UNIT: Final = "feedings"

DEFAULT_NAME: Final = "Baby Buddy"
DEFAULT_PORT: Final = 8000
DEFAULT_SCAN_INTERVAL: Final = 60

ATTR_ACTIVE: Final = "active"
ATTR_AMOUNT: Final = "amount"
ATTR_BIRTH_DATE: Final = "birth_date"
ATTR_CHANGES: Final = "changes"
ATTR_CHILD: Final = "child"
ATTR_CHILDREN: Final = "children"
ATTR_COLOR: Final = "color"
ATTR_COUNT: Final = "count"
ATTR_DURATION: Final = "duration"
ATTR_END: Final = "end"
ATTR_FEEDINGS: Final = "feedings"
ATTR_FIRST_NAME: Final = "first_name"
ATTR_LAST_NAME: Final = "last_name"
ATTR_METHOD: Final = "method"
ATTR_MILESTONE: Final = "milestone"
ATTR_NOTE: Final = "note"
ATTR_NOTES: Final = "notes"
ATTR_RESULTS: Final = "results"
ATTR_PICTURE: Final = "picture"
ATTR_SLEEP: Final = "sleep"
ATTR_SOLID: Final = "solid"
ATTR_START: Final = "start"
ATTR_TIMER: Final = "timer"
ATTR_TIMERS: Final = "timers"
ATTR_TUMMY_TIMES: Final = "tummy-times"
ATTR_TYPE: Final = "type"
ATTR_WEIGHT: Final = "weight"
ATTR_WET: Final = "wet"

FEEDING_TYPE: Final = "feeding_type"
FEEDING_TYPES: Final = ["Breast milk", "Formula", "Fortified breast milk", "Solid food"]
FEEDING_METHOD: Final = "feeding_method"
FEEDING_METHODS: Final = [
    "Bottle",
    "Left breast",
    "Right breast",
    "Both breasts",
    "Parent fed",
    "Self fed",
]
DIAPER_TYPE: Final = "change_type"
DIAPER_TYPES: Final = ["Wet", "Solid"]
DIAPER_COLOR: Final = "diaper_color"
DIAPER_COLORS: Final = ["Black", "Brown", "Green", "Yellow"]
DEFAULT_FEEDING_TYPE: Final = "Breast milk"
DEFAULT_FEEDING_METHOD: Final = "Both breasts"
DEFAULT_DIAPER_TYPE: Final = ATTR_WET
DEFAULT_DIAPER_COLOR: Final = "Brown"


@dataclass
class BabyBuddyEntityDescription(SensorEntityDescription, SwitchEntityDescription):
    """Describe Baby Buddy sensor entity."""

    state_key: Callable[[dict], int] | str = ""


SENSOR_TYPES: tuple[BabyBuddyEntityDescription, ...] = (
    BabyBuddyEntityDescription(
        key=ATTR_CHANGES,
        state_key=ATTR_TIME,
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="mdi:paper-roll-outline",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_FEEDINGS,
        state_key=ATTR_AMOUNT,
        unit_of_measurement=VOLUME_MILLILITERS,
        icon="mdi:baby-bottle-outline",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_NOTES,
        state_key=ATTR_TIME,
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="mdi:note-multiple-outline",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_SLEEP,
        state_key=lambda value: int(
            time_period_str(value[ATTR_DURATION]).total_seconds() / 60
        ),
        unit_of_measurement=TIME_MINUTES,
        icon="mdi:sleep",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_TEMPERATURE,
        state_key=ATTR_TEMPERATURE,
        device_class=DEVICE_CLASS_TEMPERATURE,
        unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_TUMMY_TIMES,
        state_key=lambda value: int(
            time_period_str(value[ATTR_DURATION]).total_seconds() / 60
        ),
        icon="mdi:baby",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_WEIGHT,
        state_key=ATTR_WEIGHT,
        state_class=STATE_CLASS_MEASUREMENT,
        unit_of_measurement=MASS_KILOGRAMS,
        icon="mdi:scale-bathroom",
    ),
    BabyBuddyEntityDescription(
        key=ATTR_TIMERS,
        state_key=ATTR_ACTIVE,
        device_class=DEVICE_CLASS_TIMESTAMP,
        icon="mdi:timer-sand",
    ),
)


@dataclass
class BabyBuddySelectDescription(SelectEntityDescription):
    """Describe Baby Buddy select entity."""

    options: list[str] = field(default_factory=list)
    default_option: str | None = None


SELECTOR_TYPES: tuple[BabyBuddySelectDescription, ...] = (
    BabyBuddySelectDescription(
        key=FEEDING_METHOD,
        name=f"{DEFAULT_NAME} Feeding method",
        options=FEEDING_METHODS,
        default_option=DEFAULT_FEEDING_METHOD,
        icon="mdi:baby-bottle-outline",
    ),
    BabyBuddySelectDescription(
        key=FEEDING_TYPE,
        name=f"{DEFAULT_NAME} Feeding type",
        options=FEEDING_TYPES,
        default_option=DEFAULT_FEEDING_TYPE,
        icon="mdi:baby-bottle-outline",
    ),
    BabyBuddySelectDescription(
        key=DIAPER_TYPE,
        name=f"{DEFAULT_NAME} Diaper type",
        options=DIAPER_TYPES,
        default_option=DEFAULT_DIAPER_TYPE,
        icon="mdi:paper-roll-outline",
    ),
    BabyBuddySelectDescription(
        key=DIAPER_COLOR,
        name=f"{DEFAULT_NAME} Diaper color",
        options=DIAPER_COLORS,
        default_option=DEFAULT_DIAPER_COLOR,
        icon="mdi:paper-roll-outline",
    ),
)

PLATFORMS: Final = ["sensor", "switch", "select"]
