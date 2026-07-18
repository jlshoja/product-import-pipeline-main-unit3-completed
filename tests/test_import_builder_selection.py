"""
Tests for the Import Builder's processed-images folder selection.

Covers the fix for the empty ``renamed_images/`` bug: the runner used to pick
the newest-by-name dated folder under ``processed_images/``. When a processing
run was interrupted (timeout/retry) it left a *newer* partial folder that
covered only a handful of the current product SKUs, so image lookup produced an
empty copy-mapping and ``renamed_images/`` stayed empty — silently.

The runner now selects by SKU coverage (preferring the completion marker) and
fails loudly when the best folder covers no current SKUs.
"""

import sys
from pathlib import Path

# Make import_builder importable the same way the pipeline does.
_IB = Path(__file__).resolve().parent.parent / "import_builder"
if str(_IB) not in sys.path:
    sys.path.insert(0, str(_IB))

import runner  # noqa: E402


def _make_folder(base, name, prefixes, marked=False, letters=("a", "b")):
    """Create a dated processed-images folder with image files per prefix."""
    folder = base / name
    folder.mkdir(parents=True, exist_ok=True)
    for pfx in prefixes:
        for letter in letters:
            (folder / f"{pfx}{letter}_black.webp").write_bytes(b"img")
    if marked:
        (folder / runner.COMPLETION_MARKER).write_text("ok", encoding="utf-8")
    return folder


# ─────────────────────────────────────────────────────────────
# coverage-based selection
# ─────────────────────────────────────────────────────────────

def test_prefers_complete_older_folder_over_partial_newer(tmp_path):
    """A complete older folder must beat a partial newer one on SKU coverage."""
    base = tmp_path / "processed_images"
    # Older folder covers all current SKUs.
    _make_folder(base, "2026-07-17_17-00-42", ["9266", "9321", "9280"])
    # Newer folder is a partial/interrupted run covering only one SKU.
    _make_folder(base, "2026-07-18_00-56-44", ["9266"])

    expected = {"9266", "9321", "9280"}
    folder, coverage, expected_count = runner._select_source_images(base, expected)

    assert folder.name == "2026-07-17_17-00-42"
    assert coverage == 3
    assert expected_count == 3


def test_completion_marker_wins_over_unmarked(tmp_path):
    """When any folder is marked complete, only marked folders are candidates."""
    base = tmp_path / "processed_images"
    # Marked but slightly older; still the trustworthy one.
    _make_folder(base, "2026-07-17_17-00-42", ["9266", "9321"], marked=True)
    # Unmarked newer folder that happens to have broader coverage — ignored
    # because it lacks the completion marker (it may be mid-write).
    _make_folder(base, "2026-07-18_00-56-44", ["9266", "9321", "9280"])

    expected = {"9266", "9321", "9280"}
    folder, coverage, _ = runner._select_source_images(base, expected)

    assert folder.name == "2026-07-17_17-00-42"
    assert coverage == 2


def test_newest_marked_folder_wins_on_tie(tmp_path):
    """Among marked folders with equal coverage, the newest name wins."""
    base = tmp_path / "processed_images"
    _make_folder(base, "2026-07-17_17-00-42", ["9266", "9321"], marked=True)
    _make_folder(base, "2026-07-18_09-00-00", ["9266", "9321"], marked=True)

    folder, coverage, _ = runner._select_source_images(base, {"9266", "9321"})

    assert folder.name == "2026-07-18_09-00-00"
    assert coverage == 2


def test_zero_coverage_is_reported(tmp_path):
    """A folder that covers none of the expected SKUs reports coverage 0."""
    base = tmp_path / "processed_images"
    _make_folder(base, "2026-07-18_00-56-44", ["3868", "4369"])

    folder, coverage, expected_count = runner._select_source_images(
        base, {"9266", "9321"}
    )

    assert coverage == 0
    assert expected_count == 2


def test_no_expected_skus_prefers_non_empty(tmp_path):
    """With no SKUs to score against, the folder with the most images wins."""
    base = tmp_path / "processed_images"
    _make_folder(base, "2026-07-17_17-00-42", ["1", "2", "3"])
    _make_folder(base, "2026-07-18_00-56-44", ["1"])

    folder, coverage, expected_count = runner._select_source_images(base, set())

    assert folder.name == "2026-07-17_17-00-42"
    assert expected_count == 0


# ─────────────────────────────────────────────────────────────
# expected-SKU parsing from product.csv
# ─────────────────────────────────────────────────────────────

def test_read_expected_skus_from_csv(tmp_path):
    csv = tmp_path / "product.csv"
    csv.write_text(
        "sku,مدل\n9266,9266\n9321,9321\n9280,9280\n",
        encoding="utf-8-sig",
    )
    skus = runner._read_expected_skus(csv)
    assert skus == {"9266", "9321", "9280"}


def test_read_expected_skus_missing_column(tmp_path):
    csv = tmp_path / "product.csv"
    csv.write_text("name,price\nfoo,10\n", encoding="utf-8-sig")
    assert runner._read_expected_skus(csv) == set()


# ─────────────────────────────────────────────────────────────
# folder prefix extraction
# ─────────────────────────────────────────────────────────────

def test_folder_prefixes_ignores_non_images(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "9266a_black.webp").write_bytes(b"img")
    (folder / "9321b.jpg").write_bytes(b"img")
    (folder / runner.COMPLETION_MARKER).write_text("ok", encoding="utf-8")
    (folder / "notes.txt").write_text("x", encoding="utf-8")

    assert runner._folder_prefixes(folder) == {"9266", "9321"}
