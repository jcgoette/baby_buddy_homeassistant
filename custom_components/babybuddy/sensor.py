"""Platform for Baby Buddy sensor integration."""
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

from .const import (
    ATTR_AMOUNT,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
    ATTR_CHILD_NAME,
    ATTR_CHILDREN,
    ATTR_COLOR,
    ATTR_END,
    ATTR_ENDPOINT,
    ATTR_ENTRY,
    ATTR_FEEDINGS,
    ATTR_FIRST_NAME,
    ATTR_LAST_NAME,
    ATTR_METHOD,
    ATTR_MILESTONE,
    ATTR_NOTE,
    ATTR_NOTES,
    ATTR_RESULTS,
    ATTR_SLEEP,
    ATTR_SOLID,
    ATTR_START,
    ATTR_TIMERS,
    ATTR_TUMMY_TIMES,
    ATTR_TYPE,
    ATTR_WEIGHT,
    ATTR_WET,
    DEFAULT_SENSOR_TYPE,
    DEFAULT_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

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
    """Setup Baby Buddy sensors."""
    address = config[CONF_ADDRESS]
    api_key = config[CONF_API_KEY]
    ssl = config[CONF_SSL]
    sensor_type = config[CONF_SENSOR_TYPE]

    if not ssl:
        _LOGGER.warning("Use of HTTPS in production environment is highly recommended")

    baby_buddy = BabyBuddyData(address, api_key, ssl, sensor_type)

    if not baby_buddy.form_address():
        return

    # TODO: Do not call update() in constructor, use add_entities(devices, True) instead
    baby_buddy.entities_update()

    sensors = []
    for data in baby_buddy.data:
        sensors.append(BabyBuddySensor(data, baby_buddy))

    add_entities(sensors, False)

    # TODO: handle loading of children
    def services_children_add(call):
        endpoint = ATTR_CHILDREN
        data = {
            ATTR_FIRST_NAME: call.data.get(ATTR_FIRST_NAME),
            ATTR_LAST_NAME: call.data.get(ATTR_LAST_NAME),
            ATTR_BIRTH_DATE: call.data.get(ATTR_BIRTH_DATE),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_changes_add(call):
        endpoint = ATTR_CHANGES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_TIME: call.data.get(ATTR_TIME),
            ATTR_WET: call.data.get(ATTR_WET),
            ATTR_SOLID: call.data.get(ATTR_SOLID),
            ATTR_COLOR: call.data[ATTR_COLOR].lower()
            if ATTR_COLOR in call.data
            else None,
            ATTR_AMOUNT: call.data.get(ATTR_AMOUNT),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_feedings_add(call):
        endpoint = ATTR_FEEDINGS
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_TYPE: call.data.get(ATTR_TYPE).lower(),
            ATTR_METHOD: call.data.get(ATTR_METHOD).lower(),
            ATTR_AMOUNT: call.data.get(ATTR_AMOUNT),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_notes_add(call):
        endpoint = ATTR_NOTES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_NOTE: call.data.get(ATTR_NOTE),
            ATTR_TIME: call.data.get(ATTR_TIME),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_sleep_add(call):
        endpoint = ATTR_SLEEP
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_temperature_add(call):
        endpoint = ATTR_TEMPERATURE
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_TEMPERATURE: call.data.get(ATTR_TEMPERATURE),
            ATTR_TIME: call.data.get(ATTR_TIME),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy.entities_add(endpoint, data)

    """
    def services_timers_add(call):
        endpoint = ATTR_TIMERS
        data = {}

        baby_buddy.entities_add(endpoint, data)
    """

    def services_tummy_times_add(call):
        endpoint = ATTR_TUMMY_TIMES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_MILESTONE: call.data.get(ATTR_MILESTONE),
        }

        baby_buddy.entities_add(endpoint, data)

    def services_weight_add(call):
        endpoint = ATTR_WEIGHT
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get(
                ATTR_ID
            ),
            ATTR_WEIGHT: call.data.get(ATTR_WEIGHT),
            ATTR_DATE: call.data.get(ATTR_DATE),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy.entities_add(endpoint, data)

    # TODO: handle unloading of children
    def services_delete(call):
        endpoint = call.data.get(ATTR_ENDPOINT).lower().replace(" ", "-")
        data = call.data.get(ATTR_ENTRY)

        baby_buddy.entities_delete(endpoint, data)

    hass.services.register(DOMAIN, "services_children_add", services_children_add)
    hass.services.register(DOMAIN, "services_changes_add", services_changes_add)
    hass.services.register(DOMAIN, "services_feedings_add", services_feedings_add)
    hass.services.register(DOMAIN, "services_notes_add", services_notes_add)
    hass.services.register(DOMAIN, "services_sleep_add", services_sleep_add)
    hass.services.register(DOMAIN, "services_temperature_add", services_temperature_add)
    # TODO: add timers service
    """hass.services.register(DOMAIN, "services_timers_add", services_timers_add)"""
    hass.services.register(DOMAIN, "services_tummy_times_add", services_tummy_times_add)
    hass.services.register(DOMAIN, "services_weight_add", services_weight_add)
    hass.services.register(DOMAIN, "services_delete", services_delete)


class BabyBuddySensor(Entity):
    """Representation of a Baby Buddy Sensor."""

    def __init__(self, data, baby_buddy):
        """Initialize the Baby Buddy sensor."""
        self._baby_buddy = baby_buddy
        self._data = data
        self._child = (
            self._data.get("slug")
            if self._data.get("slug")
            else self._data.get(ATTR_CHILD)
        )
        self._endpoint = self._data.get(ATTR_ENDPOINT)

    @property
    def name(self):
        """Return the name of the Baby Buddy sensor."""
        name = self._data.get(ATTR_CHILD_NAME)
        if self._endpoint != ATTR_CHILDREN:
            name = f"{name}_last_{self._endpoint}"
            if name[-1] == "s":
                name = name[:-1]
        name = name.replace("_", " ").title()
        return name

    @property
    def state(self):
        """Return the state of the Baby Buddy sensor."""
        keys = [ATTR_BIRTH_DATE, ATTR_DATE, ATTR_START, ATTR_TIME]
        state = [value for key, value in self._data.items() if key in keys][0]
        return state

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes for Baby Buddy."""
        attributes = []
        for attribute in self._data.items():
            attributes.append(attribute)
        return attributes

    @property
    def icon(self):
        """Return the icon to use in Baby Buddy frontend."""
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
        """Update data from Baby Buddy for the sensor."""
        if self._endpoint == ATTR_CHILDREN:
            return
        if not self._baby_buddy.form_address():
            return
        try:
            self._data = self._baby_buddy.entities_update(self._child, self._endpoint)[
                0
            ]

        except IndexError:
            _LOGGER.error(
                "Baby Buddy database entry %s has been removed since last Home Assistant start",
                self.name,
            )


class BabyBuddyData:
    """Coordinate retrieving and updating data from Baby Buddy."""

    def __init__(self, address, api_key, ssl, sensor_type):
        """Initialize the BabyBuddyData object."""
        self._address = address
        self._api_key = api_key
        self._ssl = ssl
        self._sensor_type = sensor_type
        self._formed_address = self.form_address()
        self._session = self.session()
        self.data = self.entities_get()

    # TODO: less expensive connection test
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

    def session(self):
        session = requests.Session()
        session.headers.update({"Authorization": f"Token {self._api_key}"})

        return session

    def entities_add(self, endpoint, data):
        add = self._session.post(f"{self._formed_address}{endpoint}/", data=data)

        if not add.ok:
            _LOGGER.error(
                "Cannot create %s, check service fields and timezones of Home Assistant vs. Baby Buddy",
                endpoint,
            )

    def entities_get(self) -> list:
        """Populate data via Baby Buddy API."""
        data = []

        children = self._session.get(f"{self._formed_address}{ATTR_CHILDREN}/")
        children = children.json()
        children = children[ATTR_RESULTS]
        for child in children:
            child_name = f"{child[ATTR_FIRST_NAME]}_{child[ATTR_LAST_NAME]}"
            child[ATTR_CHILD_NAME] = child_name
            child[ATTR_ENDPOINT] = ATTR_CHILDREN
            data.append(child)
            for endpoint in self._sensor_type:
                endpoint_data = self._session.get(
                    f"{self._formed_address}{endpoint}/?child={child[ATTR_ID]}&limit=1"
                )
                endpoint_data = endpoint_data.json()
                endpoint_data = endpoint_data[ATTR_RESULTS]
                if endpoint_data:
                    endpoint_data = endpoint_data[0]
                    endpoint_data[ATTR_CHILD_NAME] = child_name
                    endpoint_data[ATTR_ENDPOINT] = endpoint
                    data.append(endpoint_data)

        return data

    def entities_update(self, child: int = None, endpoint: str = None) -> list:
        if not child and not endpoint:
            return self.entities_get()

        data = []

        endpoint_data = self._session.get(
            f"{self._formed_address}{endpoint}/?child={child}&limit=1"
        )
        endpoint_data = endpoint_data.json()
        endpoint_data = endpoint_data[ATTR_RESULTS]
        if endpoint_data:
            endpoint_data = endpoint_data[0]
            endpoint_data[ATTR_ENDPOINT] = endpoint
            data.append(endpoint_data)

        return data

    def entities_delete(self, endpoint, data):
        delete = self._session.delete(f"{self._formed_address}{endpoint}/{data}/")

        if not delete.ok:
            _LOGGER.error(
                "Cannot delete %s, check service fields",
                endpoint,
            )
