# nrgkick-api

Async Python client for NRGkick Gen2 EV charger local REST API.

[![PyPI version](https://badge.fury.io/py/nrgkick-api.svg)](https://badge.fury.io/py/nrgkick-api)
[![Python Versions](https://img.shields.io/pypi/pyversions/nrgkick-api.svg)](https://pypi.org/project/nrgkick-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This library provides an async Python interface for communicating with NRGkick Gen2 EV chargers via their local REST JSON API. It powers the [NRGkick integration in Home Assistant](https://www.home-assistant.io/integrations/nrgkick) but can be used standalone in any async Python application.

## Features

- **Async/await support** - Built on aiohttp for efficient async I/O
- **Automatic retry logic** - Handles transient network errors with exponential backoff
- **Authentication support** - Optional HTTP Basic Auth
- **Type hints** - Full type annotation for better IDE support
- **Enums for numeric codes** - `IntEnum` types for status, connector type, errors, etc.
- **Minimal dependencies** - Only requires aiohttp

## Installation

```bash
pip install nrgkick-api
```

## Quick Start

```python
import asyncio
import aiohttp
from nrgkick_api import NRGkickAPI


async def main():
    async with aiohttp.ClientSession() as session:
        api = NRGkickAPI(
            host="192.168.1.100",
            username="admin",  # Optional
            password="secret",  # Optional
            session=session,
        )

        # Get device information
        info = await api.get_info()
        print(f"Device: {info['general']['device_name']}")
        print(f"Serial: {info['general']['serial_number']}")

        # Get current values
        values = await api.get_values()
        print(f"Power: {values['powerflow']['total_active_power']}W")

        # Control charging
        await api.set_current(16.0)  # Set to 16A
        await api.set_charge_pause(True)  # Pause charging


asyncio.run(main())
```

## API Reference

### NRGkickAPI

The main client class for communicating with NRGkick devices.

#### Constructor

```python
NRGkickAPI(
    host: str,
    username: str | None = None,
    password: str | None = None,
    session: aiohttp.ClientSession | None = None,
)
```

- `host`: IP address or hostname of the NRGkick device
- `username`: Optional username for HTTP Basic Auth
- `password`: Optional password for HTTP Basic Auth
- `session`: aiohttp ClientSession (required for making requests)

#### Methods

| Method                                    | Description                          |
| ----------------------------------------- | ------------------------------------ |
| `get_info(sections=None, *, raw=False)`   | Get device information               |
| `get_control()`                           | Get current control parameters       |
| `get_values(sections=None, *, raw=False)` | Get real-time telemetry data         |
| `set_current(current)`                    | Set charging current (6.0-32.0A)     |
| `set_charge_pause(pause)`                 | Pause/resume charging                |
| `set_energy_limit(limit)`                 | Set energy limit in Wh (0=unlimited) |
| `set_phase_count(phases)`                 | Set phase count (1-3)                |
| `test_connection()`                       | Test device connectivity             |

#### Raw Mode

The `get_info()` and `get_values()` methods support a `raw` parameter. When `raw=True`, the API returns raw numeric values instead of human-readable strings for certain fields:

```python
# Normal mode (default) - returns strings
info = await api.get_info()
print(info["connector"]["type"])  # "CEE"
print(info["grid"]["phases"])  # "L1, L2, L3"

# Raw mode - returns numeric values
info = await api.get_info(raw=True)
print(info["connector"]["type"])  # 1
print(info["grid"]["phases"])  # 7

# Convert raw numeric values to enums (enums are exported from the package)
from nrgkick_api import ChargingStatus, ConnectorType, GridPhases

info = await api.get_info(["connector", "grid"], raw=True)
connector_type = ConnectorType(info["connector"]["type"])
grid_phases = GridPhases(info["grid"]["phases"])
print(connector_type)  # ConnectorType.CEE
print(grid_phases)  # GridPhases.L1_L2_L3

values = await api.get_values(["general"], raw=True)
charging_status = ChargingStatus(values["general"]["status"])
if charging_status is ChargingStatus.CHARGING:
    print("Charging")

# If you want to be defensive about new/unknown codes, catch ValueError
try:
    charging_status = ChargingStatus(values["general"]["status"])
except ValueError:
    charging_status = ChargingStatus.UNKNOWN

# Can be combined with sections
info = await api.get_info(["connector", "grid"], raw=True)
values = await api.get_values(["general"], raw=True)
```

### Exceptions

All exceptions inherit from `NRGkickError`.

```text
NRGkickError
├── NRGkickConnectionError
│   ├── NRGkickTimeoutError
│   ├── NRGkickUnreachableError
│   └── NRGkickHTTPError
├── NRGkickAuthenticationError
├── NRGkickAPIDisabledError
├── NRGkickCommandRejectedError
└── NRGkickInvalidResponseError
```

| Exception                     | Description                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| `NRGkickError`                | Base exception for all NRGkick errors                                                |
| `NRGkickConnectionError`      | Network/communication errors (base class; also raised for e.g. a connection reset)   |
| `NRGkickTimeoutError`         | The device did not respond in time                                                   |
| `NRGkickUnreachableError`     | No connection could be established (connection refused, DNS failure, no route)      |
| `NRGkickHTTPError`            | The device answered with an HTTP error status; the code is in `status: int`          |
| `NRGkickAuthenticationError`  | Authentication failures (401/403)                                                    |
| `NRGkickAPIDisabledError`     | Device JSON API is disabled                                                          |
| `NRGkickCommandRejectedError` | Device explicitly rejected a command (reason is user-facing)                         |
| `NRGkickInvalidResponseError` | Unexpected/malformed payload (invalid JSON, not an object, missing keys, wrong type) |

Transient errors (timeouts, network errors, HTTP 5xx) are retried up to `MAX_RETRIES` times before an exception is raised.

#### Connection errors

The exception type (plus `status` for `NRGkickHTTPError`) tells you what went wrong, so you can build your own, e.g. translated, message. The exception text is English and intended for logs; it may include the device URL.

```python
from nrgkick_api import (
    NRGkickConnectionError,
    NRGkickHTTPError,
    NRGkickTimeoutError,
    NRGkickUnreachableError,
)

try:
    values = await api.get_values()
except NRGkickTimeoutError:
    ...  # The charger did not respond in time
except NRGkickUnreachableError:
    ...  # The charger could not be reached
except NRGkickHTTPError as err:
    ...  # The charger answered with HTTP error err.status
except NRGkickConnectionError:
    ...  # Any other communication error
```

Because the specific types are subclasses of `NRGkickConnectionError`, code that only catches `NRGkickConnectionError` keeps working.

#### Command rejections vs invalid responses

- `NRGkickCommandRejectedError`: The device accepted the HTTP request but refused to apply the command. The `reason` string is safe to display to users.
- `NRGkickInvalidResponseError`: The device (or protocol) returned an unexpected payload shape/type (e.g., a body that is not valid JSON, missing expected key, wrong type that cannot be coerced).

Note: The device may also return HTTP errors like `406 Not Acceptable` for invalid command inputs, but still include a JSON payload with a `Response` string. This library treats that as a device command rejection and raises `NRGkickCommandRejectedError`.

## API Endpoints

The library communicates with three main endpoints:

- `/info` - Device information (serial, model, versions, etc.)
- `/control` - Control parameters (current, pause, limits)
- `/values` - Real-time telemetry (power, energy, temperatures)

## Requirements

- Python 3.14+
- aiohttp 3.14.5+
- NRGkick Gen2 with JSON API enabled

## Enabling the JSON API

The local REST API must be enabled in the NRGkick mobile app:

1. Open the NRGkick app
2. Connect to your device
3. Navigate to Settings → JSON API
4. Enable the API
5. Optionally configure authentication

If the JSON API is disabled, the device may respond with `{"Response":"API must be enabled within the NRGkick App"}`.
In that case, this library raises `NRGkickAPIDisabledError`.

## Development

The project uses [uv](https://docs.astral.sh/uv/). To create the virtual environment (`.venv`) with all development dependencies and run the checks:

```bash
uv sync
./validate.sh
```

Single tools can be run with `uv run`, e.g. `uv run pytest` or `uv run mypy src/nrgkick_api`.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [NRGkick integration for Home Assistant](https://www.home-assistant.io/integrations/nrgkick) - Home Assistant core integration using this library ([source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/nrgkick))

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for notable changes.
