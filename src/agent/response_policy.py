"""
Response enforcement policies.

Three policy functions ensure that outputs conform to the rules defined in
the overall context:

- Local file search → JSON only, no markdown
- Microsoft Learn   → concise text, ≤ 2 000 characters
- Unsupported       → exact refusal message
"""

from __future__ import annotations

import logging

from src.mcp_local_file_search.models import FileSearchResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNSUPPORTED_MESSAGE: str = (
    "Unsupported query. This agent only supports local file search "
    "and Microsoft/Azure documentation questions."
)


# ---------------------------------------------------------------------------
# Policy functions
# ---------------------------------------------------------------------------


def enforce_file_json_response(response: FileSearchResponse) -> str:
    """
    Serialise *response* to a JSON string.

    Rules enforced:
    - No markdown code fences.
    - No explanatory prose.
    - 2-space indented JSON via Pydantic's ``model_dump_json``.

    Parameters
    ----------
    response:
        A validated ``FileSearchResponse`` instance.

    Returns
    -------
    str
        Pretty-printed JSON string.
    """
    return response.model_dump_json(indent=2)


def enforce_microsoft_response_limit(text: str, max_chars: int = 2000) -> str:
    """
    Trim *text* to *max_chars* characters if necessary.

    Attempts to end the trimmed text at the nearest sentence boundary
    (full stop) in the latter half of the allowed range to avoid cutting
    mid-sentence.  Falls back to a hard truncation with ``"…"`` appended.

    Parameters
    ----------
    text:
        Raw response text from the Microsoft Learn MCP path.
    max_chars:
        Upper limit on the returned string length (default 2 000).

    Returns
    -------
    str
        Text guaranteed to be ≤ *max_chars* characters.
    """
    if len(text) <= max_chars:
        return text

    # Reserve one character for the ellipsis in the hard-truncation branch
    budget = max_chars - 1
    candidate = text[:max_chars]

    # Try to find a sentence boundary in the latter half of the allowed range
    last_period = candidate.rfind(".")
    if last_period > max_chars // 2:
        # End at the sentence boundary (includes the period); guaranteed ≤ max_chars
        truncated = candidate[: last_period + 1]
    else:
        # Hard-truncate leaving room for the ellipsis
        truncated = text[:budget].rstrip() + "…"

    logger.warning(
        "Microsoft Learn response truncated: %d → %d chars",
        len(text),
        len(truncated),
    )
    return truncated


def unsupported_response() -> str:
    """
    Return the standardised refusal message for unsupported queries.

    The exact text is defined in ``UNSUPPORTED_MESSAGE`` and tested in the
    response-policy test suite.
    """
    return UNSUPPORTED_MESSAGE
