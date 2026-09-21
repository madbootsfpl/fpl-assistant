# ADR-220 — The fix reached the engine and not its callers

**Date:** 2026-09-21
**Status:** Accepted
**Completes:** ADR-219 (Phase 3 — the remaining five squad endpoints)
**Repairs the reach of:** ADR-209

---

## Context

ADR-219 built one endpoint and held the other five *"until the first proved its shape."* It has, so this
builds them: `transfers`, `captain`, `gameweek-plan`, `route`, `build`.

The five were expected to be mechanical. They were not — replicating a recipe five times meant reading how
each engine function is *actually* called, and that reading found ADR-209 had been shipped into the engine
and threaded through only some of its callers.

---

## Part 1 — The five endpoints

| endpoint | engine | reads |
|---|---|---|
| `POST /api/v1/squad/transfers` | `suggest_transfers` / `suggest_transfer_plan` | the published board |
| `POST /api/v1/squad/captain` | `captain_picks` | ⚠️ the raw history — see below |
| `POST /api/v1/squad/gameweek-plan` | `gameweek_plan` | the raw history |
| `POST /api/v1/squad/route` | `route_to_player` (ADR-207) | the published board |
| `POST /api/v1/squad/build` | `select_squad` (PuLP) | the published board |

**`src/service/` grew three modules** rather than six copies of an assembly: `requests.py` (the DTOs and
their validation), `inputs.py` (one loader), `answers.py` (the six questions). ⭐ Six endpoints each
assembling their own inputs is ADR-181's failure with six chances to happen.

### Loading is opt-in per dataset, and that is a cost decision

`history` + `gw_history` are 1.9 MB — roughly eight of a cold load's eleven seconds (spike 017). Transfers,
routes and build rank on the published board instead (ADR-218).

⚠️ **Captain cannot.** `captain_picks` reprices at horizon 1 through `player_xp`; reading a stored
multi-gameweek total instead would be a second recipe for the same number, which is the drift ADR-041
exists to prevent. ⭐ *The cheaper path is only cheaper if it answers the same question.*

---

## Part 2 — What replicating the recipe found

### ⭐⭐⭐ ADR-209 had reached the engine and four of its ten call sites

ADR-209 established two things about ranking transfers:

1. **`window`** — how many gameweeks the xP map covers. It sizes the tie-break band, and **defaults to
   five**. On a one-gameweek map the band should be 0.89 and was 2.0.
2. **`horizon_xp`** — a wider map, so a near-tie can be broken on what the move is worth over five
   gameweeks rather than one. This is the half that moves expected points: the owner's week offered two
   moves at +1.2 apiece, and the app took the one worth **−1.5 over five gameweeks** over the one worth
   **+3.1**.

Both are **optional arguments**. A caller that omits them gets no error: the ranking returns, and simply
names a different player.

**Six of ten production call sites omitted them:**

| where | what it ranks | consequence |
|---|---|---|
| **Streamlit Transfer tab** ×3 | **horizon 1** under My Squad | band more than twice too wide; the longer view never consulted |
| **`cli.py cmd_transfer`** ×2 | `--next`, manager's choice | same, whenever `--next < 5` |
| **`gameweek.py`'s rival plan** | the wide map | default happened to be right — by coincidence, and unwritten |

🔬 **Measured before claiming.** On 120 random legal squads at horizon 1, **89 got a different top
recommendation** with the arguments supplied than without.

⚠️ **What that number is not.** Grading those 89 on the five-gameweek map would be partly circular — the
tie-break optimises that very map, so it would be scoring its own arithmetic (ADR-202's lesson). The
defensible claim is **divergence**: on most squads the app named a different player. *Which* player is
right is what ADR-209 already decided; the Transfer tab simply never received the decision.

⭐⭐ **The shape is ADR-212's, one level down.** That was documentation describing a system that had changed
underneath it. This is a *fix* describing a call convention that most callers never adopted. Both are a
correction scoped to what was visible when it was made.

### The guard sweeps for the claim

⚠️ **Fixing six call sites fixes today.** Two earlier guards in this project each checked the same two
files, and a retired claim survived on six surfaces for fourteen days (ADR-184). So the guard is a sweep:
**every** `suggest_transfers` / `suggest_transfer_plan` call in `src/` must state `window` and `horizon_xp`.

⭐ **Not by making the arguments required**, which was the first instinct. That would have churned 35 engine
tests which legitimately rank at the default window, for no gain in the thing being protected — the
*callers*.

Writing the sweep was itself instructive:

* ⚠️ The first version reported a call site inside a **comment** (`gameweek.py` explains a past decision
  with the words *"this used to call `suggest_transfers(limit=2)`"*). ⭐ *The paragraphs that warn about a
  pattern contain the pattern* — ADR-178, again.
* ⚠️ Three call sites legitimately pass the arguments via a `**splat` of a dict built once. Widening the
  check to *the enclosing function* made those pass — **and made the guard blind to a single call dropping
  the splat**, because the dict was still in scope. ⭐⭐ **I only found that by breaking the guard after
  improving it**: it had just reported three call sites clean that were not. *A guard you have improved is
  exactly the guard you have to re-break.*
* The final form reads each call's own arguments and resolves a splat to wherever the dict is defined —
  including at module level, which is where `ask.py` keeps its. ⭐ *A guard that follows only the
  indirection you happened to write is a guard against yourself.*
* ⚠️ The exemption count is pinned, because a skip is invisible in a green run (ADR-178). ⭐ And pinned by
  **measuring** it: the first version asserted 2, having read "2 skipped" off the summary — which was one
  exempt call site counted once per test.

### Smaller findings

* **`route_to_player` never received `reported_out`.** The CLI has never passed it, so a manager could be
  routed *through* a player the rest of the app knows is leaving — ADR-155's species, one function along.
  The endpoint passes it.
* ⚠️ **My own `route` endpoint appended the target to the squad's ids** so one check could name an unknown
  id. That made an already-owned target look like a sixteenth player and **deleted `route_to_player`'s
  "you already own him" answer** — caught by a test, not by review.
* **`build` needed its own request shape.** It is the one question with no `player_ids`; making it inherit
  `SquadRequest` would have forced a meaningless empty list on every caller.

---

## Verification

* **75 tests** across the two service files, **30/30 mutations killed**.
* ⚠️ Four mutations survived the first sweep and each named a real gap:
  * *"captain never gets the raw history"* survived **because the seed has no published board** — so
    `want_rows` was true regardless and every assertion passed vacuously. The test now publishes a board so
    the case exists at all. ⭐ *Does the population contain the case?* — the seventh time in this project.
  * *"an unknown target is not checked"* survived because the test sent a bad squad **and** a bad target, so
    the earlier check fired first.
  * *"build ranks on nothing"* survived because every structural assertion — legal shape, within budget,
    fifteen players — **passes against a squad chosen on the wrong objective**.
  * *"captain loses its baselines"* survived because the test asserted the history reached the engine and
    never that the baselines derived from it did.
* ⚠️ One assertion was **hollow**: `wider != seen.get("xp_by_id")` compared against a key that was never
  there, because `xp_by_id` is passed positionally — so it read `wider is not None` wearing the costume of a
  comparison. ⭐ *A hedge is not a weaker assertion; it is the absence of one* (ADR-180).
* Every one of the **ten** call sites was broken individually and the sweep caught all ten.

## Consequences

**Good:** the mobile client can ask every squad question the web app can; one loader means a seventh
endpoint inherits the departure fact, the exodus threshold and the tie-break window by default; six live
call sites now apply a decision made twelve days ago.

**Costs:** `src/service/` is a layer the CLI does not use — ⚠️ *it must never become the place a rule lives*,
or the CLI and the API become the two implementations this was built to avoid. The sweep is a source scan,
with ADR-178's limits: it asserts code was **written**, not that it **runs**.

**Open:** authentication for owner-scoped data (Stage C). These endpoints take ids in and analysis out, so
there is no user row to protect — but a *saved squad* is a different question.
