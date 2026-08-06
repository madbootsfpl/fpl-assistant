# Lessons Learned

**Sprint:** Sprint 070 — Differentials / value `ask` intent

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add two natural-language capabilities — **"best differentials"** (a low-owned lens on the shortlist) and
**"is X worth the money?"** (a single-player value verdict) — grounded + verified like every `ask`, by
**reusing** the shortlist, the one xP, the ownership threshold, and the compare player-matcher.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Extending the keyword-routed `ask`/`chat` layer without letting the LLM decide anything.
- Keeping a shared renderer backward-compatible via an opt-in flag (`show_own`).
- Grounding a *judgment* ("worth it") in fact-derived tiers so the model only phrases it.

### New Skills Acquired

- **Routing precedence as a design lever** — ordering intents (worth *before* transfer) is how you stop a
  broad keyword ("buy") from swallowing a specific phrase ("worth buying").
- A **verdict from a benchmark** — rank + position-median value turns "is it worth it?" into a grounded,
  self-explaining answer instead of an opinion.

---

# What Went Well ✅

- **Reuse over reinvention** — the differential lens is a filter on the existing shortlist; the value
  verdict reuses the compare matcher + the one xP. Small surface, no new data/deps.
- **No regressions by construction** — `render_shortlist(show_own=…)` keeps the plain shortlist
  byte-identical (a test asserts no `Own%` leaks); every other intent is untouched.
- **Real-data-first** confirmed the picks are useful *and* named the honest preseason caveat (flat
  ownership → the filter sharpens at GW1), which became a caption rather than a surprise.
- **The smoke earned its keep** — it caught a tuple-sort crash on a value tie that the unit tests missed.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "worth buying" could route to transfer | "buy" is a transfer keyword | Place `worth` before transfer; use value-specific phrases (not bare "worth") — a routing test pins it |
| Adding Own% risked changing the plain shortlist | one shared renderer | `render_shortlist(..., show_own=False)` — the column is opt-in; a test asserts byte-identical plain output |
| Sorting `(value, player)` crashed on a tie | sqlite3.Row isn't orderable, so equal values fell through to comparing rows | Sort with `key=_value` instead of tuple-sorting |
| "differential" is weakly discriminating now | preseason ownership is flat (497/570 ≤5%) | Keep it (removes template picks, xP-ranks); a caption says it sharpens at GW1 |
| "worth it" is a judgment | subjective by nature | Derive the verdict from a tier vs the position median; always show the rank + median facts |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Intent ordering | First-match-wins routing means *order is policy* — a specific phrase must be checked before a broad keyword that contains it |
| Opt-in rendering | An added column behind a default-off flag keeps a shared renderer's old output exactly, and old tests green |
| Ground the judgment | A "verdict" stays honest when it's a fact-derived tier (vs a median), not the model's opinion |
| Tuple sorts bite | `sorted((score, obj))` compares `obj` on a score tie — sort by a `key=` to avoid ordering un-orderable objects |
| Smoke > units here | The tie-crash only appears on real data with duplicate values — the manual smoke found what the crafted units didn't |

---

# Development Lessons 💻

- Reuse the existing seam (shortlist, xP, matcher) before adding a new one — less surface, fewer regressions.
- Default-off flags protect existing callers when you extend a shared function.
- Run the manual smoke on real data even when the unit tests are green — ties/edge shapes live there.

---

# AI Collaboration Lessons 🤖

- The owner's steer — build **both** lenses; show the verdict as **rank *and* median** — set a concrete,
  gradeable target; the real-data gate then de-risked the differential threshold before building.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-061 | **Differentials / value `ask` intent** — a **differential** filter on the shortlist (≤`DIFFERENTIAL_OWN` owned, +Own% column, plain shortlist byte-identical) + a new single-player **`worth`** intent ("is X worth the money?" → xP/£m · rank among position peers · vs the position median · a tiered fact-derived verdict; degrades on no match); routing `worth` before transfer/captain, "differentials"→shortlist, "most owned"→trends; grounded (ADR-037); preseason-honest | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **At GW1 (2026-08-21):** the differential lens sharpens as ownership concentrates — worth re-checking the
  picks then; revisit the value-verdict tiers (1.15× / 0.9× the median) once real form moves prices. Related
  open items: pronoun-aware chat ("is *he* worth it?"), a team-level squad-fixtures view, and (post-GW1) the
  Data Hardening flip + a crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the real-data gate before building; keep shared renderers extended behind default-off flags; keep the
  manual smoke in the DoD (it caught the tie bug).

---

# Key Commands Learned

```text
python app.py ask "best differential forwards under £7m"   # the differential shortlist (Own% column)
python app.py ask "is Haaland worth the money?"            # the single-player value verdict
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Differential (shortlist) | A low-owned (≤5%) player surfaced by the differential lens — off-template but ranked by xP |
| Value (xP/£m) | Expected points per million of price — the shortlist's value metric and the verdict's basis |
| Value verdict | A tiered judgment ("good / fair / pricey") derived from a player's value vs the position median |
| Routing precedence | The intent order that decides which keyword wins when phrases overlap |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-061 | The differential-lens + value-verdict design and the routing precedence |
| `src/ask.py` `_decide_worth` / `_decide_shortlist` | The value verdict + the differential filter |
| `src/ui/shortlist.py` | The `show_own` opt-in column pattern (backward-compatible rendering) |

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

- US-198 Differential shortlist lens — "best differentials [position] [under £X]", ≤5%-owned, +Own% column
- US-199 Single-player value verdict — "is X worth the money?" → xP/£m + rank + median + a tiered verdict

**Stories Carried Forward:**

- None. (The differential lens sharpens at GW1; verdict tiers may want recalibration then.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
