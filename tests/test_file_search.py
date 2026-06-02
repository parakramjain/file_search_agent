"""Tests for LocalFileSearchService and in-process tool wrappers."""

from __future__ import annotations

import json
from pathlib import Path

from src.mcp_local_file_search.models import FileSearchFilters
from src.mcp_local_file_search.search import LocalFileSearchService
from src.mcp_local_file_search.server import (
    get_all_files_tool,
    list_files_by_extension_tool,
    search_files_tool,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_service(root: Path) -> LocalFileSearchService:
    return LocalFileSearchService(root_path=root)


# ---------------------------------------------------------------------------
# get_all_files – basic scan
# ---------------------------------------------------------------------------


class TestGetAllFiles:
    """Service returns metadata for all supported files."""

    def test_returns_all_supported_files(self, temp_file_root: Path) -> None:
        service = make_service(temp_file_root)
        resp = service.get_all_files()
        # Fixture has 7 supported files (txt×2, pdf×2, docx×1, xlsx×1, jpg×1)
        assert resp.result_count == 7
        assert resp.result_count == len(resp.results)

    def test_result_count_matches_results_len(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).get_all_files()
        assert resp.result_count == len(resp.results)

    def test_query_type_is_local_file_search(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).get_all_files()
        assert resp.query_type == "local_file_search"

    def test_no_errors_on_valid_root(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).get_all_files()
        assert resp.errors == []

    def test_results_sorted_by_filename_ascending(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).get_all_files()
        names = [r.file_name.lower() for r in resp.results]
        assert names == sorted(names)

    def test_missing_root_returns_error_not_exception(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        resp = make_service(missing).get_all_files()
        assert resp.result_count == 0
        assert len(resp.errors) > 0


# ---------------------------------------------------------------------------
# search – extension filter
# ---------------------------------------------------------------------------


class TestSearchByExtension:
    """Extension filter returns only files with the matching extension."""

    def test_pdf_filter_returns_only_pdfs(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(FileSearchFilters(extension=".pdf"))
        assert resp.result_count > 0
        assert all(r.file_extension == ".pdf" for r in resp.results)

    def test_txt_filter_returns_only_txts(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(FileSearchFilters(extension=".txt"))
        assert all(r.file_extension == ".txt" for r in resp.results)

    def test_uppercase_extension_normalised_by_model(self, temp_file_root: Path) -> None:
        """Uppercase extension in query is normalised → still returns results."""
        resp = make_service(temp_file_root).search(FileSearchFilters(extension="PDF"))
        assert resp.result_count > 0
        assert all(r.file_extension == ".pdf" for r in resp.results)

    def test_extension_without_dot_normalised(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(FileSearchFilters(extension="pdf"))
        assert resp.result_count > 0

    def test_unknown_extension_returns_empty(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(FileSearchFilters(extension=".xyz"))
        assert resp.result_count == 0


# ---------------------------------------------------------------------------
# search – file name filter
# ---------------------------------------------------------------------------


class TestSearchByFileName:
    """file_name_contains filter is case-insensitive."""

    def test_match_by_partial_name(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(file_name_contains="amphibian")
        )
        assert resp.result_count == 1
        assert "amphibian" in resp.results[0].file_name.lower()

    def test_case_insensitive_match(self, temp_file_root: Path) -> None:
        resp_lower = make_service(temp_file_root).search(
            FileSearchFilters(file_name_contains="amphibian")
        )
        resp_upper = make_service(temp_file_root).search(
            FileSearchFilters(file_name_contains="AMPHIBIAN")
        )
        assert resp_lower.result_count == resp_upper.result_count

    def test_no_match_returns_empty(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(file_name_contains="ZZZNOMATCH")
        )
        assert resp.result_count == 0


# ---------------------------------------------------------------------------
# search – folder path filter
# ---------------------------------------------------------------------------


class TestSearchByFolderPath:
    """folder_path_contains filter is case-insensitive."""

    def test_zoology_folder_returns_only_zoology_files(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(folder_path_contains="zoology")
        )
        assert resp.result_count > 0
        assert all("zoology" in r.folder_path.lower() for r in resp.results)

    def test_biology_folder(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(folder_path_contains="biology")
        )
        assert resp.result_count > 0
        assert all("biology" in r.folder_path.lower() for r in resp.results)

    def test_no_match_returns_empty(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(folder_path_contains="ZZZNOFOLDER")
        )
        assert resp.result_count == 0


# ---------------------------------------------------------------------------
# search – size range filter
# ---------------------------------------------------------------------------


class TestSearchBySizeRange:
    """min/max size filters are applied inclusively."""

    def test_large_max_returns_all(self, temp_file_root: Path) -> None:
        resp_all = make_service(temp_file_root).get_all_files()
        resp_sized = make_service(temp_file_root).search(
            FileSearchFilters(max_size_bytes=10 * 1024 * 1024)
        )
        assert resp_sized.result_count == resp_all.result_count

    def test_zero_max_returns_only_empty_files(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(FileSearchFilters(max_size_bytes=0))
        assert all(r.file_size_bytes == 0 for r in resp.results)

    def test_huge_min_returns_empty(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).search(
            FileSearchFilters(min_size_bytes=999_999_999)
        )
        assert resp.result_count == 0


# ---------------------------------------------------------------------------
# Unsupported file types are excluded
# ---------------------------------------------------------------------------


class TestUnsupportedFilesIgnored:
    """Files with unsupported extensions are silently skipped."""

    def test_unsupported_extension_not_in_results(self, tmp_path: Path) -> None:
        (tmp_path / "readme.md").write_text("ignored", encoding="utf-8")
        (tmp_path / "script.py").write_text("ignored", encoding="utf-8")
        (tmp_path / "data.csv").write_text("a,b,c", encoding="utf-8")
        resp = make_service(tmp_path).get_all_files()
        assert resp.result_count == 0

    def test_hidden_files_excluded(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden.txt").write_text("hidden", encoding="utf-8")
        resp = make_service(tmp_path).get_all_files()
        assert resp.result_count == 0

    def test_mixed_valid_and_invalid(self, tmp_path: Path) -> None:
        (tmp_path / "valid.txt").write_text("visible", encoding="utf-8")
        (tmp_path / "invalid.py").write_text("ignored", encoding="utf-8")
        resp = make_service(tmp_path).get_all_files()
        assert resp.result_count == 1
        assert resp.results[0].file_name == "valid.txt"


# ---------------------------------------------------------------------------
# list_by_extension shorthand
# ---------------------------------------------------------------------------


class TestListByExtension:
    def test_list_by_extension_matches_search(self, temp_file_root: Path) -> None:
        resp_list = make_service(temp_file_root).list_by_extension(".pdf")
        resp_search = make_service(temp_file_root).search(FileSearchFilters(extension=".pdf"))
        assert resp_list.result_count == resp_search.result_count

    def test_list_by_extension_without_dot(self, temp_file_root: Path) -> None:
        resp = make_service(temp_file_root).list_by_extension("pdf")
        assert resp.result_count > 0
        assert all(r.file_extension == ".pdf" for r in resp.results)


# ---------------------------------------------------------------------------
# Direct in-process tool wrappers (from server.py)
# ---------------------------------------------------------------------------


class TestToolWrappers:
    """Direct wrapper functions work correctly without MCP wire protocol."""

    def test_get_all_files_tool(self, temp_file_root: Path) -> None:
        resp = get_all_files_tool(root_path=temp_file_root)
        assert resp.result_count > 0

    def test_list_files_by_extension_tool(self, temp_file_root: Path) -> None:
        resp = list_files_by_extension_tool(".txt", root_path=temp_file_root)
        assert all(r.file_extension == ".txt" for r in resp.results)

    def test_search_files_tool(self, temp_file_root: Path) -> None:
        filters = FileSearchFilters(folder_path_contains="zoology")
        resp = search_files_tool(filters=filters, root_path=temp_file_root)
        assert resp.result_count > 0
        assert all("zoology" in r.folder_path.lower() for r in resp.results)

    def test_tool_response_serialises_to_json(self, temp_file_root: Path) -> None:
        resp = get_all_files_tool(root_path=temp_file_root)
        payload = resp.model_dump_json()
        data = json.loads(payload)
        assert "results" in data
        assert "result_count" in data
        assert data["query_type"] == "local_file_search"

    def test_empty_root_returns_error_in_response(self, empty_root: Path) -> None:
        missing = empty_root / "nonexistent"
        resp = get_all_files_tool(root_path=missing)
        assert resp.result_count == 0
        assert len(resp.errors) > 0
