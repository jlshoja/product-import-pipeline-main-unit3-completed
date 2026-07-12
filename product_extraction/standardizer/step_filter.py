import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _is_empty(value):
    """Check if a value is effectively empty (NaN, None, or blank string)."""
    if pd.isna(value):
        return True
    return str(value).strip() == ''


def process(df):
    """Step 0: Remove out-of-stock, no-color, and empty rows."""
    initial_count = len(df)

    name_col = next((c for c in df.columns if 'نام' in c), None)
    price_col = next((c for c in df.columns if 'قیمت_اصلی' in c), None)
    status_col = next((c for c in df.columns if 'وضعیت' in c), None)

    bad_values = {'ناموجود', 'OUT_OF_STOCK', 'No Color', 'Failed'}

    # Remove rows where any cell contains a bad value
    mask = df.apply(
        lambda row: not any(
            str(v).strip() in bad_values for v in row if not pd.isna(v)
        ), axis=1
    )
    df = df[mask].copy()

    # Remove rows where both name AND price are empty/NaN
    if name_col and price_col:
        empty_mask = ~(
            df[name_col].apply(_is_empty) & df[price_col].apply(_is_empty)
        )
        df = df[empty_mask].copy()

    removed = initial_count - len(df)
    return df, removed
