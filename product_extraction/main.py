#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Entry Point -    
"""

import sys
import os
from pathlib import Path
import argparse
import signal

#    
from common.path_registry import ROOT_DIR

project_root = ROOT_DIR / "product_extraction"
sys.path.insert(0, str(project_root))

from common.file_registry import get_file
from common.path_registry import RUNTIME_CACHE_DIR, RUNTIME_REPORTS_DIR, get_dated_reports_dir
from common.file_utils import find_latest_dated
from config import get_config
from utils.logger import LoggerSetup, log_execution_time
from common.pipeline_state import (
    read_state, start_run, update_step, mark_complete,
    record_step_output, step_output_is_current,
)


class ProductScraperApp:
    """  """
    
    def __init__(self):
        """ """
        self.config = get_config()
        self.logger = LoggerSetup.get_main_logger()
        
    def print_banner(self):
        """Display application banner"""
        # Simple ASCII version for Windows compatibility
        banner = f"""
================================================================
        Product Scraper & Tracker v{self.config.version}
        Complete Product Scraping & Tracking System
================================================================
        """
        
        # Try UTF-8 version first, fallback to ASCII
        try:
            utf_banner = f"""

                                                                
          Product Scraper & Tracker v{self.config.version}              
                                                                
         Complete Product Scraping & Tracking System            
                                                                

            """
            print(utf_banner)
        except UnicodeEncodeError:
            print(banner)
        
        self.config.print_summary()
    
    @staticmethod
    def _file_mtime(path):
        """Return a file's mtime, or None if it does not exist."""
        try:
            return Path(path).stat().st_mtime
        except OSError:
            return None

    def _validate_fresh_output(self, output_path, mtime_before, stage_name):
        """Validate that `stage_name` produced a fresh, non-empty output this run.

        Requires all of:
        - the file exists and is non-empty,
        - it reads as a table with at least one row,
        - its mtime advanced past `mtime_before` (proving THIS run wrote it,
          not a stale leftover from a previous run).

        Returns True only when every check passes; logs the specific failure
        otherwise.
        """
        from common.file_utils import file_exists_and_non_empty
        import pandas as pd

        if not file_exists_and_non_empty(output_path):
            self.logger.error(f"{stage_name} produced no output: {output_path}")
            return False

        mtime_after = self._file_mtime(output_path)
        if mtime_before is not None and mtime_after is not None and mtime_after <= mtime_before:
            self.logger.error(
                f"{stage_name} did not write a fresh output — the file on disk is "
                f"stale (unchanged since before this run). Refusing to treat stale "
                f"data as success: {output_path}"
            )
            return False

        # Read as a table to confirm at least one data row. Pick the reader by
        # extension so .csv outputs (e.g. the standardizer's product.csv) are
        # validated the same way as .xlsx scraper outputs.
        try:
            if str(output_path).lower().endswith('.csv'):
                df = pd.read_csv(output_path, encoding='utf-8-sig')
            else:
                df = pd.read_excel(output_path)
        except Exception as e:
            self.logger.error(f"{stage_name} output could not be read as a table: {e}")
            return False

        if df.empty or len(df) == 0:
            self.logger.error(f"{stage_name} extracted zero rows")
            return False

        return True

    def _upstream_output_ready(self, upstream_step, path):
        """Return True if a downstream stage may safely consume `path`.

        Enforces the dependency gate: a stage must not run on an upstream's
        output unless that output belongs to the current run. When a tracked run
        recorded an output for `upstream_step`, we require it to be current
        (matching run_id + on-disk size/mtime) — this rejects stale leftovers.

        When there is no tracked run or the upstream recorded no output (e.g. the
        scrapers invoked standalone, outside run_auto_pipeline), we fall back to
        a plain non-empty file check so standalone use is not broken.
        """
        from common.file_utils import file_exists_and_non_empty

        state = read_state()
        # A run is "active" (tracked) whenever a pipeline run is currently
        # running. Inside an active run the dependency is strict: the upstream's
        # output must be current (recorded this run + unchanged on disk). A
        # missing record means the upstream did NOT complete in this run, so a
        # leftover file on disk is stale and must be rejected.
        #
        # We key off 'running' specifically (not 'failed'): in the auto pipeline a
        # downstream stage only runs while the run is 'running' (a failure breaks
        # the loop before downstream runs), and a stale 'failed' state left by a
        # prior run must not make an unrelated later invocation reject valid input.
        run_active = bool(state) and state.get('status') == 'running'
        if run_active:
            if not step_output_is_current(upstream_step, path):
                self.logger.error(
                    f"Refusing to run: {upstream_step} did not produce a current "
                    f"output at {path} in this run (missing or stale). Upstream must "
                    f"complete successfully in this run first."
                )
                return False
            return True

        # No active tracked run (e.g. a scraper invoked standalone, outside
        # run_auto_pipeline): fall back to a plain non-empty file check so
        # standalone use is not broken.
        if not file_exists_and_non_empty(path):
            self.logger.error(f"Required input missing or empty: {path}")
            return False
        return True

    @log_execution_time()
    def run_link_scraper(self, input_file=get_file('archive_urls'), resume=False):
        """Run Link Scraper"""
        self.logger.info("="*70)
        self.logger.info("[1]  Running Link Scraper")
        self.logger.info("="*70)
        
        try:
            import scrapers.link_scraper as link_scraper_module
            from common.path_registry import INTERMEDIATE_DIR
            import os

            output_file = get_file('extracted_links')
            output_path = str(INTERMEDIATE_DIR / output_file)

            # Capture the output file's mtime BEFORE running. A stale file from a
            # previous run may already exist on disk. We only accept the run as
            # successful if this run actually (re)wrote the file, proven by the
            # mtime advancing. This prevents a swallowed-exception failure from
            # passing validation on stale data.
            mtime_before = self._file_mtime(output_path)

            # Set AUTO_MODE for link_scraper to use resume logic
            os.environ['AUTO_MODE'] = '1'
            # Set AUTO_RESUME based on the caller's resume decision. The pipeline
            # forces resume=True on retry attempts so a mid-stage failure resumes
            # from checkpoint instead of wiping completed work.
            os.environ['AUTO_RESUME'] = '1' if resume else '0'

            # Run the scraper
            link_scraper_module.main()

            # Content + freshness validation: the file must exist, contain at
            # least one product row, AND have been written by this run.
            if not self._validate_fresh_output(output_path, mtime_before, "Link Scraper"):
                return False

            # Record the produced output against the current run_id so downstream
            # stages can verify they are consuming this run's output, not a stale one.
            record_step_output("Link Scraper", output_path)
            self.logger.info(" Link Scraper completed successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Error in Link Scraper: {e}", exc_info=True)
            return False
    
    @log_execution_time()
    def run_spec_scraper(self, input_file=get_file('extracted_products'), resume=False):
        """Run Spec Scraper"""
        self.logger.info("="*70)
        self.logger.info("[2]  Running Spec Scraper")
        self.logger.info("="*70)
        
        try:
            import scrapers.spec_scraper as spec_scraper_module
            from common.path_registry import INTERMEDIATE_DIR, OUTPUTS_DIR

            # Dependency gate: the Link Scraper's output (extracted_links) is a
            # REQUIRED input. It must belong to the current run — a stale file
            # from a previous, failed run must not be consumed.
            links_filename = get_file('extracted_links')
            links_file = str(INTERMEDIATE_DIR / links_filename)
            if not self._upstream_output_ready("Link Scraper", links_file):
                return False

            # spec_scraper writes product_details to OUTPUTS_DIR. Capture its
            # mtime before running so we can prove this run (re)wrote it.
            output_path = str(OUTPUTS_DIR / get_file('product_details'))
            mtime_before = self._file_mtime(output_path)

            # Drive resume/fresh explicitly. The pipeline forces resume=True on
            # retry attempts so a mid-stage failure resumes from checkpoint
            # instead of restarting the full scan.
            os.environ['AUTO_MODE'] = '1'
            os.environ['AUTO_RESUME'] = '1' if resume else '0'

            # Run the scraper
            spec_scraper_module.main()

            # Content + freshness validation on the real output file.
            if not self._validate_fresh_output(output_path, mtime_before, "Spec Scraper"):
                return False

            record_step_output("Spec Scraper", output_path)
            self.logger.info(" Spec Scraper completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error in Spec Scraper: {e}", exc_info=True)
            return False

    @log_execution_time()
    def run_standardizer(self):
        """Run Product Standardizer"""
        self.logger.info("="*70)
        self.logger.info("[3]  Running Standardizer")
        self.logger.info("="*70)

        try:
            import standardizer
            from common.path_registry import OUTPUTS_DIR

            # Dependency gate: the standardizer consumes the Spec Scraper's output
            # (product_details in OUTPUTS_DIR, per standardizer/runner.py). Require
            # it to belong to the current run so a stale file cannot be consumed.
            input_file = str(OUTPUTS_DIR / get_file('product_details'))
            if not self._upstream_output_ready("Spec Scraper", input_file):
                return False

            # Capture the standardizer's output (product.csv) mtime before running
            # so we can prove this run produced it and record it for downstream
            # stages (Import Builder) to verify currency against.
            output_path = str(OUTPUTS_DIR / get_file('standardized_output'))
            mtime_before = self._file_mtime(output_path)

            result = standardizer.main()

            # Validate the standardizer actually wrote a fresh, non-empty CSV this
            # run. If it silently produced nothing (or only a stale file remains),
            # do not report success — Import Builder must not consume stale data.
            if not self._validate_fresh_output(output_path, mtime_before, "Standardizer"):
                return False

            record_step_output("Standardizer", output_path)
            self.logger.info(" Standardizer completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error in Standardizer: {e}", exc_info=True)
            return False
    
    @log_execution_time()
    def run_import_builder(self):
        """Run Import Builder (WooCommerce CSV generation)"""
        self.logger.info("="*70)
        self.logger.info("[4]  Running Import Builder")
        self.logger.info("="*70)

        try:
            import_builder_dir = str(ROOT_DIR / "import_builder")
            if import_builder_dir not in sys.path:
                sys.path.insert(0, import_builder_dir)

            from runner import main as import_builder_main
            from common.path_registry import OUTPUTS_DIR

            # Dependency gate: Import Builder consumes the Standardizer's output
            # (product.csv in OUTPUTS_DIR, per import_builder/runner.py). Require
            # it to belong to the current run so a stale CSV from a prior run is
            # not turned into a WooCommerce import.
            standardized_input = str(OUTPUTS_DIR / get_file('standardized_output'))
            if not self._upstream_output_ready("Standardizer", standardized_input):
                return False

            # Manifest env vars drive the new/updated CSV split. Change Detection
            # is the source of truth and already set NEW_MANIFEST / UPDATED_MANIFEST
            # / IMPORT_EXPECTED_SKUS for incremental runs (see run_change_detection).
            # Here we only cover the STANDALONE case — run_import_builder invoked
            # directly without Change Detection having run this process — by
            # locating the newest reports folder's manifests as a best-effort
            # fallback. We never override values Change Detection set.
            try:
                if not self.change_result and not os.environ.get('NEW_MANIFEST') \
                        and not os.environ.get('UPDATED_MANIFEST'):
                    reports_root = Path(RUNTIME_REPORTS_DIR)
                    subdirs = [d for d in reports_root.iterdir() if d.is_dir()]
                    if subdirs:
                        latest = max(subdirs, key=lambda p: p.stat().st_mtime)
                        mn = latest / 'new_products_list.csv'
                        mu = latest / 'updated_products_list.csv'
                        if mn.exists():
                            os.environ['NEW_MANIFEST'] = str(mn)
                        if mu.exists():
                            os.environ['UPDATED_MANIFEST'] = str(mu)

                mn_env = os.environ.get('NEW_MANIFEST')
                mu_env = os.environ.get('UPDATED_MANIFEST')
                if mn_env or mu_env:
                    self.logger.info(f"Import Builder: NEW_MANIFEST={mn_env}, UPDATED_MANIFEST={mu_env}")
            except Exception:
                self.logger.warning("Import Builder: failed to resolve fallback manifests", exc_info=True)

            result = import_builder_main()

            self.logger.info(" Import Builder completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error in Import Builder: {e}", exc_info=True)
            return False

    @staticmethod
    def _sku_to_code(sku):
        """Extract the numeric product code (3–6 digits) from a SKU/name.

        Matches the extraction compare_scans and the image scripts use so the
        processor's allowlist keys agree with the downloaded filenames.
        """
        from common.text_utils import extract_numeric_code
        return extract_numeric_code(str(sku), min_digits=3, max_digits=6) or ''

    def _resolve_incremental_mode(self):
        """Decide whether this run is 'full' or 'incremental'.

        Honours the requested mode:
          - 'full'        → always full.
          - 'incremental' → incremental (falls back to full if no prior catalog).
          - 'auto'        → full when there is no previous WooCommerce catalog to
                            diff against (first run); otherwise incremental. When
                            attended (interactive TTY and not AUTO_RESUME/CI
                            unattended) the user is asked to confirm once.

        Returns 'full' or 'incremental'. Does not run the comparison.
        """
        import trackers.compare_scans as cs

        requested = getattr(self, 'requested_mode', 'auto')
        if requested == 'full':
            return 'full'

        prev_catalog = cs.find_previous_woo_file()
        if not prev_catalog:
            self.logger.info(
                "No previous WooCommerce catalog found — running FULL (first run)."
            )
            return 'full'

        if requested == 'incremental':
            return 'incremental'

        # requested == 'auto' and a previous catalog exists.
        unattended = os.getenv('AUTO_RESUME') is not None or not sys.stdin.isatty()
        if unattended:
            self.logger.info(
                "Previous catalog found — auto-selecting INCREMENTAL (unattended)."
            )
            return 'incremental'

        # Attended: ask once.
        try:
            ans = input(
                "A previous WooCommerce catalog exists.\n"
                "  [1] Incremental update (only new / changed products)  [default]\n"
                "  [2] Full reprocess (all products from scratch)\n"
                "Choose (1/2): "
            ).strip()
        except Exception:
            ans = ''
        return 'full' if ans == '2' else 'incremental'

    @log_execution_time()
    def run_change_detection(self):
        """Resolve full vs incremental and, when incremental, compute the subset.

        - In FULL mode: process everything (subset = None), never skip.
        - In INCREMENTAL mode: run compare_scans against the previous catalog.
            * new = 0 and changed = 0  → nothing to do; skip image + import.
            * otherwise → image subset = new ∪ colour-changed; wire the
              new/updated manifests so the import builder splits the two CSVs and
              the downloader fetches only the subset.

        Always returns True (a comparison producing "no changes" is a success,
        not a failure) unless an unexpected error occurs.
        """
        self.logger.info("="*70)
        self.logger.info("[CHANGE] Running Change Detection")
        self.logger.info("="*70)

        try:
            self.effective_mode = self._resolve_incremental_mode()
            self.logger.info(f"[CHANGE] Effective mode: {self.effective_mode}")

            if self.effective_mode == 'full':
                # Full run: no subset, no skip, no manifests. Clear any manifest
                # env vars a previous run may have left set in this process.
                self.image_subset_skus = None
                self.skip_image_and_import = False
                for var in ('NEW_MANIFEST', 'UPDATED_MANIFEST', 'IMG_MANIFEST',
                            'IMPORT_EXPECTED_SKUS'):
                    os.environ.pop(var, None)
                return True

            # Incremental: run the comparison.
            import trackers.compare_scans as cs
            result = cs.run_auto_compare()

            if not result:
                # No scan or no previous catalog surfaced late → treat as full so
                # we never silently skip work.
                self.logger.warning(
                    "[CHANGE] Comparison unavailable — falling back to FULL."
                )
                self.effective_mode = 'full'
                self.image_subset_skus = None
                self.skip_image_and_import = False
                return True

            self.change_result = result
            counts = result.get('counts', {})
            self.logger.info(
                f"[CHANGE] new={counts.get('new', 0)} "
                f"changed={counts.get('changed', 0)} "
                f"(price={counts.get('price', 0)}, colour={counts.get('color', 0)}) "
                f"removed={counts.get('removed', 0)}"
            )

            new_skus = result.get('new_skus', [])
            image_subset = result.get('image_subset_skus', [])
            manifests = result.get('manifests', {})

            # Scenario: nothing new and nothing changed → stop early.
            if counts.get('new', 0) == 0 and counts.get('changed', 0) == 0:
                self.logger.info(
                    "[CHANGE] No new products and no changes detected. "
                    "Skipping image processing and import build."
                )
                print("\n" + "="*70)
                print("No new products and no changes were detected.")
                print("Nothing to download, process, or import. Pipeline stops here.")
                print("="*70 + "\n")
                self.skip_image_and_import = True
                self.image_subset_skus = []
                return True

            # There is work to do. Record the image subset (new ∪ colour-changed).
            self.skip_image_and_import = False
            self.image_subset_skus = list(image_subset)

            # Wire manifests for the downstream stages:
            #  - NEW_MANIFEST / UPDATED_MANIFEST → generator splits the two CSVs.
            #  - IMPORT_EXPECTED_SKUS → runner scopes coverage/gate to the subset.
            new_manifest = manifests.get('new')
            updated_manifest = manifests.get('updated')
            if new_manifest and Path(new_manifest).exists():
                os.environ['NEW_MANIFEST'] = new_manifest
            if updated_manifest and Path(updated_manifest).exists():
                os.environ['UPDATED_MANIFEST'] = updated_manifest
            # The import builder only needs images for the subset; pass the exact
            # SKU list so its coverage/gate is scoped correctly.
            os.environ['IMPORT_EXPECTED_SKUS'] = ','.join(str(s) for s in image_subset)

            if not image_subset:
                # Changed products are price-only (no new colour): no images to
                # (re)process, but we still emit the updated CSV via import build.
                self.logger.info(
                    "[CHANGE] Only price changes detected — no images to "
                    "reprocess; will still build the updated-products CSV."
                )
                self.skip_image_only = True
            else:
                self.skip_image_only = False
                self.logger.info(
                    f"[CHANGE] {len(image_subset)} product(s) need image "
                    f"processing ({len(new_skus)} new)."
                )

            return True

        except Exception as e:
            self.logger.error(f"Error in Change Detection: {e}", exc_info=True)
            return False

    @log_execution_time()
    def run_image_processing(self):
        """Run image download + processing non-interactively (automatic mode).

        The image_processing scripts are driven entirely by env vars / CLI flags,
        so we invoke them directly (bypassing the interactive menu.py) with the
        same paths and settings menu.py would use. Two sub-steps run in order:
        download (Image_Downloader.py) then process/compress (unified_image_processor.py).
        """
        import subprocess

        self.logger.info("="*70)
        self.logger.info("[IMG] Running Image Processing (download + process)")
        self.logger.info("="*70)

        from common.path_registry import INTERMEDIATE_DIR

        image_dir = ROOT_DIR / "image_processing"
        data_outputs = ROOT_DIR / "data" / "outputs"

        # Image download reads product URLs from the Link Scraper's output. Use
        # the registered filename (extracted_links.xlsx) rather than a hardcoded
        # 'extracted_products.xlsx' — the latter was a different, stale physical
        # file on disk. Gate it so a stale leftover from a prior run is refused.
        excel_file        = str(INTERMEDIATE_DIR / get_file('extracted_links'))
        downloaded_folder = str(data_outputs / "downloaded_images")
        output_folder     = str(data_outputs / "processed_images")

        if not self._upstream_output_ready("Link Scraper", excel_file):
            return False

        # --- Sub-step 1: download images (fresh, full, no prompts) ---
        download_env = os.environ.copy()
        download_env["IMG_EXCEL"]    = excel_file
        download_env["IMG_OUTPUT"]   = downloaded_folder
        download_env["IMG_SELENIUM"] = "1"
        download_env["IMG_RETRIES"]  = "3"

        # Incremental vs full download selection.
        #
        # In incremental mode Change Detection wrote an image-subset manifest
        # (image_subset_list.csv: sku,url,image_urls,reason) listing exactly the
        # products whose images must be fetched (new ∪ colour-changed). We hand
        # that to the downloader so it fetches ONLY those pages. Existing
        # unchanged products keep their already-downloaded images.
        #
        # In full mode we download every product from the links file.
        subset = getattr(self, 'image_subset_skus', None)
        manifest_file = None
        if subset is not None:
            # Incremental: prefer the image-subset manifest written this run.
            if self.change_result:
                cand = (self.change_result.get('manifests') or {}).get('image_subset')
                if cand and Path(cand).exists():
                    manifest_file = cand
            if not manifest_file:
                # Fallback: newest reports folder holding an image_subset_list.csv
                try:
                    reports_root = Path(RUNTIME_REPORTS_DIR)
                    subdirs = [d for d in reports_root.iterdir() if d.is_dir()]
                    if subdirs:
                        latest = max(subdirs, key=lambda p: p.stat().st_mtime)
                        c = latest / 'image_subset_list.csv'
                        if c.exists():
                            manifest_file = str(c)
                except Exception:
                    manifest_file = None

        if manifest_file:
            download_env["IMG_MANIFEST"] = manifest_file
            download_env["IMG_MODE"]     = "full"
            download_env["IMG_RESUME"]   = "fresh"
            # The downloader dedups per-file (identical {sku}{letter}{ext} on
            # disk is reused), so colour-changed products still fetch their new
            # images while unchanged files are skipped automatically.
            self.logger.info(f"[IMG] Incremental download via subset manifest: {manifest_file}")
        else:
            # Full download of all products.
            download_env.pop("IMG_MANIFEST", None)
            download_env["IMG_MODE"]     = "full"
            download_env["IMG_RESUME"]   = "fresh"

        self.logger.info("[IMG] Step 1/2 - Downloading images (full, fresh)...")
        # run with timeout and retry
        timeout_sec = int(os.environ.get('PROCESS_TIMEOUT', '900'))
        retry_count = int(os.environ.get('PROCESS_SUBPROCESS_RETRY', '1'))
        attempt = 0
        download_ok = False
        while attempt <= retry_count and not download_ok:
            try:
                attempt += 1
                self.logger.info(f"[IMG] download attempt {attempt}/{retry_count + 1}")
                result = subprocess.run(
                    [sys.executable, "Image_Downloader.py"],
                    cwd=str(image_dir),
                    env=download_env,
                    timeout=timeout_sec,
                )
                if result.returncode == 0:
                    download_ok = True
                else:
                    self.logger.error(f"Image download failed with returncode {result.returncode}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Image download subprocess timed out after {timeout_sec}s (attempt {attempt})")
            except Exception as e:
                self.logger.error(f"Image download subprocess error: {e}")

        if not download_ok:
            self.logger.error("Image download ultimately failed")
            return False

        # --- Sub-step 2: process and compress images ---
        process_cmd = [
            sys.executable, "unified_image_processor.py",
            "-i", downloaded_folder,
            "-o", output_folder,
            "-s", "50",   # gallery size KB (menu.py default)
            "-m", "100",  # main size KB (menu.py default)
        ]

        # In incremental mode, restrict processing to the subset's category
        # numbers so the processor doesn't reprocess every previously-downloaded
        # session. The processor reads IMG_PROCESS_SKUS (comma-separated codes).
        process_env = download_env.copy()
        if subset is not None:
            codes = [self._sku_to_code(s) for s in subset]
            codes = [c for c in codes if c]
            process_env["IMG_PROCESS_SKUS"] = ','.join(codes)
            self.logger.info(f"[IMG] Processing restricted to {len(codes)} subset code(s).")
        else:
            process_env.pop("IMG_PROCESS_SKUS", None)

        self.logger.info("[IMG] Step 2/2 - Processing and compressing images...")
        # processing step also gets a timeout and retry
        proc_ok = False
        attempt = 0
        while attempt <= retry_count and not proc_ok:
            try:
                attempt += 1
                self.logger.info(f"[IMG] processing attempt {attempt}/{retry_count + 1}")
                result = subprocess.run(process_cmd, cwd=str(image_dir), env=process_env, timeout=timeout_sec)
                if result.returncode == 0:
                    proc_ok = True
                else:
                    self.logger.error(f"Image processing failed with returncode {result.returncode}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Image processing subprocess timed out after {timeout_sec}s (attempt {attempt})")
            except Exception as e:
                self.logger.error(f"Image processing subprocess error: {e}")

        if not proc_ok:
            self.logger.error("Image processing ultimately failed")
            return False

        self.logger.info(" Image Processing completed successfully")
        return True

    def run_auto_pipeline(self, mode='auto'):
        """Run the entire pipeline unattended (automatic execution mode).

        Order: link scrape -> spec scrape (fresh) -> standardize ->
        change detection -> image download+process -> import build. No
        interactive prompts (unless attended + auto mode, where the user is
        asked to confirm full vs incremental once).

        mode:
          'full'        — always scrape, download, process and build for ALL
                          products (the original behaviour).
          'incremental' — after standardizing, compare against the previous
                          WooCommerce catalog and only download/process/rename
                          images for NEW products and products that gained a new
                          colour. Existing unchanged products are reused. Two
                          WooCommerce CSVs are emitted (new / updated).
          'auto'        — pick automatically: first run (no previous catalog)
                          runs full; otherwise incremental. When attended
                          (interactive terminal, not unattended) the user is
                          asked to confirm.

        Sets AUTO_MODE=1 so spec_scraper skips its resume menu. At the end,
        prints an English warning if Gemini left any unknown colors/names
        unresolved during standardization.
        """
        import os
        os.environ['AUTO_MODE'] = '1'

        # Per-run incremental state (reset every invocation).
        self.requested_mode = mode
        self.effective_mode = None            # resolved to 'full' or 'incremental'
        self.change_result = None             # dict from compare_scans, or None
        self.image_subset_skus = None         # None = all products; set = subset
        self.skip_image_and_import = False    # True when nothing changed at all
        self.skip_image_only = False          # True when only price changed (no images)

        self.logger.info(f"\n Starting AUTOMATIC pipeline execution (mode={mode})...\n")

        # Track the standardizer's unresolved-unknown report for the final warning
        unresolved_colors = []
        unresolved_names = []

        steps = [
            ("Link Scraper", self.run_link_scraper),
            ("Spec Scraper", self.run_spec_scraper),
            ("Standardizer", self.run_standardizer),
            # Change detection resolves full vs incremental and, when
            # incremental, computes the subset of SKUs whose images must be
            # (re)processed and writes the new/updated manifests the CSV split
            # and image download consume.
            ("Change Detection", self.run_change_detection),
            # Image processing and import builder honour the subset / skip flags
            # that Change Detection sets.
            ("Image Processing", self.run_image_processing),
            ("Import Builder", self.run_import_builder),
        ]

        # Pipeline resume logic: check existing state and prompt once
        existing = read_state()
        resume = False
        if existing and existing.get('status') != 'complete':
            # AUTO_RESUME env flag allows skipping the prompt
            auto_resume_env = os.getenv('AUTO_RESUME')
            if auto_resume_env is not None:
                resume = str(auto_resume_env).strip().lower() in ('1', 'true', 'yes')
                if resume:
                    self.logger.info('AUTO_RESUME enabled: resuming previous pipeline run')
                else:
                    self.logger.info('AUTO_RESUME set to false: starting fresh')
            else:
                # ask one-time confirmation
                try:
                    ans = input("A previous pipeline run appears incomplete. Resume remaining steps? (y/N): ").strip().lower()
                    resume = ans in ('y', 'yes')
                except Exception:
                    resume = False

        # If not resuming, start a fresh state
        if not resume:
            start_run()

            # Clear individual scraper progress files when starting fresh so
            # each scraper begins from scratch rather than resuming a prior run.
            # Paths are resolved against RUNTIME_STATE_DIR (absolute) — using
            # cwd-relative paths silently failed to clear anything when the
            # pipeline was launched from outside the project root (e.g. a .bat).
            from common.path_registry import RUNTIME_STATE_DIR
            individual_progress_files = [
                RUNTIME_STATE_DIR / get_file('link_scraper_progress'),
                RUNTIME_STATE_DIR / get_file('scraper_progress'),
                RUNTIME_STATE_DIR / get_file('checkpoint'),
            ]

            for progress_file in individual_progress_files:
                if progress_file.exists():
                    progress_file.unlink()
                    self.logger.info(f"  → Cleared individual scraper progress: {progress_file}")
        else:
            self.logger.info('Resuming previous pipeline run based on pipeline_state.json')

        results = {}
        max_retries = 1  # Retry each step once
        for step_name, step_func in steps:
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  {step_name}")
            self.logger.info(f"{'='*70}")

            # If resuming and this step already completed in THIS run, skip it —
            # but only if its recorded output is still current (belongs to this
            # run and is unchanged on disk). A step marked 'done' whose output is
            # missing or stale is re-run rather than trusted.
            if resume:
                s = existing.get('steps', {}).get(step_name, {})
                if s.get('status') == 'done':
                    recorded = (s.get('info') or {}).get('output')
                    if recorded and recorded.get('path'):
                        step_valid = step_output_is_current(step_name, recorded['path'])
                        if not step_valid:
                            self.logger.warning(
                                f"  {step_name} marked done but its output is stale/missing "
                                f"- will re-run"
                            )
                    else:
                        # No recorded output (older state format): fall back to a
                        # plain existence check for the known-output stages.
                        step_valid = True
                        if step_name == "Link Scraper":
                            from common.file_utils import file_exists_and_non_empty
                            from common.path_registry import INTERMEDIATE_DIR
                            output_file = str(INTERMEDIATE_DIR / get_file('extracted_links'))
                            step_valid = file_exists_and_non_empty(output_file)
                            if not step_valid:
                                self.logger.warning(
                                    f"  {step_name} marked as done but output file missing - will re-run"
                                )

                    if step_valid:
                        self.logger.info(f" Skipping {step_name} (already done in this run)")
                        results[step_name] = True
                        continue

            # When change detection determined nothing needs (re)processing,
            # Image Processing and Import Builder are legitimately skipped —
            # record them as successful-skips, not failures, so the pipeline
            # completes cleanly (Scenario: "no new products / no changes").
            if self.skip_image_and_import and step_name in ("Image Processing", "Import Builder"):
                self.logger.info(f" Skipping {step_name} (no new or changed products this run)")
                update_step(step_name, 'done', {'skipped': 'no changes'})
                results[step_name] = True
                continue

            # Price-only changes: no images to (re)process, but the import
            # builder still runs to emit the updated-products CSV. Skip only the
            # Image Processing stage.
            if self.skip_image_only and step_name == "Image Processing":
                self.logger.info(" Skipping Image Processing (price-only changes, no new images)")
                update_step(step_name, 'done', {'skipped': 'price-only changes'})
                results[step_name] = True
                continue

            retry_count = 0
            result = False
            step_succeeded = False
            while retry_count <= max_retries:
                try:
                    # Resume decision for scraper stages:
                    # - First attempt uses the pipeline-level resume flag.
                    # - Every RETRY forces resume=True so a mid-stage failure
                    #   continues from checkpoint instead of restarting fresh
                    #   (which would delete the progress of already-completed items).
                    if step_name in ("Link Scraper", "Spec Scraper"):
                        step_resume = resume or retry_count > 0
                        result = step_func(resume=step_resume)
                    else:
                        result = step_func()

                    # Standardizer returns a dict with unresolved counts
                    if step_name == "Standardizer" and isinstance(result, dict):
                        unresolved_colors = result.get('unresolved_colors', [])
                        unresolved_names = result.get('unresolved_names', [])

                    if result:
                        step_succeeded = True
                        # Only update state as 'done' on final success
                        update_step(step_name, 'done')
                        self.logger.info(f" {step_name} succeeded")
                        break  # Exit retry loop on success
                    else:
                        retry_count += 1
                        # Don't update state as failed on intermediate attempts
                        if retry_count <= max_retries:
                            self.logger.warning(f" {step_name} failed - retry {retry_count}/{max_retries}")
                        else:
                            # Only mark as failed after all retries exhausted
                            update_step(step_name, 'failed')
                            self.logger.error(f" {step_name} failed after {max_retries} retries - aborting pipeline")
                            break
                except Exception as e:
                    retry_count += 1
                    self.logger.error(f" Error in {step_name}: {e}", exc_info=True)
                    # Don't update state as failed on intermediate attempts
                    if retry_count <= max_retries:
                        self.logger.warning(f" Retrying {step_name} ({retry_count}/{max_retries})...")
                    else:
                        # Only mark as failed after all retries exhausted
                        update_step(step_name, 'failed', {'error': str(e)})
                        results[step_name] = False
                        break

            results[step_name] = step_succeeded
            if not step_succeeded:
                break  # Stop the pipeline if the step ultimately fails

        # Display summary
        self.logger.info("\n" + "="*70)
        self.logger.info(" Automatic Pipeline Summary")
        self.logger.info("="*70)

        for step_name, _ in steps:
            if step_name in results:
                status = " Success" if results[step_name] else " Failed"
            else:
                status = " Skipped"
            self.logger.info(f"  {step_name:<20}: {status}")

        self.logger.info("="*70)

        # Final English warning about Gemini-unresolved unknowns
        if unresolved_colors or unresolved_names:
            self.logger.warning("\n" + "!"*70)
            self.logger.warning("WARNING: Some items could not be translated by Gemini")
            if unresolved_colors:
                self.logger.warning(
                    f"  {len(unresolved_colors)} unknown color(s) remain unresolved: "
                    f"{', '.join(str(c) for c in unresolved_colors[:20])}"
                    + (" ..." if len(unresolved_colors) > 20 else "")
                )
            if unresolved_names:
                self.logger.warning(
                    f"  {len(unresolved_names)} unknown name(s) remain unresolved: "
                    f"{', '.join(str(n) for n in unresolved_names[:20])}"
                    + (" ..." if len(unresolved_names) > 20 else "")
                )
            self.logger.warning("  Please review and add them to the mapping files manually.")
            self.logger.warning("!"*70 + "\n")

        all_success = len(results) == len(steps) and all(results.values())
        if all_success:
            # Mark the run complete so the next invocation starts a genuinely
            # fresh run instead of re-prompting to resume a "running" run that
            # actually finished. (mark_complete was previously never called, so
            # status was stuck at 'running' forever.)
            mark_complete()
            self.logger.info(" Automatic pipeline completed successfully!")
        else:
            self.logger.warning("  Automatic pipeline did not complete all steps")

        return all_success

    @log_execution_time()
    def run_price_tracker(self, input_file=get_file('extracted_products')):
        """Run Price Tracker"""
        self.logger.info("="*70)
        self.logger.info("[5]  Running Price Tracker")
        self.logger.info("="*70)
        
        try:
            # Import the main function from price_tracker
            import sys
            import trackers.price_tracker as price_tracker_module
            
            # Run the tracker
            price_tracker_module.main()
            
            self.logger.info(" Price Tracker completed successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Error in Price Tracker: {e}", exc_info=True)
            return False
    
    @log_execution_time()
    def generate_dashboard(self):
        """Generate Dashboard"""
        self.logger.info("="*70)
        self.logger.info("[6]  Generating Dashboard")
        self.logger.info("="*70)
        
        try:
            from dashboard_generator import DashboardGenerator
            import pandas as pd
            
            # Sample data
            generator = DashboardGenerator()
            
            current_df = pd.DataFrame({
                'No': [1, 2, 3],
                ' ': ['Test Product 1', 'Test Product 2', 'Test Product 3'],
                ' ': ['001', '002', '003'],
                ' ': [100000, 150000, 200000],
                ' ': ['#'] * 3,
                '': ['New', 'Price Changed', 'Unchanged']
            })
            
            output_path = generator.generate(
                current_df=current_df,
                new_products=[],
                price_changes=[],
                removed_products=[]
            )
            
            self.logger.info(f" Dashboard generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating Dashboard: {e}", exc_info=True)
            return False
    
    def run_full_pipeline(self):
        """Run complete pipeline"""
        self.logger.info("\n Starting full pipeline execution...\n")
        
        steps = [
            ("Link Scraper", self.run_link_scraper),
            ("Spec Scraper", self.run_spec_scraper),
            ("Standardizer", self.run_standardizer),
            ("Import Builder", self.run_import_builder),
            ("Dashboard", self.generate_dashboard)
        ]
        
        results = {}
        for step_name, step_func in steps:
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  {step_name}")
            self.logger.info(f"{'='*70}")
            
            try:
                # Special handling: after Standardizer, run tracker to generate manifests
                if step_name == 'Standardizer':
                    result = step_func()
                    # Run tracker: prefer compare_scans if Woo CSV exists, else price_tracker
                    try:
                        # check for woo csv in runtime cache uploads
                        woo_uploads = Path(RUNTIME_CACHE_DIR) / 'import_builder' / 'uploads'
                        woo_exists = False
                        if woo_uploads.exists():
                            for _ in woo_uploads.glob('woocommerce_import_*.csv'):
                                woo_exists = True
                                break

                        if woo_exists:
                            # run compare_scans auto mode to produce manifests
                            import trackers.compare_scans as cs
                            scan_path = cs.find_latest_scan(str(RUNTIME_REPORTS_DIR))
                            woo_path = cs.find_latest_woo_file(str(woo_uploads))
                            # output into today's dated reports folder
                            from datetime import datetime
                            dt = datetime.now().strftime('%Y%m%d_%H%M%S')
                            dated_dir = get_dated_reports_dir(None)
                            output_path = str(Path(dated_dir) / f"product_changes_{dt}.xlsx")
                            links_path = None
                            for d in [str(Path(get_file('extracted_products')).parent), str(RUNTIME_REPORTS_DIR)]:
                                lp = cs.find_links_file(d)
                                if lp:
                                    links_path = lp
                                    break
                            if scan_path and woo_path:
                                cs.compare(scan_path, woo_path, output_path, links_path)
                        else:
                            # run price tracker
                            self.run_price_tracker()
                    except Exception as e:
                        self.logger.error(f"Error running tracker: {e}", exc_info=True)
                else:
                    result = step_func()
                results[step_name] = result
                
                if result:
                    self.logger.info(f" {step_name} succeeded")
                else:
                    self.logger.warning(f"  {step_name} failed")
            except Exception as e:
                self.logger.error(f" Error in {step_name}: {e}")
                results[step_name] = False
        
        # Display summary
        self.logger.info("\n" + "="*70)
        self.logger.info(" Results Summary")
        self.logger.info("="*70)
        
        for step_name, result in results.items():
            status = " Success" if result else " Failed"
            self.logger.info(f"  {step_name:<20}: {status}")
        
        self.logger.info("="*70 + "\n")
        
        # Check overall success
        all_success = all(results.values())
        if all_success:
            self.logger.info(" All steps completed successfully!")
        else:
            self.logger.warning("  Some steps failed")
        
        return all_success
    
    def run_tests(self):
        """Run unit tests"""
        self.logger.info(" Running tests...")
        
        try:
            import pytest
            exit_code = pytest.main([
                'tests/',
                '-v',
                '--tb=short'
            ])
            
            if exit_code == 0:
                self.logger.info(" All tests passed")
                return True
            else:
                self.logger.error(" Some tests failed")
                return False
                
        except ImportError:
            self.logger.warning("  pytest not installed")
            
            # Run tests directly
            from tests import test_color_manager
            result = test_color_manager.run_tests()
            return result.wasSuccessful()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Product Scraper & Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['scrape-links', 'scrape-specs', 'standardize', 'import-build', 'track', 'dashboard', 'full', 'auto', 'test'],
        default='full',
        help='Command to execute'
    )
    
    parser.add_argument(
        '--input',
        '-i',
        help='Input file',
        default=None
    )
    
    parser.add_argument(
        '--output',
        '-o',
        help='Output file',
        default=None
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show more details'
    )

    parser.add_argument(
        '--mode',
        choices=['auto', 'full', 'incremental'],
        default='auto',
        help=(
            "Processing mode for the 'auto' pipeline: "
            "'auto' = detect changes vs the previous catalog and process only "
            "new/changed products (full on the first run); "
            "'full' = always reprocess everything; "
            "'incremental' = force change-detection even if it would otherwise "
            "fall back to full. Default: auto."
        )
    )
    
    args = parser.parse_args()
    
    # Create application instance
    app = ProductScraperApp()
    
    # Display banner
    app.print_banner()
    
    # Execute command
    if args.command == 'scrape-links':
        success = app.run_link_scraper(args.input or get_file('archive_urls'))
    elif args.command == 'scrape-specs':
        success = app.run_spec_scraper(args.input or get_file('extracted_products'))
    elif args.command == 'standardize':
        success = app.run_standardizer()
    elif args.command == 'import-build':
        success = app.run_import_builder()
    elif args.command == 'track':
        success = app.run_price_tracker(args.input or get_file('extracted_products'))
    elif args.command == 'dashboard':
        success = app.generate_dashboard()
    elif args.command == 'test':
        success = app.run_tests()
    elif args.command == 'auto':
        success = app.run_auto_pipeline(mode=args.mode)
    else:  # full
        success = app.run_full_pipeline()
    
    # Exit
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
