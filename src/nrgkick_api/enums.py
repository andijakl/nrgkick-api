"""Enum types for NRGkick API values.

The NRGkick device returns various numeric codes (status, connector type, warnings,
errors, etc.). These are exposed as `IntEnum` types for better readability and
type-safety while remaining fully compatible with `int`.
"""

from __future__ import annotations

from enum import IntEnum


class ChargingStatus(IntEnum):
    """Charging status returned by the API's status field."""

    UNKNOWN = 0
    STANDBY = 1
    CONNECTED = 2
    CHARGING = 3
    ERROR = 6
    WAKEUP = 7


class RcdTriggerStatus(IntEnum):
    """RCD trigger status codes."""

    NO_FAULT = 0
    AC_30MA_FAULT = 1
    AC_60MA_FAULT = 2
    AC_150MA_FAULT = 3
    DC_POSITIVE_6MA_FAULT = 4
    DC_NEGATIVE_6MA_FAULT = 5


class WarningCode(IntEnum):
    """Warning code values reported by the device."""

    NO_WARNING = 0
    NO_PE = 1
    BLACKOUT_PROTECTION = 2
    ENERGY_LIMIT_REACHED = 3
    EV_DOES_NOT_COMPLY_STANDARD = 4
    UNSUPPORTED_CHARGING_MODE = 5
    NO_ATTACHMENT_DETECTED = 6
    NO_COMM_WITH_TYPE2_ATTACHMENT = 7
    INCREASED_TEMPERATURE = 16
    INCREASED_HOUSING_TEMPERATURE = 17
    INCREASED_ATTACHMENT_TEMPERATURE = 18
    INCREASED_DOMESTIC_PLUG_TEMPERATURE = 19


class ErrorCode(IntEnum):
    """Error code values reported by the device."""

    NO_ERROR = 0
    GENERAL_ERROR = 1
    ATTACHMENT_32A_ON_16A_UNIT = 2
    VOLTAGE_DROP_DETECTED = 3
    UNPLUG_DETECTION_TRIGGERED = 4
    TYPE2_NOT_AUTHORIZED = 5
    RESIDUAL_CURRENT_DETECTED = 16
    CP_SIGNAL_VOLTAGE_ERROR = 32
    CP_SIGNAL_IMPERMISSIBLE = 33
    EV_DIODE_FAULT = 34
    PE_SELF_TEST_FAILED = 48
    RCD_SELF_TEST_FAILED = 49
    RELAY_SELF_TEST_FAILED = 50
    PE_AND_RCD_SELF_TEST_FAILED = 51
    PE_AND_RELAY_SELF_TEST_FAILED = 52
    RCD_AND_RELAY_SELF_TEST_FAILED = 53
    PE_AND_RCD_AND_RELAY_SELF_TEST_FAILED = 54
    SUPPLY_VOLTAGE_ERROR = 64
    PHASE_SHIFT_ERROR = 65
    OVERVOLTAGE_DETECTED = 66
    UNDERVOLTAGE_DETECTED = 67
    OVERVOLTAGE_WITHOUT_PE_DETECTED = 68
    UNDERVOLTAGE_WITHOUT_PE_DETECTED = 69
    UNDERFREQUENCY_DETECTED = 70
    OVERFREQUENCY_DETECTED = 71
    UNKNOWN_FREQUENCY_TYPE = 72
    UNKNOWN_GRID_TYPE = 73
    GENERAL_OVERTEMPERATURE = 80
    HOUSING_OVERTEMPERATURE = 81
    ATTACHMENT_OVERTEMPERATURE = 82
    DOMESTIC_PLUG_OVERTEMPERATURE = 83


class RelayState(IntEnum):
    """Relay state bitmask.

    Bit 0: N, Bit 1: L1, Bit 2: L2, Bit 3: L3
    """

    NO_RELAY = 0
    N = 1
    L1 = 2
    N_L1 = 3
    L2 = 4
    N_L2 = 5
    L1_L2 = 6
    N_L1_L2 = 7
    L3 = 8
    N_L3 = 9
    L1_L3 = 10
    N_L1_L3 = 11
    L2_L3 = 12
    N_L2_L3 = 13
    L1_L2_L3 = 14
    N_L1_L2_L3 = 15


class ConnectorType(IntEnum):
    """Connector type reported by the device."""

    UNKNOWN = 0
    CEE = 1
    DOMESTIC = 2
    TYPE2 = 3
    WALL = 4
    AUS = 5


class GridPhases(IntEnum):
    """Grid phases bitmask.

    Bit 0: L1, Bit 1: L2, Bit 2: L3
    """

    UNKNOWN = 0
    L1 = 1
    L2 = 2
    L1_L2 = 3
    L3 = 4
    L1_L3 = 5
    L2_L3 = 6
    L1_L2_L3 = 7


class CellularMode(IntEnum):
    """Cellular mode/state codes."""

    UNKNOWN = 0
    NO_SERVICE = 1
    GSM = 2
    LTE_CAT_M1 = 3
    LTE_NB_IOT = 4


__all__ = [
    "CellularMode",
    "ChargingStatus",
    "ConnectorType",
    "ErrorCode",
    "GridPhases",
    "RcdTriggerStatus",
    "RelayState",
    "WarningCode",
]
