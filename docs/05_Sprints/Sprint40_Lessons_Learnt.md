# Lessons Learned

**Sprint:** Sprint 040 — One xP metric (unify the optimiser) + a squad-build `ask` intent

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Answer *"why does `transfer` improve my optimal squad?"* — the optimiser and the recommendations were
optimising different metrics. Unify them on one xP (`decision_xp`), make `xp` the default `squad`
objective so a default squad is consistent with `transfer`, and then extend Phase 4 with
`ask "build me a squad [for £X]"`. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Diagnosing a disagreement as an *objective mismatch*, not a code bug.
- Extracting a single shared function to make consistency structural.
- Reading a grounding check's failure to a real root cause (JSON escaping).

### New Skills Acquired

- One "decision xP" recipe as the app's single currency.
- A budget parser + exposing an optimiser through a grounded NL intent.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The question had a clean, provable answer** — two metrics (last-season points vs forward xP) were in
  play; unifying them gave a *better* squad (305.8 vs 239.0) and zero free transfers.
- **Consistency made structural, again** — `decision_xp` is now the one place xP is defined (like
  `best_legal_xi` for the XI); three duplicated assemblies removed for free.
- **A new feature surfaced an old bug** — `build_squad`'s `£` facts exposed a latent `verify_grounding`
  flaw; the same pattern as Enes Ünal last sprint.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| transfer improves an "optimal" squad | `squad` optimised `points` (last-season total); transfer ranks xP | Unify on one `decision_xp`; make `xp` the default |
| Even `--objective xp` disagreed | It used a degraded xP (horizon 1, no baseline/xMins) | Route the xp objective through `decision_xp` |
| `£100.0m` flagged as unverified | `json.dumps` escaped `£`→`£`; its `00`/`3` polluted the number set | `ensure_ascii=False` in `verify_grounding` + `_build_prompt` |
| build vs start/bench routing | "build me a squad" contains no start/bench keywords | Keyword order: build after start_bench |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Same quantity first | Two tools disagree → check they optimise the same thing before the code |
| Structural consistency | One shared function beats two that coincide (`decision_xp`, `best_legal_xi`) |
| New shapes flush bugs | A `£` in the facts (a first) exposed a dormant grounding flaw |
| JSON + non-ASCII | `ensure_ascii=True` escapes `£`/accents to `\uXXXX` — digits leak into number parsing |
| Metric vs display | Optimising xP while showing last-season Pts confuses — say so, or show the metric |

---

# Development Lessons 💻

- When outputs contradict, suspect the objective before the algorithm.
- De-duplicate the recipe that must stay consistent — the DRY *is* the guarantee.
- Re-run the checks against every new input shape; latent bugs hide until exercised.

---

# AI Collaboration Lessons 🤖

- The owner's "why weren't those in the squad?" was, again, a precise lead — it exposed a real metric
  split and a hidden grounding bug in one thread.
- A worked example at the gate (squad-on-full-xp → 0 transfers) turned "explain it" into "prove it".

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-041 | One xP metric: `decision_xp` (baseline + fallback + xMins) shared by squad/analyse/transfer/ask; `xp` the default `squad` objective (`--no-xmins` for raw; `--objective points` kept); an xp-optimal squad → 0 transfers. Phase 4: `ask "build me a squad [for £X]"`. Plus a grounding fix (`ensure_ascii=False`) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Show xP in the squad table when `--objective xp` (a note bridges it now). A more robust intent
  classifier if intents keep growing. (GW1) partial-season baseline tuning; the full Phase-5 xMins.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate probe broad; keep the 3-part DoD — the smoke exposed the `£` bug.

---

# Key Commands Learned

```text
python app.py squad --full --budget 100            # default objective is now xp (forward-looking)
python app.py squad --full --objective points      # last season's total instead
python app.py ask "build me a squad for £100m"     # the optimal 15 on xP, grounded + a ✓ line
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Objective mismatch | Two tools optimising different quantities (points vs xP) → they disagree |
| decision_xp | The single "decision xP" recipe (baseline + fallback + xMins) used everywhere |
| ensure_ascii | JSON option: False keeps `£`/accents literal so digits don't leak into parsing |
| Structural consistency | Agreement guaranteed by sharing one function, not by coincidence |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-041 | The one-metric design + the squad-build intent |
| ADR-040 / ADR-038 / ADR-011 | The fallback + xMins + the squad-objective toggle this unifies |
| ADR-037 | The grounding verifier the `£` fix corrects |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Objective mismatches | | |
| Structural consistency (DRY) | | |
| Grounded NL intents | | |
| Architecture | | |
| AI-assisted Development | | |

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

- US-118 Gate — ADR-041 (unify xP; xp default; the answer)
- US-119 One metric — `decision_xp`; squad-on-xp → 0 transfers
- US-120 `ask "build me a squad"` + the `£` grounding fix

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
