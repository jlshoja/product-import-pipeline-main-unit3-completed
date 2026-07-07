#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized path management.
"""

from pathlib import Path

try:
    from common.file_registry import get_file
except ImportError:
    from product_extraction.common.file_registry import get_file

# Repository root used by import_builder utilities.
ROOT_DIR = Path(__file__).resolve().parent.parent

# Shared workspace folders for import_builder.
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Shared mapping files live in the canonical data layout.
COLOR_MAPPING_FILE = str(ROOT_DIR / "data" / "mappings" / get_file("color_mapping"))
PRODUCT_NAMES_FILE = str(ROOT_DIR / "data" / "mappings" / get_file("product_names"))
MISSING_PRODUCTS_LOG = str(LOGS_DIR / get_file("missing_products_log"))

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
