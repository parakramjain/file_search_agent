"""
Deterministic query router.

Classifies a user query into one of three ``QueryType`` values without
relying on an LLM.  Keyword matching is used so that the routing is fast,
predictable, and fully unit-testable.

``parse_file_search_filters`` extracts a ``FileSearchFilters`` object from
a natural-language local file search query using simple pattern matching.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from src.mcp_local_file_search.models import FileSearchFilters

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Query-type enum
# ---------------------------------------------------------------------------


class QueryType(StrEnum):
    """The three supported query classifications."""

    LOCAL_FILE_SEARCH = "local_file_search"
    MICROSOFT_LEARN = "microsoft_learn"
    UNSUPPORTED = "unsupported"


# ---------------------------------------------------------------------------
# Keyword sets
# ---------------------------------------------------------------------------

# Terms that strongly suggest a local file search query.
# Checked after Microsoft keywords to avoid false positives.
_FILE_KEYWORDS: frozenset[str] = frozenset(
    {
        "file",
        "files",
        "pdf",
        "docx",
        "xlsx",
        "xls",
        "jpg",
        "jpeg",
        "txt",
        "folder",
        "directory",
        "local system",
        "available in our system",
        "modified",
        "created",
        "size",
        "extension",
        "document",
        "documents",
        "search files",
        "list files",
        "find files",
        "show files",
    }
)

# Terms that strongly suggest a Microsoft / Azure documentation query.
# These are checked first because some overlap with common words.
_MICROSOFT_KEYWORDS: frozenset[str] = frozenset(
    {
        "microsoft",
        "azure",
        "blob storage",
        "entra",
        "fabric",
        "power bi",
        "synapse",
        "dataverse",
        "sharepoint",
        "teams",
        "copilot",
        "dynamics",
        ".net",
        "c#",
        "visual studio",
        "windows server",
        "azure active directory",
        "aad",
        "azure kubernetes",
        "aks",
        "app service",
        "cosmos db",
        "azure sql",
        "devops",
        "bicep",
        "arm template",
        "azure functions",
        "logic apps",
        "azure devops",
        "ms learn",
    }
)

# Folders that can be referenced in a local file search query.
_KNOWN_FOLDERS: frozenset[str] = frozenset({"zoology", "biology", "ecology"})

# Mapping from query keyword → normalised extension.
# Longer / more specific entries are placed first so that ".pdf" beats "pdf"
# when both are present (though the dict is iterated in insertion order).
_EXTENSION_MAP: dict[str, str] = {
    ".pdf": ".pdf",
    "pdf": ".pdf",
    ".docx": ".docx",
    "docx": ".docx",
    ".xlsx": ".xlsx",
    "xlsx": ".xlsx",
    ".xls": ".xls",
    "xls": ".xls",
    ".jpeg": ".jpeg",
    "jpeg": ".jpeg",
    ".jpg": ".jpg",
    "jpg": ".jpg",
    ".txt": ".txt",
    "txt": ".txt",
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def classify_query(query: str) -> QueryType:
    """
    Classify *query* as LOCAL_FILE_SEARCH, MICROSOFT_LEARN, or UNSUPPORTED.

    Microsoft keywords are checked first so that a query like
    "Find Azure Blob Storage documents" is routed to Microsoft Learn.

    Parameters
    ----------
    query:
        Raw user input string.

    Returns
    -------
    QueryType
    """
    lower = query.lower()

    for keyword in _MICROSOFT_KEYWORDS:
        if keyword in lower:
            logger.info("Query classified as MICROSOFT_LEARN (matched keyword: %r)", keyword)
            return QueryType.MICROSOFT_LEARN

    for keyword in _FILE_KEYWORDS:
        if keyword in lower:
            logger.info("Query classified as LOCAL_FILE_SEARCH (matched keyword: %r)", keyword)
            return QueryType.LOCAL_FILE_SEARCH

    logger.info("Query classified as UNSUPPORTED")
    return QueryType.UNSUPPORTED


# ---------------------------------------------------------------------------
# Filter parser
# ---------------------------------------------------------------------------


def parse_file_search_filters(query: str) -> FileSearchFilters:
    """
    Extract ``FileSearchFilters`` from a natural-language query.

    Uses simple substring matching – no NLP or LLM required.  This covers
    the common cases for the "Good version" scope:

    - Extension detection (pdf, docx, xlsx, xls, jpg/jpeg, txt)
    - Folder detection (zoology, biology, ecology)
    - "all files" → clear extension filter

    Parameters
    ----------
    query:
        Raw user input string.

    Returns
    -------
    FileSearchFilters
        Partially populated filters.  Fields that could not be inferred
        remain ``None``.
    """
    lower = query.lower()
    extension: str | None = None
    folder_path_contains: str | None = None

    # Detect "all files" before extension detection so we can skip ext filter
    if "all files" in lower or "all file" in lower:
        extension = None
    else:
        for keyword, ext in _EXTENSION_MAP.items():
            if keyword in lower:
                extension = ext
                break

    # Detect known folder references
    for folder in _KNOWN_FOLDERS:
        if folder in lower:
            folder_path_contains = folder
            break

    logger.debug(
        "Parsed file search filters – extension=%r folder_path_contains=%r",
        extension,
        folder_path_contains,
    )

    return FileSearchFilters(
        extension=extension,
        folder_path_contains=folder_path_contains,
    )
