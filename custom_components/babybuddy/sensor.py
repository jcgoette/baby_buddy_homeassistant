"""Platform for babybuddy sensor integration."""
import logging

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_ADDRESS, CONF_API_KEY, CONF_SSL
from homeassistant.helpers.entity import Entity
from requests_toolbelt import sessions

_LOGGER = logging.getLogger(__name__)

DEFAULT_SSL = True

"""Validation of the user's configuration"""
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
    }
)

"""Babybuddy API endpoints"""
ENDPOINTS = {
    "changes",
    "feedings",
    "notes",
    "sleep",
    "temperature",
    "timers",
    "tummy-times",
    "weight",
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    address = config[CONF_ADDRESS]
    api_key = config[CONF_API_KEY]
    ssl = config[CONF_SSL]

    if not ssl:
        _LOGGER.warning("Use of HTTPS in production environment is highly recommended")

    baby_buddy_data = BabyBuddyData(address, api_key, ssl)
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
            if key == "time":
                return value
            elif key == "birth_date":
                return value
            elif key == "start":
                return value
            elif key == "date":
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
        if name[-1] == "s":
            return name[:-1]
        return name

    @property
    def icon(self):
        """Return the icon to use in the frontend"""
        if self._endpoint == "changes":
            return "mdi:paper-roll-outline"
        elif self._endpoint == "feedings":
            return "mdi:baby-bottle-outline"
        elif self._endpoint == "notes":
            return "mdi:note-multiple-outline"
        elif self._endpoint == "sleep":
            return "mdi:sleep"
        elif self._endpoint == "temperature":
            return "mdi:thermometer"
        elif self._endpoint == "timers":
            return "mdi:timer-sand"
        elif self._endpoint == "weight":
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
    def __init__(self, address, api_key, ssl):
        self._address = address
        self._api_key = api_key
        self._ssl = ssl

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
        children = children["results"]
        for child in children:
            child_name = f'{child["first_name"]}_{child["last_name"]}'
            sensors.append((child_name, child, None))
            for endpoint in ENDPOINTS:
                r = session.get(f"{endpoint}").json()
                data = next(
                    (i for i in r["results"] if i["child"] == child["id"]), None
                )
                if data:
                    endpoint_name = f"{child_name}_last_{endpoint}"
                    sensors.append((endpoint_name, data, endpoint))

        return sensors

    def entities_update(self, sensor):
        sensor = [sensors for sensors in self.entities_get() if sensors[0] == sensor]

        return sensor
