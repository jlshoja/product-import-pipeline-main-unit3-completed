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
OUTPUTS_DIR = DATA_DIR / "outputs"
MAPPINGS_DIR = DATA_DIR / "mappings"
REFERENCE_DIR = DATA_DIR / "reference"
ARCHIVES_DIR = DATA_DIR / "archives"

RUNTIME_DIR = ROOT_DIR / "runtime"
RUNTIME_LOGS_DIR = RUNTIME_DIR / "logs"
RUNTIME_REPORTS_DIR = RUNTIME_DIR / "reports"
RUNTIME_STATE_DIR = RUNTIME_DIR / "state"
RUNTIME_CACHE_DIR = RUNTIME_DIR / "cache"

ASSETS_DIR = ROOT_DIR / "assets"
ASSET_IMAGES_DIR = ASSETS_DIR / "images"
ASSET_TEMPLATES_DIR = ASSETS_DIR / "templates"
ASSET_HELP_DIR = ASSETS_DIR / "help"

# ============================================================
# Compatibility Directories
# ============================================================

REPORTS_DIR = ROOT_DIR / "reports" / "outputs"
TEMPLATES_DIR = ROOT_DIR / "reports" / "templates"
LOGS_DIR = ROOT_DIR / "logs"

LEGACY_DATA_DIR = LEGACY_APP_DIR
LEGACY_REPORTS_DIR = LEGACY_APP_DIR / "reports" / "outputs"
LEGACY_TEMPLATES_DIR = LEGACY_APP_DIR / "reports" / "templates"
LEGACY_LOGS_DIR = LEGACY_APP_DIR / "logs"

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
    "assets": ASSETS_DIR,
    "asset_images": ASSET_IMAGES_DIR,
    "asset_templates": ASSET_TEMPLATES_DIR,
    "asset_help": ASSET_HELP_DIR,
    "reports": REPORTS_DIR,
    "templates": TEMPLATES_DIR,
    "logs": LOGS_DIR,
    "legacy_data": LEGACY_DATA_DIR,
    "legacy_reports": LEGACY_REPORTS_DIR,
    "legacy_templates": LEGACY_TEMPLATES_DIR,
    "legacy_logs": LEGACY_LOGS_DIR,
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


# ============================================================
# Ensure Directories Exist
# ============================================================

def _ensure_directory(directory: Path) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Registry import should not fail just because a target folder
        # cannot be materialized in the current environment.
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
    ASSETS_DIR,
    ASSET_IMAGES_DIR,
    ASSET_TEMPLATES_DIR,
    ASSET_HELP_DIR,
    REPORTS_DIR,
    TEMPLATES_DIR,
    LOGS_DIR,
    LEGACY_REPORTS_DIR,
    LEGACY_TEMPLATES_DIR,
    LEGACY_LOGS_DIR,
):
    _ensure_directory(directory)
