# Sprint 121: Finish the fixtures planner — a budget cap + value on the targets

**Dates:** 2026-08-22
**Status:** ✅ Complete (2/2 stories)
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
- [x] **US-303 (a max-price cap)** — a **`Max price`** slider (£4.0m–£15.5m, default max = all) above the Target
      table; `target_by_fixtures` filters candidates to `price ≤ cap` **before** picking each team's top players.
      A clear note when the cap empties the list.
- [x] **US-304 (value column + sort)** — a **Val/£m** column (the app's `points_per_million`, ADR-042) on the
      Target table + a **`Sort`** toggle (**xP** / **Val/£m**) that switches the per-team ranking key. xP stays the
      default (consistent with the section's headline metric).
- [x] **No drift** — display only; `target_by_fixtures` gains `max_price`/`sort_by`/`value_by_id` params but the
      FDR + xP + value analytics are unchanged; the read-only web guardrail holds; existing **771** stay green
      (**775** with +4); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README, Help, Feedback_Log (extends the **fixtures + xP/value** families
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
| US-303 | **A max-price cap on the targets** — a slider; show only affordable picks per team. | High | ✅ Done | ~¼ session |
| US-304 | **Value column + sort** — a Val/£m column + an xP↔Val/£m sort toggle. | High | ✅ Done | ~¼ session |

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
- **US-304 (value column + sort)** — added `sort_by` ("xp"/"value") + `value_by_id` params to `target_by_fixtures`:
  the per-team ranking key becomes `value_by_id` when `sort_by=="value"`, and every row now carries `value`. Page:
  built `value_by_id` from `points_per_million(total_points, price)` (the app's one Val/£m, ADR-042), added a
  `st.segmented_control("Sort", ["xP","Val/£m"], default="xP")` and a **Val/£m** column (`NumberColumn`, `%.1f`).
  xP stays the default (the section's headline metric). Display only — no new value metric. Smoke: by xP → EVE
  Pickford/Tarkowski/Mykolenko; by Val/£m → Tarkowski/Keane/Pickford (a cheaper high-value pick rises). +2 tests
  (1 unit: value sort reranks + the row carries value; 1 page AppTest: the column + a non-increasing value block).
  ruff clean. **775** total.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ both stories shipped. **🎯 Target by fixtures** is now **budget-aware**: a **Max price** slider
caps the list to what you can afford, and a **Val/£m** column + an **xP↔Val/£m** sort surface bang-for-buck for a
tight wildcard budget. Both extended the existing `target_by_fixtures` (+ four small page controls); the FDR, xP
and value analytics are untouched.

**Delivered**
- **US-303** — a `max_price` param that drops pricier players *before* the per-team top-K pick (so a cap reveals
  the best *affordable* name, not a truncation); a `Max price` slider. +2 tests.
- **US-304** — `sort_by` ("xp"/"value") + `value_by_id` params (every row carries `value`); a **Val/£m** column
  (`points_per_million`, ADR-042 — the app's one value metric) + a **Sort** toggle (xP default). +2 tests.

**Verified at planning (real data)** — prices span £4.0m–£15.5m (a clean slider domain); `points_per_million` is
the app's single Val/£m, so reusing it keeps **one** value definition (Pool / stat boards / targets). Smoke: cap
£6.0m → dearer names swapped for cheaper same-team picks; Sort → Val/£m surfaces Keane £5.0m / Shaw £4.5m.

**Metrics** — 775 tests (771 → +4), all green · ruff clean · 93 ADRs (no new) · 2 stories, ~½ session.

**What went well**
- One function grew four small params (`position`/`max_price`/`sort_by`/`value_by_id`) and stayed pure + unit-
  testable — the page is still a thin renderer.
- **Reused the one value metric** (ADR-042) rather than inventing an xP/£m — no second "value" to reconcile.
- The "filter before the per-team pick" detail (a cap *reveals* affordable names) is what makes the slider useful
  rather than a blunt truncation — and a unit test pins it.

**Even better if**
- Affordability is a flat **price cap**, not **squad-aware** (bank + a sell) — that needs the Fixtures page to
  know your squad (deferred; bigger).
- The Val/£m is **points-based** (last-season points per £m) — it under-rates new signings whose xP is high but
  whose points are low (Isak). Honest and consistent with the rest of the app, but a known limitation of Val/£m.
- No **"widen"** control (top-N teams / per-team count) — the cap + sort cover the budget case; deferred.

**Deferred / backlog** — squad-aware affordability (cap = bank + a sell); a "widen" control; an xP/£m *future*-
value metric (a second value definition — deliberately avoided; ADR-042 stays the one Val/£m).

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **One thing to change next sprint:**
- **Does the budget-aware Target list fit how you'd plan a wildcard? (1–5):**
