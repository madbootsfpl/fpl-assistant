# ADR-261 — The tests ran somewhere the bug could not exist

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner, using the hosted app — *"Tell us Something ← Get a 'Not Sent - FormatException:
Unexpected character (at character 1) Internal Server Error'"*
**Fixes:** ADR-231 (feedback relay), ADR-250 (the API image)

---

## What happened

Every feedback submission from the phone answered **HTTP 500**, and the app reported the JSON parser's
complaint *about* the error in place of the error.

Two independent faults, stacked so that the second hid the first.

### 1. The API imported a module its own image excludes

`service/answers.py` reached for `relay_result` from `src.web_streamlit`. ⚠️ `.dockerignore` excludes that
package — deliberately, since ADR-250: Streamlit's stack is **247 MB of the 481 MB** the API does not need.

The import sat **inside the function**, so nothing failed at start-up: `/health` stayed green and every
other endpoint worked. Only the feedback path touched it, and only in the container.

⭐⭐⭐ **The whole suite was green, because the tests ran somewhere the bug could not exist.** A developer
checkout contains `web_streamlit/`; the deployed image does not. ⚠️ *A function being pure is not the same
as a function being reachable* — `relay_result` never touched Streamlit, and was still unimportable from
the one place that mattered.

### 2. The client assumed every error body is JSON

`_post` decoded the body of any non-200. Its comment reasoned carefully about FastAPI's 422 (a list) and
400 (a string) — ⭐ *both of which FastAPI generates as JSON*. An **unhandled** exception does not come
from FastAPI at all; it comes from Starlette as the plain text `Internal Server Error`. Decoding that threw
a `FormatException` that escaped the client entirely, never becoming an `ApiException`.

⭐ **So the reader was handed the parser's complaint about the error instead of the error.** A proxy or a
cold host answering HTML would have done exactly the same thing.

## Decisions

**1. `relay_result` moves to `src/relay.py`** — outside both edges, importable by either.

**2. The client describes a body it cannot parse, instead of parsing it.** `errorDetail(status, body)` is
pure and directly tested. A failed decode is now an **expected outcome, not an exception**. ⚠️ A 5xx is
named as **ours** and the body is deliberately *not* repeated: *"Internal Server Error"* tells a tester
nothing they can act on and reads as though they broke it.

**3. ⭐⭐ The guardrail that should have caught this is now self-maintaining.**

`test_core_never_imports_a_web_edge` already existed, was AST-exact, and had itself been mutation-tested
after two earlier repairs. It missed this anyway — because `_CORE` is a **hand-written list**, and
`src/service` had never been added to it. ⭐ *A guardrail is only as wide as its list, and a
hand-maintained list does not grow when the codebase does.*

So a second test asserts that **every** top-level module under `src/` is either an edge or covered by the
rule. ⚠️ Running it the first time found **eight more** uncovered modules — including `kits.py` and
`glossary.py`, which had been *moved out* of the Streamlit package for this very reason and then left with
nothing to stop them sliding back. A new package now fails on the day it is created.

**4. The feature is tested with the package genuinely absent** — both branches, because ⚠️ *the failing
import sat past the early return*, so a test hitting only the unconfigured path would still have missed it.

## 3. And with the 500 gone, feedback still would not have arrived

⚠️ Fixing the crash exposed the next layer: `FPL_FEEDBACK_WEBHOOK` is not in the hosting runbook. It was
written up in `docs/BETA.md` as a **Streamlit secret** and never carried across to the host, so *Tell us
something* could not have worked on the live build no matter what else was right.

⭐ **A variable documented for one deployment is not documented for the next one.** And this failure is
**silent by design** — the endpoint answers honestly (*"no feedback sink is configured"*) and the note is
still never delivered.

So the runbook now carries a table of every variable the API reads and **what its absence costs**, and
`tests/test_hosting_doc.py` derives that list from the code rather than trusting it: a new `os.environ.get`
in the service layer fails on the day it is written. ⚠️ A second test asserts the webhook row says what is
*lost*, because a row reading merely *"optional"* would leave the runbook technically complete and
practically wrong.

📌 **Still to do, and it is the owner's to do:** set `FPL_FEEDBACK_WEBHOOK` in Render. It is his secret and
it does not belong in this repo.

## Consequences

📌 **The lesson generalises past this bug.** Everything the container does differently from a checkout is
untested by default, and the excluded package is only the visible half. ✅ The static guard stops the
import being written; the absence tests prove the feature survives without it.

## Verification

* **Reproduced first** against the live API — HTTP 500, body `Internal Server Error`, byte for byte the
  string the phone failed to parse.
* **9 new Dart tests**, 4/4 mutations killed (blind decode restored, body echoed, truncation dropped,
  5xx branch disabled).
* **2 new Python tests** with `src.web_streamlit` made unimportable; both confirmed to **fail against the
  original import** and pass against the fix.
* **1 new layering test**; the widened rule confirmed to catch the original offender.
* 2,475 Python · 123 Dart.
