# Sprint 113: A robust Ask scroll + an explained differential shortlist

**Dates:** 2026-08-14 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (Ask presentation + explainability — no analytics change)
**Carried Over:** none

> **Direction (tester feedback — two Ask-tab items):**
> 1. *The example-question auto-scroll "works for some, not all" — sometimes you still scroll manually.*
> 2. *"best differential midfielders under £8m" needs a **why** — explain the **benefit** of a differential,
>    and maybe **why these ones** if known. (Currently a bare table + a "Start Ollama" note.)*

---

### 🔎 Verified at planning (on real data)

- **Item 1 — the scroll is timing-fragile.** US-283 made the nudge unique per turn (so it re-runs), but it's a
  **single** `setTimeout(…, 150ms)` **smooth** scroll to `body.scrollHeight`. It fires once — before the
  example **expander collapses** (`expanded = not history` shrinks the page on the first turn) and can be
  overridden by Streamlit restoring the prior scroll position mid-animation — so it lands *sometimes*. The fix:
  scroll **several times over ~0.8 s** (instant, not smooth) so it reliably ends at the bottom after layout
  settles.
- **Item 2 — the shortlist has no "why".** `_decide_shortlist` → `render_shortlist` is a ranked table + a note;
  no rationale. But the rows carry what a grounded "why" needs: **xP**, **ownership**, **xMins**
  (`minutes_weight`), **set-piece** order, **penalties**, **form** — e.g. today's top differential MIDs:
  *Stach 18.4 xP · 1.3% · ~62 mins · 🎯 FK*, *Zubimendi 17.1 · 1.5% · ~78 mins (nailed)*. Preseason the per-pick
  signals are **thin** (mostly xP + minutes; set-pieces/form/penalties sparse → richer at GW1), so the
  **benefit** explanation is the always-valuable part, with per-pick signals layered where known.

---

### 🎯 Sprint Goal

**Objective:** clicking an example **reliably scrolls** to the answer, and the **differential** shortlist
**explains itself** — why a differential is worth considering, and the standout signal behind each leader.
Presentation + a grounded rationale; the analytics/ranking untouched.

#### Success Criteria
- [ ] **US-287 (robust auto-scroll)** — the Ask scroll nudge scrolls the parent to the bottom **several times
      over ~0.8 s** (instant), still **unique per turn**, so it lands reliably regardless of the
      expander-collapse / rerun-timing (not a single smooth attempt). No content change.
- [ ] **US-288 (explain the differential shortlist)** — the **differential** shortlist answer gains a grounded
      **"Why a differential?"** lead (the rank-lever benefit + the variance trade-off) and a compact **per-pick
      "why these"** — each leader's standout signal from the data (highest xP · nailed ~N mins / rotation risk ·
      set-pieces · penalty taker · in form), gracefully thin preseason. The **plain** shortlist stays
      byte-identical; the answer still **verifies (✓)**.
- [ ] **No drift** — display/rationale only; `decision_xp`/the ranking unchanged; existing **737** stay green
      (+ new scroll / differential-why tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends **ADR-052** (Ask scroll) +
      **ADR-042/061** (shortlist) — noted; no new ADR).

---

### 🧭 Design sketch

**US-287 — robust scroll.** In `4_Ask.py`, replace the single `setTimeout` with a small **multi-tick** instant
scroll — e.g. `[50, 200, 450, 800].forEach(d => setTimeout(scrollToBottom, d))` — keeping the `/*turn N*/`
token for per-turn uniqueness. Instant (not smooth) so Streamlit's scroll-restore can't win, and repeated so it
catches the expander collapse + any late layout. (The AppTest still asserts the srcdoc is unique per turn + it
scrolls to `scrollHeight`.)

**US-288 — explain the differential.** In `_decide_shortlist` (differential branch only): build a grounded
**lead** — *"Few managers own a ≤5%-owned player, so a haul gains you rank on the template while a blank costs
little relative rank; the trade-off is variance — play them for upside."* — and a per-pick **signals** list for
the top few, from a small helper over the row (nailed `~N mins` vs rotation risk, `🎯/🚩` set-pieces, penalty
taker, in form; xP is the headline). `render_shortlist(…, lead=…, reasons=…)` prepends the lead + a *"standout
signals"* block; without them the output is byte-identical (the plain shortlist is untouched). The facts already
carry the ranked-by + top players, so narration still verifies (✓, ADR-037).

**Deferred:** a "why" on the plain (non-differential) shortlist (its rationale is just "ranked by xP");
per-pick confidence scores (a list isn't a single decision); a web-native card.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-287 | **Robust Ask auto-scroll** — a multi-tick instant scroll (per turn) so it lands reliably. | High | ⬜ To do | ~¼ session |
| US-288 | **Explain the differential shortlist** — a grounded benefit lead + per-pick standout signals. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Ask scroll nudge emits a **multi-tick** script (≥3 scheduled scrolls to `scrollHeight`),
   still unique per turn; the **differential** shortlist detail carries the *"Why a differential?"* lead + a
   *standout signals* line for a leader (nailed/set-pieces where present), and its facts still include the
   ranked-by + top players (verifies ✓); the **plain** shortlist output is unchanged. Existing **737** stay
   green. No `.save(` / no analytics change.
2. **Manual smoke** — clicking a few example questions scrolls to the answer each time; `ask "best differential
   midfielders under £8m"` leads with the benefit + names a couple of picks' standout signals.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

**US-287 — robust Ask auto-scroll.** ✅ Done.
- Replaced the single `setTimeout(…, 150ms)` **smooth** scroll with a **multi-tick instant** scroll —
  `[50,200,450,800].forEach(d => setTimeout(scrollToBottom, d))` — still carrying the `/*turn N*/` per-turn
  token. Instant (not smooth) so Streamlit's scroll-restore can't win mid-animation; repeated so it lands after
  the example expander collapses + any late layout settles (the "works for some, not all" cause).
- **Test (updated):** the nudge is unique per turn (`/*turn 1*/` → `/*turn 2*/`) **and** multi-tick (the
  `[50,200,450,800]` `forEach` scroll to `scrollHeight`, no `smooth`). **737** green, ruff clean.
- **Manual smoke:** clicking example questions scrolls to the answer each time.

_(US-288 next — "start US-288".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
