"""
Local file metadata search service.

The ``LocalFileSearchService`` recursively scans a root directory,
collects file metadata, and applies the requested ``FileSearchFilters``.
All results are returned as strongly typed ``FileSearchResponse`` objects.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .models import FileMetadata, FileSearchFilters, FileSearchResponse
from .utils import is_supported_file, normalize_extension, safe_iso_datetime_from_timestamp

logger = logging.getLogger(__name__)


class LocalFileSearchService:
    """
    Service that searches a local directory tree by file metadata.

    Parameters
    ----------
    root_path:
        Absolute or relative path to the folder that will be scanned
        recursively.  Resolved to an absolute path on construction.
    """

    def __init__(self, root_path: Path) -> None:
        self.root_path: Path = root_path.resolve()
        logger.debug("LocalFileSearchService ready – root: %s", self.root_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_all_metadata(self) -> tuple[list[FileMetadata], list[str]]:
        """
        Walk the root directory tree and collect metadata for every
        supported, non-hidden file.

        Returns
        -------
        tuple[list[FileMetadata], list[str]]
            A pair of (results, errors).  *errors* contains human-readable
            messages for files that could not be read; the scan continues
            past those files instead of raising.
        """
        results: list[FileMetadata] = []
        errors: list[str] = []

        if not self.root_path.exists():
            errors.append(f"Root path does not exist: {self.root_path}")
            logger.error("Root path does not exist: %s", self.root_path)
            return results, errors

        for path in sorted(self.root_path.rglob("*")):
            if not is_supported_file(path):
                continue
            try:
                stat = path.stat()
                # Use a path relative to the *parent* of root so the
                # folder_path includes the root folder name itself.
                relative_folder = path.parent.relative_to(self.root_path.parent)
                metadata = FileMetadata(
                    file_name=path.name,
                    folder_path=str(relative_folder).replace("\\", "/"),
                    file_extension=path.suffix.lower(),
                    created_date=safe_iso_datetime_from_timestamp(stat.st_ctime),
                    modified_date=safe_iso_datetime_from_timestamp(stat.st_mtime),
                    file_size_bytes=stat.st_size,
                )
                results.append(metadata)
            except (OSError, PermissionError) as exc:
                msg = f"Could not read '{path}': {exc}"
                errors.append(msg)
                logger.warning(msg)

        # Sort by file name (case-insensitive, ascending)
        results.sort(key=lambda m: m.file_name.lower())
        return results, errors

    @staticmethod
    def _apply_filters(
        files: list[FileMetadata], filters: FileSearchFilters
    ) -> list[FileMetadata]:
        """
        Apply the given *filters* to *files* and return the matching subset.

        All string comparisons are case-insensitive.
        Date and size comparisons are inclusive.
        """
        filtered = files

        if filters.file_name_contains:
            needle = filters.file_name_contains.lower()
            filtered = [f for f in filtered if needle in f.file_name.lower()]

        if filters.extension:
            ext = filters.extension.lower()
            filtered = [f for f in filtered if f.file_extension == ext]

        if filters.folder_path_contains:
            needle = filters.folder_path_contains.lower()
            filtered = [f for f in filtered if needle in f.folder_path.lower()]

        if filters.created_after:
            filtered = [f for f in filtered if f.created_date >= filters.created_after]

        if filters.created_before:
            filtered = [f for f in filtered if f.created_date <= filters.created_before]

        if filters.modified_after:
            filtered = [f for f in filtered if f.modified_date >= filters.modified_after]

        if filters.modified_before:
            filtered = [f for f in filtered if f.modified_date <= filters.modified_before]

        if filters.min_size_bytes is not None:
            filtered = [f for f in filtered if f.file_size_bytes >= filters.min_size_bytes]

        if filters.max_size_bytes is not None:
            filtered = [f for f in filtered if f.file_size_bytes <= filters.max_size_bytes]

        return filtered

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, filters: FileSearchFilters) -> FileSearchResponse:
        """
        Search for files that match all non-None fields in *filters*.

        Parameters
        ----------
        filters:
            A ``FileSearchFilters`` instance.  Any field set to ``None``
            is ignored (i.e. it is not used as a filter criterion).

        Returns
        -------
        FileSearchResponse
            Strongly typed response containing matched files and any
            non-fatal scan errors.
        """
        logger.info(
            "File search started – filters: %s",
            filters.model_dump(exclude_none=True),
        )
        all_files, errors = self._collect_all_metadata()
        matched = self._apply_filters(all_files, filters)
        logger.info("File search complete – %d result(s)", len(matched))
        return FileSearchResponse(
            filters=filters,
            results=matched,
            result_count=len(matched),
            errors=errors,
        )

    def list_by_extension(self, extension: str) -> FileSearchResponse:
        """
        Convenience method: list all files that match *extension*.

        The extension is normalised (lowercase, leading dot ensured) before
        the search.
        """
        normalised = normalize_extension(extension) or extension
        filters = FileSearchFilters(extension=normalised)
        return self.search(filters)

    def get_all_files(self) -> FileSearchResponse:
        """
        Return metadata for every supported file under the root path.
        No filters are applied.
        """
        return self.search(FileSearchFilters())
