"""Tests for response enforcement policies."""

from __future__ import annotations

import json
from datetime import datetime

from src.agent.response_policy import (
    UNSUPPORTED_MESSAGE,
    enforce_file_json_response,
    enforce_microsoft_response_limit,
    unsupported_response,
)
from src.mcp_local_file_search.models import (
    FileMetadata,
    FileSearchFilters,
    FileSearchResponse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(files: list[FileMetadata] | None = None) -> FileSearchResponse:
    """Build a minimal FileSearchResponse for testing."""
    results = files or []
    return FileSearchResponse(
        filters=FileSearchFilters(extension=".pdf"),
        results=results,
        result_count=len(results),
    )


def _make_file(name: str = "test.pdf") -> FileMetadata:
    return FileMetadata(
        file_name=name,
        folder_path="data/sample_files/zoology",
        file_extension=".pdf",
        created_date=datetime(2026, 1, 1),
        modified_date=datetime(2026, 1, 1),
        file_size_bytes=2048,
    )


# ---------------------------------------------------------------------------
# enforce_file_json_response
# ---------------------------------------------------------------------------


class TestEnforceFileJsonResponse:
    """Local file search must return JSON only."""

    def test_returns_valid_json_string(self) -> None:
        resp = _make_response()
        output = enforce_file_json_response(resp)
        # Must be parseable as JSON without errors
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_output_contains_query_type(self) -> None:
        output = enforce_file_json_response(_make_response())
        data = json.loads(output)
        assert data["query_type"] == "local_file_search"

    def test_output_contains_results_array(self) -> None:
        output = enforce_file_json_response(_make_response([_make_file()]))
        data = json.loads(output)
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1

    def test_no_markdown_fences_in_output(self) -> None:
        output = enforce_file_json_response(_make_response())
        assert "```" not in output

    def test_empty_results_serialises_cleanly(self) -> None:
        output = enforce_file_json_response(_make_response())
        data = json.loads(output)
        assert data["result_count"] == 0
        assert data["results"] == []

    def test_result_count_matches_results(self) -> None:
        resp = _make_response([_make_file("a.pdf"), _make_file("b.pdf")])
        data = json.loads(enforce_file_json_response(resp))
        assert data["result_count"] == len(data["results"]) == 2


# ---------------------------------------------------------------------------
# enforce_microsoft_response_limit
# ---------------------------------------------------------------------------


class TestEnforceMicrosoftResponseLimit:
    """Microsoft Learn responses must be trimmed to ≤ 2 000 characters."""

    def test_short_text_unchanged(self) -> None:
        text = "Azure Blob Storage is a scalable object storage service."
        result = enforce_microsoft_response_limit(text)
        assert result == text

    def test_long_text_trimmed_to_max(self) -> None:
        # 3 000-character string
        long_text = "A" * 3000
        result = enforce_microsoft_response_limit(long_text)
        assert len(result) <= 2000

    def test_custom_max_chars_respected(self) -> None:
        text = "B" * 500
        result = enforce_microsoft_response_limit(text, max_chars=100)
        assert len(result) <= 100

    def test_trim_at_sentence_boundary(self) -> None:
        # Build text where a period sits within first 2000 chars
        sentence = "Azure Blob Storage is object storage. " * 60  # ~2220 chars
        result = enforce_microsoft_response_limit(sentence)
        assert len(result) <= 2000
        # Should end with a period (sentence boundary trim)
        assert result.endswith(".") or result.endswith("…")

    def test_exactly_2000_chars_unchanged(self) -> None:
        text = "X" * 2000
        result = enforce_microsoft_response_limit(text)
        assert result == text

    def test_2001_chars_trimmed(self) -> None:
        text = "X" * 2001
        result = enforce_microsoft_response_limit(text)
        assert len(result) <= 2000


# ---------------------------------------------------------------------------
# unsupported_response
# ---------------------------------------------------------------------------


class TestUnsupportedResponse:
    """Unsupported query returns the exact required message."""

    EXACT_MESSAGE = (
        "Unsupported query. This agent only supports local file search "
        "and Microsoft/Azure documentation questions."
    )

    def test_returns_exact_message(self) -> None:
        assert unsupported_response() == self.EXACT_MESSAGE

    def test_matches_module_constant(self) -> None:
        assert unsupported_response() == UNSUPPORTED_MESSAGE

    def test_message_is_string(self) -> None:
        assert isinstance(unsupported_response(), str)

    def test_message_not_empty(self) -> None:
        assert unsupported_response().strip() != ""
