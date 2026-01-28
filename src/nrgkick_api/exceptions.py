"""Exceptions for the NRGkick API client."""

from __future__ import annotations


class NRGkickError(Exception):
    """Base exception for NRGkick API errors.

    All NRGkick-specific exceptions inherit from this class,
    allowing consumers to catch all NRGkick errors with a single
    except clause if desired.
    """


class NRGkickConnectionError(NRGkickError):
    """Exception for connection and communication errors.

    Raised when:
    - Connection to the device times out
    - Network errors occur (device unreachable)
    - HTTP 5xx server errors persist after retries
    - Other aiohttp client errors occur
    """


class NRGkickAuthenticationError(NRGkickError):
    """Exception for authentication errors.

    Raised when:
    - HTTP 401 Unauthorized is returned
    - HTTP 403 Forbidden is returned
    - Invalid credentials are provided
    """


class NRGkickAPIDisabledError(NRGkickError):
    """Exception raised when the device JSON API is disabled.

    The device can respond with a JSON payload indicating that the local JSON
    API must be enabled in the NRGkick app.
    """


class NRGkickCommandRejectedError(NRGkickError):
    """Exception raised when the device explicitly rejects a command.

    The device may return HTTP 200 but include a JSON payload like:
    {"Response": "Charging pause is blocked by solar-charging"}

    Attributes:
        reason: User-facing reason string returned by the device.
        raw: Optional raw payload.
    """

    def __init__(self, reason: str, *, raw: dict[str, object] | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw = raw


class NRGkickInvalidResponseError(NRGkickError):
    """Exception raised when a response payload does not match expectations.

    This indicates a protocol mismatch, unexpected payload type, missing keys,
    or values that cannot be coerced to the expected type.

    Attributes:
        message: Human-readable explanation of what was invalid.
        raw: Optional raw payload.
    """

    def __init__(self, message: str, *, raw: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.raw = raw
