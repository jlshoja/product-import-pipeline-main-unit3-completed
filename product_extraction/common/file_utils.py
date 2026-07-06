"""
Shared filesystem utility functions.

Provides reusable wrappers for common file and directory operations.

Unit 4 - File Operations Consolidation
"""

import shutil
from pathlib import Path


def ensure_exists(path) -> bool:
    """Return True when the path exists."""
    return Path(path).exists()


def ensure_directory(path) -> Path:
    """Create a directory if needed and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_copy(src, dst, overwrite=True) -> bool:
    """
    Copy a file with optional overwrite protection.

    Returns True when the copy succeeds, otherwise False.
    """
    source = Path(src)
    destination = Path(dst)

    if not source.exists():
        return False

    if destination.exists() and not overwrite:
        return False

    try:
        if destination.parent:
            ensure_directory(destination.parent)
        shutil.copy2(source, destination)
        return True
    except OSError:
        return False


def safe_delete(path, missing_ok=True) -> bool:
    """
    Delete a file path.

    Returns True when the file is deleted or already missing with missing_ok.
    """
    target = Path(path)

    try:
        target.unlink()
        return True
    except FileNotFoundError:
        return missing_ok
    except OSError:
        return False
