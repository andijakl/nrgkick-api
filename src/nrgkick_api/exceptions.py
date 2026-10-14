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

    Base class for all transport-level errors. The subclasses below identify
    the specific cause, so consumers can map them to their own (translated)
    messages without parsing the English exception text.

    Raised directly (not as a subclass) when the exchange with the device
    broke off for another reason, e.g. the connection was reset or the
    server disconnected mid-response.
    """


class NRGkickTimeoutError(NRGkickConnectionError):
    """Exception raised when the device did not respond in time.

    Covers both connect and read timeouts, after all retries are exhausted.
    """


class NRGkickUnreachableError(NRGkickConnectionError):
    """Exception raised when no connection to the device could be established.

    Raised when, after all retries are exhausted:
    - The connection is refused
    - The hostname cannot be resolved (DNS failure)
    - The network or host is unreachable
    """


class NRGkickHTTPError(NRGkickConnectionError):
    """Exception raised when the device answers with an HTTP error status.

    Authentication failures (HTTP 401/403) raise NRGkickAuthenticationError
    instead.

    Attributes:
        status: HTTP status code returned by the device.
    """

    def __init__(self, message: str, *, status: int) -> None:
        super().__init__(message)
        self.status = status


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

    This indicates a protocol mismatch: a body that is not valid JSON, an
    empty or non-object payload, missing keys, or values that cannot be
    coerced to the expected type.

    Attributes:
        message: Human-readable explanation of what was invalid.
        raw: Optional raw payload.
    """

    def __init__(self, message: str, *, raw: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.raw = raw
