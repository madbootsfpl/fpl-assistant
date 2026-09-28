# ADR-322 — Three guards that already existed

*The Dart suite nothing ran · the pin that missed the file that ships · the staleness test that exempted its own subject.*

**Date:** 2026-09-28
**Status:** Accepted
**Closes:** ADR-221's deferred action (*"wiring `flutter test` into the workflow belongs with creating the real app"*)
**Completes:** ADR-310's pin, which landed in one requirements file and not the two that build the deploys
**From:** a whole-project health check

---

## Context

Three findings from a repository sweep, all the same kind: **a guard this project had already designed,
sitting one step short of doing anything.** Not one is a new idea — two are written down here already, in
ADR-221 and ADR-310, as things to finish; the third is a test that had been running green all along while
skipping the very line it was written for.

### 1. 29,691 lines of Dart, 481 tests, nothing running them

`mobile/` carries **481 test cases across 45 files**. No workflow in `.github/workflows/` mentions Flutter;
`scripts/release_android.sh` goes from bumping `versionCode` straight to `flutter build apk`, and
`release_ios.sh` straight to `flutter build ios`. So the tests run when somebody remembers, and a release
cannot be stopped by them.

The project already said so, twice, in its own words:

* **ADR-221, Consequences:** *"the Dart half runs locally and not in CI — CI is ruff + pytest, and Flutter
  is not installed there. ⭐ A test nobody runs is not a guard, so wiring `flutter test` into the workflow
  belongs with creating the real app."*
* **`tests/test_brand_dart.py`:** *"This lives in the Python suite on purpose — that is the suite CI runs, so
  it is the one that can actually stop a commit. The Dart side has no equivalent gate yet (ADR-221)."*

⭐ **The condition ADR-221 deferred against has arrived.** The real app exists, is on nine phones, and
publishes itself (ADR-290). The sentence that justified waiting is now the sentence that requires acting.

Measured before deciding, which is the point: `flutter analyze` **3.2s**, `flutter test` **481 passing in
15s**. ⭐ *The guard costs eighteen seconds and has never once run by itself.*

### 2. 🔴 ADR-310's pin is missing from the file the container installs

ADR-310 spent 24 days of red CI on eight root causes, and the largest single one was **unpinned `pulp`**:
PuLP 4.0.0 (2026-09-25) removes `PULP_CBC_CMD`, which was **277 failures from one cause**. It also caught
what would have been worse — *"Render installs the same `requirements.txt`, so the next deploy would have
removed the solver in production"* — and pinned `pulp==3.3.2` there with a comment explaining exactly why.

⚠️⚠️ **The pin went into `requirements.txt`. The API container installs `requirements-api.txt`**, where
`pulp` is still unpinned — as are `fastapi`, `uvicorn`, `requests` and `psycopg`. The `Dockerfile` says so
in one line: `COPY requirements-api.txt .` And `requirements-pipeline.txt`, which the scheduled Actions
install, pins nothing either.

So the break ADR-310 describes in the past tense is **still live in the image the phone talks to**. It is
held shut by nothing but the absence of a rebuild — and ADR-292's build filter, which suppresses 57% of
redeploys, is the only reason the window has stayed closed since 2026-09-25.

Scope, stated precisely rather than dramatically: `import pulp` still succeeds under PuLP 4, so the
container **boots**. `optimizer` reaches `pulp.PULP_CBC_CMD` at *solve* time (`optimizer.py:276`), so what
breaks is every optimiser-backed answer — squad builds, gameweek plans, My Squad — with a healthy container
serving them.

⭐⭐ *A fix applied to the file you were reading rather than to the file that ships is indistinguishable from
no fix, and it is worse than none, because the comment explaining it reads as protection.*

## Decision

### 1. Wire the Dart guard, in CI and in the release path

**`.github/workflows/mobile.yml`** — `flutter analyze` then `flutter test`, on pushes and PRs that touch
`mobile/`, with the Flutter version **pinned to 3.47.5** (the version the app is built with today).

⭐ *Pinned, for the same reason PuLP is.* A toolchain that floats turns "the tests broke" and "Flutter
changed" into the same red tick, and finding out which is a morning. `subosito/flutter-action` is pinned to
a major tag and given a `cache: true`, so a run is ~1 minute rather than a toolchain download.

⚠️ **Path-filtered on purpose.** The Dart suite has nothing to say about a Python commit, and a job that
runs on everything is a job people learn to ignore.

**Both release scripts** get the gate immediately before the build, not after: `release_android.sh` and
`release_ios.sh` run `flutter analyze` and `flutter test` first, and `set -euo pipefail` stops the release
on a failure. ⭐ *ADR-290 made cutting a release the same act as shipping it, which means the last place a
test can still stop something is before the build, not in a review afterwards.*

### 2. Delete the dead `formatter:` block that was making `analyze` exit 1

`flutter analyze` **exits 1 today** — on one warning, from `mobile/analysis_options.yaml`:

```
warning • The option 'exclude' isn't supported by 'formatter'. Try removing the option
```

So the gate could not simply be switched on. ⭐⭐ **And the block it complains about is config this project
already replaced and already knows does not work** — `tests/test_brand_dart.py` says it in a docstring:
*"`formatter: exclude:` in `analysis_options.yaml` does not help"*, and the mechanism that does work is the
verbatim `// dart format off` marker emitted into the generated file by
`scripts/generate_brand_dart.py:54` and `generate_glossary_dart.py:38`, pinned by a test.

Removing the block therefore **takes away no protection** — the marker and the byte-for-byte comparison are
untouched. What it takes away is a warning standing between the repo and a working gate.

⚠️ Its comment also cited **ADR-242** for the exclusion; ADR-242 is *"A space drawn for data that never
arrived"* and says nothing about formatting. The replacement comment points at
`tests/test_brand_dart.py`, which is the live guard and can be checked. ⭐ *This is Sprint 307's lesson in a
different file — a comment describing an intent the code does not carry out stops the next person
re-reading the line.*

### 3. Pin every deploy requirements file

`requirements-api.txt` and `requirements-pipeline.txt` pin to the versions running today; the remaining
floats in `requirements.txt` are pinned too. **`pulp==3.3.2` in all three**, which is the specific hole
ADR-310 left open.

| file | installed by | was | now |
|---|---|---|---|
| `requirements-api.txt` | `Dockerfile` → Render | 0 of 5 pinned | 5 of 5 |
| `requirements-pipeline.txt` | `data.yml`, `backfill.yml` | 0 of 3 pinned | 3 of 3 |
| `requirements.txt` | Streamlit Cloud, CI, local | 4 of 16 pinned | 16 of 16 |

⭐ **Pinned, not bounded.** `>=` on a deploy file is a floating version with extra characters: it still
installs whatever is newest, which is precisely how PuLP 4 arrived. `Authlib>=1.3.2` was the one real
lower-bound requirement (`st.login()` needs it) and it becomes an exact pin at the version that is running.

⚠️ **This is a deliberate trade for a maintenance cost**, and the cost is real: security updates now arrive
only when someone bumps a file. Accepted because the alternative is the failure mode this project has
already paid for once, and because nine testers now depend on the API being the thing that was tested.
Revisit with Dependabot if the bumps become the annoyance rather than the breaks.

### 4. Pin every one of these claims, because not one is self-enforcing

**`tests/test_mobile_gate.py`** and **`tests/test_deploy_pins.py`**, in the Python suite — ADR-221's own
reasoning about which suite can actually stop a commit, applied to the guards themselves:

* the mobile workflow exists, runs `analyze` **and** `test`, and pins its Flutter version
* both release scripts run the tests **before** their `flutter build`
* every deploy requirements file is fully pinned with `==`, with `pulp` named explicitly
* `analysis_options.yaml` has no unsupported `formatter:` key, so the gate stays exit-0

⭐ *Each of these is a claim that, unwatched, decays back to exactly where it started* — which is the
observation both halves of this ADR are instances of.

### 5. 🔴🔴🔴 And the third finding, which was the guard itself

Correcting `PROJECT_STATUS.md`'s first line — it still said *"**Next:** the Flutter mobile app"* four lines
above *"THE APP IS SHIPPED AND SHIPPING ITSELF"* — raised the only question that mattered: **ADR-294/295
wrote a test for this exact sentence. Why had it never fired?**

`tests/test_orientation_docs_are_current.py` matched the claim correctly. It then threw the match away:

```python
# ⭐ A line that marks it done may quote the old claim to explain the drift.
if "✅" in line or "*This" in line or "said" in line:
    continue
```

⚠️⚠️ **`Current Phase` is a 742-character paragraph carrying three `✅`s** — against the pipeline, against
Supabase, against the endpoints. So the line-wide exemption skipped the whole field, *including* the stale
clause at the end of it. The guard written for this sentence had been exempting this sentence since the day
it was written.

⭐⭐⭐ *An escape hatch scoped more widely than the claim it excuses exempts the thing it was written to
catch.* And this one failed **silently**, which is the property that let it survive: a guard that skips is
indistinguishable, in a green run, from a guard that passes.

**Fixed by scoping the exemption to the clause around each match** rather than the whole line — the regex
never spans a full stop, so the nearest full stops bound it the same way.

⭐ **Verified by watching it object, three times:** on the real stale sentence; then on this sprint's own
status line while it still said *"left open"*; then on a planted decoy where a `✅` elsewhere in the line no
longer excused the claim — while a genuine historical quote in the same clause is still allowed. *A guard is
only known to work once you have seen it refuse something.*

⚠️ `Current Version` also read `0.0.1` beside a shipped `1.0.0+30`. It now says which artefact it means (the
Python package). **Whether the package should claim 1.x is left as an open call** — that is a packaging
decision, not a stale line.

## Consequences

**Good:** the Dart suite can stop a release for the first time; the deployed image is reproducible; the
PuLP 4 window in `requirements-api.txt` is shut; five guards that were prose are now tests — and the
orientation guard that was silently skipping its own subject now works.

**Costs:** version bumps are manual across three files. CI gains a ~1 minute job on `mobile/` changes.

⭐⭐ **The pattern all three findings share**, worth naming because it is the one this project keeps paying
for: **every guard already existed.** The Dart tests existed and nothing ran them; the PuLP pin existed and
sat in the wrong file; the staleness test existed and exempted the line it was written for. ⚠️ *None of
these was a missing idea — each was a guard whose wiring nobody re-checked, and all three were invisible in
a green run.*

**Open, not addressed here:** `src/analytics/__init__.py` eagerly imports `optimizer`, which is the only
reason `pulp` is on the pipeline's import path at all (its own requirements file admits it in a comment);
`src/ask.py` (2409 lines) and `src/service/answers.py` (2368) against *"keep modules small"*; sprint records
stopping at Sprint270 while the status file reads Sprint 308; `docs/01_Journal/` last written 2026-08-05
though Documentation Rules lists it as must-update; and 7.0 MB of markdown against 1.8 MB of Python, with a
498 KB ADR index.
