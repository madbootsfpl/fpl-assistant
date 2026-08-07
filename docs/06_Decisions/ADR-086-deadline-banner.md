# Architectural Decision Record: A season countdown / deadline banner (derived from fixtures)

**Decision ID:** ADR-086
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new display + a small pure analytic. No schema/ingest change. Triggered by an
owner request ("a season countdown / deadline banner").
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner request: *"a season countdown / deadline banner."* The app should surface the **next FPL deadline** —
useful all season, and a countdown to **GW1 (2026-08-21)** right now.

**Verified:** every fixture carries a populated `kickoff_time` (380/380). The FPL deadline is **90 minutes
before the first match** of a gameweek, so the next deadline is derivable: the earliest `kickoff_time` of the
next unfinished gameweek, minus 90 minutes. There is **no `events` table** and (per the owner's
lightweight-over-completeness preference, ADR-016) we don't need one — the derivation matches the API's exact
`deadline_time`. `get_upcoming_fixtures` doesn't currently return `kickoff_time`, but the column is stored.

#### Decision Drivers
- **Surface the next deadline** — a countdown that's useful preseason (→ GW1) and rolls forward all season.
- **Lightweight** — reuse the stored `kickoff_time`; no new table, no new ingest.
- **Testable + honest** — a pure function taking `now`; empty-safe; degrade to nothing when no fixtures.

---

### ✅ Decision

**1. Derive the deadline from fixtures (US-262).** A pure `analytics/deadline.py::next_deadline(fixtures, now)`
— groups upcoming fixtures by `event`, takes each gameweek's **earliest** `kickoff_time`, subtracts **90
minutes**, and returns the first `(gameweek, deadline)` whose `deadline > now` (so it **rolls forward** once a
gameweek's deadline passes). Timezone-aware (parses the ISO `Z`); returns `None` when nothing is ahead or no
fixture has a kickoff time. `storage.get_upcoming_fixtures` adds `f.kickoff_time` to its SELECT (additive;
existing callers ignore it).

**2. A banner renderer (US-262).** `ui/deadline.py::deadline_banner(gameweek, deadline, now)` → a string like
*"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 14 days"*: a human countdown (days/hours) + the date in **UK
time** (`zoneinfo`, "Europe/London", stdlib). Pure — the caller passes `now`.

**3. Where it shows.** The web computes `now = datetime.now(timezone.utc)` and shows the banner **prominently on
Home** (`st.info`) and as a **compact caption on Squads**. Empty-safe (no deadline ahead → nothing shown).

---

### 🔀 Alternatives Considered

- **Ingest `events.deadline_time`** (the API's exact deadline). Rejected — a new table + ingest for a value the
  fixtures derivation already matches (kickoff − 90). Reconsider only if we need per-GW deadline metadata for
  something else.
- **A live-ticking countdown.** Rejected — needs JS / an auto-refresh component; the banner recomputes each
  interaction, which is enough for a deadline days/hours away.
- **A banner on every page.** Rejected — intrusive; Home (prominent) + Squads (compact) is where it helps.

---

### 🧭 Consequences

**Positive**
- The next deadline is visible, preseason and all season (it rolls each GW), with zero new data.
- Pure + `now`-injected → unit-tested deterministically; degrades to nothing when there's no fixture data.

**Negative / risks (mitigations)**
- **Derivation vs the API's exact deadline** → they match (kickoff − 90); if FPL ever set an atypical deadline
  for a GW, we'd be off by minutes — acceptable for a countdown, and a later `events` ingest could pin it.
- **Timezone** → shown in **UK time** (FPL is UK-based) via stdlib `zoneinfo`; the countdown itself is
  tz-agnostic (UTC math).
- **"now" in the app** → passed in from the web edge (`datetime.now`); the core function stays pure/testable.

---

### 📊 Validation

Verified: 380/380 fixtures carry `kickoff_time`; GW1's earliest is `2026-08-21T19:00Z` → deadline 17:30 UTC
(18:30 UK), ~14 days out today. Acceptance: `next_deadline` returns the next-GW deadline (earliest kickoff −
90) and **rolls forward** when a gameweek's deadline is in the past, `None` when nothing's ahead / no kickoff;
`deadline_banner` formats the countdown + the UK date; the Home banner renders; existing **673** tests stay
green (new tests added); ruff clean.
