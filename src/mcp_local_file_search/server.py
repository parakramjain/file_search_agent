"""
Local File Search MCP server and direct in-process tool wrappers.

This module has two layers:

1. **FastMCP server** – A proper MCP-protocol server that can be launched
   standalone (``python -m src.mcp_local_file_search.server``) so that any
   MCP-compatible client can discover and call the three tools.

2. **Direct wrapper functions** – Thin wrappers around
   ``LocalFileSearchService`` that skip the MCP wire protocol.  They are
   used by the CLI agent for in-process calls and by the test suite.

Tool names
----------
- ``search_files``          – filter by any metadata field
- ``list_files_by_extension`` – shorthand extension-only filter
- ``get_all_files``         – return every supported file
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .models import FileSearchFilters, FileSearchResponse
from .search import LocalFileSearchService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Local File Search MCP",
    instructions=(
        "Returns JSON-only responses.  "
        "Do not wrap output in markdown or prose."
    ),
)


# ---------------------------------------------------------------------------
# Internal helper – resolve service instance
# ---------------------------------------------------------------------------


def _get_service(root_path: Path | None = None) -> LocalFileSearchService:
    """
    Return a ``LocalFileSearchService`` for *root_path*.

    If *root_path* is ``None``, the path is loaded from application settings
    (``LOCAL_FILE_ROOT`` environment variable).
    """
    if root_path is None:
        from src.agent.config import get_settings  # lazy import to avoid cycles

        root_path = get_settings().local_file_root
    return LocalFileSearchService(root_path=root_path)


# ---------------------------------------------------------------------------
# MCP tool: search_files
# ---------------------------------------------------------------------------


@mcp.tool()
def search_files(
    file_name_contains: str | None = None,
    extension: str | None = None,
    folder_path_contains: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    min_size_bytes: int | None = None,
    max_size_bytes: int | None = None,
) -> str:
    """
    Search local files using metadata filters.

    All parameters are optional.  ISO 8601 datetime strings are accepted for
    date parameters.  Returns a ``FileSearchResponse`` serialised as JSON.
    """
    filters = FileSearchFilters(
        file_name_contains=file_name_contains,
        extension=extension,
        folder_path_contains=folder_path_contains,
        created_after=datetime.fromisoformat(created_after) if created_after else None,
        created_before=datetime.fromisoformat(created_before) if created_before else None,
        modified_after=datetime.fromisoformat(modified_after) if modified_after else None,
        modified_before=datetime.fromisoformat(modified_before) if modified_before else None,
        min_size_bytes=min_size_bytes,
        max_size_bytes=max_size_bytes,
    )
    response = _get_service().search(filters)
    return response.model_dump_json()


# ---------------------------------------------------------------------------
# MCP tool: list_files_by_extension
# ---------------------------------------------------------------------------


@mcp.tool()
def list_files_by_extension(extension: str) -> str:
    """
    List all local files that match *extension* (e.g. ``.pdf``).

    Returns a ``FileSearchResponse`` serialised as JSON.
    """
    response = _get_service().list_by_extension(extension)
    return response.model_dump_json()


# ---------------------------------------------------------------------------
# MCP tool: get_all_files
# ---------------------------------------------------------------------------


@mcp.tool()
def get_all_files() -> str:
    """
    Return metadata for every supported file in the configured root folder.

    Returns a ``FileSearchResponse`` serialised as JSON.
    """
    response = _get_service().get_all_files()
    return response.model_dump_json()


# ---------------------------------------------------------------------------
# Direct in-process wrapper functions
# (used by the CLI agent and the test suite without MCP wire protocol)
# ---------------------------------------------------------------------------


def search_files_tool(
    filters: FileSearchFilters,
    root_path: Path | None = None,
) -> FileSearchResponse:
    """
    In-process file search wrapper – no MCP overhead.

    Parameters
    ----------
    filters:
        ``FileSearchFilters`` instance defining the search criteria.
    root_path:
        Override the configured ``LOCAL_FILE_ROOT``.  Useful in tests.
    """
    return _get_service(root_path).search(filters)


def list_files_by_extension_tool(
    extension: str,
    root_path: Path | None = None,
) -> FileSearchResponse:
    """In-process wrapper for extension-only file listing."""
    return _get_service(root_path).list_by_extension(extension)


def get_all_files_tool(root_path: Path | None = None) -> FileSearchResponse:
    """In-process wrapper that returns all supported files."""
    return _get_service(root_path).get_all_files()


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server() -> None:
    """
    Launch the Local File Search MCP server over stdio.

    Called by the ``local-file-search-mcp`` console script and by
    ``python -m src.mcp_local_file_search.server``.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Local File Search MCP server (stdio transport)…")
    mcp.run()


if __name__ == "__main__":
    run_server()
