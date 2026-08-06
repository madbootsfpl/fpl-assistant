# Lessons Learned

**Sprint:** Sprint 076 — Tech-debt sweep (PuLP API + squad renderer)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Clear the two standing tech-debt items — the PuLP deprecations (blanket-suppressed) and the duplicated
squad renderers — with **no behaviour or output change**, migrating what's safe and honestly documenting
what a naive migration would break.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Refactoring behind a strong test net (behavioural + byte-output assertions) so "no change" is provable.
- Probing a library's *actual* behaviour before trusting a deprecation message's suggestion.

### New Skills Acquired

- PuLP 3.3.2: `problem.add_variable(...)` is the 4.0-ready variable API; **`COIN_CMD` needs an external CBC
  binary** (`pip install pulp[cbc]`) while `PULP_CBC_CMD` bundles one.
- `warnings.filterwarnings(message=…)` gives a **targeted** suppression, unlike a blanket
  `simplefilter("ignore", DeprecationWarning)` that hides everything.

---

# What Went Well ✅

- **Verify-before-migrate paid off twice** — `COIN_CMD` fails here, and `render_rows` can't reproduce the
  squad bytes; both naive migrations would have caused harm, and the probe caught it at planning.
- **Honest partial done** — migrate the safe bits (variables, shared header), keep/close the rest with a
  rationale in the Backlog + ADR-066.
- **Provably safe** — the 65 optimizer + 19 render assertions passed unchanged; a build leaks no
  deprecation to the caller.
- **A real hygiene gain** — the blanket `DeprecationWarning` ignore became a targeted PULP_CBC_CMD filter,
  so future deprecations surface.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `COIN_CMD` (the deprecation's suggestion) fails | it needs an external CBC; `PULP_CBC_CMD` bundles one | Keep `PULP_CBC_CMD`; suppress only its notice; document the deferral |
| Blanket `DeprecationWarning` ignore hides everything | one broad filter | Narrow to `filterwarnings(message=".*PULP_CBC_CMD.*")` |
| `render_rows` can't render the squad layout | flat single-space join vs mid-table heading + glued markers + divergent price cells | Share only header + bench-heading; close the fold with a rationale |
| The two squad renderers differ more than they look | loaded prints an unpadded `£X.Xm`; squad pads to 6 | Keep the row bodies per-renderer; don't force a shared row |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Trust behaviour, not the message | A deprecation's "use X instead" can be non-viable in your env (COIN_CMD/CBC) — test it |
| Targeted suppression | `filterwarnings(message=…)` silences one notice while keeping the rest honest |
| Byte-output tests enable refactors | Golden assertions let you prove a de-dup changed nothing |
| Backlog debt can be over-stated | Migrate the safe part; keep + document what a naive change would break |

---

# Development Lessons 💻

- Probe the library's real behaviour at planning; let it re-scope the work.
- Prefer a targeted warning filter over a blanket ignore.
- When a "shared renderer" would change bytes, share only the byte-safe pieces and document the rest.

---

# AI Collaboration Lessons 🤖

- The owner's "do the tech-debt sweep" was best served by *not* doing it literally — verifying showed the
  naive migrations would break things, so the honest outcome was migrate-safe + document-the-close.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-066 | **Tech debt — PuLP + squad renderer** — migrate `LpVariable`→`add_variable`, **keep `PULP_CBC_CMD`** (COIN_CMD needs external CBC — would break the Cloud), narrow the blanket DeprecationWarning ignore to a **targeted** PULP_CBC_CMD filter; share the squad renderers' **header + bench-heading** but **don't** fold into `render_rows` (not byte-identical-feasible); no behaviour/output change | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Revisit `COIN_CMD` only if we adopt `pulp[cbc]` or PuLP 4.0 lands and CBC packaging settles. Open items:
  a team-scoped player multiselect, pronoun-aware chat, a team-level squad-fixtures view, and — post-GW1 —
  the Data Hardening flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying library behaviour at planning; keep the byte-output tests that make refactors safe.

---

# Key Commands Learned

```text
python -m pytest tests/test_optimizer.py tests/test_analyse.py -q   # behaviour + byte-output pin the refactors
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Targeted warning filter | `filterwarnings(message=…)` — silence one notice, not all of a category |
| Bundled vs external solver | `PULP_CBC_CMD` ships CBC; `COIN_CMD` expects CBC on the system |
| Byte-identical refactor | A change proven by golden tests to leave output exactly the same |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-066 | The revised tech-debt decisions + the COIN_CMD/render_rows rationale |
| `src/analytics/optimizer.py` | `add_variable` + the targeted PULP_CBC_CMD filter |
| `src/ui/squad.py` | `_header` + `_BENCH_HEADING` (the shared, byte-safe squad pieces) |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-211 PuLP API tidy — `add_variable`; kept the bundled `PULP_CBC_CMD`; targeted the warning suppression
- US-212 Squad renderer de-dup — shared `_header` + `_BENCH_HEADING`; closed the `render_rows` fold

**Stories Carried Forward:**

- None. (`PULP_CBC_CMD` stays deprecated-but-bundled — revisit at `pulp[cbc]` / PuLP 4.0.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
