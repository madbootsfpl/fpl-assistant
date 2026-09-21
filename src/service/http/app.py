"""`POST /api/v1/squad/*` — the squad-shaped questions, over HTTP (mobile audit §4.2).

⚠️ **Separate from `src/web`, deliberately.** That is ADR-050's read-only HTML edge, which renders text
into a `<pre>` block for a browser. This returns JSON for a client that draws its own screens. Sharing an
app object would make one of them the other's constraint.

⭐ **No auth, and that is a fact about these endpoints rather than an omission.** Every one takes *player
ids in, analysis out* — there is no user row to protect. Owner-scoped data (your saved squad, your
preferences) is Stage C and is not served from here.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.service import SquadRequest, analysis

app = FastAPI(
    title="MADBOOTS service",
    version="1",
    # The interactive docs are the contract a client author reads first, so they stay on.
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)


class SquadBody(BaseModel):
    """What a client posts.

    ⭐ Ids, not rows (audit §4.2). A client that uploaded player rows would be defining the engine's input,
    which is how one rule becomes two implementations.
    """

    player_ids: list[int] = Field(..., min_length=1, description="The squad's players, by FPL element id.")
    bench_ids: list[int] = Field(default_factory=list,
                                 description="Optional. Omit and the best legal XI is derived.")
    horizon: int = Field(5, ge=1, le=8, description="Gameweeks to look ahead.")


@app.get("/api/v1/health")
def health() -> dict:
    """Is the service up? Deliberately does not touch the database — a health check that fails when the
    database is slow tells you about the database, not the service."""
    return {"ok": True}


@app.post("/api/v1/squad/analysis")
def squad_analysis(body: SquadBody) -> dict:
    """A squad's health over the horizon: projected XI xP, the bench, weak links, club concentration.

    ⚠️ **`by_gameweek` arrives keyed by gameweek as a STRING**, because JSON has no integer object keys —
    the same shape PostgREST already serves for the published board, so a client that reads one reads the
    other. ⭐ *Parse them to integers before sorting.* As text, `"10"` sorts before `"6"`, so a prefix sum
    over "the next two gameweeks" would quietly answer for the wrong two. Pair them with `gameweeks`, which
    is returned in order.
    """
    try:
        return analysis(SquadRequest(player_ids=body.player_ids,
                                     bench_ids=body.bench_ids,
                                     horizon=body.horizon))
    except ValueError as exc:
        # ⭐ A bad squad is the caller's mistake, not a server fault — 400, with the reason. Returning 500
        # would tell a client author to retry something that will never work.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
