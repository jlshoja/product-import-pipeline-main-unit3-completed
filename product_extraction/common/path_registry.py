from pathlib import Path

# ============================================================
# Repository Root
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LEGACY_APP_DIR = ROOT_DIR / "product_extraction"

# ============================================================
# Canonical Repository Layout
# ============================================================

DATA_DIR = ROOT_DIR / "data"
INPUTS_DIR = DATA_DIR / "inputs"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
MAPPINGS_DIR = DATA_DIR / "mappings"
REFERENCE_DIR = DATA_DIR / "reference"
ARCHIVES_DIR = DATA_DIR / "archives"

RUNTIME_DIR = ROOT_DIR / "runtime"
RUNTIME_LOGS_DIR = RUNTIME_DIR / "logs"
RUNTIME_REPORTS_DIR = RUNTIME_DIR / "reports"
RUNTIME_STATE_DIR = RUNTIME_DIR / "state"
RUNTIME_CACHE_DIR = RUNTIME_DIR / "cache"
RUNTIME_OUTPUTS_DIR = RUNTIME_DIR / "outputs"

ASSETS_DIR = ROOT_DIR / "assets"
ASSET_IMAGES_DIR = ASSETS_DIR / "images"
ASSET_TEMPLATES_DIR = ASSETS_DIR / "templates"
ASSET_HELP_DIR = ASSETS_DIR / "help"

# ============================================================
# Aliases
# ============================================================

# Product artifacts (product.csv, product_details_complete.xlsx, images,
# WooCommerce import CSV) all live under data/outputs/. The image-processing
# and import_builder modules read/write there with hardcoded paths, so the
# standardizer and spec_scraper must target the same folder for the handoff
# to work. Logs and reports stay consolidated under runtime/.
OUTPUTS_DIR = DATA_DIR / "outputs"
LOGS_DIR = RUNTIME_LOGS_DIR
REPORTS_DIR = RUNTIME_REPORTS_DIR

# ============================================================
# Registry Helpers
# ============================================================

PATHS = {
    "root": ROOT_DIR,
    "legacy_app": LEGACY_APP_DIR,
    "data": DATA_DIR,
    "data_inputs": INPUTS_DIR,
    "data_intermediate": INTERMEDIATE_DIR,
    "data_outputs": OUTPUTS_DIR,
    "data_mappings": MAPPINGS_DIR,
    "data_reference": REFERENCE_DIR,
    "data_archives": ARCHIVES_DIR,
    "runtime": RUNTIME_DIR,
    "runtime_logs": RUNTIME_LOGS_DIR,
    "runtime_reports": RUNTIME_REPORTS_DIR,
    "runtime_state": RUNTIME_STATE_DIR,
    "runtime_cache": RUNTIME_CACHE_DIR,
    "runtime_outputs": RUNTIME_OUTPUTS_DIR,
    "assets": ASSETS_DIR,
    "asset_images": ASSET_IMAGES_DIR,
    "asset_templates": ASSET_TEMPLATES_DIR,
    "asset_help": ASSET_HELP_DIR,
    "reports": REPORTS_DIR,
    "logs": LOGS_DIR,
}


def get_path(name):
    """Return a registered path by key."""
    return PATHS[name]


def has_path(name):
    """Check whether a path key exists."""
    return name in PATHS


def get_all_paths():
    """Return a copy of the path registry."""
    return PATHS.copy()


def resolve_existing_path(*candidates: Path) -> Path:
    """Return the first existing path, or the first candidate if none exist."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def get_dated_reports_dir(date_str: str = None, create: bool = True) -> Path:
    """
    Return a reports directory for a given date.

    - date_str: optional string in YYYY-MM-DD format. If None, uses today's date
      (ISO date). The returned path is RUNTIME_REPORTS_DIR / YYYY-MM-DD.
    - create: if True, ensure the directory exists.

    This helper allows saving reports in per-day subfolders without replacing
    the existing RUNTIME_REPORTS_DIR constant so older code keeps working.
    """
    if date_str is None:
        date = Path().cwd()  # placeholder to import datetime only when needed
        from datetime import date as _date

        date_str = _date.today().isoformat()

    dated = RUNTIME_REPORTS_DIR / date_str
    if create:
        _ensure_directory(dated)
    return dated


# ============================================================
# Ensure Directories Exist
# ============================================================

def _ensure_directory(directory: Path) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


for directory in (
    DATA_DIR,
    INPUTS_DIR,
    INTERMEDIATE_DIR,
    OUTPUTS_DIR,
    MAPPINGS_DIR,
    REFERENCE_DIR,
    ARCHIVES_DIR,
    RUNTIME_DIR,
    RUNTIME_LOGS_DIR,
    RUNTIME_REPORTS_DIR,
    RUNTIME_STATE_DIR,
    RUNTIME_CACHE_DIR,
    RUNTIME_OUTPUTS_DIR,
    ASSETS_DIR,
    ASSET_IMAGES_DIR,
    ASSET_TEMPLATES_DIR,
    ASSET_HELP_DIR,
):
    _ensure_directory(directory)
