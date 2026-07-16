"""
Tests for pipeline resume / checkpoint integrity and output lifecycle.

Covers the fixes for:
  #1  LinkScraper resume + status tracking (retry must not restart from scratch;
      eventual success must not leave the pipeline in a failed state).
  #2  Stage dependency handling (downstream must not run on an upstream that did
      not complete in the current run).
  #3  Stale output files (a fresh run must not consume a prior run's leftovers).

The pipeline_state module writes to a fixed STATE_FILE path; each test
monkeypatches it to a tmp file so the real runtime state is never touched.
"""

import importlib
import time
from pathlib import Path

import pytest

# Make product_extraction importable (mirrors the pattern in the other tests).
import sys
_PE = Path(__file__).resolve().parent.parent / "product_extraction"
if str(_PE) not in sys.path:
    sys.path.insert(0, str(_PE))

from common import pipeline_state as ps
from common.file_registry import get_file as get_file_name


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Redirect pipeline_state's STATE_FILE to an isolated tmp location."""
    f = tmp_path / "pipeline_state.json"
    monkeypatch.setattr(ps, "STATE_FILE", f)
    return f


def _write_output(tmp_path, name="out.xlsx", data=b"x"):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


# ─────────────────────────────────────────────────────────────
# pipeline_state: status transitions (Issue #1b)
# ─────────────────────────────────────────────────────────────

def test_eventual_success_clears_failed_status(state_file):
    """A step that fails then later succeeds must leave status 'running', not 'failed'."""
    ps.start_run()
    ps.update_step("Link Scraper", "failed")
    assert ps.read_state()["status"] == "failed"

    # Retry succeeds.
    ps.update_step("Link Scraper", "done")
    st = ps.read_state()
    assert st["steps"]["Link Scraper"]["status"] == "done"
    assert st["status"] == "running"  # no longer failed


def test_status_failed_only_while_a_step_is_failed(state_file):
    ps.start_run()
    ps.update_step("Link Scraper", "done")
    ps.update_step("Spec Scraper", "failed")
    assert ps.read_state()["status"] == "failed"
    ps.update_step("Spec Scraper", "done")
    assert ps.read_state()["status"] == "running"


def test_mark_complete_sets_complete(state_file):
    ps.start_run()
    ps.update_step("Link Scraper", "done")
    ps.mark_complete()
    assert ps.read_state()["status"] == "complete"


def test_update_step_preserves_recorded_output(state_file, tmp_path):
    """update_step(..., info=None) must not erase a previously recorded output."""
    ps.start_run()
    out = _write_output(tmp_path)
    ps.record_step_output("Link Scraper", out)
    # Marking done without passing info must keep the recorded output.
    ps.update_step("Link Scraper", "done")
    info = ps.read_state()["steps"]["Link Scraper"]["info"]
    assert info.get("output", {}).get("path") == out


# ─────────────────────────────────────────────────────────────
# output currency / stale detection (Issues #2, #3)
# ─────────────────────────────────────────────────────────────

def test_output_is_current_for_this_run(state_file, tmp_path):
    ps.start_run()
    out = _write_output(tmp_path)
    ps.record_step_output("Link Scraper", out)
    assert ps.step_output_is_current("Link Scraper", out) is True


def test_stale_output_from_previous_run_is_rejected(state_file, tmp_path):
    """An output recorded under a prior run_id must not validate for a new run."""
    ps.start_run(run_id="RUN_A")
    out = _write_output(tmp_path)
    ps.record_step_output("Link Scraper", out)
    assert ps.step_output_is_current("Link Scraper", out) is True

    # A brand-new run starts; the file on disk is now a stale leftover.
    ps.start_run(run_id="RUN_B")
    assert ps.step_output_is_current("Link Scraper", out) is False


def test_output_modified_after_record_is_rejected(state_file, tmp_path):
    ps.start_run()
    out = _write_output(tmp_path)
    ps.record_step_output("Link Scraper", out)
    # Simulate the file changing without going through record_step_output.
    time.sleep(0.01)
    Path(out).write_bytes(b"different content entirely")
    assert ps.step_output_is_current("Link Scraper", out) is False


def test_missing_output_is_not_current(state_file, tmp_path):
    ps.start_run()
    out = _write_output(tmp_path)
    ps.record_step_output("Link Scraper", out)
    Path(out).unlink()
    assert ps.step_output_is_current("Link Scraper", out) is False


def test_no_record_is_not_current(state_file, tmp_path):
    ps.start_run()
    out = _write_output(tmp_path)
    assert ps.step_output_is_current("Link Scraper", out) is False


# ─────────────────────────────────────────────────────────────
# Orchestration: dependency gate + fresh-output validation
# (ProductScraperApp helpers). These exercise the guards without
# running any browser/network by driving the helpers directly.
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    import main
    return main.ProductScraperApp()


def _xlsx_with_rows(path, rows=1):
    """Write a real .xlsx with `rows` data rows so pd.read_excel sees content."""
    import pandas as pd
    df = pd.DataFrame({"Product URL": [f"u{i}" for i in range(rows)]})
    pd.DataFrame(df).to_excel(str(path), index=False)
    return str(path)


def test_dependency_gate_rejects_stale_upstream(app, state_file, tmp_path):
    """Spec Scraper must refuse a Link Scraper output from a previous run."""
    links = _xlsx_with_rows(tmp_path / "extracted_links.xlsx")

    # Link Scraper recorded this output under RUN_A.
    ps.start_run(run_id="RUN_A")
    ps.record_step_output("Link Scraper", links)
    assert app._upstream_output_ready("Link Scraper", links) is True

    # A new run begins; the file is now a stale leftover -> gate must reject.
    ps.start_run(run_id="RUN_B")
    assert app._upstream_output_ready("Link Scraper", links) is False


def test_dependency_gate_standalone_fallback(app, state_file, tmp_path):
    """With no tracked run, the gate falls back to a plain non-empty check."""
    links = _xlsx_with_rows(tmp_path / "extracted_links.xlsx")
    # No run started / no recorded output -> existing non-empty file is accepted.
    assert app._upstream_output_ready("Link Scraper", links) is True
    # Missing file is rejected.
    assert app._upstream_output_ready("Link Scraper", str(tmp_path / "nope.xlsx")) is False


def test_validate_fresh_output_rejects_stale_file(app, tmp_path):
    """A file untouched since before the run (mtime not advanced) is rejected."""
    out = _xlsx_with_rows(tmp_path / "out.xlsx")
    mtime_now = Path(out).stat().st_mtime
    # Pretend the run started AFTER the file already existed.
    assert app._validate_fresh_output(out, mtime_before=mtime_now, stage_name="X") is False


def test_validate_fresh_output_accepts_freshly_written(app, tmp_path):
    out = tmp_path / "out.xlsx"
    mtime_before = None  # file did not exist before the run
    _xlsx_with_rows(out)
    assert app._validate_fresh_output(str(out), mtime_before, "X") is True


def test_validate_fresh_output_rejects_empty_table(app, tmp_path):
    import pandas as pd
    out = tmp_path / "out.xlsx"
    pd.DataFrame({"Product URL": []}).to_excel(str(out), index=False)
    assert app._validate_fresh_output(str(out), mtime_before=None, stage_name="X") is False


@pytest.fixture
def tmp_intermediate(tmp_path, monkeypatch):
    """Redirect INTERMEDIATE_DIR to a tmp dir so tests never touch real data.

    run_link_scraper imports INTERMEDIATE_DIR from common.path_registry inside
    the function body, so patching the module attribute is sufficient.
    """
    import common.path_registry as pr
    d = tmp_path / "intermediate"
    d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pr, "INTERMEDIATE_DIR", d)
    return d


def test_link_scraper_rejects_stale_output_on_failure(app, state_file, tmp_intermediate, monkeypatch):
    """
    Issue #2/#3 end-to-end at the stage level: a stale output already exists,
    the scraper 'fails' (swallows its exception and writes nothing new), and the
    stage must return False instead of trusting the stale file.
    """
    import scrapers.link_scraper as link_scraper_module

    out = tmp_intermediate / get_file_name('extracted_links')
    _xlsx_with_rows(out)  # stale leftover from a previous run

    ps.start_run()
    # Simulate a scraper that fails silently: main() returns without rewriting.
    monkeypatch.setattr(link_scraper_module, "main", lambda: None)

    assert app.run_link_scraper(resume=False) is False


def test_link_scraper_accepts_freshly_written_output(app, state_file, tmp_intermediate, monkeypatch):
    import scrapers.link_scraper as link_scraper_module

    out = tmp_intermediate / get_file_name('extracted_links')

    ps.start_run()

    def fake_main():
        _xlsx_with_rows(out, rows=3)

    monkeypatch.setattr(link_scraper_module, "main", fake_main)

    assert app.run_link_scraper(resume=False) is True
    # And the output was recorded against the current run.
    assert ps.step_output_is_current("Link Scraper", str(out)) is True
