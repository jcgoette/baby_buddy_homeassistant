"""Baby buddy client class"""  # pylint: disable=logging-fstring-interpolation
from __future__ import annotations

import logging
from asyncio import TimeoutError as AsyncIOTimeoutError
from datetime import datetime, time
from http import HTTPStatus
from typing import Any

import async_timeout
import homeassistant.util.dt as dt_util
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientError, ClientResponseError
from homeassistant.const import ATTR_DATE, ATTR_TIME

from .errors import AuthorizationError, ConnectError, ValidationError

_LOGGER = logging.getLogger(__name__)


class BabyBuddyClient:
    """Class for babybuddy API interface."""

    def __init__(
        self, host: str, port: int, path: str, api_key: str, session: ClientSession
    ) -> None:
        """Initialize the client."""
        _LOGGER.debug("Initializing BabyBuddyClient")
        self.headers = {"Authorization": f"Token {api_key}"}
        _LOGGER.debug(
            f"Client API Token, obfuscated: {api_key[:4]}{'.' * (len(api_key)-8)}{api_key[-4:]}"
        )
        self.url = f"{host}:{port}{path}"
        _LOGGER.debug(f"Client URL: {host}:{port}{path}")
        self.session = session
        self.endpoints: dict[str, str] = {}

    async def async_get(
        self, endpoint: str | None = None, entry: str | None = None
    ) -> Any:
        """GET request to babybuddy API."""
        url = f"{self.url}/api/"
        if endpoint:
            url = self.endpoints[endpoint]
            if entry:
                url = f"{url}{entry}"
        with async_timeout.timeout(10):
            _LOGGER.debug(f"GET URL: {url}")
            resp = await self.session.get(
                url=url,
                headers=self.headers,
                raise_for_status=True,
            )

        _LOGGER.debug(f"GET response: {await resp.text()}")
        return await resp.json()

    async def async_post(
        self, endpoint: str, data: dict[str, Any], call_time: datetime | None = None
    ) -> None:
        """POST request to babybuddy API."""
        _LOGGER.debug(f"POST data: {data}")
        try:
            with async_timeout.timeout(10):
                resp = await self.session.post(
                    self.endpoints[endpoint],
                    headers=self.headers,
                    data=data,
                )
        except (AsyncIOTimeoutError, ClientError) as err:
            _LOGGER.error(err)

        if resp.status != HTTPStatus.CREATED:
            error = await resp.json()
            _LOGGER.error(
                f"Could not create {endpoint}. error: {error}. Please upgrade to babybuddy v1.11.0. In the meantime, attempting to use 'now()'..."
            )

            # crude backward compatibility fix for babybuddy < v1.11.0
            if error == {"time": ["This field is required."]}:
                data[ATTR_TIME] = call_time
                await self.async_post(endpoint, data)
            if error == {"date": ["This field is required."]}:
                data[ATTR_DATE] = call_time
                await self.async_post(endpoint, data)

    async def async_patch(
        self, endpoint: str, entry: str, data: dict[str, str]
    ) -> None:
        """PATCH request to babybuddy API."""
        try:
            with async_timeout.timeout(10):
                resp = await self.session.patch(
                    f"{self.endpoints[endpoint]}{entry}/",
                    headers=self.headers,
                    data=data,
                )
        except (AsyncIOTimeoutError, ClientError) as err:
            _LOGGER.error(err)

        if resp.status != HTTPStatus.OK:
            error = await resp.json()
            _LOGGER.error(f"Could not update {endpoint}/{entry}. error: {error}")

    async def async_delete(self, endpoint: str, entry: str) -> None:
        """DELETE request to babybuddy API."""
        try:
            with async_timeout.timeout(10):
                resp = await self.session.delete(
                    f"{self.endpoints[endpoint]}{entry}/",
                    headers=self.headers,
                )
        except (AsyncIOTimeoutError, ClientError) as err:
            _LOGGER.error(err)

        if resp.status != 204:
            error = await resp.json()
            _LOGGER.error(f"Could not delete {endpoint}/{entry}. error: {error}")

    async def async_connect(self) -> None:
        """Check connection to babybuddy API."""
        try:
            self.endpoints = await self.async_get()
            _LOGGER.debug(f"Endpoints: {self.endpoints}")
        except ClientResponseError as err:
            raise AuthorizationError from err
        except (TimeoutError, ClientError) as err:
            raise ConnectError(err) from err


def get_datetime_from_time(value: datetime | time) -> datetime:
    """Return datetime for start/end/time service fields."""
    if isinstance(value, time):
        value = datetime.combine(dt_util.now().date(), value, dt_util.DEFAULT_TIME_ZONE)
    if isinstance(value, datetime):
        value = value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    if value > dt_util.now():
        raise ValidationError("Time cannot be in the future.")
    return value
