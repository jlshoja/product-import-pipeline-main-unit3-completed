"""
Central configuration access layer.

Phase A:
Read-only mirror layer.
"""

try:
    from product_extraction.common.file_registry import FILES
    from product_extraction.config.history_config import (
        HISTORY_COLUMNS,
        HISTORY_SETTINGS,
    )
    from product_extraction.config.settings import (
        AppConfig,
        ColorConfig,
        DatabaseConfig,
        LoggingConfig,
        ScraperConfig,
        TrackerConfig,
        get_config,
        reload_config,
    )
except ImportError:
    from common.file_registry import FILES
    from config.history_config import (
        HISTORY_COLUMNS,
        HISTORY_SETTINGS,
    )
    from config.settings import (
        AppConfig,
        ColorConfig,
        DatabaseConfig,
        LoggingConfig,
        ScraperConfig,
        TrackerConfig,
        get_config,
        reload_config,
    )


def get_app_config():
    return get_config()


def get_history_settings():
    return HISTORY_SETTINGS


def get_history_columns():
    return HISTORY_COLUMNS


__all__ = [
    "FILES",
    "AppConfig",
    "ScraperConfig",
    "ColorConfig",
    "TrackerConfig",
    "LoggingConfig",
    "DatabaseConfig",
    "get_config",
    "reload_config",
    "get_app_config",
    "get_history_settings",
    "get_history_columns",
    "HISTORY_SETTINGS",
    "HISTORY_COLUMNS",
]
