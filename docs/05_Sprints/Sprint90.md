# Sprint 090: A quick-stats summary on the My Squad banner

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a metrics row + a flagged-players line, all from data already on hand)
**Carried Over:** none

> **Direction (owner, tester feedback):**
> Squads → **My Squad**: the green banner only shows *"£99.5m — ✓ a legal 15"*, and there's real estate to
> add a **quick-view summary** of the team — **xP over the selected gameweeks**, **how many players are
> injured / suspended**, etc. *(Confirmed: include all — the projected XI xP, availability counts, who's
> flagged by name, and bench + captain xP.)*

---

### 🔎 Verified at planning (code)

- **Everything's already on hand in `render_my_squad`** — `owned` (with `status`/`chance`/`price`), the
  **horizon-aware** `xp_by_id` (ADR-077's *Gameweeks ahead*), the XI/bench split (`bench_ids`), the
  `captain_id`, and the `cost`/legal-15 check. So the summary is **display-only**, reusing existing data —
  no analytics change.
- **Reuse the existing helpers** — `is_unavailable` (i/s/u/n) + `status == "d"` for the counts, and
  `availability_flag` (ADR-074, now with a chance% on ❓) for the "who's flagged" line.
- **`st.metric`** is the clean fit (as on Build's formation preview / AI Tips); it renders a scannable row.
- **The horizon flows in** — the Projected-XI number updates as the *Gameweeks ahead* dropdown changes; the
  metric label carries the window ("5 GW" / "next GW").

---

### 🎯 Sprint Goal

**Objective:** the My Squad banner becomes a **quick-view team summary** — projected XI xP over the chosen
horizon, the captain's (doubled) xP, bench strength, and an availability snapshot (counts + who's flagged) —
above the existing pitch. Display-only; no analytics change.

#### Success Criteria
- [x] **US-239 (the metrics row)** — above the pitch, a compact `st.metric` row: **Projected XI (N GW)** ·
      **Captain (2×)** · **Bench xP** · **Unavailable** (🚑/🚫/⛔ count) · **Doubtful** (❓ count). The
      £value / legal-15 banner stays. The Projected-XI figure reflects the *Gameweeks ahead* horizon; a
      missing captain shows "—".
- [x] **US-240 (who's flagged)** — a caption naming the flagged players with their flag (reusing
      `availability_flag`, e.g. *"Saliba 🚑 · Wharton ❓ 75%"*), or **"✓ all 15 available"** when none.
- [ ] **No drift** — display-only; `decision_xp`/the analytics unchanged; existing **627** stay green; ruff
      clean. No new ADR (reuses ADR-074/077).
- [ ] Docs: PROJECT_STATUS, Architecture, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-239 | **My Squad summary metrics** — a metrics row (Projected XI over N GW · Captain 2× · Bench xP · Unavailable · Doubtful) above the pitch. | High | ✅ Done | ~¼ session |
| US-240 | **Who's flagged** — a caption naming the injured/suspended/doubtful players (with flags), else "all 15 available". | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-239.** In `render_my_squad`, after the legal-15 banner and once `xi`/`bench` are known, compute
`xi_xp = sum(xp_by_id[p] for p in xi)`, `bench_xp = sum(... for p in bench)`, `cap_xp = xp_by_id.get(
captain_id)` (×2), `unavailable = Σ is_unavailable(owned)`, `doubtful = Σ status == "d"`. Render a
`st.columns(5)` of `st.metric`s: `Projected XI ({horizon} GW)` · `Captain (2×)` · `Bench` · `Unavailable` ·
`Doubtful` (helps on each). (Move the `xi`/`bench` split above the summary.)

**US-240.** Build `flagged = [(p, availability_flag(p)) for p in owned if availability_flag(p)]`; render a
caption `"⚠ Flagged: " + " · ".join(f"{p['web_name']} {flag}")` or `"✓ All 15 available."`. `availability_flag`
already appends the chance% on doubtful (US-236), so a doubtful reads `❓ 75%`.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — My Squad shows a Projected-XI metric whose label reflects the horizon (set Gameweeks to 2
   → "2 GW"); the availability metrics count a known-injured / doubtful squad correctly; the flagged caption
   names them (or "all 15 available" for a clean squad). Existing **627** stay green.
2. **Manual smoke** — My Squad shows the metrics row + the flagged line; changing *Gameweeks ahead* moves the
   Projected-XI number; a squad with an injured player names them.
3. **Docs updated** — PROJECT_STATUS, Architecture, README.

---

### 📝 Session Progress Log

**US-239 (the metrics row).** Above the pitch, `render_my_squad` now renders a `st.columns(5)` of
`st.metric`s — **Projected XI ({horizon} GW)** · **Captain (2×)** · **Bench** · **Unavailable** · **Doubtful**
— reusing the horizon-aware `xp_by_id`, `is_unavailable`, and `captain_id`; the £value / legal-15 banner
stays. The **Projected XI** uses the declared XI (if a bench is set) else `best_legal_xi` — same as Health —
so it's the best **11** (not all 15), with **Bench** the other 4 (verified: 236.6 XI + 63.8 bench = the old
all-15 300.4). The label tracks the *Gameweeks ahead* selector ("2 GW" when set to 2). Captain shows "—"
when none is set. Display-only; no analytics change; no new ADR. +1 test
(`test_my_squad_shows_a_quick_stats_summary`). ruff clean, full suite **628** green.

**US-240 (who's flagged).** Below the metrics, a caption names the flagged owned players with their flag —
`flagged = [(p, availability_flag(p)) for p in owned if availability_flag(p)]` → *"⚠ Flagged: Garner 🚑 —
see the News tab for detail."* (❓ carries the chance%, US-236), or **"✓ All 15 available."** when none.
Reuses `availability_flag` (ADR-074). Smoke: the demo squad → all-clear; a squad with an injured player →
names them + 🚑. +1 test (`test_my_squad_flags_unavailable_players_by_name`, a session squad with an injured
player). ruff clean, full suite **629** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **627 → 629** (+2); ruff clean; CI-parity green. No
new ADR (reuses ADR-074/077).

**Delivered**
- **US-239 — the metrics row.** Above the pitch: Projected XI (N GW) · Captain (2×) · Bench · Unavailable ·
  Doubtful, alongside the existing £value / legal-15 banner.
- **US-240 — who's flagged.** A caption naming the injured/suspended/doubtful players (with flags), else
  "✓ all 15 available".

**What went well**
- **All from data already on hand** — the horizon-aware `xp_by_id`, `is_unavailable`, `availability_flag`
  (with the US-236 chance%), and `captain_id`. Display-only, no analytics change, no new ADR.
- **It compounds prior sprints** — the Projected-XI metric moves with the Sprint-089 *Gameweeks ahead*
  selector, and the flagged line reuses the Sprint-088 chance% on ❓.
- **A correctness catch** — "Projected XI" uses the best legal XI (11), not all 15, matching Health.

**Watch-outs / follow-ups**
- The pitch still shows all 15 when no bench is declared (pre-existing); the summary uses the best XI, so
  the numbers are meaningful either way.
- A benign `seed.db` byte-touch can appear after a manual AppTest smoke (content unchanged, 572=572); pytest
  itself leaves it clean. Habit: `git checkout -- data/seed.db` before staging if it shows dirty.

See `Sprint90_Lessons_Learnt.md` for the detailed retro.
