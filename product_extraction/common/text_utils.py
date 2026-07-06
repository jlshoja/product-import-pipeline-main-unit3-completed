"""
Shared text parsing helpers.

Unit 7 - Shared Utility Consolidation
"""

import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


PERSIAN_DIGITS = "".join(chr(0x06F0 + i) for i in range(10))
ARABIC_DIGITS = "".join(chr(0x0660 + i) for i in range(10))
ENGLISH_DIGITS = "0123456789"
THOUSANDS_SEPARATORS = ",\u066c"
PERSIAN_CODE_WORD = "\u06a9\u062f"

_DIGIT_TRANSLATION = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ENGLISH_DIGITS + ENGLISH_DIGITS,
)


def normalize_digits(text):
    """Convert Persian and Arabic-Indic digits to English digits."""
    if text is None:
        return ""
    return str(text).translate(_DIGIT_TRANSLATION)


def normalize_text(text):
    """Remove invisible Unicode control-format characters and strip whitespace."""
    if text is None:
        return ""
    return "".join(
        char for char in str(text)
        if unicodedata.category(char) != "Cf"
    ).strip()


def extract_product_code(text):
    """Extract a product code following the Persian word for code."""
    normalized = normalize_digits(text)
    match = re.search(rf"{PERSIAN_CODE_WORD}\s*(\d+)", normalized)
    return match.group(1) if match else ""


def extract_numeric_code(text, min_digits=3, max_digits=6):
    """Extract a generic numeric product code from text."""
    if text is None:
        return None
    normalized = normalize_text(normalize_digits(text))
    match = re.search(rf"(\d{{{min_digits},{max_digits}}})", normalized)
    return match.group(1) if match else None


def clean_product_name(text):
    """Remove price-like suffixes and normalize whitespace in a product name."""
    if not text:
        return ""

    cleaned = normalize_digits(text)
    cleaned = re.sub(
        rf"[0-9{re.escape(THOUSANDS_SEPARATORS)}\s]+"
        r"\s*(\u062a\u0648\u0645\u0627\u0646|\u0631\u06cc\u0627\u0644)",
        "",
        cleaned,
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.replace("\n", " ").replace("\t", " ").strip()


def extract_product_name(text):
    """Extract a product name from text by removing trailing price data."""
    if text is None:
        return ""

    product_name = normalize_digits(text).strip()
    code_match = re.search(rf"{PERSIAN_CODE_WORD}\s*\d+", product_name)

    if code_match:
        product_name = product_name[:code_match.end()].strip()

    product_name = re.sub(r"\s+\d{5,}.*$", "", product_name)
    product_name = re.sub(rf"[\u060c{re.escape(THOUSANDS_SEPARATORS)}]+", "", product_name)
    return " ".join(product_name.split()).strip()


def normalize_url(url):
    """Normalize URL by dropping query/fragment and preferring https."""
    if not url:
        return ""

    parsed = urlsplit(str(url).strip())
    scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
    return urlunsplit((scheme, parsed.netloc, parsed.path, "", ""))


def extract_domain(url):
    """Extract a URL domain without protocol."""
    if not url:
        return ""

    parsed = urlsplit(str(url).strip())
    if parsed.netloc:
        return parsed.netloc
    return str(url).replace("https://", "").replace("http://", "").split("/")[0]
