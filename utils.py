from datetime import datetime, timezone
from dateutil import parser as date_parser


def normalize_timestamp(value):
    """
    Handles ISO-8601 and Unix epoch (int or float, including negative) timestamps.
    """
    if not value or not value.strip():
        return None
    value = value.strip()
    try:
        float_val = float(value)
        # datetime.fromtimestamp() rejects negative values on Windows;
        # use UTC-aware construction instead.
        return datetime.fromtimestamp(float_val, tz=timezone.utc).replace(tzinfo=None)
    except (ValueError, OSError):
        pass
    try:
        return date_parser.parse(value)
    except Exception:
        return None
