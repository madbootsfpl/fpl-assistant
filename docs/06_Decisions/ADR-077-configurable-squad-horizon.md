# Architectural Decision Record: A configurable prediction horizon on the Squads tab

**Decision ID:** ADR-077
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** exposes the existing horizon parameter (ADR-041 `decision_xp`, ADR-031
`analyse_squad`, ADR-030 transfers) as a **web control**; adds a backward-compatible `horizon` to the `ask`
layer for AI Tips (ADR-070). No analytics change. Triggered by tester request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester: *"Need the flexibility to select the number of gameweeks the tool predicts over. Starting the season
or wildcarding → the next 4–6 GW matter; mid-season → the next 1–2. Want that flexibility throughout the
Squads tab and sub-tabs — maybe a dropdown."*

**Verified in code:** the analytics are already parameterised — `decision_xp(..., horizon=5)`,
`analyse_squad(..., horizon=5)`, and the CLI's `--next N`. The **web Squads views hard-use the default 5**
(they call `decision_xp` with no horizon; `gameweeks == [1,2,3,4,5]`), and `render_squad_analysis` already
labels the window from the horizon ("next GW" for 1, "N GW" otherwise). So this is **plumbing a chosen N**
where 5 is implicit — **default 5 = unchanged behaviour**. Two nuances: **Captain** is inherently a one-week
decision (`captain_picks` is next-GW) — the horizon must not apply to it; **AI Tips** routes through the
`ask` layer's module `_HORIZON = 5`, so covering it needs a small `horizon` param on `ask.answer`.

#### Decision Drivers
- **The tester's real workflow** — a wildcard/start wants 4–6 GW; mid-season wants 1–2.
- **One control, everywhere** — a single dropdown that flows through the sub-tabs.
- **No surprise** — default 5 keeps today's numbers; no analytics change.
- **Honest per-view** — Captain is a one-week call; don't pretend the horizon changes it.

---

### ✅ Decision

**1. A shared "Gameweeks ahead" dropdown on the Squads page (US-237).** `pages/3_Squads.py` renders
`st.selectbox("Gameweeks ahead", 1..8, index=4 → default 5)` alongside the Tool control, and passes the
chosen `horizon` into the views. **Build · My Squad · Health · Transfer** take a `horizon` param and thread
it to `decision_xp(..., horizon=…)` (and `analyse_squad(..., horizon=…)` on Health; the transfer renderers'
`horizon=` for their label). **Captain** is unchanged — it stays next-GW, with a caption saying captaincy is
a one-gameweek decision.

**2. AI Tips respects the horizon (US-238).** `ask.answer(..., horizon=_HORIZON)` gains a backward-compatible
`horizon` keyword, threaded `_fresh → _dispatch → _decide_gameweek → _squad_xp(..., horizon=…)` (a new
keyword on `_squad_xp`, default `_HORIZON`, so the other squad decides are unchanged). The gameweek plan
renders "over N GW" (was a hard "5 GW"). The AI Tips view passes the selected horizon.

**3. Range + default.** **1–8**, default **5**. 1–8 covers the tester's "next 1–2 … next 4–6" plus headroom;
5 matches today. No analytics change (the horizon params already existed); no server writes.

---

### 🔀 Alternatives Considered

- **A slider instead of a dropdown.** Rejected — the tester asked for a dropdown; discrete GW counts read
  cleanly as a select.
- **Apply the horizon to Captain too.** Rejected — captaincy is a single-gameweek bet; a multi-GW captain
  number would mislead. Captain stays next-GW with a caption.
- **Leave AI Tips at 5.** Rejected (owner) — "throughout the tab" includes AI Tips; the `ask` `horizon`
  param is small and backward-compatible.
- **Thread the horizon through *every* `ask` intent.** Deferred — only the gameweek decide needs it now; the
  Ask tab has no horizon control, so the other decides keep the `_HORIZON` default.
- **A wider range (to 38).** Rejected — beyond ~8 GW the projection is too noisy to act on; 1–8 is the useful
  planning window.

---

### 🧭 Consequences

**Positive**
- A manager plans over the horizon that matters (short mid-season, long for a wildcard/start), across the
  whole Squads tab.
- Reuses the existing horizon params — no analytics change; default 5 preserves current behaviour.
- Captain stays honest (next-GW); the analysis label already adapts.

**Negative / risks (mitigations)**
- **A longer horizon is noisier** (fixtures further out are less certain) → the manager chooses; the tool
  shows what it's asked. Preseason all data is carryover anyway.
- **The `ask` change touches a shared helper (`_squad_xp`)** → a defaulted `horizon` keyword keeps the other
  decides (transfer/analyse/start-bench) and the CLI/Ask-tab behaviour identical (a test pins default 5).
- **Build over a long horizon changes the "best" 15** → intended (wildcard planning); the preview/compare
  already show the effect.

---

### 📊 Validation

Verified: the web views currently use horizon 5 implicitly; the analytics + renderer already parameterise it.
Acceptance: the Squads page has a "Gameweeks ahead" dropdown (default 5); setting it to 2 makes Health/My
Squad/Transfer/Build project over 2 GW (the analysis window + `by_gameweek` reflect 2); `ask.answer(horizon=2)`
yields a gameweek plan whose transfer line reads "over 2 GW"; Captain is unchanged; the CLI / Ask tab keep the
5-GW default; the existing 625 tests stay green (new tests added).
