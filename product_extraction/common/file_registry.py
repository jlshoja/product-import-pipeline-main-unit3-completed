"""
Central file registry.

Phase A:
Read-only registry.
"""

FILE_GROUPS = {
    "pipeline": {
        "archive_urls": "archive_urls.xlsx",
        "extracted_products": "extracted_products.xlsx",
        "product_details": "product_details_complete.xlsx",
        "standardized_output": "product.csv",
        "product_tracking_latest": "product_tracking_LATEST.xlsx",
    },
    "state": {
        "checkpoint": "checkpoint.xlsx",
        "link_scraper_progress": "link_scraper_progress.json",
        "scraper_progress": "scraper_progress.json",
        "download_state": "download_state.json",
        "price_history": "price_history.xlsx",
    },
    "mappings": {
        "color_mapping": "color_mapping.xlsx",
        "product_names": "product_names.xlsx",
        "standard_categories": "standard_categories.xlsx",
        "standard_colors": "standar_colors.xlsx",
        "pricing_sample": "pricing_sample.xlsx",
        "word_index": "word index.xlsx",
    },
    "logs": {
        "main_log": "main.log",
        "tracker_log": "tracker.log",
        "scraper_log": "scraper.log",
        "standardizer_log": "standardizer.log",
        "error_log": "error.log",
        "color_manager_log": "color_manager.log",
        "missing_products_log": "missing_products.log",
    },
    "templates": {
        "dashboard_template": "dashboard_template.html",
        "report_template": "report_template.html",
    },
}

FILES = {}
for group in FILE_GROUPS.values():
    FILES.update(group)


def get_file(name):
    """Return registered filename by key."""
    return FILES[name]


def has_file(name):
    """Check whether a file key exists."""
    return name in FILES


def get_file_group(name):
    """Return a copy of a registered file group."""
    return FILE_GROUPS[name].copy()


def get_all_files():
    """Return a copy of the registry."""
    return FILES.copy()
