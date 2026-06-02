"""
Pydantic models for local file search.

All structured inputs and outputs for the local file search feature are
represented as Pydantic v2 models so they can be validated, serialised to
JSON, and consumed directly by the agent framework.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)


class FileSearchFilters(BaseModel):
    """
    Metadata filters applied when searching the local file system.

    All fields are optional.  When a field is ``None`` it is not applied
    as a filter.
    """

    file_name_contains: str | None = None
    """Case-insensitive substring to match against the file name."""

    extension: str | None = None
    """File extension, e.g. ``".pdf"``.  Normalised to lowercase with a
    leading dot by the validator."""

    folder_path_contains: str | None = None
    """Case-insensitive substring to match against the folder path."""

    created_after: datetime | None = None
    """Include files created on or after this datetime (inclusive)."""

    created_before: datetime | None = None
    """Include files created on or before this datetime (inclusive)."""

    modified_after: datetime | None = None
    """Include files modified on or after this datetime (inclusive)."""

    modified_before: datetime | None = None
    """Include files modified on or before this datetime (inclusive)."""

    min_size_bytes: int | None = None
    """Minimum file size in bytes (inclusive, non-negative)."""

    max_size_bytes: int | None = None
    """Maximum file size in bytes (inclusive, non-negative)."""

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("extension", mode="before")
    @classmethod
    def _normalise_extension(cls, value: str | None) -> str | None:
        """Normalise extension to lowercase and ensure it starts with '.'."""
        if value is None:
            return None
        value = value.strip().lower()
        if value and not value.startswith("."):
            value = f".{value}"
        return value or None

    @field_validator("min_size_bytes", "max_size_bytes", mode="before")
    @classmethod
    def _validate_non_negative(cls, value: int | None) -> int | None:
        """Reject negative byte-size values."""
        if value is not None and value < 0:
            raise ValueError("File size filters must be non-negative.")
        return value

    @model_validator(mode="after")
    def _validate_ranges(self) -> FileSearchFilters:
        """
        Ensure that date and size ranges are logically consistent
        (lower bound ≤ upper bound).
        """
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValueError("created_after must not be later than created_before.")

        if self.modified_after and self.modified_before:
            if self.modified_after > self.modified_before:
                raise ValueError("modified_after must not be later than modified_before.")

        if (
            self.min_size_bytes is not None
            and self.max_size_bytes is not None
            and self.min_size_bytes > self.max_size_bytes
        ):
            raise ValueError("min_size_bytes must be <= max_size_bytes.")

        return self


class FileMetadata(BaseModel):
    """Metadata record for a single file returned by a search."""

    file_name: str
    """Base name of the file, e.g. ``"amphibian_notes.pdf"``."""

    folder_path: str
    """Relative folder path from the search root (forward-slash separators)."""

    file_extension: str
    """Lowercase extension including leading dot, e.g. ``".pdf"``."""

    created_date: datetime
    """File creation timestamp (UTC, naive datetime)."""

    modified_date: datetime
    """File last-modified timestamp (UTC, naive datetime)."""

    file_size_bytes: int
    """File size in bytes."""


class FileSearchResponse(BaseModel):
    """
    Top-level response returned by every local file search operation.

    Serialises cleanly to JSON with no extra text.
    """

    query_type: Literal["local_file_search"] = "local_file_search"
    """Discriminator field – always ``"local_file_search"``."""

    filters: FileSearchFilters
    """The filters that were applied to produce this result."""

    results: list[FileMetadata]
    """Matching files sorted by file name (ascending, case-insensitive)."""

    result_count: int
    """Must equal ``len(results)``; validated automatically."""

    errors: list[str] = []
    """Non-fatal errors encountered while scanning (e.g. permission denied)."""

    @model_validator(mode="after")
    def _validate_result_count(self) -> FileSearchResponse:
        """Keep ``result_count`` in sync with the length of ``results``."""
        if self.result_count != len(self.results):
            raise ValueError(
                f"result_count ({self.result_count}) does not match "
                f"len(results) ({len(self.results)})."
            )
        return self
