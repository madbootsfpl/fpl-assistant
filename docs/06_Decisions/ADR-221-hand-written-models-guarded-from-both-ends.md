# ADR-221 — Hand-written Dart models, guarded from both ends

**Date:** 2026-09-21
**Status:** Accepted
**Amends:** `Mobile_Platform_Audit.md` §5 (*"generate from the OpenAPI schema FastAPI already emits"*)
**Builds on:** ADR-219, ADR-220

---

## Context

The audit planned to generate the Flutter client's models from FastAPI's OpenAPI schema: *"one contract, no
hand-written duplicates."* Checked against the schema the service actually emits, rather than assumed:

```
POST /api/v1/squad/analysis   request=SquadBody   response={"additionalProperties": true, "type": "object"}
```

Every route is typed `-> dict`. **Requests are fully typed; every response is an untyped bag.** A generator
would emit six request models and `Map<String, dynamic>` for every response — so the response models get
hand-written anyway, which is the duplication the plan existed to prevent.

⭐ *The plan named a mechanism, and the mechanism was never checked against the thing it was meant to
operate on.*

## Options

| option | cost | what it buys |
|---|---|---|
| **Type the responses** with Pydantic models | a day, and **two definitions of every answer** — the dict the engine builds and the model describing it | real codegen |
| **Hand-write, unguarded** | hours | nothing keeps client and server in step |
| **Hand-write, guarded from both ends** ← chosen | hours | drift fails in CI rather than on a phone |

⚠️ **The first option is not merely expensive, it is the failure this codebase keeps writing ADRs about.**
`analyse_squad` returns twelve keys of nested player dicts; a Pydantic model describing it is a second
statement of the same shape, free to drift from the first. ADRs 123, 127 and 181 are each an instance of one
rule having two implementations — and ADR-219 and ADR-220 both exist because a *contract* grew a second
version of a fact.

⭐ Typing six nested responses before a single screen exists also optimises a problem nobody has measured.

## Decision

**Hand-write the Dart models, and pin the contract from both ends.**

```
      the server                    the samples                    the client
  src/service/answers.py  ──1──▶  api-samples/*.json  ──2──▶  lib/api/models.dart
```

1. **`tests/test_api_contract.py`** regenerates every endpoint's response and compares its **shape** —
   keys and types — against the committed sample. ⭐ *Shape, never values*: the seed is refreshed
   constantly, so asserting `projected_xp == 258.9` would fail on every data update and train everyone to
   regenerate without reading the diff.
2. **`test/api_models_test.dart`** parses those same committed samples through the real classes.

⚠️ **Neither half is sufficient.** The Python test stays green while a Dart model reads the wrong key; a
Dart test against a hand-made fixture stays green while the server changes underneath it. ⭐ *The samples
are the only thing both ends can be wrong about together, which is why they are the artefact and not a
convenience.*

Verified by breaking the shape guard four ways — a field disappearing, changing type, a nested key
vanishing, a nullable becoming non-null — and confirming it ignores value churn.

---

## What writing the models found

### ⭐⭐ The API returns four different player shapes

Found immediately, by parsing the real payloads rather than reading the server:

| where | keys |
|---|---|
| `analysis` — xi · bench · issues · weakest · top_pick | **11**, curated |
| `transfers.moves[].in` / `.out` | **5–6** |
| `route.target` | **6** |
| `route.blocked[].out`, `build.selected[]` | **42–45 raw database columns** |

Consequences, in order of how much they matter:

* **`build` ships 45 columns per player to a phone** — `cbi`, `corners_order`, `cost_change_event`,
  `creativity`. That is a 16.3 KB response where a curated one would be ~3 KB, on the client whose entire
  architecture was justified by measuring payload (spike 017).
* ⚠️ **It makes the database schema part of the API contract.** Rename a column and the mobile app's
  response changes, with nothing in between to notice.
* **`transfers.moves[].in` carries no `position`**, so a transfer card cannot show a position chip without
  a second lookup. (`out` carries `leaving` and `in` does not — that one is *correct*: only a player you
  hold can be reported as leaving.)

🔴 **Recommendation: normalise every endpoint on the curated summary.** Not done tonight — it changes three
endpoints' responses, and a contract change deserves its own agreement rather than being folded into a
models task at the end of a session. The models describe what is actually on the wire today, because ⭐ *a
model that flatters the contract is how a client discovers the truth at runtime.*

### The models are not speculative

`dart analyze` clean, and **14 Dart tests pass against the real committed responses**. What they pin is
mostly what a client would otherwise get wrong:

* ⚠️ **Gameweek keys arrive as strings and are parsed to `int` once**, at the boundary. Sorted as text
  `"10"` precedes `"6"`, so a prefix sum over *the next two gameweeks* answers for the wrong two.
* **Availability is three separate facts** — `status`, `chance` and `leaving` — and none is derivable from
  the others. ADR-206 priced every doubt at zero by reading a flag as a verdict; ADR-155 found FPL
  reporting an agreed transfer as fully available.
* **`coordinated`** distinguishes a plan whose gains add up from a menu of alternatives that double-count
  the same bank (ADR-191).
* **`status` on a build** is the solver's own word: `Infeasible` means *nothing fits these constraints*,
  which is an answer. A client that ignored it renders an empty pitch with no reason.

---

## Consequences

**Good:** the morning starts with compiling, tested models and a client; drift is caught in CI; no second
definition of any answer was created.

**Costs:** ⚠️ **the Dart half runs locally and not in CI** — CI is ruff + pytest, and Flutter is not
installed there. ⭐ *A test nobody runs is not a guard*, so wiring `flutter test` into the workflow belongs
with creating the real app, and until then the Python shape guard is the one that actually gates a commit.

**Open:** normalising the four player shapes (above). Revisit typed responses if the models ever disagree
with the server in a way the shape test did not catch — that would be evidence this decision was wrong, and
there is currently none.
