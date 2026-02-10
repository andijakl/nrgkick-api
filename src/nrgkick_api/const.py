"""Constants for the NRGkick API client."""

from __future__ import annotations

from typing import Final

# API Endpoints
ENDPOINT_INFO: Final = "/info"
ENDPOINT_CONTROL: Final = "/control"
ENDPOINT_VALUES: Final = "/values"

# Common query parameters
QUERY_PARAM_RAW: Final = "raw"
QUERY_VALUE_TRUE: Final = "1"
QUERY_VALUE_FALSE: Final = "0"

# Common JSON keys / payload fields
JSON_KEY_RESPONSE: Final = "Response"

# Control keys (used for both request params and response parsing)
CONTROL_KEY_CURRENT_SET: Final = "current_set"
CONTROL_KEY_CHARGE_PAUSE: Final = "charge_pause"
CONTROL_KEY_ENERGY_LIMIT: Final = "energy_limit"
CONTROL_KEY_PHASE_COUNT: Final = "phase_count"

# Retry configuration for transient errors
MAX_RETRIES: Final = 3
RETRY_BACKOFF_BASE: Final = 1.5  # seconds
RETRY_STATUSES: Final = frozenset({500, 502, 503, 504})  # Transient HTTP errors

# HTTP status codes
HTTP_ERROR_STATUS: Final = 400  # Status codes >= this indicate errors
