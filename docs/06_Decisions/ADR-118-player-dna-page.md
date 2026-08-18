# Architectural Decision Record: Player DNA — a rich single-player analysis page

**Decision ID:** ADR-118
**Date:** 2026-08-18
**Status:** Accepted — owner-approved from a real-data preview. Build = **post-GW1** (the time-series panels need
in-season data anyway). Preview: `scratchpad/player_dna_preview.html` (real Haaland numbers).
**Superseded By / Replaces:** Evolves the existing **player card** (ADR-084) into a full page. Reuses the
percentile/analytics engine, the brand tokens (ADR-114), the FDR colours (S166), the Watchlist ⭐ (ADR-117) and the
fixtures/FDR view. Does **not** change `decision_xp`.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner idea (2026-08-18): a **differentiator** for MADBOOTS — a rich, single-player analysis page (a "Player DNA"
dashboard) that goes well beyond the current card. The reference mockup showed a percentile radar, an AI verdict,
per-90 rates, a performance trend, a shot map, a fixture run and AI insights.

The question was **feasibility**: how much of that can we build with the data we hold and with Streamlit, and where
are we limited? A real-data preview (Haaland — Salah has left the league) answered it and the owner approved the
shape. This ADR records **what we're building, in which order, and what we're deliberately leaving out.**

#### Decision Drivers
- **On-brand.** *The analytics decide, the AI explains, you make the call* — a page that shows a player's shape and
  reasons about it is the brand in one screen.
- **Build on data we already have.** ~70% is buildable today; another slice self-populates from GW1; one corner
  needs event data we deferred (ADR-016).
- **No tab bloat / no duplication.** One component, reachable from two places (owner steer: too many tabs already).
- **Honesty over gloss.** Don't fake time-series or dress a proxy up as real event data — show what's live vs
  what arrives later (the preview does exactly this with per-panel badges).

---

### ✅ Decision *(owner-approved: dark brand look · these radar axes · Players = home, My Squad links in)*

**1. Placement — one component, two doorways (no new tab, no subtab).** The Player DNA page **is** the evolved
player card and **lives on the Players tab** (browse pool → open any of ~590 players → deep-dive). **My Squad ▸
Players & lineup** opens the *same* component for a tapped squad player. A standalone "Player DNA" subtab under My
Squad was rejected — it could only ever show your 15; the page's job is *any* player.

**2. Build tiers — ship the live core first; the rest self-populates.** Each panel is gated by the data behind it:

- 🟢 **Live now (v1 core):**
  - **Player DNA radar** — 8 axes, **percentile-within-position** (a cross-sectional rank, so it works preseason):
    Goal Threat (xG/90) · Creativity (xA/90) · Set-Piece involvement (penalty/corner/FK order) · FPL Output
    (pts/90) · Consistency (minutes) · Value (pts/£m) · Bonus Potential (**ICT/90 proxy** — we don't store raw
    BPS) · Team Attack (team xG). Axes are owner-approved and easy to revisit.
  - **AI Verdict** — a Buy/Hold/Sell + a 0–100 score + a grounded one-liner, derived from the existing
    xP/Edge/Risk/ownership signals (no new model).
  - **Key-rate cards** (xG/90, xA/90, pts/90, goals) with percentile.
  - **Fixture Run** (next 5, FDR — mirrors the official colours) and **AI Insights** bullets (grounded facts).
- 🟡 **From GW1 (auto-populates, no extra decision):** the **Performance Trend** line (xGI/90 per GW vs positional
  avg), the card **sparklines**, and the **form W-D-L dots** — all need per-GW history, which is wired and dormant
  until the season starts. v1 renders honest "fills in from GW1" states in these slots.
- 🔴 **Not in v1 (needs event data):** the **Shot Map** (shot x/y, big chances, xG-per-shot) is Opta/Understat
  event data we deliberately don't carry (ADR-016). Shown as a clearly-gated "not in v1" panel; a future "Pro"
  add-on behind **its own ADR** if we ever take on `soccerdata`.

**3. Look.** Dark, brand-purple/teal product surface (deliberate single-theme — it's the intended identity, per the
approved preview), built from the brand tokens (ADR-114) and FDR colours. Radar drawn client-side; no new data
dependency.

**What this is *not*.** Not a change to `decision_xp` or the Radar algorithm. Not a new tab or subtab. Not a shot
map (v1). Not a custom React frontend — Streamlit gets ~80% of the bespoke polish; a custom component/frontend is
**out of scope** and only revisited if this becomes *the* flagship and pixel-parity starts mattering commercially.

---

### 🔀 Alternatives Considered

- **A "Player DNA" subtab under My Squad.** Rejected (owner + reuse) — it could only show your 15; the page must
  serve any player, so it belongs on Players, reused from My Squad.
- **Build the whole mockup at once (incl. shot map).** Rejected — the shot map needs an event-data source we
  deferred; bundling it would either delay the whole feature or force a proxy-dressed-as-real (breaks the brand).
- **Take on `soccerdata`/Understat now for shots & touches.** Deferred — reverses ADR-016 and adds scraping /
  reliability / complexity debt against the owner's lightweight-over-completeness preference. Its own future ADR.
- **A custom React frontend for pixel-parity.** Rejected for now — large scope change; the Streamlit version is a
  genuine differentiator on its own.
- **Build before GW1.** Rejected — half the panels need in-season data, and the next 3 days are the GW1 runbook.

---

### 🧭 Consequences

**Positive** — a genuine differentiator built mostly on data we already hold; the radar + verdict land day one; the
🟡 panels light up for free at GW1; no new tab, no duplication, no new data dependency; honest about what's not
there.
**Negative / risks (mitigations)** — Bonus-Potential is an ICT proxy (*mitigation:* labelled as such; swappable);
Streamlit won't match a bespoke frontend's polish (*mitigation:* accepted; revisit only if flagship); the shot map
is a visible gap (*mitigation:* framed as a deliberate "Pro" future, not a bug); percentile pools are noisy for
low-minute players (*mitigation:* a minutes floor, as in the preview).

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**post-GW1 sprint**): evolve the player card → full page; the radar (percentile-in-position,
  minutes floor); the AI Verdict from existing signals; key-rate cards; wire the Players entry + the My Squad ▸
  Players-&-lineup entry to the one component; honest GW1/event-data placeholders; 3-part DoD (tests + smoke +
  docs).
- **Not this ADR / follow-ups:** the Shot Map + Shots/90 + Touches-in-Box (its own `soccerdata` ADR); a
  Compare-on-DNA view (extends ADR-110); a custom component/frontend if pixel-parity ever matters; revisiting the
  radar axes after real GW data.

**Build progress (the ADR-118 arc):**
- ✅ **Sprint 168 — the percentile radar (US-410/411).** `src/analytics/player_dna.py` (the pure
  percentile-within-position engine, 8 axes, dict/`Row`-safe) + `src/web_streamlit/dna_card.py` (a **server-built
  SVG** radar — `st.markdown` can't run `<script>`, so not the preview's canvas) wired into **Players ▸ Card**.
  +18 tests; no `decision_xp` change; live-render verified on real data (Haaland/Gabriel/B.Fernandes).
- ◻ **Sprint 169 — the AI Verdict** (Buy/Hold/Sell + a 0–100 gauge + a grounded line, reusing `explain_worth`).
- ◻ **Sprint 170 — key-rate cards + AI Insights** (reuse the engine's percentiles).
- ◻ **Sprint 171 — the full-page reflow + the My Squad ▸ Players & lineup entry + 🟡 GW1 placeholders.**
