# Sprint 155: Boot Battle compare-pool selector (extends ADR-110/111)

**Dates:** 2026-08-13
**Status:** ✅ Complete — US-380 (no ADR). 985 → 986 tests
**Capacity:** ~½ session
**Carried Over:** none

> **Direction:** a well-received-feature enhancement (2026-08-13 PM testing) — on the My Squad ⚙ panel's **⚔️ Boot
> Battle**, add a **pool selector**: **My team** (same-position owned — today's behaviour) · **All players**
> (same-position, whole pool) · **By club** (same-position, one chosen club). Reuses `compare_card_html`; the compare
> target's per-GW fixtures are built on demand (`card_bg_by_id`/`xp_by_id` already cover all players).

---

### 🔎 Verified at planning (on the code)

- `ranked = decision_xp(players, …)` is over **all** players → `xp_by_id` + `card_bg_by_id` cover **any** player.
- `fixtures_by_id` is built only for **owned** players → a non-owned target needs its per-GW fixtures built on demand
  (same `team_schedule` + `card_bg_by_id` logic → extract a `_pergw_fixtures(p)` helper).
- The ⚙ panel Boot Battle today: `bb` scoped to **same-position owned** (US-377).

---

### 🎯 Sprint Goal

The ⚙ panel Boot Battle lets you pick the compare pool (My team · All · By club), all same-position, and compares
against any of them — with the suite green.

#### Success criteria
- [ ] **US-380 (pool selector)** — before the "compare with…" picker, a **"⚔️ Boot Battle — pool"** segmented control
      (**My team** default · **All** · **By club**); **By club** reveals a **Club** picker. The candidate list =
      the chosen pool, **same position** as the selected player, excluding it. Compare via `render_player_compare`
      with the target's per-GW fixtures built on demand (`_pergw_fixtures`, refactored out of the owned loop). Reuses
      `xp_by_id` (all players). Tests: default My-team still works; **All** compares with a non-owned same-position
      player; **By club** filters to one club.
- [ ] **No drift** — display-only; no analytics change; the single-card path + the Players Card view unchanged; ruff
      + suite green.
- [ ] **Docs** — PROJECT_STATUS; Architecture; memory; mark the item shipped in Backlog.

---

### 🧭 Design sketch

`render_my_squad`, the ⚙ panel `if picked:`:
```
pool = segmented_control("⚔️ Boot Battle — pool", [My team, All, By club], default=My team)
base = owned            if pool == My team
     = players          if pool == All
     = players@club     if pool == By club  (a Club selectbox)
cands = [same position as picked, ≠ picked] from base, sorted
bb = selectbox("⚔️ Boot Battle — compare with…", [—, *cands])
if bb: render_player_compare(picked, bb, …, a/b_fixtures=_pergw_fixtures(…), a/b_xp=xp_by_id[…])
```

**DoD:** tests (default + All + By-club) + a manual smoke + docs.

---

### 📋 Sprint Review

**Delivered — the Boot Battle pool selector; display-only, 986 tests, ruff clean.**

- **US-380** — the ⚙ panel ⚔️ Boot Battle gains a **"pool"** segmented control: **My team** (owned, default) ·
  **All** (same-position, whole pool) · **By club** (a Club picker → same-position from that club). The candidate
  list is always same-position, excluding the picked player. Comparing with a **non-owned** target works because
  `xp_by_id`/`card_bg_by_id` already cover all players; refactored the per-GW fixtures into a **`_pergw_fixtures(p)`**
  helper so the target's card row builds on demand. Reuses `compare_card_html` — no analytics change.

**DoD:** tests (default My-team; All → compares with a non-owned player; By-club → Club picker) + docs. The existing
Boot Battle test held (it filters `at.selectbox`, so the new pool *segmented control* doesn't confuse it). **Follow-on
(optional):** the same pool selector on the Players Card view.

### 🧠 Lessons
*(see `Sprint155_Lessons_Learnt.md`)*
