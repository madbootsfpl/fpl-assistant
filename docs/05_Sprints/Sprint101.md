# Sprint 101: Pitch on Build + a season countdown / deadline banner

**Dates:** 2026-08-07 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (reuse the pitch on Build; a deadline banner derived from fixtures)
**Carried Over:** none

> **Direction (owner):** *"let's get these 2 done — pitch-on-Build reuse, a season countdown / deadline
> banner."*

---

### 🔎 Verified at planning (real data)

- **The pitch is reusable as-is.** `web_streamlit/pitch.py::render_pitch(xi, bench, …)` (ADR-084) is a pure
  presentation over data the Build page already holds — the built 15, `best_legal_xi` (the XI), `bench_order`
  (the bench roles), the horizon xP, photos and the next-opponent map. So Build can show its result **on the
  same green pitch** with no new analytics.
- **The next deadline can be derived from fixtures — no new ingest.** Every fixture carries a populated
  `kickoff_time` (verified: **380/380**). The FPL deadline is **90 minutes before the first match** of a
  gameweek, so the next deadline = the earliest `kickoff_time` of the next unfinished gameweek − 90 min. There
  is **no `events` table** and we don't need one (the owner's lightweight-over-completeness preference).
  Verified: GW1's earliest kickoff is `2026-08-21T19:00Z` → deadline **17:30 UTC (18:30 UK)**, ~**14 days**
  away today. It rolls to the next GW automatically all season.
- **`get_upcoming_fixtures` doesn't return `kickoff_time`** (it's in the table, not the SELECT) — one additive
  column to the query unlocks the banner; existing callers ignore the extra field.

---

### 🎯 Sprint Goal

**Objective:** (1) the **Build** page shows its optimal 15 on the **green pitch** (reusing ADR-084), not only
a table; (2) a **season countdown / deadline banner** — "the GW1 deadline is in 14 days" — surfaces the next
FPL deadline across the app, derived from fixtures.

#### Success Criteria
- [ ] **US-261 (pitch on Build)** — `render_build` renders the built 15 on `render_pitch` (XI + bench, the
      bench in `bench_order`, no captain), above the existing sortable table (the picture *and* the detail).
      Display-only; reuses the horizon xP + photos the page already computes.
- [ ] **US-262 (deadline banner, ADR-086)** — a pure `analytics.next_deadline(fixtures, now)` → `(gameweek,
      deadline)` for the next gameweek whose deadline is still ahead (earliest kickoff − 90 min), or None; a
      `ui`/web renderer `deadline_banner` → *"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 14 days"* (UK time
      via `zoneinfo`). `get_upcoming_fixtures` returns `kickoff_time`. Shown on **Home** (prominent) + a compact
      line on **Squads**. Empty-safe (no fixtures / all finished → nothing).
- [ ] **No drift** — display-only; the analytics/engine + `decision_xp` unchanged; existing **672** stay green;
      ruff clean.
- [ ] Docs: ADR-086 + index, PROJECT_STATUS, Architecture, Roadmap, README, Help.

---

### 🧭 Design sketch

**US-261.** In `views/squads.py::render_build`, after the solve, split `selected` into the XI (`best_legal_xi`
on the display xP) + bench, compute `bench_roles` via `bench_order` (as My Squad does), and call
`render_pitch(xi, bench, captain_id=None, xp_by_id=display_xp, photos=photos, next_opp=next_opp,
bench_roles=bench_roles)` **above** the existing `render_player_table` + `render_squad` block. `next_opp` is the
team→next-fixture map the pitch needs (build it from `get_upcoming_fixtures` like My Squad, or a shared
helper). No engine change.

**US-262 (ADR-086).** `analytics/deadline.py::next_deadline(fixtures, now)` — group upcoming fixtures by
`event`, take each GW's earliest `kickoff_time`, subtract 90 minutes, and return the first `(gw, deadline)`
with `deadline > now` (so it rolls forward mid-GW); pure, tz-aware (parse the ISO `Z`), None when nothing is
ahead. `storage.get_upcoming_fixtures` adds `f.kickoff_time` to the SELECT. A renderer `deadline_banner(gw,
deadline, now)` → the countdown string (days/hours) + the date in **Europe/London** (`zoneinfo`, stdlib). The
web pages pass `datetime.now(timezone.utc)`; Home shows it as a banner (`st.info`/a metric), Squads a compact
caption. Season-long (rolls each GW); preseason it counts down to GW1.

**Deferred:** ingesting `events.deadline_time` (the API's exact deadline) — the fixtures derivation matches it
(kickoff − 90) and needs no new table; a live-ticking countdown (needs JS/auto-refresh — the banner recomputes
each interaction).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-261 | **Pitch on Build** — show the optimal 15 on the green pitch (reuse `render_pitch`), above the table. | High | ⬜ To do | ~⅓ session |
| US-262 | **Season countdown / deadline banner** — a pure `next_deadline` from fixtures + a banner on Home/Squads. ADR-086. | High | ⬜ To do | ~⅔ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Build page renders the pitch (`fpl-pitch` in the markdown) alongside its table;
   `next_deadline` returns the next-GW deadline (earliest kickoff − 90) and **rolls forward** when a GW's
   deadline has passed, None when nothing's ahead; `deadline_banner` formats the countdown + UK date; the Home
   banner renders. Existing **672** stay green.
2. **Manual smoke** — Build shows the 15 on a pitch; Home shows *"⏳ GW1 deadline … in 14 days"*; with the DB
   refreshed mid-season it would show the next GW's deadline.
3. **Docs updated** — ADR-086 + index, PROJECT_STATUS, Architecture, Roadmap, README, Help.

---

### 📝 Session Progress Log

**US-261 — pitch on Build (reuses ADR-084).** ✅ Done.
- `views/squads.py::render_build`: after the solve, split `selected` into the XI (`best_legal_xi`) + bench,
  order the bench via `bench_order`, build the `next_opp` map (`team_schedule`), and `render_pitch(xi, bench,
  captain_id=None, xp_by_id=display_xp, …)` **above** the existing sortable table + `render_squad` block — the
  picture *and* the detail. No captain on a fresh build; display-only, no engine change.
- **Tests (+1):** the Build page renders the pitch (`fpl-pitch` + **15** `.kit` cards) alongside its table.
  **673** green, ruff clean.
- **Manual smoke:** Build shows the optimal 15 on the green pitch (XI in formation + bench strip), with the
  table beneath.

**US-262 — season countdown / deadline banner (ADR-086).** ✅ Done.
- `analytics/deadline.py::next_deadline(fixtures, now)` — pure, tz-aware: each gameweek's **earliest**
  `kickoff_time` − 90 min; returns the first `(gw, deadline)` still ahead of `now`, **rolling forward** once a
  deadline passes; empty-safe (no event/kickoff → skipped, None when nothing ahead). Exported from `analytics`.
- `storage.get_upcoming_fixtures` now returns `f.kickoff_time` (additive; existing callers ignore it).
- `ui/deadline.py::deadline_banner(gw, deadline, now)` → *"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 14
  days"* — a days/hours countdown + the date in **UK time** (stdlib `zoneinfo`).
- Wired: a prominent `st.info` banner on **Home** + a compact caption on **Squads**, each passing
  `datetime.now(timezone.utc)`. Empty-safe (no deadline → nothing).
- **Tests (+6):** `next_deadline` (earliest − 90, roll-forward, empty-safe); `deadline_banner` (UK time +
  the countdown, and an hours/minutes case); the Home banner renders. **679** green, ruff clean.
- **Manual smoke:** Home + Squads show *"⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 13 days, 21h"* (17:30
  UTC → 18:30 BST); rolls to GW2 once GW1's deadline passes. No new ingest — derived from fixtures.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **672 → 679** (+7); ruff clean; CI-parity green.
ADRs **85 → 86** (ADR-086). No engine change (a pitch reuse + a pure derivation + a display).

**Delivered**
- **US-261 — pitch on Build.** The optimal 15 render on the green pitch (reuse `render_pitch`, ADR-084) above
  the sortable table — the picture *and* the detail.
- **US-262 — deadline banner (ADR-086).** A pure `next_deadline(fixtures, now)` (earliest kickoff − 90 min,
  rolling each GW) + `deadline_banner` (countdown + UK time), on Home + Squads. No new ingest.

**What went well**
- **Both were reuse, not new machinery** — the pitch was already a pure renderer; the deadline came from the
  `kickoff_time` we already store. Small, low-risk changes.
- **Verified the data first** — 380/380 fixtures carry `kickoff_time`, so the derive-from-fixtures call (no
  `events` table) was a safe, lightweight decision (owner's preference, ADR-016).
- **Pure + `now`-injected** — `next_deadline`/`deadline_banner` are deterministic and unit-tested (including
  the roll-forward and the UK-time conversion); no flaky "today" tests.
- **It rolls all season** — a countdown to GW1 now, the next GW's deadline once the season starts.

**Watch-outs / follow-ups**
- **Derived deadline vs the API's exact `deadline_time`** — they match (kickoff − 90); a later `events` ingest
  could pin it if FPL ever set an atypical deadline (deferred).
- **No live tick** — the banner recomputes each interaction (fine for a days-away deadline; a JS ticker was
  out of scope).
- **Build now solves + renders a pitch + a table** — a touch more render work per Build; still snappy.

See `Sprint101_Lessons_Learnt.md` for the detailed retro.
