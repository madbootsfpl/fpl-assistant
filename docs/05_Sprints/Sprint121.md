# Sprint 121: Finish the fixtures planner — a budget cap + value on the targets

**Dates:** 2026-08-22 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (two controls + a column on the 🎯 Target-by-fixtures list — display only)
**Carried Over:** none

> **Direction:** the Sprint-120 retro flagged two follow-ups on **🎯 Target by fixtures** — it has no
> **price/affordability** filter, and it ignores **bang-for-buck** (every pick shares its team's FDR, ranked by
> raw xP). For planning a **budget** wildcard/new squad you want "who can I *afford*, and who's best *per £*".

---

### 🔎 Verified at planning (on real data)

- **The Target list today** (Sprint 120, `pages/2_Fixtures.py` + `analytics/targets.py::target_by_fixtures`):
  for the easiest-run teams it names each team's best **available** players ranked by **`decision_xp`** (ADR-041),
  shown as Team · FDR · Next · Player · Pos · £m · Own% · Fit · xP. No price filter, no value column/sort.
- **Prices span £4.0m–£15.5m** — a clean slider domain (min→max; default max = "show all").
- **Value already has one definition** — `analytics.points_per_million(total_points, price)` (ADR-042, the app's
  **Val/£m**, points-based; `None` when price ≤ 0). Reusing it keeps **one** value metric across the app (Pool,
  stat boards, and now the targets) — no new metric, no drift. Sample xP/£m sanity: LIV Virgil £6.5m xP 21.2,
  Szoboszlai £7.0m xP 19.7 — a value sort would reorder these toward the cheaper high-returners.
- **No analytics touched** — both stories extend the existing `target_by_fixtures` composition + the page; the
  FDR maths, `decision_xp`, and `points_per_million` are unchanged (display lenses).

---

### 🎯 Sprint Goal

**Objective:** make 🎯 Target by fixtures **budget-aware** — cap the price so you only see affordable targets, and
show/sort by **Val/£m** so a tight-budget planner finds the best pick per £. Display only; analytics untouched.

#### Success Criteria
- [ ] **US-303 (a max-price cap)** — a **`Max price`** slider (£4.0m–£15.5m, default max = all) above the Target
      table; `target_by_fixtures` filters candidates to `price ≤ cap` **before** picking each team's top players.
      A clear note when the cap empties the list.
- [ ] **US-304 (value column + sort)** — a **Val/£m** column (the app's `points_per_million`, ADR-042) on the
      Target table + a **`Sort`** toggle (**xP** / **Val/£m**) that switches the per-team ranking key. xP stays the
      default (consistent with the section's headline metric).
- [ ] **No drift** — display only; `target_by_fixtures` gains `max_price`/`sort_by`/`value_by_id` params but the
      FDR + xP + value analytics are unchanged; the read-only web guardrail holds; existing **771** stay green
      (+ cap / value-sort tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends the **fixtures + xP/value** families
      — ADR-041/042; no new ADR — a display lens).

---

### 🧭 Design sketch

**US-303.** Add `max_price=None` to `target_by_fixtures`; when set, skip any player with `price > max_price` in the
grouping loop (before the per-team top-K pick, so a cap genuinely reveals the best *affordable* names, not just
truncates). Page: `cap = st.slider("Max price", 4.0, 15.5, 15.5, step=0.5)` → pass it through. The existing
"No available targets…" caption already covers an empty result.

**US-304.** Add `sort_by="xp"` and `value_by_id=None` to `target_by_fixtures`: the per-team ranking key becomes
`value_by_id` when `sort_by=="value"` (else `xp_by_id`), and every row carries `value = value_by_id.get(id)`.
Page: build `value_by_id` from `points_per_million(p["total_points"], p["price"])`; a
`st.segmented_control("Sort", ["xP","Val/£m"], default="xP")` picks the key; add a **Val/£m** column
(`NumberColumn`, `%.1f`, a dash when None). Keep the team grouping (easiest-run first) — the sort reorders
*within* each team.

**Deferred:** a **squad-aware** affordability (cap = bank + a sell — needs the Fixtures page to know your squad,
bigger); a **"widen"** control (top-N teams / per-team count — the cap+sort cover the budget case); an xP/£m
*future*-value metric (a second value definition → avoid; ADR-042 stays the one Val/£m).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-303 | **A max-price cap on the targets** — a slider; show only affordable picks per team. | High | ⬜ To do | ~¼ session |
| US-304 | **Value column + sort** — a Val/£m column + an xP↔Val/£m sort toggle. | High | ⬜ To do | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the Target section renders a **Max price** slider that drops candidates above the cap
   (AppTest: lowering it removes the dearer names), and a **Val/£m** column + a **Sort** toggle that reorders by
   value (unit test on `target_by_fixtures`: `max_price` filters; `sort_by="value"` ranks by `value_by_id`).
   Existing **771** stay green. No `.save(` / no analytics change.
2. **Manual smoke** — Fixtures → 🎯 Target: drag **Max price** down → only affordable targets; switch **Sort** to
   **Val/£m** → cheaper high-returners rise; the value column reads sensibly; a low cap shows the empty note.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log.

---

### 📝 Session Progress Log

- **US-303 (a max-price cap)** — added a `max_price` param to `analytics/targets.py::target_by_fixtures` — it
  drops players with `price > max_price` (or a `None` price) **in the grouping loop, before** the per-team top-K
  pick, so a cap surfaces the best *affordable* name rather than truncating. Wired a
  `st.slider("Max price", 4.0, 15.5, 15.5, step=0.5)` above the Target table in `pages/2_Fixtures.py`. Display
  only — no analytics change. Smoke: full → 18 rows (max £12.0m); cap £6.0m → 18 rows all ≤ £6.0m (dearer names
  swapped for cheaper same-team picks); cap £4.0m → 11 rows. +2 tests (1 unit in `test_targets.py` that proves the
  cap swaps in the best affordable, not just truncates + 1 page AppTest). ruff clean.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
