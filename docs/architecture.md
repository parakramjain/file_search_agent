# Architecture

## Component Overview

The MCP File Search Agent consists of five main layers:

| Layer | Module(s) | Responsibility |
|---|---|---|
| Configuration | `src/agent/config.py` | Load env vars via `pydantic-settings` |
| Router | `src/agent/router.py` | Classify query type deterministically |
| Local File Search | `src/mcp_local_file_search/` | MCP server + search service + Pydantic models |
| Microsoft Learn | `src/agent/cli.py` + openai-agents | Connect to remote MCP endpoint |
| Response Policy | `src/agent/response_policy.py` | Enforce output format rules |

---

## Query Flow

```
User Input
    │
    ▼
classify_query()  ←── deterministic keyword matching (no LLM)
    │
    ├─── LOCAL_FILE_SEARCH
    │        │
    │        ▼
    │    parse_file_search_filters()
    │        │
    │        ▼
    │    search_files_tool()  ←── LocalFileSearchService.search()
    │        │
    │        ▼
    │    enforce_file_json_response()  →  JSON printed to stdout
    │
    ├─── MICROSOFT_LEARN
    │        │
    │        ▼
    │    answer_with_microsoft_learn()
    │        │
    │        ▼
    │    OpenAI Agents SDK + MCPServerSse(https://learn.microsoft.com/api/mcp)
    │        │
    │        ▼
    │    enforce_microsoft_response_limit()  →  text printed to console
    │
    └─── UNSUPPORTED
             │
             ▼
         unsupported_response()  →  refusal message printed
```

---

## Local File Search MCP Design

The local file search is implemented with two layers:

### 1. Pydantic Models (`models.py`)

- `FileSearchFilters` – input schema with field validators
- `FileMetadata` – single file result record
- `FileSearchResponse` – top-level response with discriminator `query_type`

### 2. Search Service (`search.py`)

`LocalFileSearchService` uses `pathlib.Path.rglob("*")` to recursively scan the root directory.  File stats are collected with `Path.stat()`:

- `st_ctime` → `created_date`
- `st_mtime` → `modified_date`
- `st_size`  → `file_size_bytes`

Files are filtered by:
- Extension (case-insensitive)
- File name contains (case-insensitive substring)
- Folder path contains (case-insensitive substring)
- Date ranges (inclusive)
- Size ranges (inclusive)

Unreadable files are caught with `OSError`/`PermissionError` and appended to `errors[]` instead of raising.

### 3. MCP Server (`server.py`)

`FastMCP` (from the `mcp` package) wraps the three tool functions:

| Tool | Input | Output |
|---|---|---|
| `search_files` | filter fields | `FileSearchResponse` as JSON |
| `list_files_by_extension` | `extension: str` | `FileSearchResponse` as JSON |
| `get_all_files` | _(none)_ | `FileSearchResponse` as JSON |

Direct in-process wrappers (`search_files_tool`, etc.) bypass the MCP wire protocol for CLI and test use.

---

## Microsoft Learn MCP Design

The remote Microsoft Learn MCP endpoint (`https://learn.microsoft.com/api/mcp`) is accessed using the **OpenAI Agents SDK** (`openai-agents`):

```python
async with MCPServerSse(params={"url": settings.microsoft_learn_mcp_url}) as server:
    agent = Agent(
        name="Microsoft Learn Agent",
        instructions=SYSTEM_PROMPT,
        model=settings.model_name,
        mcp_servers=[server],
    )
    result = await Runner.run(agent, query)
```

The agent is constrained by `SYSTEM_PROMPT` (see `prompts.py`) to only use the MCP server tools and to keep responses under 2 000 characters.

---

## Response Policy

| Query Type | Policy |
|---|---|
| `LOCAL_FILE_SEARCH` | `FileSearchResponse.model_dump_json()` – pure JSON, no markdown |
| `MICROSOFT_LEARN` | Truncated at 2 000 chars at sentence boundary |
| `UNSUPPORTED` | Exact fixed string |

---

## Trade-offs

| Decision | Reason |
|---|---|
| Deterministic router (no LLM) | Fast, free, testable, no API cost |
| In-process local search | No IPC overhead; simplest maintainable impl |
| `pydantic-settings` for config | Standard, type-safe, `.env` file support |
| `FastMCP` for local server | Minimal boilerplate; easy to extend |
| `rich` for CLI | Colour output without heavy TUI dependencies |

---

## Future Extension Points

- **Full-text search** – index `.txt`, `.docx`, `.pdf` content with `pypdf` / `python-docx`
- **SQLite index** – pre-build metadata index for large folder trees
- **Semantic search** – embed file contents, store in a vector DB
- **Docker** – containerise for portable deployment
- **GitHub Actions CI** – run `pytest` + `ruff` on every push
- **Web UI** – FastAPI + React frontend
