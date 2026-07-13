"""Reusable golden-file comparison for the product pipeline.

Encodes the rules from baseline/comparison_manifest.md so any plan that
regenerates a WooCommerce CSV can assert it did not regress.
"""
from pathlib import Path
import pandas as pd


def load_woocommerce_csv(path):
    """Load a WooCommerce import CSV as a DataFrame (all columns as strings)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def compare_woocommerce(candidate_path, golden_path):
    """Return a list of human-readable difference strings (empty == identical
    by the manifest's rules): same row count, same column set, same SKU
    multiset."""
    diffs = []
    cand = load_woocommerce_csv(candidate_path)
    gold = load_woocommerce_csv(golden_path)

    if set(cand.columns) != set(gold.columns):
        diffs.append(f"columns differ: only-in-candidate={set(cand.columns)-set(gold.columns)}, "
                     f"only-in-golden={set(gold.columns)-set(cand.columns)}")
        return diffs

    if len(cand) != len(gold):
        diffs.append(f"row count differs: candidate={len(cand)}, golden={len(gold)}")

    sku_col = next((c for c in gold.columns if c.strip().lower() == "sku"), None)
    if sku_col is not None:
        if sorted(cand[sku_col]) != sorted(gold[sku_col]):
            cand_skus, gold_skus = set(cand[sku_col]), set(gold[sku_col])
            diffs.append(f"SKU set differs: only-in-candidate={cand_skus-gold_skus}, "
                         f"only-in-golden={gold_skus-cand_skus}")

    return diffs
