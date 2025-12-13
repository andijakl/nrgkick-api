"""Async Python client for NRGkick Gen2 EV charger local REST API."""

from .api import NRGkickAPI
from .const import (
    ENDPOINT_CONTROL,
    ENDPOINT_INFO,
    ENDPOINT_VALUES,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    RETRY_STATUSES,
)
from .exceptions import NRGkickAuthenticationError, NRGkickConnectionError, NRGkickError

__all__ = [
    "ENDPOINT_CONTROL",
    "ENDPOINT_INFO",
    "ENDPOINT_VALUES",
    "MAX_RETRIES",
    "RETRY_BACKOFF_BASE",
    "RETRY_STATUSES",
    "NRGkickAPI",
    "NRGkickAuthenticationError",
    "NRGkickConnectionError",
    "NRGkickError",
]

__version__ = "1.0.0"
