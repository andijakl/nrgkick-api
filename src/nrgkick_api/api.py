"""NRGkick API client for local REST API communication.

This module provides an async Python client for communicating with
NRGkick Gen2 EV chargers via their local REST JSON API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError

from .const import (
    ENDPOINT_CONTROL,
    ENDPOINT_INFO,
    ENDPOINT_VALUES,
    HTTP_ERROR_STATUS,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    RETRY_STATUSES,
)
from .exceptions import NRGkickAuthenticationError, NRGkickConnectionError, NRGkickError

_LOGGER = logging.getLogger(__name__)


class NRGkickAPI:
    """API client for NRGkick Gen2 EV chargers.

    This client communicates with NRGkick devices via their local REST API.
    It supports authentication via HTTP Basic Auth and implements automatic
    retry logic for transient errors.

    Example:
        async with aiohttp.ClientSession() as session:
            api = NRGkickAPI(
                host="192.168.1.100",
                username="admin",
                password="secret",
                session=session,
            )
            info = await api.get_info()
            values = await api.get_values()
    """

    def __init__(
        self,
        host: str,
        username: str | None = None,
        password: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            host: IP address or hostname of the NRGkick device.
            username: Optional username for Basic Auth.
            password: Optional password for Basic Auth.
            session: Optional aiohttp ClientSession. If not provided,
                     a session must be set before making requests.
        """
        self.host = host
        self.username = username
        self.password = password
        self._session = session
        self._base_url = f"http://{host}"

    def _handle_auth_error(self, response_status: int, url: str) -> None:
        """Handle authentication errors with detailed logging.

        Args:
            response_status: HTTP status code (401 or 403).
            url: The URL that returned the auth error.

        Raises:
            NRGkickAuthenticationError: Always raised with details.
        """
        _LOGGER.warning(
            "Authentication failed (HTTP %d). Verify BasicAuth settings. Target: %s",
            response_status,
            url,
        )
        raise NRGkickAuthenticationError(
            f"Authentication failed with HTTP {response_status} for {url}. "
            "Please verify your username and password."
        )

    def _handle_timeout_error(self, exc: asyncio.TimeoutError, url: str) -> None:
        """Handle timeout errors with detailed troubleshooting info.

        Args:
            exc: The timeout exception.
            url: The URL that timed out.

        Raises:
            NRGkickConnectionError: Always raised with details.
        """
        _LOGGER.error(
            "Connection timeout after %d attempts. Target: %s", MAX_RETRIES, url
        )
        raise NRGkickConnectionError(
            f"Connection timeout after {MAX_RETRIES} attempts to {url}. "
            "Please check that the device is powered on and reachable."
        ) from exc

    def _handle_http_error(self, exc: aiohttp.ClientResponseError, url: str) -> None:
        """Handle HTTP response errors with troubleshooting info.

        Args:
            exc: The HTTP response error.
            url: The URL that returned the error.

        Raises:
            NRGkickConnectionError: Always raised with details.
        """
        _LOGGER.error(
            "Device returned HTTP error %d (%s). URL: %s",
            exc.status,
            exc.message,
            url,
        )
        raise NRGkickConnectionError(
            f"HTTP error {exc.status} ({exc.message}) from {url}. "
            "The device may be busy or experiencing issues."
        ) from exc

    def _handle_connection_error(
        self,
        exc: aiohttp.ClientConnectorError | aiohttp.ClientOSError,
        url: str,
    ) -> None:
        """Handle connection errors with troubleshooting info.

        Args:
            exc: The connection error.
            url: The URL that failed to connect.

        Raises:
            NRGkickConnectionError: Always raised with details.
        """
        _LOGGER.error(
            "Network connection failed after %d attempts: %s. Target: %s",
            MAX_RETRIES,
            exc,
            url,
        )
        raise NRGkickConnectionError(
            f"Failed to connect to {url} after {MAX_RETRIES} attempts: {exc}. "
            "Please check network connectivity and device availability."
        ) from exc

    def _handle_generic_error(self, exc: ClientError, url: str) -> None:
        """Handle generic client errors with troubleshooting info.

        Args:
            exc: The client error.
            url: The URL that caused the error.

        Raises:
            NRGkickConnectionError: Always raised with details.
        """
        _LOGGER.error(
            "Connection failed after %d attempts: %s. Target: %s",
            MAX_RETRIES,
            exc,
            url,
        )
        raise NRGkickConnectionError(
            f"Connection to {url} failed after {MAX_RETRIES} attempts: {exc}"
        ) from exc

    async def _make_request_attempt(  # pylint: disable=too-many-arguments
        self,
        *,
        session: aiohttp.ClientSession,
        url: str,
        auth: aiohttp.BasicAuth | None,
        params: dict[str, Any],
        attempt: int,
    ) -> dict[str, Any] | None:
        """Make a single request attempt, handling transient errors.

        Args:
            session: The aiohttp session to use.
            url: The full URL to request.
            auth: Optional Basic Auth credentials.
            params: Query parameters for the request.
            attempt: Current attempt number (0-indexed).

        Returns:
            Response data if successful, None if should retry.

        Raises:
            NRGkickAuthenticationError: If authentication fails.
        """
        async with asyncio.timeout(10):
            async with session.get(url, auth=auth, params=params) as response:
                # Check authentication (don't retry)
                if response.status in (401, 403):
                    self._handle_auth_error(response.status, url)

                # Retry on transient HTTP errors
                if response.status in RETRY_STATUSES and attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_BASE**attempt
                    _LOGGER.warning(
                        "Transient HTTP error %d from %s, "
                        "retrying in %.1f seconds (attempt %d/%d)",
                        response.status,
                        url,
                        wait_time,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(wait_time)
                    return None  # Signal retry needed

                # Read JSON response (even on errors)
                try:
                    data = await response.json()
                except Exception:  # pylint: disable=broad-exception-caught
                    response.raise_for_status()
                    return {}

                # Check HTTP status after reading JSON
                if response.status >= HTTP_ERROR_STATUS and "Response" not in data:
                    response.raise_for_status()

                return data if data is not None else {}

    async def _handle_retry_exception(
        self,
        exc: Exception,
        url: str,
        attempt: int,
    ) -> bool:
        """Handle exceptions during retry attempts.

        Args:
            exc: The exception that occurred.
            url: The URL that caused the exception.
            attempt: Current attempt number (0-indexed).

        Returns:
            True if should retry, False if should raise.

        Raises:
            NRGkickConnectionError: If retries exhausted or non-retryable error.
            NRGkickAuthenticationError: If auth error (via handlers).
        """
        if isinstance(exc, asyncio.TimeoutError):
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF_BASE**attempt
                _LOGGER.warning(
                    "Connection timeout to %s, retrying in %.1f "
                    "seconds (attempt %d/%d)",
                    url,
                    wait_time,
                    attempt + 1,
                    MAX_RETRIES,
                )
                await asyncio.sleep(wait_time)
                return True
            self._handle_timeout_error(exc, url)

        elif isinstance(exc, aiohttp.ClientResponseError):
            # Don't retry 4xx client errors
            self._handle_http_error(exc, url)

        elif isinstance(exc, aiohttp.ClientConnectorError | aiohttp.ClientOSError):
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF_BASE**attempt
                _LOGGER.warning(
                    "Network error connecting to %s: %s. "
                    "Retrying in %.1f seconds (attempt %d/%d)",
                    url,
                    str(exc),
                    wait_time,
                    attempt + 1,
                    MAX_RETRIES,
                )
                await asyncio.sleep(wait_time)
                return True
            self._handle_connection_error(exc, url)

        elif isinstance(exc, ClientError):
            # Generic aiohttp errors - retry with backoff
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF_BASE**attempt
                _LOGGER.warning(
                    "Client error connecting to %s: %s. "
                    "Retrying in %.1f seconds (attempt %d/%d)",
                    url,
                    str(exc),
                    wait_time,
                    attempt + 1,
                    MAX_RETRIES,
                )
                await asyncio.sleep(wait_time)
                return True
            self._handle_generic_error(exc, url)

        return False

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the API with automatic retry.

        Args:
            endpoint: API endpoint path (e.g., "/info").
            params: Optional query parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            RuntimeError: If session is not initialized.
            NRGkickAuthenticationError: If authentication fails.
            NRGkickConnectionError: If connection fails after retries.
        """
        if self._session is None:
            raise RuntimeError("Session not initialized")

        url = f"{self._base_url}{endpoint}"
        auth = None
        if self.username and self.password:
            auth = aiohttp.BasicAuth(self.username, self.password)

        request_params = params if params is not None else {}

        # Retry loop for transient errors
        last_exception: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                result = await self._make_request_attempt(
                    session=self._session,
                    url=url,
                    auth=auth,
                    params=request_params,
                    attempt=attempt,
                )
                if result is None:
                    # Transient error, retry requested
                    continue

                # Success - log if this was a retry
                if attempt > 0:
                    _LOGGER.info(
                        "Successfully connected to NRGkick after %d retry attempt(s)",
                        attempt,
                    )
                return result

            except NRGkickError:
                # Re-raise our own exceptions
                raise
            except Exception as exc:  # pylint: disable=broad-exception-caught
                last_exception = exc
                should_retry = await self._handle_retry_exception(exc, url, attempt)
                if should_retry:
                    continue
                # Exception handler raised its own exception, won't reach here
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise NRGkickConnectionError(
                f"Failed after {MAX_RETRIES} attempts to {url}. "
                f"Last error: {last_exception}"
            ) from last_exception
        return {}

    async def get_info(
        self,
        sections: list[str] | None = None,
        *,
        raw: bool = False,
    ) -> dict[str, Any]:
        """Get device information.

        Args:
            sections: Optional list of sections to retrieve.
                     Available: "general", "connector", "grid", "network", "versions"
                     If None, all sections are returned.
            raw: If True, return raw numeric values instead of human-readable strings.
                 For example, connector type returns 1 instead of "CEE".

        Returns:
            Device information dictionary with requested sections.

        Example:
            # Get all info
            info = await api.get_info()

            # Get specific sections
            info = await api.get_info(["general", "network"])

            # Get raw values
            info = await api.get_info(raw=True)
        """
        params: dict[str, Any] = {}
        if raw:
            params["raw"] = "1"
        if sections:
            for section in sections:
                params[section] = "1"
        return await self._request(ENDPOINT_INFO, params)

    async def get_control(self) -> dict[str, Any]:
        """Get control parameters.

        Returns:
            Current control settings including:
            - current_set: Charging current in amps
            - charge_pause: Pause state (0=charging, 1=paused)
            - energy_limit: Energy limit in Wh (0=unlimited)
            - phase_count: Number of phases (1-3)
        """
        return await self._request(ENDPOINT_CONTROL)

    async def get_values(
        self,
        sections: list[str] | None = None,
        *,
        raw: bool = False,
    ) -> dict[str, Any]:
        """Get current telemetry values.

        Args:
            sections: Optional list of sections to retrieve.
                     Available: "energy", "powerflow", "status", "temperatures"
                     If None, all sections are returned.
            raw: If True, return raw numeric values instead of human-readable strings.
                 For example, charging state returns numeric code instead of string.

        Returns:
            Current values dictionary with telemetry data.

        Example:
            # Get all values
            values = await api.get_values()

            # Get specific sections
            values = await api.get_values(["powerflow", "energy"])

            # Get raw values
            values = await api.get_values(raw=True)
        """
        params: dict[str, Any] = {}
        if raw:
            params["raw"] = "1"
        if sections:
            for section in sections:
                params[section] = "1"
        return await self._request(ENDPOINT_VALUES, params)

    async def set_current(self, current: float) -> dict[str, Any]:
        """Set charging current.

        Args:
            current: Desired charging current in amps (6.0-32.0).

        Returns:
            Response from the device confirming the new setting.

        Raises:
            NRGkickConnectionError: If the command fails.
        """
        return await self._request(ENDPOINT_CONTROL, {"current_set": current})

    async def set_charge_pause(self, pause: bool) -> dict[str, Any]:
        """Set charge pause state.

        Args:
            pause: True to pause charging, False to resume.

        Returns:
            Response from the device confirming the new state.

        Raises:
            NRGkickConnectionError: If the command fails.
        """
        return await self._request(
            ENDPOINT_CONTROL, {"charge_pause": "1" if pause else "0"}
        )

    async def set_energy_limit(self, limit: int) -> dict[str, Any]:
        """Set energy limit for the charging session.

        Args:
            limit: Energy limit in Wh. Use 0 for unlimited.

        Returns:
            Response from the device confirming the new limit.

        Raises:
            NRGkickConnectionError: If the command fails.
        """
        return await self._request(ENDPOINT_CONTROL, {"energy_limit": limit})

    async def set_phase_count(self, phases: int) -> dict[str, Any]:
        """Set the number of phases for charging.

        Args:
            phases: Number of phases (1, 2, or 3).

        Returns:
            Response from the device confirming the new setting.

        Raises:
            ValueError: If phases is not 1, 2, or 3.
            NRGkickConnectionError: If the command fails.
        """
        if phases not in [1, 2, 3]:
            raise ValueError("Phase count must be 1, 2, or 3")
        return await self._request(ENDPOINT_CONTROL, {"phase_count": phases})

    async def test_connection(self) -> bool:
        """Test if we can connect to the device.

        Returns:
            True if connection successful.

        Raises:
            NRGkickAuthenticationError: If authentication fails.
            NRGkickConnectionError: If connection fails.
        """
        await self.get_info(["general"])
        return True
