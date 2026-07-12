import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def process(df):
    """Step 2: Copy model column to SKU column."""
    model_col = next((c for c in df.columns if 'مدل' in c.lower()), None)
    sku_col = next((c for c in df.columns if 'sku' in c.lower()), None)

    if model_col is None:
        return df, 0

    if sku_col is None:
        sku_col = 'SKU'
        df[sku_col] = ''

    mask = df[model_col].astype(str).str.strip().ne('')
    df.loc[mask, sku_col] = df.loc[mask, model_col]
    count = mask.sum()

    return df, count
