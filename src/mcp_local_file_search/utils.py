"""
Utility helpers for local file search.

Provides pure functions for path inspection, extension normalisation,
and safe timestamp conversion that are shared by the search service and
the MCP tool layer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported file extensions
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".txt"}
)


# ---------------------------------------------------------------------------
# Public utility functions
# ---------------------------------------------------------------------------


def normalize_extension(extension: str | None) -> str | None:
    """
    Normalise a file extension to lowercase and ensure it starts with '.'.

    Returns ``None`` when *extension* is ``None`` or empty after stripping.

    Examples::

        normalize_extension("PDF")   → ".pdf"
        normalize_extension(".Pdf")  → ".pdf"
        normalize_extension(None)    → None
    """
    if extension is None:
        return None
    extension = extension.strip().lower()
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    return extension or None


def safe_iso_datetime_from_timestamp(timestamp: float) -> datetime:
    """
    Convert a POSIX timestamp (float) to a naive UTC ``datetime``.

    Uses ``timezone.utc`` for conversion then strips tzinfo so the result
    is a plain naive datetime (consistent with what Pydantic serialises as
    a JSON ISO string without offset).
    """
    return datetime.fromtimestamp(timestamp, tz=UTC).replace(tzinfo=None)


def is_hidden_path(path: Path) -> bool:
    """
    Return ``True`` if any component of *path* starts with a dot.

    Works on both POSIX and Windows paths.  On Windows, files with the
    "hidden" attribute are not detected here; only dot-prefixed names are
    checked (which is the convention used by the project).
    """
    return any(part.startswith(".") for part in path.parts)


def is_supported_file(path: Path) -> bool:
    """
    Return ``True`` when *path* is a regular file with a supported
    extension and is not hidden.

    Skips:
    - Directories
    - Hidden files / files inside hidden directories
    - Files with unsupported extensions
    """
    if not path.is_file():
        return False
    if is_hidden_path(path):
        return False
    return path.suffix.lower() in SUPPORTED_EXTENSIONS
