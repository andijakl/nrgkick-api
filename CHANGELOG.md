# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-13

### Changed

- Migrated linting stack from black, isort, flake8, and pylint to **ruff**
- Updated pre-commit hooks to latest versions:
  - pre-commit-hooks v6.0.0
  - ruff-pre-commit v0.14.9
  - mirrors-mypy v1.19.0
- Code formatting improvements via ruff formatter
- Aligned ruff configuration with Home Assistant core standards

### Added

- `ruff.toml` configuration file
- `validate.sh` script for local validation
- `create_release.sh` script for release preparation
- GitHub issue templates (bug report, feature request)
- `HTTP_ERROR_STATUS` constant for improved code clarity

### Removed

- Deprecated linting tools: black, isort, flake8, pylint
- `.flake8` configuration file (replaced by ruff.toml)

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
