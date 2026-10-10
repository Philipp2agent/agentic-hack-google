"""Gemini Interactions API Client for DawnDispatch (claude-02 / gemini-01).

Primary access through client.interactions.create with structured outputs,
falling back to client.models.generate_content.
"""

from __future__ import annotations

import json
import os
from typing import Any


def gemini_json(
    system: str,
    user: str,
    schema: Any,
    previous_interaction_id: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    """Call Gemini 3.8 Flash with structured JSON output.

    Returns (parsed_json_dict, interaction_id_or_none).
    Raises RuntimeError if GEMINI_API_KEY is not set.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment")

    from google import genai

    client = genai.Client(api_key=key)

    # 1. Primary: Interactions API (google-genai >= 2.3.0)
    try:
        kwargs: dict[str, Any] = {
            "model": "gemini-3.8-flash",
            "system_instruction": system,
            "input": user,
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
            "response_mime_type": "application/json",
        }
        if previous_interaction_id:
            kwargs["previous_interaction_id"] = previous_interaction_id

        ix = client.interactions.create(**kwargs)
        if getattr(ix, "output_text", None):
            parsed = json.loads(ix.output_text)
            return parsed, getattr(ix, "id", None)
    except Exception:
        # Fall back to models.generate_content
        pass

    # 2. Fallback: models.generate_content
    prompt = f"System: {system}\n\nUser: {user}"
    res = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    parsed = json.loads(res.text)
    return parsed, None
