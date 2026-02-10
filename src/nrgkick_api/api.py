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
    CONTROL_KEY_CHARGE_PAUSE,
    CONTROL_KEY_CURRENT_SET,
    CONTROL_KEY_ENERGY_LIMIT,
    CONTROL_KEY_PHASE_COUNT,
    ENDPOINT_CONTROL,
    ENDPOINT_INFO,
    ENDPOINT_VALUES,
    HTTP_ERROR_STATUS,
    JSON_KEY_RESPONSE,
    MAX_RETRIES,
    QUERY_PARAM_RAW,
    QUERY_VALUE_FALSE,
    QUERY_VALUE_TRUE,
    RETRY_BACKOFF_BASE,
    RETRY_STATUSES,
)
from .exceptions import (
    NRGkickAPIDisabledError,
    NRGkickAuthenticationError,
    NRGkickCommandRejectedError,
    NRGkickConnectionError,
    NRGkickError,
    NRGkickInvalidResponseError,
)

_LOGGER = logging.getLogger(__name__)


_CURRENT_SET_TOLERANCE = 0.1


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
                    _LOGGER.debug(
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
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    # If the server indicated an error status, keep the existing
                    # behavior of surfacing it via raise_for_status().
                    response.raise_for_status()
                    # For successful status codes, a non-JSON payload is an
                    # unexpected protocol/communication error.
                    raise NRGkickConnectionError(
                        f"Invalid JSON response from {url} (HTTP {response.status})."
                    ) from exc

                if data is None:
                    raise NRGkickConnectionError(
                        f"No data returned from {url} (HTTP {response.status})."
                    )

                # All known endpoints return a JSON object. If we get a list,
                # string, etc., surface it as a protocol error to consumers.
                if not isinstance(data, dict):
                    raise NRGkickConnectionError(
                        f"Unexpected response type {type(data).__name__} from {url} "
                        f"(HTTP {response.status})."
                    )

                # The device uses this JSON message when the local JSON API is disabled.
                if (
                    isinstance(data, dict)
                    and data.get(JSON_KEY_RESPONSE)
                    == "API must be enabled within the NRGkick App"
                ):
                    raise NRGkickAPIDisabledError(data[JSON_KEY_RESPONSE])

                # Check HTTP status after reading JSON
                if (
                    response.status >= HTTP_ERROR_STATUS
                    and JSON_KEY_RESPONSE not in data
                ):
                    response.raise_for_status()

                return data

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
                _LOGGER.debug(
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
                _LOGGER.debug(
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
                _LOGGER.debug(
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
            params[QUERY_PARAM_RAW] = QUERY_VALUE_TRUE
        if sections:
            for section in sections:
                params[section] = QUERY_VALUE_TRUE
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
            params[QUERY_PARAM_RAW] = QUERY_VALUE_TRUE
        if sections:
            for section in sections:
                params[section] = QUERY_VALUE_TRUE
        return await self._request(ENDPOINT_VALUES, params)

    @staticmethod
    def _validate_expected_value(
        *,
        expected_key: str,
        normalized: Any,
        expected_value: int | float | str | None,
        tolerance: float | None,
        raw: dict[str, Any],
    ) -> Any:
        """Validate a normalized value against an expected value.

        Note: `_parse_command_response` already normalizes `normalized` based on
        `expected_value`'s type. This helper focuses on value comparison.
        """
        if expected_value is None:
            return normalized

        if tolerance is not None and isinstance(expected_value, float):
            if not isinstance(normalized, float):
                raise NRGkickInvalidResponseError(
                    f"key '{expected_key}' expected float, got {normalized!r} ({type(normalized).__name__})",
                    raw=raw,
                )

            if abs(normalized - expected_value) > tolerance:
                raise NRGkickInvalidResponseError(
                    f"key '{expected_key}' expected {expected_value!r}±{tolerance!r}, got {normalized!r}",
                    raw=raw,
                )
            return normalized

        if normalized != expected_value:
            raise NRGkickInvalidResponseError(
                f"key '{expected_key}' expected {expected_value!r}, got {normalized!r}",
                raw=raw,
            )

        return normalized

    @staticmethod
    def _parse_command_response(
        raw: Any,
        *,
        expected_key: str,
        expected_value: int | float | str | None = None,
        tolerance: float | None = None,
    ) -> Any:
        """Parse and normalize a device command response.

        Args:
            raw: Parsed JSON response from the device.
            expected_key: Key expected to be present on success.
            expected_value: Optional value to validate against; also used to infer
                the expected type for normalization.

        Returns:
            The normalized value for expected_key.

        Raises:
            NRGkickCommandRejectedError: If device payload indicates rejection.
            NRGkickInvalidResponseError: If payload type/shape/value is unexpected.
        """
        if not isinstance(raw, dict):
            raise NRGkickInvalidResponseError(
                f"expected JSON object, got {type(raw).__name__}", raw=raw
            )

        response_reason = raw.get(JSON_KEY_RESPONSE)
        if isinstance(response_reason, str) and response_reason.strip():
            raise NRGkickCommandRejectedError(
                response_reason,
                raw=raw,
            )

        if expected_key not in raw:
            keys = ", ".join(sorted(str(k) for k in raw))
            raise NRGkickInvalidResponseError(
                f"missing expected key '{expected_key}' (keys: {keys})",
                raw=raw,
            )

        value = raw[expected_key]

        # Normalize value type based on expected_value, if provided.
        normalized: Any = value
        if isinstance(expected_value, int) and not isinstance(expected_value, bool):
            try:
                if isinstance(value, bool):
                    raise ValueError("bool is not a valid int payload")
                normalized = int(value)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                raise NRGkickInvalidResponseError(
                    f"key '{expected_key}' expected int, got {value!r} ({type(value).__name__})",
                    raw=raw,
                ) from exc
        elif isinstance(expected_value, float):
            try:
                if isinstance(value, bool):
                    raise ValueError("bool is not a valid float payload")
                normalized = float(value)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                raise NRGkickInvalidResponseError(
                    f"key '{expected_key}' expected float, got {value!r} ({type(value).__name__})",
                    raw=raw,
                ) from exc
        elif isinstance(expected_value, str):
            if not isinstance(value, str):
                raise NRGkickInvalidResponseError(
                    f"key '{expected_key}' expected str, got {value!r} ({type(value).__name__})",
                    raw=raw,
                )
            normalized = value

        return NRGkickAPI._validate_expected_value(
            expected_key=expected_key,
            normalized=normalized,
            expected_value=expected_value,
            tolerance=tolerance,
            raw=raw,
        )

    async def set_current(self, current: float) -> float:
        """Set charging current.

        Args:
            current: Desired charging current in amps (6.0-32.0).

        Returns:
            The updated current setpoint as float, as reported by the device.

        Raises:
            NRGkickCommandRejectedError: If the device rejects the command.
            NRGkickInvalidResponseError: If response payload is unexpected.
            NRGkickConnectionError: If the request fails.
        """
        raw = await self._request(ENDPOINT_CONTROL, {CONTROL_KEY_CURRENT_SET: current})
        actual = self._parse_command_response(
            raw,
            expected_key=CONTROL_KEY_CURRENT_SET,
            expected_value=float(current),
            tolerance=_CURRENT_SET_TOLERANCE,
        )
        return float(actual)

    async def set_charge_pause(self, pause: bool) -> int:
        """Set charge pause state.

        Args:
            pause: True to pause charging, False to resume.

        Returns:
            The updated pause state as int (0 or 1).

        Raises:
            NRGkickCommandRejectedError: If the device rejects the command.
            NRGkickInvalidResponseError: If response payload is unexpected.
            NRGkickConnectionError: If the request fails.
        """
        expected = 1 if pause else 0
        raw = await self._request(
            ENDPOINT_CONTROL,
            {
                CONTROL_KEY_CHARGE_PAUSE: QUERY_VALUE_TRUE
                if pause
                else QUERY_VALUE_FALSE
            },
        )
        return int(
            self._parse_command_response(
                raw,
                expected_key=CONTROL_KEY_CHARGE_PAUSE,
                expected_value=expected,
            )
        )

    async def set_energy_limit(self, limit: int) -> int:
        """Set energy limit for the charging session.

        Args:
            limit: Energy limit in Wh. Use 0 for unlimited.

        Returns:
            The updated energy limit as int (Wh).

        Raises:
            NRGkickCommandRejectedError: If the device rejects the command.
            NRGkickInvalidResponseError: If response payload is unexpected.
            NRGkickConnectionError: If the request fails.
        """
        raw = await self._request(ENDPOINT_CONTROL, {CONTROL_KEY_ENERGY_LIMIT: limit})
        return int(
            self._parse_command_response(
                raw,
                expected_key=CONTROL_KEY_ENERGY_LIMIT,
                expected_value=int(limit),
            )
        )

    async def set_phase_count(self, phases: int) -> int:
        """Set the number of phases for charging.

        Args:
            phases: Number of phases (1, 2, or 3).

        Returns:
            The updated phase count as int.

        Raises:
            NRGkickCommandRejectedError: If the device rejects the command.
            NRGkickInvalidResponseError: If response payload is unexpected.
            NRGkickConnectionError: If the request fails.
        """
        raw = await self._request(ENDPOINT_CONTROL, {CONTROL_KEY_PHASE_COUNT: phases})
        return int(
            self._parse_command_response(
                raw,
                expected_key=CONTROL_KEY_PHASE_COUNT,
                expected_value=int(phases),
            )
        )

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
