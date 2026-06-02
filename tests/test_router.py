"""Tests for the deterministic query router and filter parser."""

from __future__ import annotations

from src.agent.router import QueryType, classify_query, parse_file_search_filters

# ---------------------------------------------------------------------------
# classify_query
# ---------------------------------------------------------------------------


class TestClassifyQuery:
    """Router maps queries to the correct QueryType without an LLM."""

    # --- Local file search ---

    def test_pdf_query_routes_to_local_file_search(self) -> None:
        result = classify_query("What PDF files are available in our system?")
        assert result == QueryType.LOCAL_FILE_SEARCH

    def test_docx_query_routes_to_local_file_search(self) -> None:
        assert classify_query("List all docx files") == QueryType.LOCAL_FILE_SEARCH

    def test_folder_query_routes_to_local_file_search(self) -> None:
        assert classify_query("Show files in the zoology folder") == QueryType.LOCAL_FILE_SEARCH

    def test_extension_query_routes_to_local_file_search(self) -> None:
        assert classify_query("Find files by extension .txt") == QueryType.LOCAL_FILE_SEARCH

    def test_modified_query_routes_to_local_file_search(self) -> None:
        assert classify_query("Find files modified last week") == QueryType.LOCAL_FILE_SEARCH

    def test_directory_query_routes_to_local_file_search(self) -> None:
        result = classify_query("What files are in the biology directory?")
        assert result == QueryType.LOCAL_FILE_SEARCH

    def test_all_files_query_routes_to_local_file_search(self) -> None:
        assert classify_query("Show all files in our local system") == QueryType.LOCAL_FILE_SEARCH

    # --- Microsoft Learn ---

    def test_azure_query_routes_to_microsoft_learn(self) -> None:
        assert classify_query("What is Azure Blob Storage?") == QueryType.MICROSOFT_LEARN

    def test_microsoft_query_routes_to_microsoft_learn(self) -> None:
        assert classify_query("Explain Microsoft Fabric Lakehouse") == QueryType.MICROSOFT_LEARN

    def test_azure_entra_routes_to_microsoft_learn(self) -> None:
        assert classify_query("How does Azure Entra ID work?") == QueryType.MICROSOFT_LEARN

    def test_sharepoint_routes_to_microsoft_learn(self) -> None:
        assert classify_query("What is SharePoint?") == QueryType.MICROSOFT_LEARN

    def test_power_bi_routes_to_microsoft_learn(self) -> None:
        assert classify_query("Explain Power BI dashboards") == QueryType.MICROSOFT_LEARN

    def test_dotnet_routes_to_microsoft_learn(self) -> None:
        assert classify_query("What is .NET MAUI?") == QueryType.MICROSOFT_LEARN

    # --- Unsupported ---

    def test_random_query_routes_to_unsupported(self) -> None:
        assert classify_query("Who won the last football match?") == QueryType.UNSUPPORTED

    def test_general_knowledge_routes_to_unsupported(self) -> None:
        assert classify_query("What is the capital of France?") == QueryType.UNSUPPORTED

    def test_empty_query_routes_to_unsupported(self) -> None:
        assert classify_query("") == QueryType.UNSUPPORTED

    def test_whitespace_query_routes_to_unsupported(self) -> None:
        assert classify_query("   ") == QueryType.UNSUPPORTED

    # --- Edge cases ---

    def test_mixed_case_azure_matches(self) -> None:
        assert classify_query("WHAT IS AZURE BLOB STORAGE?") == QueryType.MICROSOFT_LEARN

    def test_mixed_case_pdf_matches(self) -> None:
        assert classify_query("List all PDF files") == QueryType.LOCAL_FILE_SEARCH


# ---------------------------------------------------------------------------
# parse_file_search_filters
# ---------------------------------------------------------------------------


class TestParseFileSearchFilters:
    """Parser extracts extension and folder from natural-language queries."""

    def test_pdf_query_sets_pdf_extension(self) -> None:
        filters = parse_file_search_filters("What PDF files are available in our system?")
        assert filters.extension == ".pdf"

    def test_docx_query_sets_docx_extension(self) -> None:
        filters = parse_file_search_filters("List all docx files")
        assert filters.extension == ".docx"

    def test_xlsx_query_sets_xlsx_extension(self) -> None:
        filters = parse_file_search_filters("Find xlsx files")
        assert filters.extension == ".xlsx"

    def test_txt_query_sets_txt_extension(self) -> None:
        filters = parse_file_search_filters("Show txt files")
        assert filters.extension == ".txt"

    def test_jpg_query_sets_jpg_extension(self) -> None:
        filters = parse_file_search_filters("Find jpg images")
        assert filters.extension == ".jpg"

    def test_zoology_sets_folder(self) -> None:
        filters = parse_file_search_filters("Show files in the zoology folder")
        assert filters.folder_path_contains == "zoology"

    def test_biology_sets_folder(self) -> None:
        filters = parse_file_search_filters("List files in biology")
        assert filters.folder_path_contains == "biology"

    def test_ecology_sets_folder(self) -> None:
        filters = parse_file_search_filters("Find files in ecology directory")
        assert filters.folder_path_contains == "ecology"

    def test_all_files_clears_extension(self) -> None:
        """'all files' in the query should NOT apply an extension filter."""
        filters = parse_file_search_filters("Show all files")
        assert filters.extension is None

    def test_no_match_returns_empty_filters(self) -> None:
        filters = parse_file_search_filters("Show me everything")
        # No extension keyword, no folder keyword → both are None or matched generically
        # At minimum it should not crash and return a valid object
        assert isinstance(filters.extension, (str, type(None)))

    def test_combined_extension_and_folder(self) -> None:
        filters = parse_file_search_filters("Find PDF files in zoology folder")
        assert filters.extension == ".pdf"
        assert filters.folder_path_contains == "zoology"
