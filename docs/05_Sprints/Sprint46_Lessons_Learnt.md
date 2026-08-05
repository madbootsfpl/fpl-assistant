# Lessons Learned

**Sprint:** Sprint 046 — XI-aware transfers (rank by the fielded-XI improvement)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make `transfer` rank single swaps by **XI-gain** — how much a swap lifts your best legal XI — instead of
raw player-xP gain, so a cheap bench "upgrade" (a big paper number that doesn't change the team you
field) stops topping the list. A fast, exact `best_xi_points` helper; XI-aware the default with `--raw`
for the old view; the plan + `ask` speak the same number. No new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Choosing the *objective* deliberately — the metric a recommender ranks by *is* the recommendation.
- Pinning a fast approximation to an exact reference by a test (formation enumeration = the ILP).
- Preserving old behaviour behind an opt-out flag while changing a default.

### New Skills Acquired

- A formation-enumeration best-XI (`best_xi_points`) as an O(1)-per-candidate alternative to an ILP.
- Separating metric-agnostic *rule* tests from *metric* tests when a default changes.

---

# What Went Well ✅

- **The gate probe carried the sprint** — the metric, the speed *and* the value were all proven on the
  live DB before code; the worked example (*Kusi-Asare → João Pedro +19.3* vs *Guéhi → Gabriel +3.0*)
  became the acceptance test.
- **A fast exact helper** — enumerating the ~7 legal formations and taking top-N per position matches
  `best_legal_xi` exactly (pinned by a test) in ~0.02s for ~750 swaps, so no per-candidate ILP.
- **The default/`--raw` split kept it honest** — the smoke showed the exact contrast (the bench-only
  *Slater → Hughes +7.2* appears only under `--raw`); nobody loses the old view.
- **`ask` came for free** — because both engines default to XI-aware, the `ask` intent inherited the
  new metric with only a wording change.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Existing transfer tests broke under the new default | Tiny test squads have no GK → best-XI is 0 → no suggestions | Pin the rule-tests to `xi_aware=False`; add XI-aware tests on a full 15 |
| Grounding could imply a raw-xP delta | Fact key read "expected_points_gain" | Reword to `starting_XI_improvement` / "+N XI xP" |
| Bench cover now scores 0 | XI-gain deliberately ignores the bench | Accepted (it's the weekly-relevant number); a bench-weighted variant is a later option |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| The metric is the recommendation | Same candidates, same rules — changing only the ranking number flipped the advice from misleading to useful |
| Fast + exact > slow + "proper" | Formation enumeration is exact *and* ~100× cheaper than re-solving the XI ILP per candidate |
| Change a default, split the tests | Rule-tests (legality/budget/dedup) are metric-agnostic — pin them to the old path; test the new metric separately |
| Opt-out keeps trust | `--raw` preserves the old behaviour, so a default change is safe |

---

# Development Lessons 💻

- When a recommender feels "off", suspect the objective before the tuning — the right number matters
  more than any amount of polish around a wrong one.
- Prove a fast approximation against the exact reference with a test, then use it freely.
- A default change ripples into the tests — expect it, and separate what's testing *rules* from what's
  testing the *metric*.

---

# AI Collaboration Lessons 🤖

- The gate probe pinned the metric + speed + value up front, so US-137/138 were mechanical.
- The grounding verifier again earned its keep — it flagged the LLM's invented figures in the `ask`
  narration (as designed); the analytics stay the source of truth.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-046 | XI-aware transfers: rank swaps by **XI-gain** = `best_xi_points(owned − out + in) − best_xi_points(owned)`; a fast `best_xi_points` (formation enumeration, matches `best_legal_xi`); **XI-aware the default**, `--raw` for the old raw-player-gain ranking; the plan + `ask` use it | Accepted |

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

- A **bench-weighted transfer value** (XI-gain + ε·bench-gain) so genuine bench-cover swaps aren't
  invisible; chip-timing / hit (−4) modelling; an intent classifier as `ask` routing grows; (GW1) the
  full Phase-5 xMins. Or the web UI (Phase 2).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep gating with a real-data probe; keep the 3-part DoD; keep an opt-out when changing a default.

---

# Key Commands Learned

```text
python app.py transfer --squad my-team            # rank by XI improvement (bench fodder drops out)
python app.py transfer --squad my-team --raw      # the old raw-player-xP-gain ranking
python app.py transfer --squad my-team --count 2  # a coordinated plan, same XI-gain metric
python app.py ask "what transfer for my-team?"    # ...the same decision, in plain English
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| XI-gain | How much a swap lifts your best legal XI = best-XI xP(after) − best-XI xP(before) |
| best_xi_points | The best legal XI's xP by formation enumeration (fast, exact; matches the ILP) |
| Bench fodder | A cheap bench player whose "upgrade" barely changes the team you field (XI-gain ≈ 0) |
| `--raw` | Opt out of XI-aware ranking; rank by raw player-xP gain (the old default) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-046 | The XI-gain metric + the fast best-XI + the default/`--raw` call |
| ADR-045 | The bench-aware build this pairs with (both maximise the XI) |
| ADR-041 / ADR-030 | The unified xP + the original transfer engine this refines |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Choosing the right objective | | |
| Fast exact approximations | | |
| Changing a default safely | | |
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

- US-136 Gate — ADR-046 (the XI-gain metric; the fast best-XI proven to match the ILP; XI-aware default)
- US-137 `best_xi_points` + XI-aware `suggest_transfers` (+ the plan threads it)
- US-138 `--raw` CLI + self-labelling renderers + `ask` wording + docs

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
