# Quick Start Guide

Get the MCP File Search Agent running in five minutes.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or newer |
| pip | latest recommended |
| OpenAI API key | required for Azure/Microsoft queries only |

---

## Step 1 – Clone the repository

```bash
git clone <repo-url>
cd mcp-file-search-agent
```

---

## Step 2 – Create and activate a virtual environment

```bash
# Create
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows cmd)
.venv\Scripts\activate.bat

# Activate (macOS / Linux)
source .venv/bin/activate
```

---

## Step 3 – Install all dependencies

```bash
pip install -e ".[dev]"
```

This installs the project in editable mode, including all development dependencies (`pytest`, `ruff`, `mypy`).

---

## Step 4 – Configure environment variables

```bash
# Copy the example file
cp .env.example .env   # macOS/Linux
copy .env.example .env  # Windows
```

Open `.env` and set your OpenAI API key:

```ini
OPENAI_API_KEY=sk-...your-key-here...
LOCAL_FILE_ROOT=./data/sample_files
MICROSOFT_LEARN_MCP_URL=https://learn.microsoft.com/api/mcp
LOG_LEVEL=INFO
MODEL_NAME=gpt-4o
```

> **Tip:** `OPENAI_API_KEY` is only required for Microsoft/Azure queries.
> Local file search works without it.

---

## Step 5 – Generate sample data files

```bash
python scripts/create_sample_data.py
```

This creates 7 natural-science sample files under `data/sample_files/`:

```
data/sample_files/
├── zoology/
│   ├── amphibian_lifecycle_notes.pdf
│   ├── mammal_habitat_summary.docx
│   └── bird_migration_observations.txt
├── biology/
│   ├── cell_structure_reference.xlsx
│   └── plant_growth_stages.txt
└── ecology/
    ├── wetland_food_chain.jpg
    └── forest_biodiversity_inventory.pdf
```

---

## Step 6 – Run the tests

```bash
pytest
```

Expected output: all tests pass.

Run with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## Step 7 – Start the interactive CLI agent

```bash
python -m src.agent.main
```

or (after `pip install -e .`):

```bash
file-search-agent
```

---

## Step 8 – Try sample queries

### Local file search (no API key needed)

```
> What PDF files are available in our system?
```

→ Returns JSON listing all `.pdf` files.

```
> Show files in the zoology folder
```

→ Returns JSON with only zoology folder files.

```
> List all txt files
```

→ Returns JSON with only `.txt` files.

### Microsoft / Azure (requires API key)

```
> What is Azure Blob Storage?
```

→ Returns a concise answer under 2 000 characters.

### Unsupported query

```
> Who won the last football match?
```

→ Returns the refusal message.

### Exit

```
> exit
```

---

## Run the standalone Local MCP Server

The local file search is also available as a standalone MCP server (stdio transport):

```bash
python -m src.mcp_local_file_search.server
```

or:

```bash
local-file-search-mcp
```

This starts the server and exposes three MCP tools:
- `search_files`
- `list_files_by_extension`
- `get_all_files`

---

## Code Quality Commands

```bash
# Lint
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Type checking
mypy src/

# Format check
ruff format --check .
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Run commands from the project root directory |
| `OPENAI_API_KEY not configured` | Set the key in `.env` and restart the CLI |
| No files returned in local search | Run `python scripts/create_sample_data.py` first |
| `mcp` import errors | Run `pip install -e ".[dev]"` again |
| Tests fail with `ModuleNotFoundError` | Ensure the virtual environment is activated |
