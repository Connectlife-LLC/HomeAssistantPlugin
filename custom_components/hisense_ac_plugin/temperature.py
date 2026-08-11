from __future__ import annotations

from typing import Any


def resolve_current_temperature(device: Any) -> tuple[float | None, str | None]:
    """Resolve the best available current temperature value for the device.

    The control panel temperature is preferred when exposed by the device. If it is
    unavailable, fall back to the indoor unit temperature. The function returns both
    the numeric value and the source key for debugging purposes.
    """

    if device is None:
        return None, None

    def _coerce_float(value: Any) -> float | None:
        if value in (None, "", False):
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    for key in ("t_temp_in", "f_temp_in", "f_temp", "t_temp"):
        value = device.get_status_value(key)
        parsed = _coerce_float(value)
        if parsed is not None:
            return parsed, key

    return None, None
