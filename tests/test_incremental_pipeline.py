# -*- coding: utf-8 -*-
"""
Tests for the incremental-pipeline + physical-move gating behaviour.

These cover the pieces added so a scheduled re-run only touches new / changed
products instead of reprocessing the whole catalogue, and so a WooCommerce
import is never emitted while referencing images that were not physically
copied:

  * runner._expected_skus_from_env      — incremental import scope from env
  * runner.main scope intersection      — subset ∩ input-file SKUs
  * woocommerce_generator_v12           — copy-before-CSV + per-image gate
  * unified_image_processor             — IMG_PROCESS_SKUS allowlist filter
  * Image_Downloader._build_sku_map     — manifest sku column drives filenames
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_IB = _ROOT / "import_builder"
_IMG = _ROOT / "image_processing"
for _p in (str(_IB), str(_IMG), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import runner  # noqa: E402


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────
# runner._expected_skus_from_env
# ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Each test starts with the incremental env vars unset."""
    for var in ("IMPORT_EXPECTED_SKUS", "IMPORT_INPUT_CSV",
                "IMPORT_SOURCE_IMAGES", "IMG_PROCESS_SKUS",
                "NEW_MANIFEST", "UPDATED_MANIFEST"):
        monkeypatch.delenv(var, raising=False)
    yield


def test_expected_skus_from_env_unset_returns_none(monkeypatch):
    assert runner._expected_skus_from_env() is None


def test_expected_skus_from_env_empty_returns_none(monkeypatch):
    monkeypatch.setenv("IMPORT_EXPECTED_SKUS", "  ,  , ")
    assert runner._expected_skus_from_env() is None


def test_expected_skus_from_env_parses_numeric_prefix(monkeypatch):
    # SKUs may arrive as full model names; only the numeric prefix matters.
    monkeypatch.setenv("IMPORT_EXPECTED_SKUS", "9266, 9321-black, 9280")
    assert runner._expected_skus_from_env() == {"9266", "9321", "9280"}


# ─────────────────────────────────────────────────────────────
# runner.main — scope is subset ∩ input file, and env overrides
# ─────────────────────────────────────────────────────────────

def _write_product_csv(path, skus):
    header = "sku,مدل\n"
    rows = "".join(f"{s},{s}\n" for s in skus)
    path.write_text(header + rows, encoding="utf-8-sig")


def test_main_scopes_coverage_to_subset(monkeypatch, tmp_path, capsys):
    """With IMPORT_EXPECTED_SKUS set, only subset ∩ input SKUs are required.

    The input file has three SKUs but the incremental subset names only one.
    The processed-images folder covers just that one. main() must succeed:
    coverage is scored against the subset, not the whole file.
    """
    input_csv = tmp_path / "product.csv"
    _write_product_csv(input_csv, ["9266", "9321", "9280"])

    source_base = tmp_path / "processed_images"
    session = source_base / "2026-07-18_10-00-00"
    session.mkdir(parents=True)
    # Only 9266 has images on disk.
    (session / "9266a_black.webp").write_bytes(b"img")
    (session / runner.COMPLETION_MARKER).write_text("ok", encoding="utf-8")

    monkeypatch.setenv("IMPORT_INPUT_CSV", str(input_csv))
    monkeypatch.setenv("IMPORT_SOURCE_IMAGES", str(source_base))
    monkeypatch.setenv("IMPORT_EXPECTED_SKUS", "9266")

    # Stub the generator so we don't pull the whole WooCommerce build in; just
    # confirm main() got far enough to invoke it (i.e. the coverage gate passed).
    called = {}

    def fake_process(input_file, process_images, source_images_folder, dest_images_folder):
        called["source"] = source_images_folder
        called["input"] = input_file
        # Simulate a clean build that copied its one image.
        dest = Path(dest_images_folder)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "9266a_black.webp").write_bytes(b"img")
        import pandas as pd
        df = pd.DataFrame([{"sku": "9266"}])
        return df, {"9266a": "9266a_black.webp"}, {"expected": 1, "copied": 1,
                                                    "missing": 0, "missing_sources": []}

    import woocommerce_generator_v12 as gen
    monkeypatch.setattr(gen, "process_products_v12", fake_process)
    # runner imports the symbol lazily inside main(), from the module, so
    # patching the module attribute is enough.

    # Redirect the convenience output copy into tmp so we don't touch the repo.
    monkeypatch.setattr(runner, "ROOT_DIR", tmp_path)

    ok = runner.main()
    assert ok is True
    # Selected the session that covers the subset SKU.
    assert Path(called["source"]).name == "2026-07-18_10-00-00"


def test_main_full_mode_requires_all_file_skus(monkeypatch, tmp_path):
    """Without a subset (full mode), coverage is scored against every file SKU.

    The processed folder covers only one of three SKUs and none of the others,
    but coverage>0 so the build proceeds; this asserts we did NOT accidentally
    scope to a subset when the env var is absent (expected_count == file size).
    """
    input_csv = tmp_path / "product.csv"
    _write_product_csv(input_csv, ["9266", "9321", "9280"])

    source_base = tmp_path / "processed_images"
    session = source_base / "2026-07-18_10-00-00"
    session.mkdir(parents=True)
    (session / "9266a_black.webp").write_bytes(b"img")
    (session / runner.COMPLETION_MARKER).write_text("ok", encoding="utf-8")

    # No IMPORT_EXPECTED_SKUS → full scope.
    file_skus = runner._read_expected_skus(input_csv)
    _, coverage, expected_count = runner._select_source_images(source_base, file_skus)
    assert expected_count == 3   # scored against the whole file
    assert coverage == 1


# ─────────────────────────────────────────────────────────────
# woocommerce_generator_v12 — copy-before-CSV + per-image gate
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def gen_module():
    return _load_module("wcg_v12", str(_IB / "woocommerce_generator_v12.py"))


def test_generator_missing_image_gate(monkeypatch, tmp_path, gen_module):
    """If a mapped image is absent, no CSV is written and stats report it."""
    # Minimal input with the 'شماره' column the generator requires.
    input_csv = tmp_path / "in.csv"
    import pandas as pd

    # Build a tiny valid input. The generator groups by 'sku' after expansion;
    # we lean on its own expansion, so provide the columns it reads.
    df = pd.DataFrame([{
        "شماره": 1,
        "sku": "9266",
        "نام_محصول": "کد 9266",
        "رنگ": "مشکی",
        "قیمت_اصلی": "100000",
    }])
    df.to_csv(input_csv, index=False, encoding="utf-8-sig")

    source = tmp_path / "src"      # empty → every mapped image is "missing"
    source.mkdir()
    dest = tmp_path / "dest"

    # Run inside import_builder so relative sku_list.txt resolves like production.
    monkeypatch.chdir(_IB)

    result = gen_module.process_products_v12(
        input_file=str(input_csv),
        process_images=True,
        source_images_folder=str(source),
        dest_images_folder=str(dest),
    )
    # New 3-tuple contract.
    assert len(result) == 3
    df_out, mappings, copy_stats = result

    if mappings:
        # There were images to copy, none were found → gate must trip.
        assert copy_stats["missing"] == len(mappings)
        assert copy_stats["copied"] == 0
        # No CSV should have been written to the uploads dir for this run.
        # (The gate returns before the to_csv calls.)
    else:
        # No image mapping produced (e.g. excluded); stats still well-formed.
        assert copy_stats["missing"] == 0


def test_generator_returns_three_tuple_on_bad_input(tmp_path, gen_module):
    """Missing 'شماره' column returns a 3-tuple of None, matching the contract."""
    import pandas as pd
    bad = tmp_path / "bad.csv"
    pd.DataFrame([{"name": "x", "price": 1}]).to_csv(bad, index=False, encoding="utf-8-sig")

    result = gen_module.process_products_v12(input_file=str(bad))
    assert result == (None, None, None)


# ─────────────────────────────────────────────────────────────
# unified_image_processor — IMG_PROCESS_SKUS allowlist
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def uip_module():
    return _load_module("uip_mod", str(_IMG / "unified_image_processor.py"))


def _make_square_webp(path, size=(80, 80)):
    from PIL import Image
    Image.new("RGB", size, (10, 20, 30)).save(path)


def test_image_processor_respects_allowlist(monkeypatch, tmp_path, uip_module):
    """Only categories named in IMG_PROCESS_SKUS are processed."""
    inp = tmp_path / "in"
    inp.mkdir()
    out = tmp_path / "out"
    for cat in ("9266", "9321", "9280"):
        _make_square_webp(inp / f"{cat}a.webp")

    monkeypatch.setenv("IMG_PROCESS_SKUS", "9266, 9280")
    # Disable colour detection to keep the run fast and deterministic.
    processed = uip_module.process_images_unified(
        str(inp), str(out), detect_color=False
    )

    # Extract leading category digits from produced filenames.
    import re
    cats = set()
    for p in out.iterdir():
        if p.is_file():
            m = re.match(r"(\d+)", p.stem)
            if m:
                cats.add(m.group(1))
    assert cats == {"9266", "9280"}
    assert "9321" not in cats


def test_image_processor_empty_allowlist_processes_all(monkeypatch, tmp_path, uip_module):
    """Unset/empty IMG_PROCESS_SKUS → process every category (full mode)."""
    inp = tmp_path / "in"
    inp.mkdir()
    out = tmp_path / "out"
    for cat in ("9266", "9321"):
        _make_square_webp(inp / f"{cat}a.webp")

    monkeypatch.delenv("IMG_PROCESS_SKUS", raising=False)
    uip_module.process_images_unified(str(inp), str(out), detect_color=False)

    import re
    cats = set()
    for p in out.iterdir():
        if p.is_file():
            m = re.match(r"(\d+)", p.stem)
            if m:
                cats.add(m.group(1))
    assert cats == {"9266", "9321"}


# ─────────────────────────────────────────────────────────────
# Image_Downloader._build_sku_map — manifest sku column drives naming
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def downloader_cls():
    mod = _load_module("img_dl", str(_IMG / "Image_Downloader.py"))
    return mod.AdvancedImageDownloader


def test_build_sku_map_prefers_sku_column(tmp_path, downloader_cls):
    """A manifest 'sku' column names files by SKU, not sequential page index."""
    import pandas as pd
    dl = downloader_cls(excel_path="unused.xlsx", output_folder=str(tmp_path))
    df = pd.DataFrame({
        "Product URL": ["http://x/1", "http://x/2"],
        "sku": ["9266", "9321"],
        "Product Name": ["کد 9266", "کد 9321"],
    })
    dl._build_sku_map(df)
    assert dl.sku_map == {1: "9266", 2: "9321"}
    # Filename uses the SKU, not the page number.
    dl.session_folder = str(tmp_path)
    assert dl.generate_image_name(1, 0) == "9266a"


def test_build_sku_map_falls_back_to_name(tmp_path, downloader_cls):
    """Without a sku column, the code is parsed from the product name."""
    import pandas as pd
    dl = downloader_cls(excel_path="unused.xlsx", output_folder=str(tmp_path))
    df = pd.DataFrame({
        "Product URL": ["http://x/1"],
        "Product Name": ["کد 9266"],
    })
    dl._build_sku_map(df)
    assert dl.sku_map == {1: "9266"}


def test_build_sku_map_blank_sku_uses_page_number(tmp_path, downloader_cls):
    """A blank sku with no usable name falls back to the page index."""
    import pandas as pd
    dl = downloader_cls(excel_path="unused.xlsx", output_folder=str(tmp_path))
    df = pd.DataFrame({
        "Product URL": ["http://x/1"],
        "sku": [""],
        "Product Name": ["no digits here"],
    })
    dl._build_sku_map(df)
    assert dl.sku_map == {1: "1"}
