"""Shared input validation and exact decimal conversion."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re


class InputError(ValueError):
    """An understandable problem to show in the application."""


def text(value, label, required=False, max_length=500):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise InputError(f"{label} must be text.")
    value = value.strip()
    if required and not value:
        raise InputError(f"{label} is required.")
    if len(value) > max_length:
        raise InputError(f"{label} must be {max_length} characters or fewer.")
    return value


def scaled_number(value, label, places, minimum=0, maximum=None):
    """Convert a decimal string into integer cents/thousandths without floats."""
    raw = str(value if value is not None else "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", raw) or len(raw) > 30:
        raise InputError(f"{label} must be a valid nonnegative number.")
    try:
        number = Decimal(raw)
    except InvalidOperation:
        raise InputError(f"{label} must be a valid number.") from None
    if number.as_tuple().exponent < -places:
        raise InputError(f"{label} can have at most {places} decimal places.")
    if number < minimum or (maximum is not None and number > maximum):
        raise InputError(f"{label} is outside the allowed range.")
    return int(number * (10 ** places))


def money(value, label):
    return scaled_number(value, label, 2, maximum=99999999)


def quantity(value):
    return scaled_number(value, "Quantity", 3, minimum=Decimal("0.001"), maximum=100000)


def tax_rate(value):
    return scaled_number(value, "Tax rate", 2, maximum=100)


def date_string(value, label, required=True):
    value = text(value, label, required, 10)
    if not value:
        return ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InputError(f"{label} must be a date in YYYY-MM-DD format.")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise InputError(f"{label} must be a valid date.") from None
    return value


def positive_id(value, label):
    if isinstance(value, bool) or not str(value).isdigit() or int(value) < 1:
        raise InputError(f"Select a valid {label}.")
    return int(value)


def decimal_string(scaled, places):
    """Convert an integer amount to a fixed-decimal string for the browser."""
    sign = "-" if scaled < 0 else ""
    scaled = abs(scaled)
    base = 10 ** places
    return f"{sign}{scaled // base}.{scaled % base:0{places}d}"
