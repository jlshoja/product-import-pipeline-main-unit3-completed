#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tracker helper compatibility wrappers.

Implementations live in product_extraction.common after Unit 7 shared
utility consolidation.
"""

from datetime import datetime
from typing import Optional, Tuple

try:
    from common.date_utils import get_persian_date as _get_persian_date
    from common.date_utils import gregorian_to_jalali as _gregorian_to_jalali
    from common.price_utils import calculate_price_change as _calculate_price_change
    from common.price_utils import extract_price_from_text as _extract_price_from_text
    from common.price_utils import format_number as _format_number
    from common.price_utils import format_persian_price as _format_persian_price
except ImportError:
    from product_extraction.common.date_utils import get_persian_date as _get_persian_date
    from product_extraction.common.date_utils import gregorian_to_jalali as _gregorian_to_jalali
    from product_extraction.common.price_utils import calculate_price_change as _calculate_price_change
    from product_extraction.common.price_utils import extract_price_from_text as _extract_price_from_text
    from product_extraction.common.price_utils import format_number as _format_number
    from product_extraction.common.price_utils import format_persian_price as _format_persian_price


def extract_price_from_text(text: str) -> Optional[int]:
    """Extract price from Persian/English text."""
    return _extract_price_from_text(text, min_value=1000)


def format_number(number: Optional[int]) -> str:
    """Format number with comma separators."""
    return _format_number(number)


def calculate_price_change(old_price: float, new_price: float) -> Tuple[float, float]:
    """Calculate price change amount and percentage."""
    return _calculate_price_change(old_price, new_price)


def gregorian_to_jalali(g_y: int, g_m: int, g_d: int) -> Tuple[int, int, int]:
    """Convert Gregorian date to Jalali (Persian) date."""
    return _gregorian_to_jalali(g_y, g_m, g_d)


def get_persian_date(date: Optional[datetime] = None) -> str:
    """Get a date in Persian YYYY/MM/DD format."""
    return _get_persian_date(date)


def format_persian_price(price: Optional[int]) -> str:
    """Format price with Persian separators."""
    return _format_persian_price(price)


if __name__ == "__main__":
    print("Testing tracker helper wrappers...")
    print(f"  1,500,000 -> {extract_price_from_text('1,500,000')}")
    print(f"  1000000 -> {format_number(1000000)}")
    print(f"  2024-01-01 -> {gregorian_to_jalali(2024, 1, 1)}")
    print(f"  Today -> {get_persian_date()}")
