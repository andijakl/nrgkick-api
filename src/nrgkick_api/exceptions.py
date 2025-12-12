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
