# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

### Added

- Initial release
- `NRGkickAPI` client class for async communication
- Support for all NRGkick Gen2 REST API endpoints:
  - `get_info()` - Device information
  - `get_control()` - Control parameters
  - `get_values()` - Real-time telemetry
  - `set_current()` - Set charging current
  - `set_charge_pause()` - Pause/resume charging
  - `set_energy_limit()` - Set energy limit
  - `set_phase_count()` - Set phase count
  - `test_connection()` - Connection test
- Automatic retry logic with exponential backoff
- HTTP Basic Auth support
- Custom exception hierarchy:
  - `NRGkickError` - Base exception
  - `NRGkickConnectionError` - Network errors
  - `NRGkickAuthenticationError` - Auth failures
- Full type annotations
- Comprehensive documentation
