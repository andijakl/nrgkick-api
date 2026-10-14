# Changelog

## 1.8.0

### ⚠️ Behaviour change

Malformed responses with a successful HTTP status now raise `NRGkickInvalidResponseError` instead of `NRGkickConnectionError`. This affects:

- a response body that is not valid JSON ("Invalid JSON response")
- an empty JSON body (`null`, "No data returned")
- a JSON body that is not an object, e.g. a list or string ("Unexpected response type"); the payload is available as `raw`

If you relied on `except NRGkickConnectionError` for these cases, also catch `NRGkickInvalidResponseError` (or catch `NRGkickError`).

HTTP error statuses (≥ 400, except 401/403) are now consistently reported as `NRGkickHTTPError`:

- Read calls (`get_info`, `get_control`, `get_values`, `test_connection`) now raise `NRGkickHTTPError` when the device answers with an error status and a `Response` message, e.g. `404 {"Response": "Error 404 - ..."}` or `501 {"Response": "Error 501 - Invalid parameter"}` for an unknown section. Previously this message was returned as if it were regular data.
- An error status with an empty or non-object body is reported as `NRGkickHTTPError` instead of a malformed payload.

Control commands (`set_*`) are unchanged: an error status with a `Response` message (e.g. `406 Invalid current entered`) still raises `NRGkickCommandRejectedError`.

### Added

- New subclasses of `NRGkickConnectionError` that identify the cause of a communication error, so consumers can show their own (e.g. translated) message without parsing the English exception text:
  - `NRGkickTimeoutError`: the device did not respond in time.
  - `NRGkickUnreachableError`: no connection could be established (connection refused, DNS failure, network unreachable).
  - `NRGkickHTTPError`: the device answered with an HTTP error status; the code is available as `status: int`.

  Other communication errors (e.g. a connection reset or the server disconnecting mid-response) still raise `NRGkickConnectionError` itself. Existing code that catches `NRGkickConnectionError` or `NRGkickError` keeps working unchanged.

### Changed

- Requires Python 3.14 or newer (in line with Home Assistant).
- Requires aiohttp 3.14.5 or newer.
- Basic Auth credentials are sent as an `Authorization` header instead of using the deprecated `aiohttp.BasicAuth` (same latin-1 encoding as before).
- Development tooling updated: ruff 0.17, mypy 2.4, pytest-asyncio 1.4, current GitHub Actions versions.
- The project now uses [uv](https://docs.astral.sh/uv/) for development, CI and publishing. Development dependencies moved from the `dev` extra to a `dev` dependency group (`uv sync`), so `pip install nrgkick-api[dev]` is no longer available. A `uv.lock` file pins the development environment.

### Fixed

- Documentation of the available sections: `get_values()` accepts `general`, `energy`, `powerflow` and `temperatures` (not `status`; the charging status is `values["general"]["status"]`), and `get_info()` also supports `cellular` and `gps`.
