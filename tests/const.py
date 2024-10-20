"""Constants for babybuddy tests."""

import os
from typing import Final

from custom_components.babybuddy.const import (
    CONF_FEEDING_UNIT,
    CONF_WEIGHT_UNIT,
    DEFAULT_PATH,
    DEFAULT_SCAN_INTERVAL,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    TEMPERATURE,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfVolume,
)

ATTR_STEP_ID_USER: Final = "user"

BABY_BUDDY_HOST = os.environ.get("BABY_BUDDY_HOST")
BABY_BUDDY_PORT = int(os.environ.get("BABY_BUDDY_PORT"))
API_KEY = os.environ.get("API_KEY")

MOCK_CONFIG = {
    CONF_HOST: BABY_BUDDY_HOST,
    CONF_PORT: BABY_BUDDY_PORT,
    CONF_PATH: DEFAULT_PATH,
    CONF_API_KEY: API_KEY,
}
INVALID_CONFIG_CONNECTERROR = {
    **MOCK_CONFIG,
    CONF_PATH: "lorem",
}
INVALID_CONFIG_AUTHORIZATIONERROR = {
    **MOCK_CONFIG,
    CONF_API_KEY: "lorem",
}
MOCK_OPTIONS = {
    TEMPERATURE: UnitOfTemperature.CELSIUS,
    CONF_WEIGHT_UNIT: UnitOfMass.GRAMS,
    CONF_FEEDING_UNIT: UnitOfVolume.MILLILITERS,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}
