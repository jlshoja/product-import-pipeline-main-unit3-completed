"""Golden-file baseline tests for the WooCommerce import output.

The full pipeline scrapes live sites and cannot run deterministically here,
so these tests (a) prove the comparison harness reports no false differences
on identical input, and (b) assert the committed golden output satisfies the
structural rules in baseline/comparison_manifest.md.
"""
from pathlib import Path
import pytest
from tests.baseline_compare import load_woocommerce_csv, compare_woocommerce

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / "baseline" / "sample_output"


def _golden_woo_csv():
    matches = sorted(GOLDEN_DIR.glob("woocommerce_import_*.csv"))
    assert matches, f"no golden woocommerce_import_*.csv in {GOLDEN_DIR}"
    return matches[-1]


def test_harness_reports_no_diff_on_identical_file():
    golden = _golden_woo_csv()
    assert compare_woocommerce(golden, golden) == []


def test_golden_output_is_nonempty_and_has_sku():
    df = load_woocommerce_csv(_golden_woo_csv())
    assert len(df) > 0, "golden WooCommerce CSV has no rows"
    sku_col = next((c for c in df.columns if c.strip().lower() == "sku"), None)
    assert sku_col is not None, f"no SKU column found in {list(df.columns)}"
    blank = df[df[sku_col].str.strip() == ""]
    assert len(blank) == 0, f"{len(blank)} rows have a blank SKU"
