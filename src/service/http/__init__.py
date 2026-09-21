"""The HTTP transport over `src.service`.

⭐ **A wrapper, not a layer.** Every route parses a request, calls one service function and returns what it
gets. Nothing here decides anything about football, and nothing a client needs should ever be computable
only here — the moment that happens, the in-process consumer and the HTTP consumer have different products.
"""

from src.service.http.app import app

__all__ = ["app"]
