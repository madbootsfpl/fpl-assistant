"""A tiny client for a local Ollama LLM (ADR-034).

`narrate` turns a prompt into text. It **returns None — never raises — when Ollama is
unavailable** (not running, timeout, bad response), so callers can degrade gracefully: in
this project the LLM is an *optional narrator*, never load-bearing. Stdlib HTTP only, so no
new dependency; local, private, free.
"""

import json
import urllib.error
import urllib.request

from src import config


def narrate(prompt: str, *, model: str | None = None, url: str | None = None,
            timeout: int | None = None) -> str | None:
    """Ask the local model to generate text for `prompt`; None if it's unavailable.

    A low temperature keeps the (narration-only) output steady. Any failure — connection
    refused, timeout, malformed response — returns None so the caller can fall back to the
    analytics decision rather than crash.
    """
    model = model or config.OLLAMA_MODEL
    url = url or config.OLLAMA_URL
    timeout = timeout or config.OLLAMA_TIMEOUT

    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=timeout))
        return (resp.get("response") or "").strip() or None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
