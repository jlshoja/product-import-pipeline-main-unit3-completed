"""
Shared price and number helpers.

Unit 7 - Shared Utility Consolidation
"""

import re

try:
    from common.text_utils import (
        THOUSANDS_SEPARATORS,
        normalize_digits,
    )
except ImportError:
    from product_extraction.common.text_utils import (
        THOUSANDS_SEPARATORS,
        normalize_digits,
    )


def _is_missing(value):
    if value is None:
        return True
    try:
        import pandas as pd

        if pd.isna(value):
            return True
    except (ImportError, TypeError, ValueError):
        pass
    try:
        return bool(value != value)
    except Exception:
        return False


def extract_price_from_text(text, min_value=1000, min_digits=None):
    """
    Extract the largest price-like integer from text.

    min_digits preserves stricter callers that historically ignored short
    numbers such as product codes.
    """
    if _is_missing(text) or text == "":
        return None

    normalized = normalize_digits(text)
    normalized = normalized.replace("\u066c", ",")
    matches = re.findall(r"[\d,]+", normalized)

    numbers = []
    for match in matches:
        raw_number = match.replace(",", "")
        if not raw_number:
            continue
        if min_digits is not None and len(raw_number) < min_digits:
            continue
        try:
            number = int(raw_number)
        except ValueError:
            continue
        if min_digits is not None or number > min_value:
            numbers.append(number)

    return max(numbers) if numbers else None


def clean_price_text(text):
    """Return only normalized price digits from price text."""
    if _is_missing(text) or text == "":
        return ""

    cleaned = normalize_digits(text)
    cleaned = cleaned.replace("\u062a\u0648\u0645\u0627\u0646", "")
    cleaned = cleaned.replace("\u0631\u06cc\u0627\u0644", "")
    for separator in THOUSANDS_SEPARATORS + "\u060c":
        cleaned = cleaned.replace(separator, "")

    return re.sub(r"[^\d]", "", cleaned)


def format_number(number):
    """Format a number with English comma separators."""
    if _is_missing(number) or number == "":
        return ""

    if isinstance(number, str):
        cleaned = number
        for separator in THOUSANDS_SEPARATORS:
            cleaned = cleaned.replace(separator, "")
        cleaned = cleaned.strip()
        if not cleaned:
            return ""
        try:
            number = float(cleaned)
        except ValueError:
            return number

    return f"{int(number):,}"


def calculate_price_change(old_price, new_price):
    """Calculate price change amount and percentage."""
    if old_price == 0:
        return (0, 0.0)

    change = new_price - old_price
    percent = (change / old_price) * 100
    return (change, percent)


def format_persian_price(price):
    """Format price with a Persian thousands separator."""
    if _is_missing(price):
        return ""
    return format_number(price).replace(",", "\u066c")
