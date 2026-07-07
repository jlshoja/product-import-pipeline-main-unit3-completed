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
RUNTIME_DIR = ROOT_DIR / "runtime"
CACHE_DIR = RUNTIME_DIR / "cache"

# Shared workspace folders for import_builder.
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = RUNTIME_DIR / "logs"
IMPORT_BUILDER_UPLOADS_DIR = CACHE_DIR / "import_builder" / "uploads"

# Shared mapping files live in the canonical data layout.
COLOR_MAPPING_FILE = str(ROOT_DIR / "data" / "mappings" / get_file("color_mapping"))
PRODUCT_NAMES_FILE = str(ROOT_DIR / "data" / "mappings" / get_file("product_names"))
MISSING_PRODUCTS_LOG = str(LOGS_DIR / get_file("missing_products_log"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
IMPORT_BUILDER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
