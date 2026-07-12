import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SEPARATORS_PATTERN = re.compile(r'[,\-/;\\،؛]')


def normalize_separators(text):
    """Replace mixed separators with | and clean up."""
    if not text:
        return text
    text = str(text)
    text = SEPARATORS_PATTERN.sub('|', text)
    text = re.sub(r'\s*\|\s*', '|', text)
    text = re.sub(r'\|+', '|', text)
    text = text.strip('|')
    return text


def process(df):
    """Step 3: Normalize usage column separators to |."""
    usage_cols = [c for c in df.columns if 'کاربرد' in c or 'مناسب' in c]

    if not usage_cols:
        return df, 0

    count = 0
    for col in usage_cols:
        original = df[col].astype(str)
        normalized = original.apply(normalize_separators)
        changed = (original != normalized) & original.str.strip().ne('')
        count += changed.sum()
        df[col] = normalized

    return df, count
