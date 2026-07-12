import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ENGLISH_ONLY_PATTERN = re.compile(r'^[a-zA-Z0-9_\s]+$')
SEPARATOR_PATTERN = re.compile(r'(\s*\|\s*|\s*،\s*|\s*,\s*|\s*;\s*|\s*؛\s*)')


def _build_translation_map(word_index_data):
    """Build English-to-Persian translation map from word index data."""
    trans_map = {}
    if not word_index_data or len(word_index_data) < 2:
        return trans_map

    for row in word_index_data[1:]:
        if not row or len(row) < 2:
            continue
        eng = str(row[0]).strip().lower() if row[0] else ''
        per = str(row[1]).strip() if row[1] else ''
        if eng and per:
            trans_map[eng] = per
    return trans_map


def _translate_cell_value(cell_value, translation_map):
    """Translate English tokens in a cell value to Persian."""
    if not cell_value and cell_value != 0:
        return cell_value, 0, []

    text = str(cell_value)
    parts = SEPARATOR_PATTERN.split(text)
    total_count = 0
    unknowns = []

    translated_parts = []
    for part in parts:
        trimmed = part.strip()
        if not trimmed:
            translated_parts.append(part)
            continue

        if ENGLISH_ONLY_PATTERN.match(trimmed):
            key = trimmed.lower()
            if key in translation_map:
                translated_parts.append(part.replace(trimmed, translation_map[key]))
                total_count += 1
            else:
                translated_parts.append(part)
                if trimmed not in unknowns:
                    unknowns.append(trimmed)
        else:
            translated_parts.append(part)

    return ''.join(translated_parts), total_count, unknowns


def process(df, word_index_data):
    """Step 6: Translate English words to Persian using word index.

    Args:
        df: DataFrame with product data
        word_index_data: list of lists from word_index.xlsx

    Returns:
        (df, total_translations, unknown_words)
    """
    translation_map = _build_translation_map(word_index_data)
    if not translation_map:
        return df, 0, []

    total_count = 0
    all_unknowns = []

    for idx in df.index:
        for col in df.columns:
            cell_value = df.at[idx, col]
            if not cell_value or not str(cell_value).strip():
                continue

            translated, count, unknowns = _translate_cell_value(cell_value, translation_map)
            if count > 0:
                df.at[idx, col] = translated
                total_count += count
            all_unknowns.extend(u for u in unknowns if u not in all_unknowns)

    return df, total_count, all_unknowns
