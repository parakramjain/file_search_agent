"""
Application configuration.

Settings are read from environment variables (or a ``.env`` file) using
``pydantic-settings``.  A cached singleton is returned by ``get_settings()``.

Environment variables
---------------------
OPENAI_API_KEY
    Required only when answering Microsoft/Azure queries.  The agent will
    return a clear error instead of crashing when the key is absent.
LOCAL_FILE_ROOT
    Root folder for local file search.  Defaults to ``./data/sample_files``.
MICROSOFT_LEARN_MCP_URL
    Remote MCP endpoint for Microsoft Learn.
LOG_LEVEL
    Python logging level string (DEBUG / INFO / WARNING / ERROR).
MODEL_NAME
    OpenAI model name used for Microsoft Learn queries (e.g. ``gpt-4o``).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    """
    Centralised application settings backed by environment variables.

    ``pydantic-settings`` automatically reads from a ``.env`` file located
    in the current working directory (project root) and from the process
    environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    """OpenAI API key – ``None`` is acceptable during local-file-only usage."""

    local_file_root: Path = Path("./data/sample_files")
    """Root directory for local file search."""

    microsoft_learn_mcp_url: str = "https://learn.microsoft.com/api/mcp"
    """Remote Microsoft Learn MCP endpoint URL."""

    log_level: str = "INFO"
    """Logging level string."""

    model_name: str = "gpt-4o"
    """OpenAI model used for Microsoft Learn queries."""


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Return the application settings singleton.

    Settings are loaded once and cached.  The root logger level is
    configured on first call.
    """
    settings = AppSettings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.debug(
        "Settings loaded – local_file_root=%s model=%s",
        settings.local_file_root,
        settings.model_name,
    )
    return settings
