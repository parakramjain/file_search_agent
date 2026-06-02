# Testing Strategy

## Overview

The test suite uses `pytest` and targets four areas:

| Test File | Area |
|---|---|
| `tests/test_models.py` | Pydantic model validation |
| `tests/test_file_search.py` | Search service + tool wrappers |
| `tests/test_router.py` | Query classification + filter parsing |
| `tests/test_response_policy.py` | Response enforcement policies |

---

## Unit Test Strategy

All unit tests are **pure unit tests**:
- No OpenAI API calls
- No network connections
- No reliance on the actual `data/sample_files/` directory
- Temporary directories created by pytest's `tmp_path` fixture

### Models (`test_models.py`)

Tests validate:
- Extension normalisation (uppercase → lowercase, missing dot added)
- Negative size rejection
- Invalid date range rejection (after > before)
- `result_count` mismatch rejection
- JSON serialisation shape

### File Search (`test_file_search.py`)

Tests use the `temp_file_root` fixture (a `tmp_path` sub-tree with 7 files across 3 folders).

Tests cover:
- `get_all_files` returns all 7 supported files
- Results sorted by file name ascending
- Missing root path returns an error (not an exception)
- Extension filter (`.pdf`, `.txt`, uppercase, without dot, unknown)
- File name contains (case-insensitive, no match)
- Folder path contains (`zoology`, `biology`, no match)
- Size range (large max = all files, zero max = only empty files, huge min = no files)
- Unsupported extensions ignored (`.md`, `.py`, `.csv`)
- Hidden files ignored
- `list_by_extension` shorthand
- Direct tool wrappers (`search_files_tool`, `list_files_by_extension_tool`, `get_all_files_tool`)
- Tool wrapper JSON serialisation

### Router (`test_router.py`)

Tests cover:
- PDF query → `LOCAL_FILE_SEARCH`
- DOCX, TXT, folder, extension, modified, directory queries → `LOCAL_FILE_SEARCH`
- Azure, Microsoft, Entra, SharePoint, Power BI, .NET queries → `MICROSOFT_LEARN`
- Football, capital of France, empty string → `UNSUPPORTED`
- Case-insensitive matching for both Microsoft and file keywords
- `parse_file_search_filters`: extension detection for all 7 supported types
- `parse_file_search_filters`: folder detection for zoology / biology / ecology
- "all files" clears extension filter

### Response Policy (`test_response_policy.py`)

Tests cover:
- `enforce_file_json_response` returns valid JSON without markdown fences
- `enforce_microsoft_response_limit` passes short text unchanged
- `enforce_microsoft_response_limit` trims 3 000-char text to ≤ 2 000 chars
- Custom `max_chars` parameter respected
- Trim at sentence boundary (ends with `.` or `…`)
- `unsupported_response` returns exact required string

---

## Integration Test Strategy

Integration tests (manual CLI checks) are described in the manual checklist below.

Automated integration tests for the Microsoft Learn MCP path are **not included** because:
1. They require a live OpenAI API key
2. They make remote network calls (non-deterministic)
3. They incur token costs

---

## Manual CLI Test Checklist

Run: `python -m src.agent.main`

| # | Input | Expected |
|---|---|---|
| 1 | `What PDF files are available in our system?` | JSON with only `.pdf` results |
| 2 | `List all txt files` | JSON with only `.txt` results |
| 3 | `Show files in the zoology folder` | JSON with only zoology folder results |
| 4 | `Show all files` | JSON with all 7 sample files |
| 5 | `Who won the last football match?` | Exact refusal message |
| 6 | `What is Azure Blob Storage?` (with API key) | Concise text answer ≤ 2 000 chars |
| 7 | `exit` | CLI exits cleanly |
| 8 | Ctrl+C | CLI exits cleanly |

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing

# Specific test file
pytest tests/test_router.py -v

# Single test class
pytest tests/test_file_search.py::TestGetAllFiles -v
```

---

## Known Limitations

- The Microsoft Learn MCP path has no automated tests (see Integration Tests section).
- Date/size filter parsing from natural language is not tested (not implemented).
- Windows-specific file creation timestamps (`st_ctime`) differ from POSIX semantics; tests use relative comparisons only.
- The minimal binary sample files (`.pdf`, `.docx`, `.xlsx`, `.jpg`) are structurally valid but contain no meaningful content.
