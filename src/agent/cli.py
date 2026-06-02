"""
Interactive CLI for the MCP File Search Agent.

Behaviour
---------
- Reads user queries in a loop.
- Routes each query using the deterministic ``classify_query`` router.
- LOCAL_FILE_SEARCH → in-process ``search_files_tool`` → JSON output.
- MICROSOFT_LEARN   → OpenAI Agents SDK + Microsoft Learn MCP → text output.
- UNSUPPORTED       → standardised refusal message.
- ``exit`` / ``quit`` terminates the loop.

The Microsoft Learn path requires ``OPENAI_API_KEY`` to be set.  A clear
error is shown (without a stack trace) when the key is absent.
"""

from __future__ import annotations

import asyncio
import logging

from rich.console import Console

from src.agent.config import get_settings
from src.agent.response_policy import (
    enforce_file_json_response,
    enforce_microsoft_response_limit,
    unsupported_response,
)
from src.agent.router import QueryType, classify_query, parse_file_search_filters
from src.mcp_local_file_search.server import search_files_tool

logger = logging.getLogger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Microsoft Learn integration (async, requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------


async def answer_with_microsoft_learn(query: str) -> str:
    """
    Query the remote Microsoft Learn MCP server using the OpenAI Agents SDK.

    The agent is initialised with the system prompt from ``prompts.py`` and
    the Microsoft Learn MCP server so that it ONLY answers from that source.

    Parameters
    ----------
    query:
        The user's Microsoft / Azure question.

    Returns
    -------
    str
        Concise answer (≤ 2 000 characters) or an error message string.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set – cannot query Microsoft Learn.")
        return (
            "Error: OPENAI_API_KEY is not configured.  "
            "Set it in your .env file to use Microsoft/Azure queries."
        )

    try:
        from agents import Agent, Runner  # openai-agents SDK
        from agents.mcp import MCPServerStreamableHttp

        from src.agent.prompts import SYSTEM_PROMPT

        logger.info("Connecting to Microsoft Learn MCP at %s", settings.microsoft_learn_mcp_url)

        # Microsoft Learn uses the Streamable HTTP (POST-based) MCP transport,
        # not SSE.  MCPServerStreamableHttp sends POST requests to the endpoint.
        async with MCPServerStreamableHttp(
            params={"url": settings.microsoft_learn_mcp_url},
            name="Microsoft Learn",
        ) as ms_server:
            agent = Agent(
                name="Microsoft Learn Agent",
                instructions=SYSTEM_PROMPT,
                model=settings.model_name,
                mcp_servers=[ms_server],
            )
            result = await Runner.run(agent, query)
            answer = str(result.final_output)
            logger.info("Microsoft Learn response received (%d chars)", len(answer))
            return enforce_microsoft_response_limit(answer)

    except ImportError as exc:
        logger.error("openai-agents not installed: %s", exc)
        return (
            "Error: The 'openai-agents' package is not installed.  "
            "Run: pip install openai-agents"
        )
    except Exception as exc:
        logger.error("Microsoft Learn query failed: %s", exc, exc_info=True)
        return f"Error querying Microsoft Learn: {type(exc).__name__} – {exc}"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run_cli() -> None:
    """
    Start the interactive CLI agent loop.

    Prints a welcome banner and reads user input until the user types
    ``exit`` or ``quit`` or sends EOF (Ctrl+D / Ctrl+Z).
    """
    # Ensure settings (and logging) are initialised
    settings = get_settings()

    console.print()
    console.print("[bold green]╔══════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║     MCP File Search Agent  v0.1      ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════╝[/bold green]")
    console.print(
        f"  Local file root : [cyan]{settings.local_file_root}[/cyan]"
    )
    console.print(
        "  Ask about [bold]local files[/bold] (PDF, DOCX, TXT …) "
        "or [bold]Azure / Microsoft[/bold] topics."
    )
    console.print("  Type [bold]exit[/bold] or [bold]quit[/bold] to stop.\n")

    while True:
        # Read input
        try:
            user_input = console.input("[bold cyan]> [/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye.[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            console.print("[yellow]Goodbye.[/yellow]")
            break

        # Classify the query
        query_type = classify_query(user_input)
        logger.info("Query type: %s | input: %r", query_type.value, user_input[:80])

        try:
            if query_type == QueryType.LOCAL_FILE_SEARCH:
                # Parse natural-language filters and call in-process tool
                filters = parse_file_search_filters(user_input)
                response = search_files_tool(
                    filters=filters,
                    root_path=settings.local_file_root,
                )
                # Print JSON only – no extra text
                print(enforce_file_json_response(response))

            elif query_type == QueryType.MICROSOFT_LEARN:
                # Async call to Microsoft Learn MCP via openai-agents
                answer = asyncio.run(answer_with_microsoft_learn(user_input))
                console.print(answer)

            else:
                # Unsupported query type
                console.print(unsupported_response())

        except Exception as exc:
            # Log full traceback internally; show only a clean message
            logger.error("Unexpected error processing query: %s", exc, exc_info=True)
            console.print(
                "[red]An unexpected error occurred.  "
                "Check the log output for details.[/red]"
            )
