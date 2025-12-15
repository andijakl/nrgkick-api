# nrgkick-api

Async Python client for NRGkick Gen2 EV charger local REST API.

[![PyPI version](https://badge.fury.io/py/nrgkick-api.svg)](https://badge.fury.io/py/nrgkick-api)
[![Python Versions](https://img.shields.io/pypi/pyversions/nrgkick-api.svg)](https://pypi.org/project/nrgkick-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This library provides an async Python interface for communicating with NRGkick Gen2 EV chargers via their local REST JSON API. It is designed to be used with Home Assistant but can be used standalone in any async Python application.

## Features

- **Async/await support** - Built on aiohttp for efficient async I/O
- **Automatic retry logic** - Handles transient network errors with exponential backoff
- **Authentication support** - Optional HTTP Basic Auth
- **Type hints** - Full type annotation for better IDE support
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

| Method | Description |
|--------|-------------|
| `get_info(sections=None, *, raw=False)` | Get device information |
| `get_control()` | Get current control parameters |
| `get_values(sections=None, *, raw=False)` | Get real-time telemetry data |
| `set_current(current)` | Set charging current (6.0-32.0A) |
| `set_charge_pause(pause)` | Pause/resume charging |
| `set_energy_limit(limit)` | Set energy limit in Wh (0=unlimited) |
| `set_phase_count(phases)` | Set phase count (1-3) |
| `test_connection()` | Test device connectivity |

#### Raw Mode

The `get_info()` and `get_values()` methods support a `raw` parameter. When `raw=True`, the API returns raw numeric values instead of human-readable strings for certain fields:

```python
# Normal mode (default) - returns strings
info = await api.get_info()
print(info["connector"]["type"])  # "CEE"
print(info["grid"]["phases"])     # "L1, L2, L3"

# Raw mode - returns numeric values
info = await api.get_info(raw=True)
print(info["connector"]["type"])  # 1
print(info["grid"]["phases"])     # 7

# Can be combined with sections
info = await api.get_info(["connector", "grid"], raw=True)
values = await api.get_values(["status"], raw=True)
```

### Exceptions

| Exception | Description |
|-----------|-------------|
| `NRGkickError` | Base exception for all NRGkick errors |
| `NRGkickConnectionError` | Network/communication errors |
| `NRGkickAuthenticationError` | Authentication failures (401/403) |

## API Endpoints

The library communicates with three main endpoints:

- `/info` - Device information (serial, model, versions, etc.)
- `/control` - Control parameters (current, pause, limits)
- `/values` - Real-time telemetry (power, energy, temperatures)

## Requirements

- Python 3.11+
- aiohttp 3.8.0+
- NRGkick Gen2 with JSON API enabled

## Enabling the JSON API

The local REST API must be enabled in the NRGkick mobile app:

1. Open the NRGkick app
2. Connect to your device
3. Navigate to Settings → JSON API
4. Enable the API
5. Optionally configure authentication

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- [nrgkick-homeassistant](https://github.com/andijakl/nrgkick-homeassistant) - Home Assistant integration using this library
