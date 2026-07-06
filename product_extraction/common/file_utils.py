"""
Shared filesystem utility functions.

Provides reusable wrappers for common file and directory operations.

Unit 4 - File Operations Consolidation
"""

import shutil
import re
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


def find_latest_dated(base_dir, pattern, date_formats, recursive=False):
    """
    Find the latest dated file matching a glob pattern.

    date_formats accepts a regex string, compiled regex, or list of either.
    Each regex must expose the sortable date value in capture group 1.
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return None

    if isinstance(date_formats, (str, re.Pattern)):
        date_patterns = [date_formats]
    else:
        date_patterns = list(date_formats)

    date_regexes = [
        item if isinstance(item, re.Pattern) else re.compile(item)
        for item in date_patterns
    ]

    files = base_path.rglob(pattern) if recursive else base_path.glob(pattern)
    dated = []

    for file_path in files:
        if not file_path.is_file():
            continue
        for date_re in date_regexes:
            match = date_re.search(file_path.name)
            if match:
                dated.append((match.group(1), file_path))
                break

    if not dated:
        return None

    dated.sort(key=lambda item: item[0])
    return dated[-1][1]
