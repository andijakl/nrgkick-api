"""Tests for public enum exports."""

from __future__ import annotations

from nrgkick_api import ChargingStatus, ConnectorType, ErrorCode


def test_enums_are_int_compatible() -> None:
    assert int(ChargingStatus.CHARGING) == 3
    assert ChargingStatus.CHARGING == 3
    assert int(ConnectorType.TYPE2) == 3


def test_error_code_renamed_member() -> None:
    # Ensure the renamed enum member exists and matches the old numeric code.
    assert int(ErrorCode.ATTACHMENT_32A_ON_16A_UNIT) == 2
