# ADR-341 — A pinned dependency is not a pinned install

**Date:** 2026-10-01
**Status:** Accepted
**Found by:** the architecture review (`docs/00_Project/REVIEW_2026-10.md`, §5)
**Completes:** ADR-310 (the 24 days of red CI) and ADR-322 (the pin applied to the wrong file)

---

## Context

ADR-310 and ADR-322 between them pinned every dependency this project *names*. The conclusion recorded in
all three requirements files was that deploys were now reproducible and upgrades deliberate.

⭐⭐ **They were not, and the dependency scan that proved it had never been run.** The September security
review said so in its own closing lines — *"no dependency-vulnerability scan"* — and the review of
2026-10-01 ran one.

It found `urllib3 2.7.0` carrying **CVE-2026-97687 / 97688 / 97689**. None is reachable in this codebase:
two require response streaming and one requires an HTTPS proxy, and `git grep -E
"stream=True|iter_content|read_chunked|proxies="` finds neither.

⚠️⚠️ **The finding that matters is not the CVE. It is that nobody chose the version.** `requests` is
pinned; `urllib3` is what `requests` installs, and nothing named it. So the installed tree was decided by
the clock at image-build time — two images built from a byte-identical file a week apart could carry
different code.

⭐ *A file of pinned direct dependencies describes what you import, not what you run.*

## Decision

**Pin the transitive tree in all three deploy files, generated on Linux.**

| file | packages named before | after |
|---|---|---|
| `requirements.txt` | 16 | **71** |
| `requirements-api.txt` | 5 | **20** |
| `requirements-pipeline.txt` | 2 | **7** |

Each file now installs to exactly what it declares, verified by installing it into a clean environment and
diffing the freeze against the file.

### 🔴 Generated on Linux, and that is not a detail

The first generation was done on the development machine (macOS) and produced **54** transitive packages
for `requirements.txt`. The same resolution on Linux produces **55**. The difference is `watchdog`, which
Streamlit declares for non-Windows platforms and which resolves differently.

⭐⭐ **Pinning the macOS list would have left exactly one package floating on the deploy** — the hole this
ADR exists to close, reopened for one package, with 54 pins reading as proof that it was not.

⚠️ Verified separately that Python **3.13 and 3.14** — both CI matrix legs — resolve identically once the
OS is held constant. So the variable was never the interpreter. It was the machine the command was typed on.

### What this costs, accepted

**Upgrades are now a deliberate regeneration**, the same bargain ADR-322 struck for the direct pins and for
the same reason: these files are installed by a scheduled job 24× a day with nobody watching, and by a
container that rebuilds in front of nine testers. Each block carries the command that regenerates it and
the warning to comment the block out first, ⚠️ *because re-freezing a pinned environment reproduces the
pins you were trying to refresh.*

### Guarded, not just done

`tests/test_deploy_pins.py` gains two tests:

- **`test_the_transitive_tree_is_named_not_just_the_direct_dependencies`** — for each deploy file, a known
  sub-tree (`requests` → `urllib3`/`certifi`/`idna`/`charset-normalizer`, `fastapi` → `starlette`/
  `pydantic`/…) must be pinned wherever its parent is. ⚠️ **A sample, not a proof of completeness** — it
  cannot resolve a tree offline. What it stops is the regression: someone bumping a direct pin and
  dropping the generated block with it.
- **`test_urllib3_is_past_the_streaming_cves`** — ⭐ held even though nothing reaches the vulnerable paths,
  because *"not reachable"* is a statement about today's code, and whoever adds the first streaming
  download will not read this file first.

Both were mutation-tested: reverting `urllib3` to 2.7.0 fails the second, deleting three lines of a
transitive block fails the first.

## Consequences

✅ All three files scan clean. ✅ The API image builds on `python:3.13-slim` and serves, with an exact tree
match inside the container. ⚠️ A dependency upgrade is now a two-step job — edit the direct pin, regenerate
the block.

📌 **Not done, and deliberately:** hashes (`--require-hashes`). That defends against a registry serving
different bytes for the same version, which is a different threat from the one here, and it makes every
upgrade materially harder. ⭐ *The gap this ADR closes is "nobody chose the version"; hashes close "the
version is not what it was", which has not happened and has no evidence behind it.*
