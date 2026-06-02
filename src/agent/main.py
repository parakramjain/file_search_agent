"""
Main entry point for the MCP File Search Agent.

Run with::

    python -m src.agent.main

or, after installing the package::

    file-search-agent
"""

from __future__ import annotations

from src.agent.cli import run_cli


def main() -> None:
    """Launch the interactive CLI agent."""
    run_cli()


if __name__ == "__main__":
    main()
