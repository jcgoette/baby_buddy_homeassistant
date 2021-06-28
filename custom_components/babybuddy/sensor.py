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
from homeassistant.core import Service
from homeassistant.helpers.entity import Entity
from requests_toolbelt import sessions

from .const import (
    ATTR_AMOUNT,
    ATTR_BIRTH_DATE,
    ATTR_CHANGES,
    ATTR_CHILD,
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

    baby_buddy_data = BabyBuddyData(address, api_key, ssl, sensor_type)
    if not baby_buddy_data.form_address():
        return

    sensors = []

    # TODO: refactor entity creation
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

    # TODO: handle loading of children
    def services_children_add(call):
        endpoint = ATTR_CHILDREN
        data = {
            ATTR_FIRST_NAME: call.data.get(ATTR_FIRST_NAME),
            ATTR_LAST_NAME: call.data.get(ATTR_LAST_NAME),
            ATTR_BIRTH_DATE: call.data.get(ATTR_BIRTH_DATE),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_changes_add(call):
        endpoint = ATTR_CHANGES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_TIME: call.data.get(ATTR_TIME),
            ATTR_WET: call.data.get(ATTR_WET),
            ATTR_SOLID: call.data.get(ATTR_SOLID),
            ATTR_COLOR: call.data.get(ATTR_COLOR).lower(),
            ATTR_AMOUNT: call.data.get(ATTR_AMOUNT),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_feedings_add(call):
        endpoint = ATTR_FEEDINGS
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_TYPE: call.data.get(ATTR_TYPE).lower(),
            ATTR_METHOD: call.data.get(ATTR_METHOD).lower(),
            ATTR_AMOUNT: call.data.get(ATTR_AMOUNT),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_notes_add(call):
        endpoint = ATTR_NOTES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_NOTE: call.data.get(ATTR_NOTE),
            ATTR_TIME: call.data.get(ATTR_TIME),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_sleep_add(call):
        endpoint = ATTR_SLEEP
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_temperature_add(call):
        endpoint = ATTR_TEMPERATURE
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_TEMPERATURE: call.data.get(ATTR_TEMPERATURE),
            ATTR_TIME: call.data.get(ATTR_TIME),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy_data.entities_add(endpoint, data)

    """
    def services_timers_add(call):
        endpoint = ATTR_TIMERS
        data = {}

        baby_buddy_data.entities_add(endpoint, data)
    """

    def services_tummy_times_add(call):
        endpoint = ATTR_TUMMY_TIMES
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_START: call.data.get(ATTR_START),
            ATTR_END: call.data.get(ATTR_END),
            ATTR_MILESTONE: call.data.get(ATTR_MILESTONE),
        }

        baby_buddy_data.entities_add(endpoint, data)

    def services_weight_add(call):
        endpoint = ATTR_WEIGHT
        data = {
            ATTR_CHILD: hass.states.get(call.data.get(ATTR_CHILD)).attributes.get("id"),
            ATTR_WEIGHT: call.data.get(ATTR_WEIGHT),
            ATTR_DATE: call.data.get(ATTR_DATE),
            ATTR_NOTES: call.data.get(ATTR_NOTES),
        }

        baby_buddy_data.entities_add(endpoint, data)

    # TODO: handle unloading of children
    def services_delete(call):
        endpoint = call.data.get(ATTR_ENDPOINT).lower().replace(" ", "-")
        data = call.data.get(ATTR_ENTRY)

        baby_buddy_data.entities_delete(endpoint, data)

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

    def __init__(self, baby_buddy_data, name, data, endpoint):
        """Initialize the Baby Buddy sensor."""
        self._baby_buddy_data = baby_buddy_data
        self._name = name
        self._data = self._state = data
        self._endpoint = endpoint

    @property
    def name(self):
        """Return the name of the Baby Buddy sensor."""
        name = self._name.replace("_", " ").title()
        if name[-1] == "s" and self._endpoint:
            return name[:-1]
        return name

    @property
    def state(self):
        """Return the state of the Baby Buddy sensor."""
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
    """Coordinate retrieving and updating data from Baby Buddy."""

    def __init__(self, address, api_key, ssl, sensor_type):
        """Initialize the BabyBuddyData object."""
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

    def session(self):
        session = sessions.BaseUrlSession(base_url=self.form_address())
        session.headers = {"Authorization": f"Token {self._api_key}"}

        return session

    def entities_add(self, endpoint, data):
        add = self.session().post(f"{endpoint}/", data=data)

        if not add.ok:
            _LOGGER.error(
                "Cannot create %s, check service fields",
                endpoint,
            )

    def entities_get(self):
        sensors = []

        children = self.session().get("children/").json()
        children = children[ATTR_RESULTS]
        for child in children:
            child_name = f"{child[ATTR_FIRST_NAME]}_{child[ATTR_LAST_NAME]}"
            sensors.append((child_name, child, None))
            for endpoint in self._sensor_type:
                r = self.session().get(f"{endpoint}").json()
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

    def entities_delete(self, endpoint, data):
        delete = self.session().delete(f"{endpoint}/{data}/")

        if not delete.ok:
            _LOGGER.error(
                "Cannot delete %s, check service fields",
                endpoint,
            )
