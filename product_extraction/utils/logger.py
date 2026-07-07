#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging System -  Logging ‌
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    from common.file_registry import get_file, has_file
    from common.path_registry import LOGS_DIR, RUNTIME_LOGS_DIR
    from config import get_config

except ImportError:
    from common.file_registry import get_file, has_file
    from common.path_registry import LOGS_DIR, RUNTIME_LOGS_DIR

RUNTIME_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ===========================
# ‌  Console Output
# ===========================


class ColoredFormatter(logging.Formatter):
    """Formatter     Console"""

    #   ANSI
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    # Simple prefixes instead of emojis
    PREFIXES = {
        "DEBUG": "[DEBUG]",
        "INFO": "[INFO]",
        "WARNING": "[WARN]",
        "ERROR": "[ERROR]",
        "CRITICAL": "[CRIT]",
    }

    def format(self, record):
        # Add color
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}"
                f"{self.PREFIXES.get(levelname, '')} "
                f"{levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


# ===========================
# Logger Setup
# ===========================


class LoggerSetup:
    """‌ Logger"""

    _loggers = {}

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[str] = None,
        level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
    ) -> logging.Logger:
        """
         Logger

        Args:
            name:  logger
            log_file:    ()
            level:  logging
            console_output:   console
            file_output:

        Returns:
            logging.Logger instance
        """

        #  logger
        if name in cls._loggers:
            return cls._loggers[name]

        #  Logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers.clear()  #   handlers

        # Format
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_format = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )

        # Console Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

        # File Handler
        if file_output:
            if log_file is None:
                registry_key = f"{name}_log"
                if has_file(registry_key):
                    log_file = RUNTIME_LOGS_DIR / get_file(registry_key)
                else:
                    log_file = RUNTIME_LOGS_DIR / f"{name}.log"
            else:
                log_file = Path(log_file)

            # Rotating File Handler (best effort)
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10 * 1024 * 1024,  # 10 MB
                    backupCount=5,
                    encoding="utf-8",
                )
                file_handler.setLevel(getattr(logging, level.upper()))
                file_handler.setFormatter(file_format)
                logger.addHandler(file_handler)
            except OSError:
                # Keep the logger usable even if the filesystem blocks log files.
                file_output = False

        # Error Handler
        error_log = RUNTIME_LOGS_DIR / get_file("error_log")
        try:
            error_handler = RotatingFileHandler(
                error_log, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_format)
            logger.addHandler(error_handler)
        except OSError:
            pass

        #   cache
        cls._loggers[name] = logger

        return logger

    @classmethod
    def get_scraper_logger(cls) -> logging.Logger:
        """Logger  Scraper"""
        return cls.get_logger(
            name="scraper", log_file=RUNTIME_LOGS_DIR / get_file("scraper_log"), level="INFO"
        )

    @classmethod
    def get_tracker_logger(cls) -> logging.Logger:
        """Logger  Tracker"""
        return cls.get_logger(
            name="tracker", log_file=RUNTIME_LOGS_DIR / get_file("tracker_log"), level="INFO"
        )

    @classmethod
    def get_color_manager_logger(cls) -> logging.Logger:
        """Logger  Color Manager"""
        return cls.get_logger(
            name="color_manager", log_file=RUNTIME_LOGS_DIR / get_file("color_manager_log"), level="INFO"
        )

    @classmethod
    def get_main_logger(cls) -> logging.Logger:
        """Logger"""
        return cls.get_logger(name="main", log_file=RUNTIME_LOGS_DIR / get_file("main_log"), level="INFO")


# ===========================
# Context Manager  Logging
# ===========================


class LogContext:
    """Context Manager  logging"""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f": {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(f" : {self.operation} (: {duration:.2f}s)")
        else:
            self.logger.error(
                f" : {self.operation} (: {duration:.2f}s) - {exc_val}", exc_info=True
            )

        return False  #   exception


# ===========================
# Decorators  Logging
# ===========================


def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator  logging"""

    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = LoggerSetup.get_main_logger()

        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f" {func_name}  args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name}    ")
                return result
            except Exception as e:
                logger.error(f"  {func_name}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator  logging"""

    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = LoggerSetup.get_main_logger()

        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_name = func.__name__

            logger.info(f"[START] {func_name}")

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"[DONE] {func_name} completed in {duration:.2f} seconds")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"[ERROR] {func_name} failed after {duration:.2f} seconds: {e}"
                )
                raise

        return wrapper

    return decorator


# ===========================
# Helper Functions
# ===========================


def setup_logging(level: str = "INFO"):
    """‌ logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_system_info(logger: logging.Logger):
    """ """
    import platform
    import sys

    logger.info("=" * 70)
    logger.info(" :")
    logger.info(f"  Python Version: {sys.version}")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Processor: {platform.processor()}")
    logger.info("=" * 70)


def clear_old_logs(days: int = 30):
    """‌ ‌  X"""
    from datetime import timedelta

    logger = LoggerSetup.get_main_logger()
    cutoff_date = datetime.now() - timedelta(days=days)

    deleted_count = 0
    for log_file in RUNTIME_LOGS_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_date.timestamp():
            log_file.unlink()
            deleted_count += 1

    if deleted_count > 0:
        logger.info(f"  {deleted_count}     ")


# ===========================
# Testing
# ===========================

if __name__ == "__main__":
    print("\n Testing Logging System...")
    print("=" * 70)

    #  Logger
    logger = LoggerSetup.get_main_logger()

    logger.debug("   DEBUG ")
    logger.info("   INFO ")
    logger.warning("   WARNING ")
    logger.error("   ERROR ")

    #  Context Manager
    print("\n" + "=" * 70)
    print("Testing Context Manager:")
    with LogContext(logger, " "):
        logger.info("   ...")

    #  Decorators
    print("\n" + "=" * 70)
    print("Testing Decorators:")

    @log_execution_time(logger)
    def test_function():
        import time

        time.sleep(1)
        return ""

    result = test_function()

    #
    print("\n" + "=" * 70)
    log_system_info(logger)

    print("\n[OK] Logging system test completed!")
    print(f"Log files are in: {RUNTIME_LOGS_DIR}")
