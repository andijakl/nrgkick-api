"""Tests for the nrgkick_api API client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

import aiohttp
import pytest

from nrgkick_api import NRGkickAPI, NRGkickAuthenticationError, NRGkickConnectionError


@pytest.fixture
def mock_session():
    """Mock aiohttp session."""
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"test": "data"})
    response.raise_for_status = MagicMock()  # Not async, just a regular method

    # Create a proper async context manager mock
    mock_get = MagicMock()
    mock_get.__aenter__ = AsyncMock(return_value=response)
    mock_get.__aexit__ = AsyncMock(return_value=None)

    session.get = MagicMock(return_value=mock_get)

    return session


class TestAPIInitialization:
    """Tests for API client initialization."""

    async def test_api_init(self):
        """Test API initialization."""
        api = NRGkickAPI(
            host="192.168.1.100",
            username="test_user",
            password="test_pass",
            session=AsyncMock(),
        )

        assert api.host == "192.168.1.100"
        assert api.username == "test_user"
        assert api.password == "test_pass"
        assert api._base_url == "http://192.168.1.100"

    async def test_api_init_no_auth(self):
        """Test API initialization without authentication."""
        api = NRGkickAPI(host="192.168.1.100", session=AsyncMock())

        assert api.host == "192.168.1.100"
        assert api.username is None
        assert api.password is None

    async def test_api_no_session_raises(self):
        """Test that API raises error when session is not set."""
        api = NRGkickAPI(host="192.168.1.100")

        with pytest.raises(RuntimeError, match="Session not initialized"):
            await api.get_info()


class TestAPIGetMethods:
    """Tests for API GET methods."""

    async def test_get_info(self, mock_session):
        """Test get_info API call."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "general": {"device_name": "Test"}
        }

        result = await api.get_info()

        assert result == {"general": {"device_name": "Test"}}
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/info"

    async def test_get_info_with_sections(self, mock_session):
        """Test get_info with specific sections."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.get_info(["general", "network"])

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"general": "1", "network": "1"}

    async def test_get_info_with_raw_mode(self, mock_session):
        """Test get_info with raw mode enabled."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "connector": {"type": 1}  # Raw numeric value instead of "CEE"
        }

        result = await api.get_info(raw=True)

        assert result == {"connector": {"type": 1}}
        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"raw": "1"}

    async def test_get_info_with_sections_and_raw(self, mock_session):
        """Test get_info with both sections and raw mode."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.get_info(["connector", "grid"], raw=True)

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"raw": "1", "connector": "1", "grid": "1"}

    async def test_get_control(self, mock_session):
        """Test get_control API call."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "charging_current": 16.0
        }

        result = await api.get_control()

        assert result == {"charging_current": 16.0}
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/control"

    async def test_get_values(self, mock_session):
        """Test get_values API call."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "powerflow": {"power": {"total": 11000}}
        }

        result = await api.get_values()

        assert result == {"powerflow": {"power": {"total": 11000}}}
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/values"

    async def test_get_values_with_sections(self, mock_session):
        """Test get_values with specific sections."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.get_values(["powerflow", "energy"])

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"powerflow": "1", "energy": "1"}

    async def test_get_values_with_raw_mode(self, mock_session):
        """Test get_values with raw mode enabled."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.json.return_value = {
            "status": {"charging_state": 2}  # Raw numeric value
        }

        result = await api.get_values(raw=True)

        assert result == {"status": {"charging_state": 2}}
        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"raw": "1"}

    async def test_get_values_with_sections_and_raw(self, mock_session):
        """Test get_values with both sections and raw mode."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.get_values(["status", "powerflow"], raw=True)

        call_args = mock_session.get.call_args
        params = call_args[1]["params"]
        assert params == {"raw": "1", "status": "1", "powerflow": "1"}


class TestAPISetMethods:
    """Tests for API SET/control methods."""

    async def test_set_current(self, mock_session):
        """Test set_current API call."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.set_current(16.0)

        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/control"
        assert call_args[1]["params"] == {"current_set": 16.0}

    async def test_set_charge_pause_true(self, mock_session):
        """Test set_charge_pause with pause=True."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.set_charge_pause(True)

        call_args = mock_session.get.call_args
        assert call_args[1]["params"] == {"charge_pause": "1"}

    async def test_set_charge_pause_false(self, mock_session):
        """Test set_charge_pause with pause=False."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.set_charge_pause(False)

        call_args = mock_session.get.call_args
        assert call_args[1]["params"] == {"charge_pause": "0"}

    async def test_set_energy_limit(self, mock_session):
        """Test set_energy_limit API call."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        await api.set_energy_limit(5000)

        call_args = mock_session.get.call_args
        assert call_args[1]["params"] == {"energy_limit": 5000}

    async def test_set_phase_count_valid(self, mock_session):
        """Test set_phase_count with valid values."""
        api = NRGkickAPI(host="192.168.1.100", session=mock_session)

        for phases in [1, 2, 3]:
            await api.set_phase_count(phases)
            call_args = mock_session.get.call_args
            assert call_args[1]["params"] == {"phase_count": phases}

    async def test_set_phase_count_invalid(self):
        """Test set_phase_count with invalid value."""
        api = NRGkickAPI(host="192.168.1.100", session=AsyncMock())

        with pytest.raises(ValueError, match="Phase count must be 1, 2, or 3"):
            await api.set_phase_count(4)

        with pytest.raises(ValueError, match="Phase count must be 1, 2, or 3"):
            await api.set_phase_count(0)


class TestAPIAuthentication:
    """Tests for API authentication handling."""

    async def test_api_with_auth(self, mock_session):
        """Test API calls with authentication."""
        api = NRGkickAPI(
            host="192.168.1.100",
            username="test_user",
            password="test_pass",
            session=mock_session,
        )

        await api.get_info()

        call_args = mock_session.get.call_args
        auth = call_args[1]["auth"]
        assert auth is not None
        assert auth.login == "test_user"
        assert auth.password == "test_pass"

    async def test_api_auth_error_401(self, mock_session):
        """Test API authentication error with 401."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.status = 401

        with pytest.raises(NRGkickAuthenticationError):
            await api.get_info()

    async def test_api_auth_error_403(self, mock_session):
        """Test API authentication error with 403."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.return_value.__aenter__.return_value.status = 403

        with pytest.raises(NRGkickAuthenticationError):
            await api.get_info()

    async def test_api_no_retry_on_auth_error(self, mock_session):
        """Test API does NOT retry on authentication errors."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        attempt_count = 0

        def mock_get_with_auth_error(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            response = AsyncMock()
            response.status = 401
            response.json = AsyncMock(return_value={})

            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=response)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            return mock_ctx

        mock_session.get = MagicMock(side_effect=mock_get_with_auth_error)

        with pytest.raises(NRGkickAuthenticationError):
            await api.get_info()

        assert attempt_count == 1  # Should only try once


class TestAPIConnectionErrors:
    """Tests for API connection error handling."""

    async def test_test_connection_success(self, mock_session):
        """Test connection test success."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        assert await api.test_connection()

    async def test_test_connection_failure(self, mock_session):
        """Test connection test failure."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.side_effect = aiohttp.ClientError

        with pytest.raises(NRGkickConnectionError):
            await api.test_connection()

    async def test_api_timeout(self, mock_session):
        """Test API timeout."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.side_effect = asyncio.TimeoutError

        with pytest.raises(NRGkickConnectionError):
            await api.get_info()

    async def test_api_client_error(self, mock_session):
        """Test API client error."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.side_effect = aiohttp.ClientError

        with pytest.raises(NRGkickConnectionError):
            await api.get_info()


class TestAPIHTTPErrors:
    """Tests for API HTTP error handling."""

    async def test_api_http_error_with_json_response(self, mock_session):
        """Test API returns error status with JSON error message."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        response_mock = mock_session.get.return_value.__aenter__.return_value
        response_mock.status = 405
        response_mock.json = AsyncMock(
            return_value={"Response": "Charging pause is blocked by solar-charging"}
        )

        result = await api.set_charge_pause(True)
        assert result == {"Response": "Charging pause is blocked by solar-charging"}

    async def test_api_http_error_without_json_response(self, mock_session):
        """Test API returns error status without valid JSON (should raise)."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        response_mock = mock_session.get.return_value.__aenter__.return_value
        response_mock.status = 500
        response_mock.json = AsyncMock(side_effect=Exception("Invalid JSON"))
        response_mock.raise_for_status = Mock(
            side_effect=aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=500,
                message="Internal Server Error",
            )
        )

        with pytest.raises(NRGkickConnectionError):
            await api.get_control()

    async def test_api_no_retry_on_client_error_4xx(self, mock_session):
        """Test API does NOT retry on 4xx client errors (except 401/403)."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        response_mock = AsyncMock()
        response_mock.status = 404
        response_mock.json = AsyncMock(side_effect=Exception("Not found"))
        response_mock.raise_for_status = Mock(
            side_effect=aiohttp.ClientResponseError(
                request_info=Mock(),
                history=(),
                status=404,
                message="Not Found",
            )
        )

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=response_mock)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_ctx

        with pytest.raises(NRGkickConnectionError):
            await api.get_info()


class TestAPIRetryLogic:
    """Tests for API retry logic."""

    async def test_api_retry_on_timeout(self, mock_session):
        """Test API retries on timeout and eventually succeeds."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        attempt_count = 0

        def mock_get_with_retry(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count <= 2:
                raise TimeoutError

            response = AsyncMock()
            response.status = 200
            response.json = AsyncMock(
                return_value={"general": {"serial_number": "123"}}
            )
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=response)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            return mock_ctx

        mock_session.get = MagicMock(side_effect=mock_get_with_retry)

        result = await api.get_info()
        assert result == {"general": {"serial_number": "123"}}
        assert attempt_count == 3

    async def test_api_retry_on_transient_http_error(self, mock_session):
        """Test API retries on 503 Service Unavailable."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        attempt_count = 0

        def mock_get_with_503_then_success(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            response = AsyncMock()
            if attempt_count <= 2:
                response.status = 503
            else:
                response.status = 200

            response.json = AsyncMock(return_value={"control": {"current_set": 16}})

            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=response)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            return mock_ctx

        mock_session.get = MagicMock(side_effect=mock_get_with_503_then_success)

        result = await api.get_control()
        assert result == {"control": {"current_set": 16}}
        assert attempt_count == 3

    async def test_api_retry_exhausted_on_timeout(self, mock_session):
        """Test API fails after exhausting all retries on timeout."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)
        mock_session.get.side_effect = asyncio.TimeoutError

        with pytest.raises(NRGkickConnectionError) as exc_info:
            await api.get_info()

        assert "timeout" in str(exc_info.value).lower()

    async def test_api_retry_on_connection_error(self, mock_session):
        """Test API retries on connection errors."""
        api = NRGkickAPI("192.168.1.100", session=mock_session)

        attempt_count = 0

        def mock_get_with_connection_error(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count <= 2:
                raise aiohttp.ClientConnectorError(
                    connection_key=Mock(), os_error=OSError("Connection refused")
                )

            response = AsyncMock()
            response.status = 200
            response.json = AsyncMock(
                return_value={"values": {"status": {"charging": 1}}}
            )
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=response)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            return mock_ctx

        mock_session.get = MagicMock(side_effect=mock_get_with_connection_error)

        result = await api.get_values()
        assert result == {"values": {"status": {"charging": 1}}}
        assert attempt_count == 3


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_exception_hierarchy(self):
        """Test that exceptions have correct inheritance."""
        from nrgkick_api import NRGkickError

        assert issubclass(NRGkickConnectionError, NRGkickError)
        assert issubclass(NRGkickAuthenticationError, NRGkickError)

    def test_catch_base_exception(self):
        """Test catching all NRGkick exceptions with base class."""
        from nrgkick_api import NRGkickError

        try:
            raise NRGkickConnectionError("test")
        except NRGkickError:
            pass  # Should catch

        try:
            raise NRGkickAuthenticationError("test")
        except NRGkickError:
            pass  # Should catch
