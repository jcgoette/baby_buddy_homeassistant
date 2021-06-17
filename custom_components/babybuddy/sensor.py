"""Platform for babybuddy sensor integration."""
import logging

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_ADDRESS,
    CONF_API_KEY,
    CONF_SENSOR_TYPE,
    CONF_SSL,
)
from homeassistant.helpers.entity import Entity
from requests_toolbelt import sessions

from .const import (
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_NOTES,
    ATTR_RESULTS,
    ATTR_SLEEP,
    ATTR_START,
    ATTR_TIMERS,
    ATTR_TUMMY_TIMES,
    ATTR_WEIGHT,
    DEFAULT_SENSOR_TYPE,
    DEFAULT_SSL,
)

_LOGGER = logging.getLogger(__name__)

"""Validation of the user's configuration"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
        vol.Optional(CONF_SENSOR_TYPE, default=DEFAULT_SENSOR_TYPE): vol.All(
            cv.ensure_list, [vol.In(DEFAULT_SENSOR_TYPE)]
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    address = config[CONF_ADDRESS]
    api_key = config[CONF_API_KEY]
    ssl = config[CONF_SSL]
    sensor_type = config[CONF_SENSOR_TYPE]

    if not ssl:
        _LOGGER.warning("Use of HTTPS in production environment is highly recommended")

    baby_buddy_data = BabyBuddyData(address, api_key, ssl, sensor_type)
    if not baby_buddy_data.form_address():
        return

    sensors = []

    """There must be a better way to do this vs. deconstructing BabyBuddyData.entities_get()..."""
    for entity in baby_buddy_data.entities_get():
        entity_list = [baby_buddy_data]
        for part in entity:
            entity_list.append(part)
        entity_list = tuple(entity_list)
        sensors.append(
            BabyBuddySensor(
                entity_list[0], entity_list[1], entity_list[2], entity_list[3]
            )
        )

    add_entities(sensors, True)


class BabyBuddySensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, baby_buddy_data, name, data, endpoint):
        """Initialize the sensor."""
        self._baby_buddy_data = baby_buddy_data
        self._name = name
        self._data = self._state = data
        self._endpoint = endpoint

    @property
    def state(self):
        """Return the state of the sensor."""
        for key, value in self._state.items():
            if key == ATTR_TIME:
                return value
            elif key == ATTR_BIRTH_DATE:
                return value
            elif key == ATTR_START:
                return value
            elif key == ATTR_DATE:
                return value

    @property
    def state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = []
        for attribute in self._data.items():
            attributes.append(attribute)
        return attributes

    @property
    def name(self):
        """Return the name of the sensor."""
        name = self._name.replace("_", " ").title()
        if name[-1] == "s" and self._endpoint:
            return name[:-1]
        return name

    @property
    def icon(self):
        """Return the icon to use in the frontend"""
        if self._endpoint == ATTR_CHANGES:
            return "mdi:paper-roll-outline"
        elif self._endpoint == ATTR_FEEDINGS:
            return "mdi:baby-bottle-outline"
        elif self._endpoint == ATTR_NOTES:
            return "mdi:note-multiple-outline"
        elif self._endpoint == ATTR_SLEEP:
            return "mdi:sleep"
        elif self._endpoint == ATTR_TEMPERATURE:
            return "mdi:thermometer"
        elif self._endpoint == ATTR_TIMERS:
            return "mdi:timer-sand"
        elif self._endpoint == ATTR_TUMMY_TIMES:
            return "mdi:baby"
        elif self._endpoint == ATTR_WEIGHT:
            return "mdi:scale-bathroom"
        return "mdi:baby-face-outline"

    def update(self):
        """Fetch new data for the sensor."""
        if not self._baby_buddy_data.form_address():
            return
        try:
            self._data = self._state = self._baby_buddy_data.entities_update(
                self._name
            )[0][1]
        except IndexError:
            _LOGGER.error(
                "Baby Buddy database entry %s has been removed since last Home Assistant start",
                self.name,
            )


class BabyBuddyData:
    def __init__(self, address, api_key, ssl, sensor_type):
        self._address = address
        self._api_key = api_key
        self._ssl = ssl
        self._sensor_type = sensor_type

    def form_address(self):
        if self._ssl:
            address = f"https://{self._address}/api/"
        else:
            address = f"http://{self._address}/api/"
        try:
            requests.get(address)
        except:
            _LOGGER.error(
                "Cannot reach %s, check address and/or SSL configuration entry",
                address[:-5],
            )
            return False
        return address

    def entities_get(self):
        session = sessions.BaseUrlSession(base_url=self.form_address())
        session.headers = {"Authorization": f"Token {self._api_key}"}

        sensors = []

        children = session.get("children/").json()
        children = children[ATTR_RESULTS]
        for child in children:
            child_name = f"{child[ATTR_FIRST_NAME]}_{child[ATTR_LAST_NAME]}"
            sensors.append((child_name, child, None))
            for endpoint in self._sensor_type:
                r = session.get(f"{endpoint}").json()
                data = next(
                    (i for i in r[ATTR_RESULTS] if i[ATTR_CHILD] == child[ATTR_ID]),
                    None,
                )
                if data:
                    endpoint_name = f"{child_name}_last_{endpoint}"
                    sensors.append((endpoint_name, data, endpoint))

        return sensors

    def entities_update(self, sensor):
        sensor = [sensors for sensors in self.entities_get() if sensors[0] == sensor]

        return sensor
