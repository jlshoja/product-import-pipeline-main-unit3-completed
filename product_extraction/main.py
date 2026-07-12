#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Entry Point -    
"""

import sys
from pathlib import Path
import argparse

#    
from common.path_registry import ROOT_DIR

project_root = ROOT_DIR / "product_extraction"
sys.path.insert(0, str(project_root))

from common.file_registry import get_file
from config import get_config
from utils.logger import LoggerSetup, log_execution_time


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
            
            # Run the scraper
            link_scraper_module.main()
            
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

            # Run the scraper
            spec_scraper_module.main()

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

            result = import_builder_main()

            self.logger.info(" Import Builder completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error in Import Builder: {e}", exc_info=True)
            return False

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
            ("Price Tracker", self.run_price_tracker),
            ("Dashboard", self.generate_dashboard)
        ]
        
        results = {}
        for step_name, step_func in steps:
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"  {step_name}")
            self.logger.info(f"{'='*70}")
            
            try:
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
        choices=['scrape-links', 'scrape-specs', 'standardize', 'import-build', 'track', 'dashboard', 'full', 'test'],
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
    else:  # full
        success = app.run_full_pipeline()
    
    # Exit
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
