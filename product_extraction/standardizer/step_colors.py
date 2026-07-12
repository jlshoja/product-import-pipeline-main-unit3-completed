import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.color_utils import normalize_persian_color_text


def _normalize_color(color):
    """Strip whitespace, ZWNJ, underscores, dashes and lowercase for comparison."""
    return re.sub(r'[\s‌_\-]+', '', str(color)).lower()


def _find_standard_color(input_color, standard_colors):
    """Sliding window match: try longest phrase first, then shorter."""
    words = input_color.strip().split()
    n = len(words)

    for length in range(n, 0, -1):
        for start in range(n - length + 1):
            phrase = ' '.join(words[start:start + length])
            norm_phrase = _normalize_color(phrase)
            for std in standard_colors:
                if _normalize_color(std) == norm_phrase:
                    return std
    return None


def process(df, color_mapping_data):
    """Step 1: Normalize colors against standard mapping.

    Args:
        df: DataFrame with product data
        color_mapping_data: list of lists from color_mapping.xlsx (header + rows)

    Returns:
        (df, count, non_standard_colors_dict)
    """
    color_raw_col = next(
        (c for c in df.columns if 'رنگ_های_اولیه' in c or 'رنگ_اولیه' in c),
        None
    )
    if color_raw_col is None:
        color_raw_col = next((c for c in df.columns if c.strip() == 'رنگ'), None)

    if color_raw_col is None:
        return df, 0, {}

    main_color_col = next(
        (c for c in df.columns if c.strip() == 'رنگ'), None
    )

    standard_colors = [
        str(row[0]).strip()
        for row in color_mapping_data[1:]
        if row and row[0]
    ]

    processed_col_name = 'رنگ_های_پردازش_شده'
    if processed_col_name not in df.columns:
        df[processed_col_name] = ''

    name_col = next((c for c in df.columns if 'نام' in c), None)
    non_standard_colors = {}
    count = 0

    for idx in df.index:
        raw_val = df.at[idx, color_raw_col]
        if pd.isna(raw_val):
            continue
        color_text = str(raw_val)
        if not color_text.strip():
            continue

        product_name = str(df.at[idx, name_col]) if name_col else ''
        colors = [c.strip() for c in re.split(r'[|,\-]', color_text) if c.strip()]

        final_colors = []
        for color in colors:
            color = re.sub(r'\bساده\b', '', color).strip()
            if not color or color.strip() == 'ناموجود':
                continue

            color = normalize_persian_color_text(color)
            matched = _find_standard_color(color, standard_colors)

            if matched:
                final_colors.append(matched)
            else:
                if color not in non_standard_colors:
                    non_standard_colors[color] = []
                if product_name:
                    non_standard_colors[color].append(product_name)
                final_colors.append(color)

        unique_colors = list(dict.fromkeys(final_colors))
        processed_value = ' | '.join(unique_colors)

        df.at[idx, processed_col_name] = processed_value
        if main_color_col and main_color_col != color_raw_col:
            df.at[idx, main_color_col] = processed_value
        count += 1

    return df, count, non_standard_colors
