"""Async Python client for NRGkick Gen2 EV charger local REST API."""

from importlib.metadata import PackageNotFoundError, version

from .api import NRGkickAPI
from .const import (
    CONTROL_KEY_CHARGE_PAUSE,
    CONTROL_KEY_CURRENT_SET,
    CONTROL_KEY_ENERGY_LIMIT,
    CONTROL_KEY_PHASE_COUNT,
    ENDPOINT_CONTROL,
    ENDPOINT_INFO,
    ENDPOINT_VALUES,
    JSON_KEY_RESPONSE,
    MAX_RETRIES,
    QUERY_PARAM_RAW,
    QUERY_VALUE_FALSE,
    QUERY_VALUE_TRUE,
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
    NRGkickCommandRejectedError,
    NRGkickConnectionError,
    NRGkickError,
    NRGkickInvalidResponseError,
)

__all__ = [
    "CONTROL_KEY_CHARGE_PAUSE",
    "CONTROL_KEY_CURRENT_SET",
    "CONTROL_KEY_ENERGY_LIMIT",
    "CONTROL_KEY_PHASE_COUNT",
    "ENDPOINT_CONTROL",
    "ENDPOINT_INFO",
    "ENDPOINT_VALUES",
    "JSON_KEY_RESPONSE",
    "MAX_RETRIES",
    "QUERY_PARAM_RAW",
    "QUERY_VALUE_FALSE",
    "QUERY_VALUE_TRUE",
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
    "NRGkickCommandRejectedError",
    "NRGkickConnectionError",
    "NRGkickError",
    "NRGkickInvalidResponseError",
    "RcdTriggerStatus",
    "RelayState",
    "WarningCode",
]

try:
    __version__ = version("nrgkick-api")
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed (e.g., running from a source checkout)
    __version__ = "0.0.0"
