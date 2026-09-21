"""The contract layer — what a client asks for, and what it gets back.

⭐⭐ **One contract, two transports.** The mobile audit §4.2 proposed that Streamlit migrate onto the HTTP
API so the contract has a real consumer before Flutter exists — *"a contract with one consumer is a guess."*
The principle is right and the mechanism would have made the web app slower, trading in-process calls for a
round trip to a separately-hosted service, on the app a whole day was spent speeding up.

So the contract lives here as **plain functions over plain dicts**. FastAPI is a thin HTTP wrapper over
these; Streamlit imports them directly. Both consumers exercise the same shapes, and only one pays for a
network.

⚠️ **Nothing here computes football.** Every function assembles inputs, calls the same engine the CLI calls,
and shapes the answer — ADR-181's rule, on a new surface. A number that appears here and nowhere else is a
second implementation.
"""

from src.service.squad import SquadRequest, analysis

__all__ = ["SquadRequest", "analysis"]
