#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management -   
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict
from dotenv import load_dotenv

#  Environment Variables
load_dotenv()

try:
    from common.file_registry import get_file
    from common.path_registry import (
        DATA_DIR,
        ARCHIVES_DIR,
        LEGACY_APP_DIR,
        LOGS_DIR,
        REPORTS_DIR,
        ROOT_DIR,
        ASSET_TEMPLATES_DIR,
        resolve_existing_path,
    )
except ImportError:
    from product_extraction.common.file_registry import get_file
    from product_extraction.common.path_registry import (
        DATA_DIR,
        ARCHIVES_DIR,
        LEGACY_APP_DIR,
        LOGS_DIR,
        REPORTS_DIR,
        ROOT_DIR,
        ASSET_TEMPLATES_DIR,
        resolve_existing_path,
    )

# ===========================
#   
# ===========================

BASE_DIR = ROOT_DIR
TEMPLATES_DIR = ASSET_TEMPLATES_DIR

#  ‌    
for directory in [DATA_DIR, REPORTS_DIR, ASSET_TEMPLATES_DIR, LOGS_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


# ===========================
#  Scraper
# ===========================

@dataclass
class ScraperConfig:
    """   Web Scraping"""
    
    # Chrome Driver Settings
    headless_mode: bool = field(default_factory=lambda: os.getenv('HEADLESS_MODE', 'false').lower() == 'true')
    window_size: str = '1920,1080'
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Performance Settings
    max_scrolls: int = int(os.getenv('MAX_SCROLLS', '15'))
    page_load_timeout: int = int(os.getenv('PAGE_TIMEOUT', '20'))
    scroll_delay: float = 2.0
    request_delay: float = 3.0
    
    # Retry Settings
    max_retries: int = 3
    retry_delay: float = 5.0
    
    # File Paths
    archive_urls_file: str = get_file('archive_urls')
    extracted_products_file: str = get_file('extracted_products')
    product_details_file: str = get_file('product_details')
    progress_file: Path = resolve_existing_path(
        DATA_DIR / get_file('link_scraper_progress'),
        LEGACY_APP_DIR / get_file('link_scraper_progress'),
    )
    
    # Chrome Options
    chrome_arguments: List[str] = field(default_factory=lambda: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-gpu',
        '--lang=fa',
        '--disable-notifications',
        '--disable-popup-blocking'
    ])
    
    def get_chrome_options(self):
        """  Chrome"""
        from selenium.webdriver.chrome.options import Options
        options = Options()
        
        for arg in self.chrome_arguments:
            options.add_argument(arg)
        
        if self.headless_mode:
            options.add_argument('--headless')
        
        options.add_argument(f'user-agent={self.user_agent}')
        
        return options


# ===========================
#  Color Manager
# ===========================

@dataclass
class ColorConfig:
    """  ‌"""
    
    color_mapping_file: Path = resolve_existing_path(
        DATA_DIR / get_file('color_mapping'),
        ARCHIVES_DIR / get_file('color_mapping'),
    )
    auto_create_mapping: bool = True
    
    # ‌ 
    standard_colors: List[str] = field(default_factory=lambda: [
        '', ' ', '', '', '', '', '', '',
        ' ', '‌', '', ' ', '', '',
        '', '', '', '‌', '', '‌',
        '‌ ', '', '', '', ' ', '‌'
    ])


# ===========================
#  Price Tracker
# ===========================

@dataclass
class TrackerConfig:
    """  """
    
    input_file: str = get_file('extracted_products')
    output_latest: Path = REPORTS_DIR / get_file('product_tracking_latest')
    
    # HTML Report Settings
    html_template: Path = resolve_existing_path(
        ASSET_TEMPLATES_DIR / get_file('dashboard_template'),
    )
    generate_html: bool = True
    
    # Excel Report Settings
    excel_sheets: List[str] = field(default_factory=lambda: [
        ' ',
        ' ',
        ' ',
        '  ',
        ''
    ])
    
    # Price Change Thresholds
    significant_change_percent: float = 5.0  #    
    
    # Notification Settings ( )
    enable_notifications: bool = False
    telegram_token: str = os.getenv('TELEGRAM_TOKEN', '')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')


# ===========================
#  Logging
# ===========================

@dataclass
class LoggingConfig:
    """ Logging"""
    
    log_dir: Path = LOGS_DIR
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Log Files
    main_log: Path = LOGS_DIR / get_file('main_log')
    scraper_log: Path = LOGS_DIR / get_file('scraper_log')
    tracker_log: Path = LOGS_DIR / get_file('tracker_log')
    error_log: Path = LOGS_DIR / get_file('error_log')
    
    # Log Format
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'
    
    # Log Rotation
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5
    
    # Console Output
    console_output: bool = True
    console_level: str = 'INFO'


# ===========================
#  Database ( )
# ===========================

@dataclass
class DatabaseConfig:
    """  """
    
    enabled: bool = False
    db_path: Path = DATA_DIR / 'products.db'
    db_type: str = 'sqlite'  # sqlite, postgresql, mysql
    
    # PostgreSQL/MySQL Settings
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_port: int = int(os.getenv('DB_PORT', '5432'))
    db_name: str = os.getenv('DB_NAME', 'products')
    db_user: str = os.getenv('DB_USER', 'admin')
    db_password: str = os.getenv('DB_PASSWORD', '')


# ===========================
# Application Config (Main)
# ===========================

@dataclass
class AppConfig:
    """  """
    
    app_name: str = 'Product Scraper & Tracker'
    version: str = '2.0.0'
    
    # Feature Flags
    enable_scraping: bool = True
    enable_tracking: bool = True
    enable_notifications: bool = False
    
    # Components
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    color: ColorConfig = field(default_factory=ColorConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    def __post_init__(self):
        """   """
        self._validate_paths()
        self._create_required_files()
    
    def _validate_paths(self):
        """   """
        required_dirs = [
            self.logging.log_dir,
            self.tracker.output_latest.parent,
        ]
        for directory in required_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
    
    def _create_required_files(self):
        """ ‌ """
        #   .env    
        env_file = BASE_DIR / '.env'
        if not env_file.exists():
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("""# Scraper Configuration
HEADLESS_MODE=false
MAX_SCROLLS=15
PAGE_TIMEOUT=20

# Logging
LOG_LEVEL=INFO

# Database (Optional)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=products
DB_USER=admin
DB_PASSWORD=

# Notifications (Optional)
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
""")
    
    def get_summary(self) -> Dict:
        """  """
        return {
            'app_name': self.app_name,
            'version': self.version,
            'headless_mode': self.scraper.headless_mode,
            'max_retries': self.scraper.max_retries,
            'log_level': self.logging.log_level,
            'reports_dir': str(REPORTS_DIR),
            'logs_dir': str(LOGS_DIR),
        }
    
    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*70)
        
        # Try to print with emoji, fallback to plain text
        try:
            print(f"  {self.app_name} v{self.version}")
        except UnicodeEncodeError:
            print(f"Settings: {self.app_name} v{self.version}")
        
        print("="*70)
        summary = self.get_summary()
        for key, value in summary.items():
            print(f"  {key:<20}: {value}")
        print("="*70 + "\n")


# ===========================
# Singleton Instance
# ===========================

_config_instance = None

def get_config() -> AppConfig:
    """ instance  (Singleton Pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


# ===========================
# Helper Functions
# ===========================

def reload_config():
    """  """
    global _config_instance
    load_dotenv(override=True)
    _config_instance = AppConfig()
    return _config_instance


def update_env_variable(key: str, value: str):
    """‌  """
    env_file = BASE_DIR / '.env'
    
    #   
    lines = []
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # ‌  
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'{key}={value}\n')
    
    # 
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    #  
    reload_config()


# ===========================
# Testing
# ===========================

if __name__ == "__main__":
    print(" Testing Configuration Module...")
    
    config = get_config()
    config.print_summary()
    
    print("\n Project Structure:")
    print(f"  Base Directory: {BASE_DIR}")
    print(f"  Data Directory: {DATA_DIR}")
    print(f"  Reports Directory: {REPORTS_DIR}")
    print(f"  Logs Directory: {LOGS_DIR}")
    
    print("\n Scraper Settings:")
    print(f"  Headless Mode: {config.scraper.headless_mode}")
    print(f"  Max Scrolls: {config.scraper.max_scrolls}")
    print(f"  Page Timeout: {config.scraper.page_load_timeout}s")
    
    print("\n Color Settings:")
    print(f"  Color Mapping File: {config.color.color_mapping_file}")
    print(f"  Standard Colors: {len(config.color.standard_colors)}")
    
    print("\n Tracker Settings:")
    print(f"  Output Latest: {config.tracker.output_latest}")
    print(f"  Generate HTML: {config.tracker.generate_html}")
    
    print("\n Logging Settings:")
    print(f"  Log Level: {config.logging.log_level}")
    print(f"  Main Log: {config.logging.main_log}")
    
    print("\n Configuration module test completed!")
