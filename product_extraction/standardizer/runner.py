#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from common.file_registry import get_file
from common.path_registry import OUTPUTS_DIR, MAPPINGS_DIR
from common.excel_utils import read_excel, write_dataframe
from config import get_config
from utils.logger import LoggerSetup, log_execution_time

from . import step_filter
from . import step_colors
from . import step_sku
from . import step_usages
from . import step_pricing
from . import step_categories
from . import step_translation
from .gemini_client import GeminiTranslator


logger = LoggerSetup.get_logger('standardizer')


def _load_reference_file(path):
    """Load an Excel file as list-of-lists (header + rows), or None if missing."""
    if not path.exists():
        logger.warning(f"Reference file not found: {path}")
        return None
    try:
        df = read_excel(path, header=None)
        return df.values.tolist()
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
        return None


def _update_mapping_file(path, new_entries, col_a_header='فارسی', col_b_header='انگلیسی'):
    """Append new entries to an Excel mapping file."""
    if not new_entries:
        return

    try:
        if path.exists():
            df = read_excel(path)
        else:
            df = pd.DataFrame(columns=[col_a_header, col_b_header])

        new_rows = pd.DataFrame([
            {col_a_header: k, col_b_header: v}
            for k, v in new_entries.items()
        ])
        df = pd.concat([df, new_rows], ignore_index=True)
        write_dataframe(df, path)
        logger.info(f"Added {len(new_entries)} entries to {path.name}")
    except Exception as e:
        logger.warning(f"Failed to update {path}: {e}")


@log_execution_time()
def main():
    """Run the full standardization pipeline."""
    config = get_config().standardizer
    input_path = OUTPUTS_DIR / get_file('product_details')

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False

    logger.info(f"Loading input: {input_path}")
    df = read_excel(input_path)
    initial_rows = len(df)
    logger.info(f"Loaded {initial_rows} rows")

    # Step 0: Filter
    logger.info("[Step 0] Filtering out-of-stock and empty rows...")
    df, removed = step_filter.process(df)
    logger.info(f"  Removed {removed} rows, {len(df)} remaining")

    # Set stock quantity on all remaining rows
    stock_col = next((c for c in df.columns if 'موجودی' in c), None)
    if stock_col is None:
        stock_col = 'موجودی'
        df[stock_col] = ''
    df[stock_col] = config.stock_quantity
    logger.info(f"  Stock quantity set to {config.stock_quantity} for all rows")

    # Step 1: Color processing
    color_mapping_path = MAPPINGS_DIR / get_file('color_mapping')
    color_mapping_data = _load_reference_file(color_mapping_path)
    translator = None

    # Track colors/names that Gemini could not resolve (for the auto-mode warning)
    unresolved_colors = []
    unresolved_names = []

    if color_mapping_data:
        logger.info("[Step 1] Processing colors...")
        df, color_count, non_standard = step_colors.process(df, color_mapping_data)
        logger.info(f"  Processed {color_count} rows, {len(non_standard)} non-standard colors")

        if non_standard and config.enable_gemini:
            translator = GeminiTranslator(config.gemini_api_key, config.enable_gemini)
            translations = translator.translate_colors(list(non_standard.keys()))
            if translations:
                _update_mapping_file(color_mapping_path, translations)
            # Anything non-standard that Gemini did not return a translation for
            resolved = set(translations.keys()) if translations else set()
            unresolved_colors = [c for c in non_standard.keys() if c not in resolved]
        elif non_standard:
            # Gemini disabled: every non-standard color is unresolved
            unresolved_colors = list(non_standard.keys())
    else:
        logger.warning("[Step 1] Skipped - color mapping file not found")
        non_standard = {}

    # Step 2: Copy SKU
    logger.info("[Step 2] Copying model to SKU...")
    df, sku_count = step_sku.process(df)
    logger.info(f"  Copied {sku_count} SKUs")

    # Step 3: Normalize usages
    logger.info("[Step 3] Normalizing usage separators...")
    df, usage_count = step_usages.process(df)
    logger.info(f"  Normalized {usage_count} cells")

    # Step 4: Pricing
    pricing_path = MAPPINGS_DIR / get_file('pricing_sample')
    pricing_data = _load_reference_file(pricing_path)

    if pricing_data:
        logger.info("[Step 4] Applying pricing rules...")
        df, prices_updated, discounts_applied = step_pricing.process(
            df, pricing_data, config.extra_discount_percent
        )
        logger.info(f"  Updated {prices_updated} prices, {discounts_applied} with discounts")
    else:
        logger.warning("[Step 4] Skipped - pricing file not found")

    # Step 5: Categories
    categories_path = MAPPINGS_DIR / get_file('standard_categories')
    categories_data = _load_reference_file(categories_path)

    logger.info("[Step 5] Generating categories...")
    df, cat_count, tagged_count = step_categories.process(df, categories_data)
    logger.info(f"  Categorized {cat_count} rows, {tagged_count} tagged as discounted")

    # Step 6: Word translation
    word_index_path = MAPPINGS_DIR / get_file('word_index')
    word_index_data = _load_reference_file(word_index_path)

    if word_index_data:
        logger.info("[Step 6] Translating words...")
        df, trans_count, unknown_words = step_translation.process(df, word_index_data)
        logger.info(f"  Translated {trans_count} words, {len(unknown_words)} unknowns")

        if unknown_words and config.enable_gemini:
            if translator is None:
                translator = GeminiTranslator(config.gemini_api_key, config.enable_gemini)
            name_translations = translator.translate_product_names(unknown_words)
            if name_translations:
                names_path = MAPPINGS_DIR / get_file('product_names')
                _update_mapping_file(names_path, name_translations, 'انگلیسی', 'فارسی')
            # Anything unknown that Gemini did not return a translation for
            resolved_names = set(name_translations.keys()) if name_translations else set()
            unresolved_names = [w for w in unknown_words if w not in resolved_names]
        elif unknown_words:
            # Gemini disabled: every unknown word is unresolved
            unresolved_names = list(unknown_words)
    else:
        logger.warning("[Step 6] Skipped - word index file not found")

    # Save output
    output_path = OUTPUTS_DIR / get_file('standardized_output')
    # Avoid setting mixed dtypes in-place which can raise FutureWarning in pandas.
    # Use a non-inplace fill to let pandas handle dtype changes safely.
    df = df.fillna('')

    # Remove intermediate column not in original output
    if 'رنگ_های_پردازش_شده' in df.columns:
        df.drop(columns=['رنگ_های_پردازش_شده'], inplace=True)

    # Strip .0 from whole numbers (e.g. 9321.0 → 9321)
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: str(int(float(x))) if isinstance(x, (int, float)) and x != '' and float(x) == int(float(x)) else x
        )

    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"Output saved: {output_path} ({len(df)} rows)")

    # Save non-standard colors report
    if non_standard:
        report_rows = []
        for color, products in non_standard.items():
            report_rows.append({
                'رنگ_غیراستاندارد': color,
                'تعداد_محصول': len(products),
                'نمونه_محصولات': ' | '.join(products[:5])
            })
        report_df = pd.DataFrame(report_rows)
        report_path = OUTPUTS_DIR / 'non_standard_colors.csv'
        report_df.to_csv(report_path, index=False, encoding='utf-8-sig')
        logger.info(f"Non-standard colors report: {report_path}")

    logger.info("Standardization complete!")

    if unresolved_colors:
        logger.warning(
            f"{len(unresolved_colors)} unknown color(s) could not be resolved by Gemini"
        )
    if unresolved_names:
        logger.warning(
            f"{len(unresolved_names)} unknown name(s) could not be resolved by Gemini"
        )

    # Return a truthy dict so callers that only check `if result:` keep working,
    # while the auto pipeline can read the unresolved counts for its final warning.
    return {
        'success': True,
        'unresolved_colors': unresolved_colors,
        'unresolved_names': unresolved_names,
    }


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
