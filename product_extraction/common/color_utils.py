"""
Shared color utility helpers.

Unit 6 - Color Management Consolidation
"""

import re


def normalize_persian_color_text(text):
    """Normalize Persian color text using the legacy ColorManager rules."""
    replacements = {
        '\u0643': '\u06a9',
        '\u064a': '\u06cc',
        '\u0649': '\u06cc',
        '\u200c': ' ',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return ' '.join(text.split()).strip()


def simple_color_slug(text):
    """Return the legacy fallback color slug for unknown colors."""
    text = re.sub(r'[^\w\s-]', '', text)
    return text.strip().replace(' ', '-').lower()


def split_color_values(colors_text):
    """Split a color field using the legacy ColorManager separators."""
    return [c.strip() for c in re.split(r'\s*[-|,]\s*', colors_text) if c.strip()]


def collect_unique_normalized_colors(colors_list, normalize_func):
    """Normalize colors and preserve first-seen order using legacy lowercase keys."""
    if not colors_list:
        return []

    standardized = []
    seen = set()

    for color in colors_list:
        normalized = normalize_func(color)
        if normalized and normalized.lower() not in seen:
            standardized.append(normalized)
            seen.add(normalized.lower())

    return standardized
