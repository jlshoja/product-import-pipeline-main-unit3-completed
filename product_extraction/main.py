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
from common.pipeline_state import read_state, start_run, update_step, mark_complete


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
    
    @log_execution_time()
    def run_link_scraper(self, input_file=get_file('archive_urls')):
        """Run Link Scraper"""
        self.logger.info("="*70)
        self.logger.info("[1]  Running Link Scraper")
        self.logger.info("="*70)
        
        try:
            import scrapers.link_scraper as link_scraper_module
            from common.file_utils import file_exists_and_non_empty
            from common.path_registry import INTERMEDIATE_DIR
            import os
            
            # Set AUTO_MODE for link_scraper to use resume logic
            os.environ['AUTO_MODE'] = '1'
            # Set AUTO_RESUME to enable resume if progress exists
            os.environ['AUTO_RESUME'] = '1'
            
            # Run the scraper
            link_scraper_module.main()
            
            # Validate output - check both possible filenames
            output_file = get_file('extracted_links')
            output_path = str(INTERMEDIATE_DIR / output_file)
            
            # Also check for extracted_products.xlsx (legacy name)
            legacy_output = str(INTERMEDIATE_DIR / get_file('extracted_products'))
            
            # Check if either output file exists and is non-empty
            if not file_exists_and_non_empty(output_path):
                if not file_exists_and_non_empty(legacy_output):
                    self.logger.error(f"Link Scraper produced no output: {output_file}")
                    return False
                else:
                    # Legacy file exists, use it
                    output_path = legacy_output
            
            # Read the output file to check if any products were extracted
            import pandas as pd
            df = pd.read_excel(output_path)
            if df.empty or len(df) == 0:
                self.logger.error("Link Scraper extracted zero products")
                return False
            
            self.logger.info(" Link Scraper completed successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Error in Link Scraper: {e}", exc_info=True)
            return False
    
    @log_execution_time()
    def run_spec_scraper(self, input_file=get_file('extracted_products')):
        """Run Spec Scraper"""
        self.logger.info("="*70)
        self.logger.info("[2]  Running Spec Scraper")
        self.logger.info("="*70)

        try:
            import scrapers.spec_scraper as spec_scraper_module
            from common.file_utils import file_exists_and_non_empty
            from common.path_registry import INTERMEDIATE_DIR

            # Validate input: extracted_links is REQUIRED
            links_filename = get_file('extracted_links')
            links_file = str(INTERMEDIATE_DIR / links_filename)
            if not file_exists_and_non_empty(links_file):
                self.logger.error(f"Spec Scraper cannot run: missing input file {links_file}")
                return False

            # Set AUTO_RESUME if we're in pipeline resume mode
            # This allows spec_scraper to resume from where it left off
            pipeline_resume = os.getenv('AUTO_RESUME', '').strip().lower() in ('1', 'true', 'yes')
            if pipeline_resume:
                os.environ['AUTO_RESUME'] = '1'

            # Run the scraper
            spec_scraper_module.main()

            # Validate output
            output_file = get_file('extracted_products')
            if not file_exists_and_non_empty(output_file):
                self.logger.error(f"Spec Scraper produced no output: {output_file}")
                return False

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
            from common.file_utils import file_exists_and_non_empty

            # Validate input
            input_file = get_file('extracted_products')
            if not file_exists_and_non_empty(input_file):
                self.logger.error(f"Standardizer missing input: {input_file}")
                return False

            result = standardizer.main()

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

            # If manifests exist, set env vars so import_builder splits new/update CSVs
            try:
                reports_root = Path(RUNTIME_REPORTS_DIR)
                subdirs = [d for d in reports_root.iterdir() if d.is_dir()]
                manifest_new = manifest_updated = None
                if subdirs:
                    latest = max(subdirs, key=lambda p: p.stat().st_mtime)
                    mn = latest / 'new_products_list.csv'
                    mu = latest / 'updated_products_list.csv'
                    if mn.exists():
                        os.environ['NEW_MANIFEST'] = str(mn)
                        manifest_new = str(mn)
                    if mu.exists():
                        os.environ['UPDATED_MANIFEST'] = str(mu)
                        manifest_updated = str(mu)
                if manifest_new or manifest_updated:
                    self.logger.info(f"Import Builder: NEW_MANIFEST={manifest_new}, UPDATED_MANIFEST={manifest_updated}")
            except Exception:
                pass

            result = import_builder_main()

            self.logger.info(" Import Builder completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error in Import Builder: {e}", exc_info=True)
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

        image_dir = ROOT_DIR / "image_processing"
        data_outputs = ROOT_DIR / "data" / "outputs"

        # Paths mirror image_processing/menu.py defaults
        excel_file        = str(ROOT_DIR / "data" / "intermediate" / "extracted_products.xlsx")
        downloaded_folder = str(data_outputs / "downloaded_images")
        output_folder     = str(data_outputs / "processed_images")

        if not Path(excel_file).exists():
            self.logger.error(f"Image input not found: {excel_file}")
            return False

        # --- Sub-step 1: download images (fresh, full, no prompts) ---
        download_env = os.environ.copy()
        download_env["IMG_EXCEL"]    = excel_file
        download_env["IMG_OUTPUT"]   = downloaded_folder
        download_env["IMG_SELENIUM"] = "1"
        download_env["IMG_RETRIES"]  = "3"
        # If tracker produced a manifest, process only new products
        # Look for the most recent dated reports folder containing new_products_list.csv
        manifest_file = None
        try:
            reports_root = Path(RUNTIME_REPORTS_DIR)
            subdirs = [d for d in reports_root.iterdir() if d.is_dir()]
            if subdirs:
                latest = max(subdirs, key=lambda p: p.stat().st_mtime)
                candidate = latest / 'new_products_list.csv'
                if candidate.exists():
                    manifest_file = str(candidate)
        except Exception:
            manifest_file = None

        if manifest_file:
            download_env["IMG_MANIFEST"] = manifest_file
            download_env["IMG_MODE"]     = "full"
            download_env["IMG_RESUME"]   = "fresh"
            self.logger.info(f"[IMG] Using manifest for image download: {manifest_file}")
        else:
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

        self.logger.info("[IMG] Step 2/2 - Processing and compressing images...")
        # processing step also gets a timeout and retry
        proc_ok = False
        attempt = 0
        while attempt <= retry_count and not proc_ok:
            try:
                attempt += 1
                self.logger.info(f"[IMG] processing attempt {attempt}/{retry_count + 1}")
                result = subprocess.run(process_cmd, cwd=str(image_dir), timeout=timeout_sec)
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

    def run_auto_pipeline(self):
        """Run the entire pipeline unattended (automatic execution mode).

        Order: link scrape -> spec scrape (fresh) -> standardize ->
        image download+process -> import build. No interactive prompts.
        Sets AUTO_MODE=1 so spec_scraper skips its resume menu. At the end,
        prints an English warning if Gemini left any unknown colors/names
        unresolved during standardization.
        """
        os.environ['AUTO_MODE'] = '1'

        self.logger.info("\n Starting AUTOMATIC pipeline execution...\n")

        # Track the standardizer's unresolved-unknown report for the final warning
        unresolved_colors = []
        unresolved_names = []

        steps = [
            ("Link Scraper", self.run_link_scraper),
            ("Spec Scraper", self.run_spec_scraper),
            ("Standardizer", self.run_standardizer),
            # After standardizer we run a tracker to produce manifests
            # then image processing and import builder consume those manifests
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
        else:
            self.logger.info('Resuming previous pipeline run based on pipeline_state.json')

        results = {}
        max_retries = 1  # Retry each step once
        for step_name, step_func in steps:
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  {step_name}")
            self.logger.info(f"{'='*70}")

            # If resuming and this step already done, skip it
            # But first validate that the step's output actually exists
            if resume:
                s = existing.get('steps', {}).get(step_name, {})
                if s.get('status') == 'done':
                    # Validate that the step actually completed successfully
                    step_valid = True
                    if step_name == "Link Scraper":
                        from common.file_utils import file_exists_and_non_empty
                        from common.path_registry import INTERMEDIATE_DIR
                        output_file = str(INTERMEDIATE_DIR / get_file('extracted_links'))
                        legacy_output = str(INTERMEDIATE_DIR / get_file('extracted_products'))
                        step_valid = (file_exists_and_non_empty(output_file) or 
                                    file_exists_and_non_empty(legacy_output))
                        if not step_valid:
                            self.logger.warning(f"  {step_name} marked as done but output file missing - will re-run")
                    
                    if step_valid:
                        self.logger.info(f" Skipping {step_name} (already done in previous run)")
                        results[step_name] = True
                        continue

            retry_count = 0
            result = False
            step_succeeded = False
            while retry_count <= max_retries:
                try:
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
        success = app.run_auto_pipeline()
    else:  # full
        success = app.run_full_pipeline()
    
    # Exit
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
