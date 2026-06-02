"""Tests for Pydantic models in mcp_local_file_search.models."""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.mcp_local_file_search.models import (
    FileMetadata,
    FileSearchFilters,
    FileSearchResponse,
)

# ---------------------------------------------------------------------------
# FileSearchFilters – extension normalisation
# ---------------------------------------------------------------------------


class TestExtensionNormalisation:
    """Extension field is normalised to lowercase with a leading dot."""

    def test_uppercase_extension_normalised(self) -> None:
        f = FileSearchFilters(extension="PDF")
        assert f.extension == ".pdf"

    def test_extension_without_dot_gets_dot(self) -> None:
        f = FileSearchFilters(extension="docx")
        assert f.extension == ".docx"

    def test_extension_already_normalised_unchanged(self) -> None:
        f = FileSearchFilters(extension=".xlsx")
        assert f.extension == ".xlsx"

    def test_none_extension_stays_none(self) -> None:
        f = FileSearchFilters(extension=None)
        assert f.extension is None

    def test_mixed_case_with_dot(self) -> None:
        f = FileSearchFilters(extension=".TXT")
        assert f.extension == ".txt"


# ---------------------------------------------------------------------------
# FileSearchFilters – size validation
# ---------------------------------------------------------------------------


class TestSizeValidation:
    """min_size_bytes and max_size_bytes must be non-negative and ordered."""

    def test_negative_min_size_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchFilters(min_size_bytes=-1)

    def test_negative_max_size_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchFilters(max_size_bytes=-100)

    def test_zero_size_allowed(self) -> None:
        f = FileSearchFilters(min_size_bytes=0, max_size_bytes=0)
        assert f.min_size_bytes == 0

    def test_min_greater_than_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchFilters(min_size_bytes=500, max_size_bytes=100)

    def test_equal_min_max_allowed(self) -> None:
        f = FileSearchFilters(min_size_bytes=1024, max_size_bytes=1024)
        assert f.min_size_bytes == f.max_size_bytes == 1024


# ---------------------------------------------------------------------------
# FileSearchFilters – date range validation
# ---------------------------------------------------------------------------


class TestDateRangeValidation:
    """created_after must not be later than created_before, same for modified."""

    def test_created_after_after_created_before_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchFilters(
                created_after=datetime(2026, 6, 2),
                created_before=datetime(2026, 6, 1),
            )

    def test_modified_after_after_modified_before_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchFilters(
                modified_after=datetime(2026, 12, 31),
                modified_before=datetime(2026, 1, 1),
            )

    def test_valid_date_range_accepted(self) -> None:
        f = FileSearchFilters(
            created_after=datetime(2026, 1, 1),
            created_before=datetime(2026, 12, 31),
        )
        assert f.created_after < f.created_before  # type: ignore[operator]

    def test_equal_dates_allowed(self) -> None:
        dt = datetime(2026, 6, 1)
        f = FileSearchFilters(created_after=dt, created_before=dt)
        assert f.created_after == f.created_before


# ---------------------------------------------------------------------------
# FileSearchResponse – result_count validation
# ---------------------------------------------------------------------------


class TestResponseResultCount:
    """result_count must match len(results)."""

    def _make_file(self) -> FileMetadata:
        return FileMetadata(
            file_name="test.pdf",
            folder_path="data/sample_files/zoology",
            file_extension=".pdf",
            created_date=datetime(2026, 1, 1),
            modified_date=datetime(2026, 1, 1),
            file_size_bytes=1024,
        )

    def test_mismatched_result_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            FileSearchResponse(
                filters=FileSearchFilters(),
                results=[self._make_file()],
                result_count=0,  # wrong – should be 1
            )

    def test_correct_result_count_accepted(self) -> None:
        file = self._make_file()
        resp = FileSearchResponse(
            filters=FileSearchFilters(),
            results=[file],
            result_count=1,
        )
        assert resp.result_count == 1

    def test_empty_result_accepted(self) -> None:
        resp = FileSearchResponse(
            filters=FileSearchFilters(),
            results=[],
            result_count=0,
        )
        assert resp.result_count == 0


# ---------------------------------------------------------------------------
# FileSearchResponse – JSON serialisation
# ---------------------------------------------------------------------------


class TestJsonSerialisation:
    """Response serialises to clean JSON with expected fields."""

    def test_response_serialises_to_json(self) -> None:
        resp = FileSearchResponse(
            filters=FileSearchFilters(extension=".pdf"),
            results=[],
            result_count=0,
        )
        payload = resp.model_dump_json()
        data = json.loads(payload)
        assert data["query_type"] == "local_file_search"
        assert data["result_count"] == 0
        assert isinstance(data["results"], list)
        assert isinstance(data["errors"], list)

    def test_filters_appear_in_serialised_output(self) -> None:
        resp = FileSearchResponse(
            filters=FileSearchFilters(extension=".txt"),
            results=[],
            result_count=0,
        )
        data = json.loads(resp.model_dump_json())
        assert data["filters"]["extension"] == ".txt"
