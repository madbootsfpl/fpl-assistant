# ADR-233 — A fix scoped to where it was noticed

**Date:** 2026-09-22
**Status:** Accepted

---

## What the owner saw

```
ClientException with SocketException: Connection refused (OS Error: Connection refused,
errno = 61), address = localhost, port = 49421, uri=http://localhost:8078/api/v1/squad/gameweek-plan
```

The API server had stopped. That is not the interesting part.

## ⭐⭐ The interesting part: a good message for exactly this already existed

`main.dart` said, on the **landing screen only**:

> *The service is not answering on http://localhost:8078.*
> *Start it with: `venv/bin/python -m uvicorn src.service.http:app --port 8078`*

Six other screens rendered `'${snapshot.error}'` — the raw Dart object, errno and all.

⭐ **A fix scoped to where it was noticed is a fix the next screen does not get.** The message was written
when the landing screen was the *only* screen. Five more arrived over the following hours, each inheriting
nothing, and the failure surfaced on **This week** rather than where the handling lived.

This is the same shape as ADR-229's finding a few hours earlier — *a guard covers the surfaces it was
pointed at* — and ADR-155's, where one fact needed re-teaching to six surfaces. ⚠️ **Three instances in one
day of "solved in the place it was seen".**

## Decision

**The message moved into the client**, which is the only thing that knows the base URL *and* what a refused
socket means. `_post` now translates a refused connection into `ApiException(0, …)`, and every screen
renders `friendlyError(...)`.

⭐ One string, one place, and the health check on the landing screen — which existed only to produce that
message — is gone with it.

### ⚠️ Two ways a refused connection arrives

On macOS and iOS it is a `SocketException`. **On web there is no such thing** — `package:http` raises a
`ClientException`. Catching only the first would have left **Chrome** showing exactly the raw text this
replaces, on the one target `flutter doctor` reports as always available.

⭐ *The platform the fix was tested on is not the platform the fix has to work on.*

### `healthy()` no longer throws

⚠️ A health check that raises takes down the screen it was meant to protect. It answers `false`.

---

## Verification

* **`tests/test_app_error_messages.py`** sweeps every Dart file for a rendered raw exception — ⚠️ in the
  **Python** suite, because the Dart suite does not run in CI (ADR-221), *and a guard that matters has to
  sit in the one that does*.
* It also pins that the message names **the address and the command**: ⭐ *"cannot connect"* without either
  tells a reader only that they are stuck.
* **3/3 regressions caught**: a screen reverting to `${snapshot.error}`, the web exception no longer being
  caught, and the command dropping out of the message.
* A Dart test hits **port 1** — a real refused connection, not a stub — and asserts the message contains
  the address and `uvicorn` and **does not contain `errno`**.

## Consequences

**Good:** every screen fails the same way, and the failure tells you how to fix it. One message, one place.

**Costs:** none worth naming — this removed code.

**Open:** ⚠️ the same reasoning applies to *any* error a screen can show, not just an unreachable server. A
400 from a squad the engine refuses now reads well; a 500 would still surface a stack. The sweep covers the
rendering, not the classification.
