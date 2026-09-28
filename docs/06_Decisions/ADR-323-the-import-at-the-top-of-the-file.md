# ADR-323 — The import at the top of the file

**Date:** 2026-09-28
**Status:** Accepted
**Overturns:** `requirements-pipeline.txt`'s own note — *"Removing that dependency would mean moving `deadline.py` out of the analytics package, which is a bigger change than this is worth"*
**Follows:** ADR-322 (which recorded this as open), ADR-310 (the PuLP pin)

---

## Context

`src/analytics/optimizer.py` began with `import pulp` at module scope. `src/analytics/__init__.py` re-exports
from it (line 64). Python initialises a package before any of its submodules, so **anything that touched
`src.analytics` at all loaded an integer-programming solver** — including `app.py pipeline`, which goes
`src.cli` → `src.analytics` and never solves anything.

Both deploy files carried the consequence, and both wrote it down as a fact of life:

* `requirements-pipeline.txt`: *"`pulp` stays, and it is not optional … Dropping it fails at import, not at
  use — measured, not assumed. Removing that dependency would mean moving `deadline.py` out of the analytics
  package, which is a bigger change than this is worth."*
* `requirements-api.txt`: *"`src.analytics.__init__` imports the optimiser, so dropping it fails at
  **import**, not at use — the same trap the pipeline's file records."*

⭐ **The observation was exactly right and the conclusion was wrong.** Dropping the *package* would indeed
have meant moving `deadline.py`. But the coupling was never the package layout — it was one line at the top
of one file.

**Every `pulp` reference in the package is inside a single function.** Thirteen call sites, all between
`optimizer.py:190` and `:278`, all within `select_squad` (147–303). The other solver-adjacent helpers —
`best_xi_points`, `best_legal_xi`, `bench_order` — sort; they do not solve.

⭐⭐ *An import at the top of a file is a dependency for every caller of every function in it.* The note
searched the package for the problem and the problem was in the file it was describing.

📏 **Measured, because the old note guessed.** PuLP 3.3.2 is **16 MB to download, 36 MB installed** — 34 MB of
that the bundled CBC binaries in `pulp/solverdir`. ⚠️ Both files claimed **71 MB** with nothing recorded about
where it came from; that is roughly double. The wheel is `py3-none-any`, so the figure is the same on the
runner as locally. ⭐ *A saving worth making is worth measuring — an inflated one invites the next reader to
re-check it and distrust the whole note.*

## Decision

**Move `import pulp` inside `select_squad`.** Two lines, and it mirrors a pattern already in the codebase:
`src/db.py:120` — `import psycopg  # imported here so the CLI runs without it installed`.

```
before   optimizer.py: import pulp  (module scope)  ->  every importer of src.analytics needs PuLP
after    optimizer.py: import pulp  (inside select_squad)  ->  only callers that actually solve need it
```

The repeated import costs nothing after the first call — it is a `sys.modules` lookup.

### Where the solver is installed now

| file | solver? | why |
|---|---|---|
| `requirements.txt` | ✅ | the app runs squad builds in-process |
| `requirements-api.txt` | ✅ | `squad/build` calls `select_squad` |
| `requirements-pipeline.txt` | 🚫 **removed** | nothing on the pipeline's path reaches it |

⚠️ **`requirements-api.txt` keeps PuLP, but its stated reason was corrected.** It said dropping PuLP *"fails
at import"*; that is no longer true — the API imports fine without it. It stays because the service **calls**
the solver. ⭐⭐ *The dependency is now where the work is, rather than wherever the import graph happened to
reach.*

### Proved, not assumed — in both directions

The claim "the pipeline does not need PuLP" is verified by making PuLP **unimportable** (a `sys.meta_path`
blocker) and then importing `src.cli`, `src.pipeline`, `src.ingest` and `src.analytics`, and parsing
`app.py pipeline`. All succeed; `pulp` never enters `sys.modules`; `src.analytics.select_squad` is still
re-exported and still solves (136 optimiser tests pass).

**The standing guard reuses a mechanism that already existed** rather than adding one: `pulp` joined the
`banned` tuple in `test_pipeline.py::test_the_scheduled_command_imports_nothing_it_does_not_install`, which
walks the import graph the command actually walks — and which already carries the lesson *"a guard on an
import graph has to walk the graph the command actually walks."* ⭐ *The test that proved the fix is the test
that prevents its regression.*

`test_deploy_pins.py` now asserts **both** directions, because the two failures are opposite and a test for
one hides the other:

* a **missing pin** is a deploy that installs PuLP 4 and stops solving (ADR-310);
* a **reappearing `pulp`** in the pipeline's file is 16 MB downloaded 24× a day for an import that no longer
  happens.

Which files should hold the solver is now **data** (`SOLVER_FILES`), so *"should this file have PuLP?"* has
one answer in one place.

⚠️ One test had to be narrowed on the way: the absence check first read the whole requirements file as text
and matched the word `pulp` **in the comment explaining its removal**. ⭐ *A test that greps a file with
comments in it is testing the comments.* It now parses package lines.

Verified by two mutations: putting `pulp` back in `requirements-pipeline.txt` (2 failures), and returning
`import pulp` to module scope in `optimizer.py` (1 failure, the import-graph guard).

## Consequences

**Good:** the scheduled pipeline stops installing a solver 24× a day — 16 MB of download and 36 MB on disk
per cold run. The dependency now sits where the work is, and both directions of that are guarded. A stale,
unsourced 71 MB figure is replaced with a measured one in both files.

**Costs:** effectively none. One function-local import, and a repeated `sys.modules` lookup on each
`select_squad` call.

⭐⭐ **The lesson is the one ADR-322 named, arriving a fourth time: the work was already written down, with
the wrong estimate attached.** *"A bigger change than this is worth"* closed the question for months, and the
change was two lines. ⚠️ *An estimate recorded next to a decision outlives the reasoning behind it, and gets
re-read as a finding.*

**Open, unchanged:** `src/ask.py` (2409 lines) and `src/service/answers.py` (2368) against *"keep modules
small"*; sprint records stopping at Sprint270; `docs/01_Journal/` last written 2026-08-05; 7.0 MB of markdown
against 1.8 MB of Python, with a 498 KB ADR index.
