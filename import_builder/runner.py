#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Builder - Automated Runner
Runs WooCommerce CSV generation without web interface.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

_this_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_this_dir))

from paths import ROOT_DIR, IMPORT_BUILDER_UPLOADS_DIR

_DATE_FOLDER_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')

# Marker file written by unified_image_processor.py when a processing run
# finishes successfully. Its presence distinguishes a complete run from a
# partial one left behind by a timeout/crash.
COMPLETION_MARKER = '.processing_complete'

_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
# Product image filenames start with the SKU digits (e.g. 9266a_black.webp).
_PREFIX_RE = re.compile(r'^(\d+)')


def _dated_subfolders(base_path):
    """Return dated subfolders under base_path, newest name last."""
    if not base_path.exists():
        return []
    dated = [
        f for f in base_path.iterdir()
        if f.is_dir() and _DATE_FOLDER_PATTERN.match(f.name)
    ]
    dated.sort(key=lambda f: f.name)
    return dated


def _folder_prefixes(folder):
    """Set of numeric SKU prefixes of the image files in a folder."""
    prefixes = set()
    try:
        for f in folder.iterdir():
            if not f.is_file() or f.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            m = _PREFIX_RE.match(f.stem)
            if m:
                prefixes.add(m.group(1))
    except OSError:
        pass
    return prefixes


def _read_expected_skus(input_file):
    """Read the SKUs the WooCommerce build expects images for, as strings.

    Mirrors how the generator derives image prefixes: the SKU column of
    product.csv (which equals the model number, e.g. 9266). Returns a set of
    digit-only strings so it can be compared against on-disk image prefixes.
    """
    try:
        import pandas as pd
    except ImportError:
        return set()

    try:
        if str(input_file).lower().endswith('.csv'):
            df = pd.read_csv(input_file, encoding='utf-8-sig', dtype=str)
        else:
            df = pd.read_excel(input_file, dtype=str)
    except Exception:
        return set()

    sku_col = next((c for c in df.columns if c.strip().lower() == 'sku'), None)
    if sku_col is None:
        return set()

    skus = set()
    for val in df[sku_col].dropna():
        m = _PREFIX_RE.match(str(val).strip())
        if m:
            skus.add(m.group(1))
    return skus


def _select_source_images(base_path, expected_skus):
    """Pick the processed-images folder that best covers the expected SKUs.

    Selection order:
      1. Prefer folders carrying the completion marker; fall back to all dated
         folders if none are marked (older runs predate the marker).
      2. Among the candidates, pick the one covering the most expected SKUs.
      3. Tie-break by newest folder name.

    Returns (folder, coverage, expected_count). coverage is the number of
    expected SKUs whose images are present in the chosen folder. When there are
    no expected SKUs to score against, coverage is reported as the folder's own
    prefix count so a non-empty folder is still preferred over an empty one.
    """
    dated = _dated_subfolders(base_path)
    if not dated:
        # No dated subfolders: fall back to the base folder itself.
        return base_path, 0, len(expected_skus)

    marked = [f for f in dated if (f / COMPLETION_MARKER).exists()]
    candidates = marked if marked else dated

    def score(folder):
        prefixes = _folder_prefixes(folder)
        if expected_skus:
            coverage = len(expected_skus & prefixes)
        else:
            coverage = len(prefixes)
        # newest name wins ties
        return (coverage, folder.name)

    best = max(candidates, key=score)
    best_prefixes = _folder_prefixes(best)
    coverage = len(expected_skus & best_prefixes) if expected_skus else len(best_prefixes)
    return best, coverage, len(expected_skus)


def _count_files(folder):
    try:
        return sum(1 for f in folder.iterdir() if f.is_file())
    except OSError:
        return 0


def main():
    input_file = ROOT_DIR / "data" / "outputs" / "product.csv"
    source_images_base = ROOT_DIR / "data" / "outputs" / "processed_images"
    dest_images = ROOT_DIR / "data" / "outputs" / "renamed_images" / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return False

    expected_skus = _read_expected_skus(input_file)
    source_images, coverage, expected_count = _select_source_images(
        source_images_base, expected_skus
    )

    if not source_images.exists() or not any(source_images.iterdir()):
        print(f"ERROR: No processed images found in: {source_images}")
        return False

    print(f"Source images: {source_images}")
    if expected_count:
        pct = (coverage / expected_count) * 100
        print(f"SKU coverage: {coverage}/{expected_count} ({pct:.0f}%)")
        # Refuse to build against a folder that covers (almost) none of the
        # current products — that is the signature of a stale or partial
        # processing run and would silently produce empty renamed_images.
        if coverage == 0:
            print(
                "ERROR: The selected processed-images folder does not cover any "
                "current product SKUs. This usually means image processing was "
                "interrupted or ran against a different scrape. Re-run image "
                "processing before building the WooCommerce import."
            )
            return False

    # Change to import_builder directory so relative paths (sku_list.txt etc.) resolve correctly
    original_cwd = os.getcwd()
    os.chdir(str(_this_dir))

    try:
        from woocommerce_generator_v12 import process_products_v12

        dest_images.mkdir(parents=True, exist_ok=True)

        df_output, mappings = process_products_v12(
            input_file=str(input_file),
            process_images=True,
            source_images_folder=str(source_images),
            dest_images_folder=str(dest_images),
        )

        if df_output is None:
            print("ERROR: Import builder processing failed.")
            return False

        # Guard against the silent-failure mode: if the generator expected to
        # copy images (a non-empty source→target mapping) but nothing landed in
        # the destination, the WooCommerce CSV would reference image URLs whose
        # files were never produced. Treat that as a hard failure.
        copied = _count_files(dest_images)
        if mappings and copied == 0:
            print(
                f"ERROR: {len(mappings)} images were expected but none were "
                f"copied into {dest_images}. Aborting so a broken import is not "
                f"emitted. Check that processed images match the product SKUs."
            )
            return False

        # Save a convenience copy to data/outputs/
        output_copy = ROOT_DIR / "data" / "outputs" / "woocommerce_import.csv"
        df_output.to_csv(str(output_copy), index=False, encoding='utf-8-sig')
        print(f"\nCopy saved: {output_copy}")
        print(f"Renamed images: {copied} files in {dest_images}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
