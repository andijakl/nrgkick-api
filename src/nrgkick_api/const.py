"""Constants for the NRGkick API client."""

from __future__ import annotations

from typing import Final

# API Endpoints
ENDPOINT_INFO: Final = "/info"
ENDPOINT_CONTROL: Final = "/control"
ENDPOINT_VALUES: Final = "/values"

# Retry configuration for transient errors
MAX_RETRIES: Final = 3
RETRY_BACKOFF_BASE: Final = 1.5  # seconds
RETRY_STATUSES: Final = frozenset({500, 502, 503, 504})  # Transient HTTP errors

# HTTP status codes
HTTP_ERROR_STATUS: Final = 400  # Status codes >= this indicate errors
