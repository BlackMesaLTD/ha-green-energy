"""API client for Green Energy cloud service."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_TIMEOUT, DEFAULT_API_URL

_LOGGER = logging.getLogger(__name__)


class GreenEnergyApiError(Exception):
    """Base exception for API errors."""


class InvalidPairingCode(GreenEnergyApiError):
    """Invalid or expired pairing code."""


class CannotConnect(GreenEnergyApiError):
    """Cannot connect to the API."""


class AuthenticationError(GreenEnergyApiError):
    """Authentication failed."""


class GreenEnergyApiClient:
    """API client for Green Energy cloud service."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_url: str = DEFAULT_API_URL,
        token: str | None = None,
        instance_id: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._api_url = api_url.rstrip("/")
        self._token = token
        self._instance_id = instance_id

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def async_pair(self, pairing_code: str) -> dict[str, Any]:
        """Exchange pairing code for API token.

        Args:
            pairing_code: The 6-digit pairing code from the web app.

        Returns:
            Dict containing api_token, instance_id, and user_email.

        Raises:
            InvalidPairingCode: If the code is invalid or expired.
            CannotConnect: If unable to reach the API.
        """
        try:
            async with asyncio.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{self._api_url}/api/ha/pair",
                    json={"pairing_code": pairing_code},
                    headers=self._headers(),
                )

            if response.status == 400:
                data = await response.json()
                if data.get("error") == "invalid_code":
                    raise InvalidPairingCode("Invalid or expired pairing code")
                raise GreenEnergyApiError(data.get("error", "Unknown error"))

            if response.status == 401:
                raise InvalidPairingCode("Invalid or expired pairing code")

            if response.status != 200:
                raise GreenEnergyApiError(f"API returned status {response.status}")

            data = await response.json()

            # Store credentials for subsequent calls
            self._token = data["api_token"]
            self._instance_id = data["instance_id"]

            return data

        except asyncio.TimeoutError as err:
            raise CannotConnect("Request timed out") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Connection error: {err}") from err

    async def async_post_readings(self, readings: list[dict[str, Any]]) -> dict[str, Any]:
        """Post sensor readings to the cloud.

        Args:
            readings: List of reading dictionaries with entity_id, state, attributes, timestamp.

        Returns:
            Response dict with status, recommendations, and savings data.

        Raises:
            AuthenticationError: If token is invalid.
            CannotConnect: If unable to reach the API.
        """
        if not self._token or not self._instance_id:
            raise AuthenticationError("Not authenticated")

        payload = {
            "instance_id": self._instance_id,
            "readings": readings,
        }

        try:
            async with asyncio.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{self._api_url}/api/ha/readings",
                    json=payload,
                    headers=self._headers(),
                )

            if response.status == 401:
                raise AuthenticationError("Invalid or expired token")

            if response.status != 200:
                raise GreenEnergyApiError(f"API returned status {response.status}")

            return await response.json()

        except asyncio.TimeoutError as err:
            raise CannotConnect("Request timed out") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Connection error: {err}") from err

    async def async_get_status(self) -> dict[str, Any]:
        """Get current status and recommendations.

        Returns:
            Dict with connection status, recommendations, and savings.

        Raises:
            AuthenticationError: If token is invalid.
            CannotConnect: If unable to reach the API.
        """
        if not self._token or not self._instance_id:
            raise AuthenticationError("Not authenticated")

        try:
            async with asyncio.timeout(API_TIMEOUT):
                response = await self._session.get(
                    f"{self._api_url}/api/ha/status",
                    params={"instance_id": self._instance_id},
                    headers=self._headers(),
                )

            if response.status == 401:
                raise AuthenticationError("Invalid or expired token")

            if response.status != 200:
                raise GreenEnergyApiError(f"API returned status {response.status}")

            return await response.json()

        except asyncio.TimeoutError as err:
            raise CannotConnect("Request timed out") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Connection error: {err}") from err

    async def async_unpair(self) -> bool:
        """Revoke the integration token.

        Returns:
            True if successfully unpaired.

        Raises:
            AuthenticationError: If token is invalid.
            CannotConnect: If unable to reach the API.
        """
        if not self._token or not self._instance_id:
            raise AuthenticationError("Not authenticated")

        try:
            async with asyncio.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{self._api_url}/api/ha/unpair",
                    json={"instance_id": self._instance_id},
                    headers=self._headers(),
                )

            if response.status == 401:
                raise AuthenticationError("Invalid or expired token")

            return response.status == 200

        except asyncio.TimeoutError as err:
            raise CannotConnect("Request timed out") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Connection error: {err}") from err
