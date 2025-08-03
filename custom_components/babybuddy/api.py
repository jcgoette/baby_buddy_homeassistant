"""Client class for babybuddy integration."""

from __future__ import annotations

import asyncio
from asyncio import TimeoutError as AsyncIOTimeoutError
from datetime import datetime, time
from http import HTTPStatus
from typing import Any

from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientError, ClientResponseError

from homeassistant.const import ATTR_DATE, ATTR_TIME
import homeassistant.util.dt as dt_util

from .const import LOGGER
from .errors import AuthorizationError, ConnectError, ValidationError


class BabyBuddyClient:
    """Class for babybuddy API interface."""

    def __init__(
        self, host: str, port: int, path: str, api_key: str, session: ClientSession
    ) -> None:
        """Initialize the client."""
        LOGGER.debug("Initializing BabyBuddyClient")
        self.headers = {"Authorization": f"Token {api_key}"}
        LOGGER.debug(
            f"Client API Token, obfuscated: {api_key[:4]}{'.' * (len(api_key) - 8)}{api_key[-4:]}"
        )
        self.url = f"{host}:{port}{path}"
        LOGGER.debug(f"Client URL: {host}:{port}{path}")
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
        async with asyncio.timeout(10):
            LOGGER.debug(f"GET URL: {url}")
            resp = await self.session.get(
                url=url,
                headers=self.headers,
                raise_for_status=True,
            )

        LOGGER.debug(f"GET response: {await resp.text()}")
        return await resp.json()

    async def async_post(
        self, endpoint: str, data: dict[str, Any], call_time: datetime | None = None
    ) -> None:
        """POST request to babybuddy API."""
        LOGGER.debug(f"POST data: {data}")
        try:
            async with asyncio.timeout(10):
                resp = await self.session.post(
                    self.endpoints[endpoint],
                    headers=self.headers,
                    data=data,
                )

            if resp.status != HTTPStatus.CREATED:
                error = await resp.json()
                LOGGER.error(
                    f"Could not create {endpoint}. error: {error}. Please upgrade to babybuddy v1.11.0. In the meantime, attempting to use 'now()'..."
                )

                # crude backward compatibility fix for babybuddy < v1.11.0
                if error == {"time": ["This field is required."]}:
                    data[ATTR_TIME] = call_time
                    await self.async_post(endpoint, data)
                if error == {"date": ["This field is required."]}:
                    data[ATTR_DATE] = call_time
                    await self.async_post(endpoint, data)

        except (AsyncIOTimeoutError, ClientError) as error:
            LOGGER.error(error)

    async def async_patch(
        self, endpoint: str, entry: str, data: dict[str, str]
    ) -> None:
        """PATCH request to babybuddy API."""
        try:
            async with asyncio.timeout(10):
                resp = await self.session.patch(
                    f"{self.endpoints[endpoint]}{entry}/",
                    headers=self.headers,
                    data=data,
                )

            if resp.status != HTTPStatus.OK:
                error = await resp.json()
                LOGGER.error(f"Could not update {endpoint}/{entry}. error: {error}")

        except (AsyncIOTimeoutError, ClientError) as error:
            LOGGER.error(error)

    async def async_delete(self, endpoint: str, entry: str) -> None:
        """DELETE request to babybuddy API."""
        try:
            async with asyncio.timeout(10):
                resp = await self.session.delete(
                    f"{self.endpoints[endpoint]}{entry}/",
                    headers=self.headers,
                )

            if resp.status != 204:
                error = await resp.json()
                LOGGER.error(f"Could not delete {endpoint}/{entry}. error: {error}")

        except (AsyncIOTimeoutError, ClientError) as error:
            LOGGER.error(error)

    async def async_connect(self) -> None:
        """Check connection to babybuddy API."""
        try:
            self.endpoints = await self.async_get()
            LOGGER.debug(f"Endpoints: {self.endpoints}")
        except ClientResponseError as error:
            raise AuthorizationError from error
        except (TimeoutError, ClientError) as error:
            raise ConnectError(error) from error


def get_datetime_from_time(value: datetime | time) -> datetime:
    """Return datetime for start/end/time service fields."""
    if isinstance(value, time):
        value = datetime.combine(dt_util.now().date(), value, dt_util.DEFAULT_TIME_ZONE)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    if value > dt_util.now():
        raise ValidationError("Time cannot be in the future.")
    return value
