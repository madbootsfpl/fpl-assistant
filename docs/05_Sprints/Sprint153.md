# Sprint 153: P1 quick-wins (2026-08-13 intake)

**Dates:** 2026-08-13
**Status:** ✅ Complete — US-373…376 (no ADR). 982 → 983 tests
**Capacity:** ~1 session (four small, independent fixes)
**Carried Over:** none

> **Direction:** four P1 quick-wins from the 2026-08-13 tester intake — clear, low-risk, ship-now. **US-373** Home
> tidy-up (owner's copy). **US-374** default horizon (My Squad 1 GW · Squad Lab 5 GW). **US-375** hide the dev-only
> "Start Ollama…" prompt from deployed users. **US-376** make the Set-pieces columns read as *order*, not counts.
> Display/config only — no analytics change.

---

### 🎯 Sprint Goal

The Home page reads cleanly and reflects the live app (auth/auto-sync); the horizon defaults match each page's job;
the Ollama prompt no longer confuses deployed users; the set-piece numbers can't be misread as counts.

#### Success criteria
- [ ] **US-373 (Home tidy-up)** — apply the owner's rewrite: tagline → *"Fantasy Football, Calculated. The analytics
      decide; you stay in control."*; the sidebar list → **"Explore the sidebar"** shorter per-tab lines; the "Your
      squad" block → bullets reflecting **auth is live** (saved to account · auto-synced across devices · upload ·
      manager-ID from GW1). Drop the internal ADR refs + the dev `python app.py refresh` line from user copy. Fix the
      draft's typos. Keep the app's established icons. *(Home.py.)* Test: the page renders; the new tagline present.
- [ ] **US-374 (default horizon)** — `pages/3_My_Squad.py` "Gameweeks ahead" default **5 → 1**; `pages/4_Squad_Lab.py`
      stays **5**. Safe: the per-GW card is horizon-independent (S152). Test: My Squad's horizon default is 1.
- [ ] **US-375 (Ollama prompt)** — the *"(Start Ollama for a written summary.)"* hint (`src/ui/ask.py`) is a dev
      affordance; a deployed user can't act on it. Suppress it in the **web** rendering (keep the full plan/facts/✓⚠),
      keeping the hint for the **CLI** (local dev). Test: the web AI Tips output doesn't tell the user to start Ollama.
- [ ] **US-376 (set-piece label clarity)** — the Set-pieces columns (`Pen · Corners · FK`) are the FPL **taking
      order** (1 = first-choice), not counts; a tester read "Corners 4" as a count. Make the header/label say *order*
      (e.g. `Pen order` / a "(1 = first)" cue) so it's clear without hovering. *(views/players.py; data unchanged.)*
      Test: the Set-pieces headers convey order.
- [ ] **No drift** — display/config only; no `decision_xp`/analytics change; ruff + suite green.
- [ ] **Docs** — PROJECT_STATUS; Architecture; memory; mark the items shipped in Backlog.

---

### 📋 Sprint Review

**Delivered — four P1 quick-wins; display/config only, 983 tests, ruff clean.**

- **US-373 Home tidy-up** — owner's copy: tagline *"…The analytics decide; you stay in control."*; "Explore the
  sidebar" short per-tab lines; "Your squad" bullets reflecting **auth/auto-sync (live)**; dropped internal ADR refs
  + the dev `refresh` line; typos fixed; our icons kept.
- **US-374 default horizon** — My Squad **5 → 1 GW** (manage this week); Squad Lab stays **5** (build for the run).
- **US-375 Ollama prompt** — `render_ask` gains `ollama_hint` (default True for the CLI); the web edges (Streamlit
  `render_ai_tips`/`render_chips`/Ask + the FastAPI reference) pass **False**, so deployed users aren't told to start
  a **local-only** Ollama — the full plan/facts/✓⚠ still render.
- **US-376 set-piece labels** — headers now read **"Pen order · Corner order · FK order"** with "1 = first-choice,
  not a count" tooltips, so "Corner order 4" reads as *4th-choice taker* (a tester had read it as 4 corners).

**Two tester "issues" were questions, not bugs** — Ollama is local-only (the live app is data-only); set-piece
numbers are the taking *order* — each resolved with a UX-clarity fix above. **Note:** the default-horizon flip
surfaced **two pre-existing tests** hard-coding the old default of 5 — both fixed. No analytics change.

### 🧠 Lessons
*(see `Sprint153_Lessons_Learnt.md`)*
