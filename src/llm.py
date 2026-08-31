"""A tiny client for a local Ollama LLM (ADR-034).

`narrate` turns a prompt into text. It **returns None — never raises — when Ollama is
unavailable** (not running, timeout, bad response), so callers can degrade gracefully: in
this project the LLM is an *optional narrator*, never load-bearing. Stdlib HTTP only, so no
new dependency; local, private, free.
"""

import json
import socket
import urllib.error
import urllib.parse
import urllib.request

from src import config


def reachable(*, url: str | None = None, timeout: float = 0.4) -> bool:
    """Is a narrator actually attached? A connect attempt, not a generation (ADR-171).

    Callers use this to decide whether an `ask.answer` costs **milliseconds or half a minute**, because that
    is the whole difference between the deployed app and a dev machine: with no Ollama, `ask.answer` returns
    the analytics in ~120 ms; with `qwen3:8b` attached it narrates for 27-86 s. ADR-166 hard-coded an answer
    to that question and it went stale the moment the model changed — so ask the socket instead of assuming.

    **The failure direction is the design.** *Connection refused* is a definitive "nothing is listening", so
    it returns False and the caller may render eagerly. **Every other failure — timeout, DNS, a bad URL — is
    ambiguous, and returns True.** Being wrong in that direction costs one click; being wrong in the other
    direction costs a 27-second page load, which is the exact outcome this whole ADR exists to avoid.
    """
    parsed = urllib.parse.urlparse(url or config.OLLAMA_URL)
    try:
        with socket.create_connection((parsed.hostname or "localhost", parsed.port or 80), timeout):
            return True
    except ConnectionRefusedError:
        return False          # definitively nothing there — the Cloud case
    except OSError:
        return True           # unknown → assume attached, so a wrong guess costs a click not a minute


def extract(prompt: str, *, model: str | None = None, url: str | None = None,
            timeout: int | None = None) -> str | None:
    """Ask the model for **structured** output — temperature 0, thinking off; None if unavailable.

    Separate from `narrate` because the two want opposite things (ADR-151). Narration wants a little warmth
    and prose; extraction wants the same answer every time and nothing but JSON. Sharing one function would
    mean one of them silently getting the wrong settings — and for the same reason it defaults to its **own
    model and timeout** (ADR-157): narration runs while a person waits, extraction runs once, unattended, in
    `refresh`, so they are not the same trade.

    The LLM is still never load-bearing: this returns None on any failure and the caller extracts nothing.
    """
    body = json.dumps({
        "model": model or config.OLLAMA_EXTRACT_MODEL, "prompt": prompt, "stream": False,
        "think": False, "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(url or config.OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=timeout or config.OLLAMA_EXTRACT_TIMEOUT))
        return (resp.get("response") or "").strip() or None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


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
