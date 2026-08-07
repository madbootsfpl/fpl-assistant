# Sprint 098: Club-shirt image fallback + captain double-points in the My Squad projection

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (a cached image resolver + a captaincy-aware projected-XI total)
**Carried Over:** none

> **Direction (tester feedback):**
> 1. *"Squad & Player: if we don't have a player image, could we just use the **club shirt** [like the
>    attached]?"*
> 2. *"MySquad: when I select a captain, the GW xP does **not account for the captain double points**. I assume
>    same for chips. Also should captain be adjusted for **next gameweek** or **all selected**? Chips have to be
>    next gameweek only. Is this feasible?"*
>
> **Owner steer (this planning):** apply the captain double for **next GW only**, and **note** on the UI that
> the ×2 counts for one GW when a multi-GW horizon is selected.

---

### 🔎 Verified at planning (real data — the live DB / CDN)

- **Missing photos are common and it's a *broken file*, not a null code.** All **573** players carry a photo
  `code`, yet the CDN **403s** the photo for ~**25%** (5/20 sampled — new/lower-profile players, e.g. McNally,
  Tchaouna). So a "code is None" check can't catch it — we need an **existence check**. The **club-shirt**
  images resolve (200): `…/dist/img/shirts/standard/shirt_{team_code}-66.png` (outfield) and
  `shirt_{team_code}_1-66.png` (GK). Team `code` is stored (ARS=3). *(The app already needs the internet at
  render to show any badge/photo, so an existence check doesn't break a property we had.)*
- **The projected-XI total ignores the captain's double.** `render_my_squad` shows **"Projected XI (N GW)"** =
  the plain XI xP sum (no doubling), and a *separate* **"Captain (2×)"** metric that doubles the captain's
  **whole-horizon** xP — so the headline never reflects the ×2, exactly as reported.
- **The next-GW captain figure is available.** `decision_xp` already returns each player's **`by_gameweek`**
  (`{gw → xP}`), so the captain's **next-GW** xP is in hand. Real example (RoboTS, captain B.Fernandes):
  XI over 5 GW = **236.6**; captain next-GW xP = **5.9** → **242.5** incl. ×2 next-GW (vs the optimistic
  whole-horizon +27.3 → 263.9, which we are **not** doing).
- **Chips are next-GW by nature** (Triple Captain / Bench Boost are single-GW) — consistent with the owner's
  "next GW only" steer; My Squad won't get a chip toggle this sprint (the **Chips** tab covers chip timing).

---

### 🎯 Sprint Goal

**Objective:** (1) every player card/table shows an image — the **photo when it exists, else the club shirt**;
(2) the My Squad **Projected XI** total reflects the **captain's ×2 for the next GW**, with a clear note that
the double counts for one GW when a longer horizon is selected.

#### Success Criteria
- [ ] **US-255 (club-shirt image fallback)** — a resolver returns the player **photo** when the CDN has it,
      else the **club shirt** (GK variant for keepers). Detection is a **cached** existence sweep (degrade to
      the photo on any error — never worse than today). Applied to the **pitch cards** and the **Player /
      squad tables** (the `photo` column). Web-edge only; no ingest/schema change.
- [ ] **US-256 (captain double-points, next-GW only — ADR-083)** — the My Squad **"Projected XI (N GW)"**
      total adds the captain's **next-GW** xP once (the ×2 bonus), when a captain is set **and in the XI**; a
      **caption notes the ×2 is for the next GW only** (shown whenever the horizon > 1). The **"Captain (2×)"**
      metric is reframed to the captain's **next-GW** doubled value (consistent). Display-only — `decision_xp`/
      the engine unchanged.
- [ ] **No drift** — existing **659** stay green (any image/summary assertions updated); ruff clean.
- [ ] Docs: ADR-083 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 🧭 Design sketch

**US-255.** `web_streamlit/badges.py`: add the shirt URLs + a resolver. Detection: one **cached** sweep
`missing_photo_codes(codes) -> frozenset` (`@st.cache_data`, long TTL) that checks each photo URL's status in
a small thread pool with a short timeout, returning the set that 403/fails; **degrade to an empty set** on any
error (→ keep every photo, today's behaviour). `photo_url_by_id(players, teams)` then returns the shirt
(`shirt_{team_code}[ _1]-66.png`, GK by `position`) for a code in that set, else the photo. Threads the
`teams` (for the short_name→code map) through the Players/Squads pages. One sweep warms the cache; render stays
offline after.

**US-256 (ADR-083).** `render_my_squad`: also pull `by_gameweek_by_id` from the `decision_xp` pass. Compute
`cap_next = by_gameweek_by_id[captain_id][gameweeks[0]]` when a captain is set and `captain_id in xi_ids`;
**Projected XI = xi_xp + cap_next** (the single ×2 bonus, next GW only). Label stays "Projected XI (N GW)";
`help` + a **caption** state the captain ×2 counts for the **next GW only** (rendered when horizon > 1). The
"Captain (2×)" metric shows `cap_next * 2` (next-GW doubled) with a matching note. If the captain is benched /
unset → no bonus (and the caption says so). No engine change.

**Deferred:** a chip toggle on My Squad (the **Chips** tab already models TC/BB, next-GW); precomputing photo
existence at `refresh` (the cached edge sweep is simpler and offline-after-warm).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-255 | **Club-shirt image fallback** — a cached photo-existence resolver → photo-or-shirt on the pitch cards + the Player/squad tables. | High | ⬜ To do | ~½ session |
| US-256 | **Captain double-points (next-GW only)** — the My Squad Projected-XI total includes the captain's ×2 next-GW, with a clear one-GW note. ADR-083. | High | ⬜ To do | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the resolver returns a shirt URL for a "missing" code and the photo for a present one (the
   sweep monkeypatched, no live network in tests); the GK shirt variant for a keeper; the My Squad Projected-XI
   total equals `XI + captain-next-GW` (a crafted squad + `by_gameweek`), and shows the one-GW note; a benched/
   unset captain adds no bonus. Existing **659** stay green.
2. **Manual smoke** — Players/Squads: a player with no CDN photo (e.g. Tchaouna) shows their club shirt; a
   keeper shows the GK shirt; My Squad Projected XI = 242.5 for RoboTS w/ B.Fernandes (C), with the "×2 next GW
   only" caption; changing the captain / the horizon updates it.
3. **Docs updated** — ADR-083 + index, PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-255 — Club-shirt image fallback.** ✅ Done.
- `badges.py`: `shirt_url(team_code, position)` (GK `_1` variant); a cached daily sweep
  `_missing_photo_codes(codes)` (threaded HEADs, 2.5s timeout, **degrades to "all present"** on any error);
  `photo_url_by_id(players, teams)` now returns the **photo when the CDN serves it, else the club shirt** (GK
  variant for keepers). `teams` threaded through the Players/Squads/Trending/News pages.
- **Test-safety:** an **autouse `conftest.py` fixture** patches the sweep to "nothing missing", so the suite
  stays offline + fast (verified: 661 tests in ~45s, unchanged) — the fallback logic is covered by a unit test
  that supplies a specific missing set.
- **Tests (+2):** `shirt_url` (outfield vs GK vs no-code); `photo_url_by_id` falls back to the shirt for a
  missing photo (GK variant for a keeper) and keeps a served photo. Existing photo/badge tests unchanged
  (teams-less path preserved). **661** green, ruff clean.
- **Real-network smoke:** the sweep correctly flags Tchaouna (469272) + McNally (505079, GK) as missing →
  outfield / GK **club shirt** (SUN code 56), while Haaland (223094) keeps his **photo**. No schema/ingest
  change; works immediately (no refresh needed); one ~daily cached sweep warms it.

**US-256 — Captain double-points, next-GW only (ADR-083).** ✅ Done.
- A pure `web_streamlit/squads.py::captain_bonus(captain_id, xi_ids, by_gameweek_by_id, next_gw)` → the
  captain's **next-GW** xP, but only when the captain is **set and in the XI** (benched/unset → 0). Empty-safe.
- `render_my_squad`: pulls `by_gameweek` + `next_gw` from the `decision_xp` pass; **Projected XI (N GW)** =
  `XI over N GW + captain_bonus` (the ×2 for next GW only); **"Captain (2×)"** reframed to the captain's
  **next-GW** doubled value; a **caption** states the ×2 is for the **next gameweek only** when horizon > 1
  (owner steer), and notes when the captain is benched.
- **Tests (+2):** `captain_bonus` (starting → next-GW xP; benched/unset/no-GW → 0); a My Squad AppTest asserts
  Projected XI = `XI + captain-next-GW` with a captain injected, and the one-GW caption shows. **663** green,
  ruff clean.
- **Manual smoke (RoboTS + B.Fernandes ©):** Projected XI **242.5** (= 236.6 + 5.9), Captain (2×) **11.8**,
  caption *"…doubled for the next gameweek only (+5.9 xP); the other 4 GW count once…"*. Display-only —
  `decision_xp`/the engine unchanged.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
