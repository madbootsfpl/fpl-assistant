# ADR-292 — More than half the deploys changed nothing

**Date:** 2026-09-25
**Status:** Accepted — ✅ **applied on Render, 2026-09-25**
**From:** the owner — *"sort the Render build filter next"*
**Follows:** ADR-288, which found this while measuring something else

---

## The measurement

Render redeploys on **every push to master**, and a redeploy is a window with nothing serving. Over the
last **120 commits**:

| | |
|---|---|
| deploys today | **120** |
| deploys that changed something in the image | **52** |
| redeploys for nothing | **68 — 57%** |

⚠️⚠️ *Every one of those was a window in which a tester could open the app and be told it was broken* —
and two of them were, on the evening ADR-288 was written.

📌 **57%, not the 83% ADR-288 reported.** That figure came from a twelve-commit evening of documentation
work. ⭐ *A sample chosen because it was in front of you is a sample chosen to agree with you*, and the
longer window is the number worth acting on — it is still more than half.

## The filter, derived rather than guessed

The image copies four things, and two more decide what it copies:

```
Dockerfile              ← changes what is built
.dockerignore           ← changes what is included
requirements-api.txt
pyproject.toml
src/**
```

and ignores the one directory under `src/` that the image explicitly drops:

```
src/web_streamlit/**
```

⭐ That second list is not an optimisation. `.dockerignore` removes `src/web_streamlit/` from the image,
so a commit touching only the Streamlit app **cannot** change the API — ⚠️ *and it is the directory this
project changes most often after `mobile/`.*

## ⚠️⚠️ Why this is a test and not a comment

The failure mode is **silence**. If the Dockerfile starts copying a directory the filter does not list,
Render stops redeploying when that directory changes, and the service keeps serving the old code while
the repo says otherwise. Nothing errors; nothing is slow; the API is simply wrong.

⭐ *A deploy filter that has drifted from the build is worse than no filter, because no filter at least
always deploys.*

So `tests/test_build_filter.py` reads the **Dockerfile's own `COPY` lines** and fails if the documented
list stops covering them. It also fails if the list grows to include `mobile/`, `docs/` or `tests/` —
⭐ *a filter that lists the repo is a filter that has been quietly given up on.*

5/5 mutations killed: a new `COPY` the filter misses, the recipe files dropping out, the list growing to
cover the app, the image no longer excluding Streamlit, and the ignored list being emptied.

## ✅ Applied, and verified by pushing this file

The owner set it, and **this commit is the test**: a docs-only change, watched against `/health` every
four seconds across the push.

```
polled 55 times over 4 minutes — failures: 0
```

⭐ *The measurement that proves a deploy filter works is a push that does not deploy* — and before this,
every push triggered a rebuild by definition.

⚠️ **This is strong evidence, not proof.** A four-second poll could in principle step over a very short
restart. ⭐ *The definitive check is the one I cannot run*: Render → `madboots-api` → **Events**, which
either lists a deploy for this commit or does not.

## ⚠️ What is not done

**Nothing on the dashboard.** ⚠️ *A setting applied by hand is a setting that exists in one place and is
recorded in none* — if the service is ever recreated, the two lists above are what has to be typed back
in, and `tests/test_build_filter.py` keeps them honest in the meantime.

📌 **Not moved into `render.yaml`.** This service was created in the dashboard and is not
blueprint-managed; adding one would change how the service is *defined*, which is a larger decision than
a filter and would want its own ADR.

📌 **This does not make deploys zero-downtime.** It makes them **rarer**. The remaining 52 are real
changes that genuinely need shipping, and each still has a gap — ⭐ *the honest description of this change
is "less often", not "fixed".*
