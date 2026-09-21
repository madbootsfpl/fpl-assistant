# ADR-219 — One contract, two transports

**Date:** 2026-09-21
**Status:** Accepted
**Implements:** `docs/03_Architecture/Mobile_Platform_Audit.md` §4.2 (Phase 3)
**Amends:** the audit's proposal that Streamlit migrate onto the HTTP API

---

## Context

Phase 1 established that a Flutter client can read the published board straight from Supabase (667 players,
162 KB, 511 ms — verified on the owner's network). That covers the **read** surface: tables, boards,
browsing.

It does not cover the **questions**. *"How does my squad look over the next five gameweeks?"* is not a
row you can select — it is `decision_xp` over the whole league, a best-legal-XI search, and a dozen
availability rules. A phone cannot run that, and the audit was explicit that it must not try: the moment a
client computes its own xP there are two implementations of one rule, which is what ADRs 123, 127 and 181
are each about.

So Phase 3 is an API. The audit proposed FastAPI, and further proposed that **Streamlit migrate onto it**,
with a reason worth quoting: *"a contract with one consumer is a guess."*

## The problem with the proposal as written

⭐⭐ **The principle is right and the mechanism would have made the web app slower.** Streamlit and the
service would be separately hosted, so every squad analysis the web app renders becomes a network round
trip — on an app where **an entire day** had just been spent removing round trips and payload (spike 017:
warm path 3,026 ms → 20 ms, cold path 2.41 MB → 0.81 MB).

⚠️ *The audit's reasoning was about coupling, and the cost it ignored was latency.* Both are real; only one
had been measured.

## Decision

**The contract is a Python module, not an HTTP endpoint.** `src/service/` holds plain functions over plain
dicts. FastAPI is a thin wrapper over them for Flutter; Streamlit imports them directly.

```
                 ┌─ src/service/http/  ──HTTP/JSON──→  Flutter
src/service/ ────┤
                 └─ import            ──in-process──→  Streamlit
```

Both consumers exercise the same functions over the same rows. Only one pays for a network.

### What keeps them honest

The thing the audit's version got for free — *you cannot diverge from an endpoint you call* — has to be
bought back with a test. `test_the_two_transports_return_the_same_answer` asserts the HTTP body equals the
in-process answer **serialised**:

```python
assert over_http == json.loads(json.dumps(in_process))
```

⭐ Encoding differences are forgiven by construction; everything else fails. A field the wrapper drops,
rounds, renames or recomputes breaks it.

### The first endpoint, and only the first

`POST /api/v1/squad/analysis` — one, end to end, rather than six at once. Same discipline as ADR-213: prove
the shape on one and the rest are mechanical. The other five (transfers, captain, gameweek plan, route,
build) wait until this one has a real consumer, which it now has.

---

## What building it found

### 1. The contract was missing a fact the web app has had since August

`render_health` passed `reported_out=` to `analyse_squad`. The service did not — so on the identical squad,
**the phone would have recommended captaining a player the web app already knows has agreed a move**.

⭐ It reaches further than the issues list: `analyse_squad` drops a reported leaver from the *captainable*
set, so the omission changes the headline recommendation, not a footnote.

⭐⭐ **ADR-151→156 is the record of this exact fact being taught to six surfaces one at a time, every gap
found by the owner using the product.** The seventh surface would have been a phone. It now lives in
`src/service/squad._reported_leavers`, which is the layer both transports share.

### 2. A departure is now read off the analysis, not derived beside it

Health's player table computed its own `leaving` set next to the analysis that already had one. Two lookups
of one fact on one page is how a page comes to contradict itself — ADR-156's lesson, one line along. The
table now reads `p["leaving"]` from the contract.

### 3. Wiring Streamlit naively would have undone spike 017

`analysis()` opens its own `Storage()` when not given one, so calling it from a view would refetch the board
on **every rerun** — the 3,026 ms the cache exists to remove, reintroduced by the refactor meant to share
code.

⭐ Fixed without adding a parameter: `dataload.CachedStore` is a duck-typed store whose six read methods
return `st.cache_data` results. The alternative — an extra `rows=` argument so Streamlit could hand its
cached data in — would have given the two transports **two code paths**, which is the divergence the
contract exists to prevent.

### 4. The guard that fired was the one written for exactly this

Moving the departure question broke `test_health_shows_a_reported_departure…` with *"the stub was never
called — Health is not asking the question at all"*. ⭐ That is the assertion doing precisely its job: the
question had moved, not vanished, and nothing else would have said so. Its seam moved down to
`headlines.leavers` — the function that actually answers *who is leaving*, which both paths route through —
so the next surface to adopt the contract does not break it again.

### 5. JSON has no integer object keys

`by_gameweek` is keyed by real gameweek number and crosses the wire as `{"6": …}`.

⚠️ **This is not cosmetic.** Sorted as text, `"10"` precedes `"6"`, so a prefix sum for *"the next two
gameweeks"* would quietly answer for the wrong two. The Flutter slice already parses to `Map<int, double>`
before sorting — against **PostgREST serving this same column**, so the shape is established rather than
new. It is now stated in the endpoint's OpenAPI description and pinned by a test.

### 6. Stale ids: named for a client, filtered for a view

The service refuses an unknown player id by name rather than dropping it — *a squad quietly analysed as
fourteen players is a wrong answer wearing the shape of a right one.* But a saved squad holding someone who
has left the league must still render, so the view filters before asking. ⭐ **The tolerance is the view's
policy, stated where it is applied**, rather than a leniency baked into the contract for everyone.

---

## Verification

* **28 tests**, all 21 mutations killed.
* ⚠️ One mutation initially reported **NOT APPLIED** rather than passing — a stale pattern in the harness.
  *The same false-confidence failure this project has hit before; the harness asserts application now.*
* ⚠️ One mutation **survived**: swapping the league for the squad when sizing ADR-210's exodus threshold.
  Every test stubbed `leavers` wholesale and never reached the argument — so a tenth of *fifteen* would have
  manufactured a departure rumour every week, and it would have looked like a working feature. Now pinned.
* The old `render_health` path and the new one were compared field-for-field on a real squad: **identical**.
* ⚠️ The seed contains **zero** reported leavers, so §1's case was **constructed, not sampled** — this
  codebase has four root causes of a fixture that could not reach the fault it was meant to guard.

## Consequences

**Good:** one implementation of each question; Health now reads the published board and the cache rather
than recomputing from history; the departure fact reaches every future surface by default; the contract has
a real consumer before Flutter exists.

**Costs:** a test now carries what the audit's design enforced structurally. `src/service/` is a layer the
CLI does not use — ⚠️ *it must never become the place a rule lives*, or the CLI and the API become the two
implementations this was built to avoid.

**Open:** the remaining five endpoints; authentication for owner-scoped data (Stage C) — these endpoints
take ids in and analysis out, so there is no user row to protect, but a saved squad is a different question.
