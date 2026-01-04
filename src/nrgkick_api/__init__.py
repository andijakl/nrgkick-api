"""Async Python client for NRGkick Gen2 EV charger local REST API."""

from importlib.metadata import PackageNotFoundError, version

from .api import NRGkickAPI
from .const import (
    ENDPOINT_CONTROL,
    ENDPOINT_INFO,
    ENDPOINT_VALUES,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    RETRY_STATUSES,
)
from .enums import (
    CellularMode,
    ChargingStatus,
    ConnectorType,
    ErrorCode,
    GridPhases,
    RcdTriggerStatus,
    RelayState,
    WarningCode,
)
from .exceptions import (
    NRGkickAPIDisabledError,
    NRGkickAuthenticationError,
    NRGkickConnectionError,
    NRGkickError,
)

__all__ = [
    "ENDPOINT_CONTROL",
    "ENDPOINT_INFO",
    "ENDPOINT_VALUES",
    "MAX_RETRIES",
    "RETRY_BACKOFF_BASE",
    "RETRY_STATUSES",
    "CellularMode",
    "ChargingStatus",
    "ConnectorType",
    "ErrorCode",
    "GridPhases",
    "NRGkickAPI",
    "NRGkickAPIDisabledError",
    "NRGkickAuthenticationError",
    "NRGkickConnectionError",
    "NRGkickError",
    "RcdTriggerStatus",
    "RelayState",
    "WarningCode",
]

try:
    __version__ = version("nrgkick-api")
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed (e.g., running from a source checkout)
    __version__ = "0.0.0"
