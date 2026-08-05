# Sprint 060: Phase 6 kickoff — the crowd lens (Tier 1, free FPL signals)

**Dates:** 2026-08-05
**Status:** 📝 Planned
**Capacity:** ~2–3 working sessions (a gate + ingest the crowd fields + a lens/flags surface + docs)
**Carried Over:** None (Sprint 059 shipped; tester-feedback intake runs in parallel, async)

> **Direction (owner):** a new **Phase 6 — Crowd & Sentiment Signals**. Fold *"what managers are doing"* +
> expert signals into the picks/analysis — as a **complementary lens + flags**, **not** baked into xP (xP
> stays grounded & verified). **Free FPL signals first** (Tier 1); external social/pundit is a later,
> optional tier. Investigation confirmed the Tier-1 signals are already **free & structured in the FPL
> API** — no scraping to start.

---

### 🔎 Verified at planning (the signals exist; timing is season-gated)

- **Tier-1 crowd fields are in `bootstrap-static` per player** (confirmed on the live API): `transfers_in_event`
  / `transfers_out_event`, `cost_change_event` / `cost_change_start`, `form`, `ict_index` (+ `influence` /
  `creativity` / `threat`), `value_form`. `selected_by_percent` is **already stored** (ADR-044).
- **Preseason = mostly 0.** Today `transfers_in_event`, `cost_change_event`, `form` all read **0** — they
  populate from **GW1 (2026-08-21)**, like the strength data. **Live now:** `selected_by_percent`,
  `ict_index` (+ components), `ep_next`. So the **ownership template/differential + ICT** lens works
  immediately; the **momentum / price / form** flags are built now and light up at GW1.
- **The schema-migration pattern exists** (`_migrate` adds missing columns, ADR-027), so adding these
  columns to a live/seed DB is a solved, idempotent step.
- **Grounding stays intact.** These are new *display/lens* fields — the xP recipe (`decision_xp`) is
  untouched; the crowd never overrides the prediction (owner's call).

---

### 🧭 What's new — the crowd, as a lens

Every player-facing surface gains **crowd flags** next to xP: **🔥 trending in / ❄️ out** (net transfers
this GW), **💰 price rising / falling**, **📈 in form**, and **template** (high-owned) vs **differential**
(low-owned). They *inform*; they never change the xP number. A first **"trends"** angle answers *"who's
most transferred in / rising / in form?"*. All from free FPL data — no scraping.

---

### 🎯 Sprint Goal

**Objective:** stand up **Phase 6, Tier 1** — ingest the free crowd/momentum fields and surface them as a
**complementary lens + flags** (xP untouched). A gate settles the model + thresholds; the lens works
preseason for ownership/ICT and auto-populates the momentum flags at GW1.

#### Success Criteria
- [ ] Approach agreed (**ADR-057**) — crowd signals as a **lens + flags, not blended into xP**; the Tier-1
      fields; the specific flags + thresholds (trending / price / form / template / differential); where
      they surface; external/pundit explicitly deferred (Tier 2/3)
- [ ] **Ingest Tier-1 fields** — `transfers_in/out_event`, `cost_change_event`/`_start`, `form`,
      `ict_index` (+ ICT components), `value_form` into the `Player` model + storage (schema + `_migrate`);
      the CLI `refresh` populates them (0 preseason, live GW1)
- [ ] **A crowd-lens helper** (analytics/edge) — pure functions turning a player row into flags
      (trending in/out · price · form · template/differential), reused by every surface
- [ ] **Surface the lens** — flags/columns on the **Players** tab (and the shared player table, so squad
      tabs get it); ownership template/differential live now, momentum/price/form graceful (muted / "—")
      when 0
- [ ] **xP untouched** — `decision_xp` and the grounded answers are unchanged (a test asserts the crowd
      fields don't feed the xP number)
- [ ] Tests — ingest/round-trip the new fields; the flag helper (thresholds, empty-safe); the Players tab
      shows the flags; xP unchanged
- [ ] Docs: ADR-057 + index, Architecture, Roadmap (Phase 6 — done), README/Handbook note, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-181 | **Gate.** Phase 6 model (**ADR-057**): crowd = a **lens + flags, not blended into xP**; the Tier-1 fields; the flag set + thresholds; the surfaces; Tier 2/3 (external / evaluation) deferred | Critical | ✅ Done | 0.5 session |
| US-182 | **Ingest the crowd fields** — add `transfers_in/out_event` · `cost_change_event`/`_start` · `form` · `ict_index` (+ ICT components) · `value_form` to the `Player` model + storage (schema + `_migrate` + getters) + `refresh` mapping. Tests | High | ✅ Done | 1 session |
| US-183 | **The crowd lens + flags** — a pure `crowd_flags(player)` helper (trending / price / form / template / differential, threshold-driven, empty-safe) surfaced on the **Players** tab + the shared player table. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-057 recorded + added to the ADR index — _US-181_
- [x] `Player` model + storage schema/migration + `ingest.refresh` mapping (+ reseed `seed.db`) — _US-182_
- [x] `crowd_flags` helper + wire into the player table(s) — _US-183_
- [x] Roadmap Phase 6 Tier-1 items ticked; Architecture/PROJECT_STATUS — _US-183_
- [ ] (Post-GW1) confirm the momentum/price/form flags light up with live data

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — the new fields ingest + round-trip; `crowd_flags` returns the right flags at
   its thresholds and is empty-safe (0/None → no flag, no crash); the Players tab renders the flags; a test
   asserts `decision_xp` is **unchanged** by the crowd fields; existing **487** stay green.
2. **Manual smoke test done** — `refresh` writes the new fields; the Players tab shows template/differential
   + ICT now, and the momentum/price/form flags render gracefully (muted) preseason. (Full momentum visible
   at GW1.)
3. **Documentation updated & checked** — ADR-057 + index, Architecture, Roadmap (Phase 6 Tier-1 done),
   README/Handbook note, PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Tier-1 **free FPL** crowd fields + a **lens + flags** | Blending sentiment **into xP** (owner: lens only) |
| Flags on Players (+ the shared squad-tab table) | External social / Reddit / X / pundit NLP (Tier 2, later) |
| A threshold-driven, empty-safe `crowd_flags` helper | Crowd-vs-xP **backtest/evaluation** (Tier 3, later) |
| ADR-057 (the model + thresholds) | Changing the xP recipe / the grounded answers |

**External Dependencies:** none new (FPL API only). **Timing:** momentum/price/form are **0 until GW1
(2026-08-21)** — this sprint builds the plumbing + the preseason-viable ownership/ICT lens; the momentum
flags light up at GW1.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Building a lens on data that's 0 preseason | Med | Ship the ownership/ICT lens (live now); the momentum plumbing is tested with 0 + a GW1 follow-up check |
| Crowd sentiment creeping into xP | Med | Keep it display-only; a test asserts `decision_xp` is unchanged; ADR-057 makes "lens, not truth" explicit |
| Flag thresholds feel arbitrary | Low | Agree them at the gate on real (ownership) data; keep them few + tunable constants |
| Scope creep toward scraping | Low | Tier 2/3 explicitly deferred in ADR-057 + the Roadmap |

---

### 🗝️ Gating decision (US-181 → ADR-057)

Proposed (confirm/redirect at "start US-181"):

1. **Crowd = a complementary lens + flags, never blended into xP** (owner's call). xP (`decision_xp`) and the
   grounded answers stay exactly as they are; the crowd is shown **alongside**.
2. **Tier-1 fields only** — `transfers_in/out_event`, `cost_change_event`/`_start`, `form`, `ict_index`
   (+ ICT components), `value_form` (+ the already-stored `selected_by`). External/pundit = Tier 2/3, later.
3. **The flag set + thresholds** — 🔥 **trending in** / ❄️ **out** (net `transfers_*_event`), 💰 **price
   rising/falling** (`cost_change_event`), 📈 **in form** (`form`), **template** (high `selected_by`) vs
   **differential** (≤5% owned, reuse ADR-044). Thresholds as tunable constants, agreed on real data.
4. **Surfaces** — the **Players** tab first (+ the shared `render_player_table`, so squad tabs inherit it);
   Captain/Transfer/`ask`-"trends" can follow (this sprint or the next).
5. **Deferred** — Tier 2 (Scout/Reddit/X, degrade like ClubElo) + Tier 3 (crowd-vs-xP backtest).

**Worked example (probed):** the fields are in `bootstrap-static` (ownership 30.9%, ICT 57.5 live now;
momentum 0 preseason → GW1); the `_migrate` pattern adds the columns; `crowd_flags(player)` is a pure,
empty-safe row→flags function reused by the tables.

---

### 📝 Session Progress Log

- **US-181 (gate) ✅** — Recorded **ADR-057** (Phase 6 opener). Crowd signals are a **complementary lens +
  flags, never blended into xP** (owner's call) — `decision_xp` + the grounded answers stay untouched (a
  test will assert it). **Tier-1 free FPL fields** only: `transfers_in/out_event` · `cost_change_event`/
  `_start` · `form` · `ict_index` (+ Influence/Creativity/Threat) · `value_form` (+ the stored
  `selected_by`); external social + pundit = Tier 2/3, deferred. A pure **`crowd_flags(player)`** helper
  (empty-safe) with **tunable thresholds** set on real data: **template ≥ 20%** owned (≈17 players now),
  **differential ≤ 5%** (ADR-044), **price ↑/↓** on any `cost_change_event` sign (£0.1m units), and
  **trending** (net transfers) / **in form** (`form ≥ ~6`) as constants **calibrated at GW1** (0 preseason).
  ICT/form/net-transfers also shown as numeric columns. Surfaces: **Players** first (via the shared
  `render_player_table`, so squad tabs inherit it); Captain/Transfer/`ask`-"trends" follow. ADR-057 indexed.
- **US-182 ✅** — **Ingest the crowd fields.** Added the 10 Tier-1 fields to the `Player` model +
  `from_api` (`transfers_in/out_event`, `cost_change_event`/`_start` as ints; `form`, `ict_index`,
  `influence`, `creativity`, `threat`, `value_form` parsed from strings → float; absent → None) and to
  storage (`CREATE_PLAYERS` + `_MIGRATIONS` + `UPSERT_PLAYER` + `save_players`; `get_players` is `SELECT *`
  so no getter change). `ingest.refresh` needed no change (it uses `from_api`). **Reseeded `data/seed.db`**
  (ran `refresh` → 570 players / 20 teams / 380 fixtures with the new schema, copied to the committed seed)
  so the deploy's seed already has the columns — opening it is a **no-op migration** (verified
  byte-identical, no sidecars), avoiding the tracked-file write that risks the Cloud git-sync glitch. Tests
  (+4 → **491**): `from_api` parses the crowd fields (and absent → None); a save/get round-trip; the
  `_migrate` adds the columns to an old players table. Smoke: refresh + round-trip + migration all pass;
  `ruff` clean. (Values are 0 preseason — live at GW1.)
- **US-183 ✅** — **The crowd lens + flags.** New pure **`src/analytics/crowd.py`** — `crowd_flags(player)`
  (empty-safe row→flags) + `net_transfers`, with **tunable threshold constants** (`TEMPLATE_OWN=20` ·
  `DIFFERENTIAL_OWN=5` · `FORM_MIN=6` · `TRENDING_NET=50k`): 🟦 template / 💎 differential (ownership),
  🔥 in / ❄️ out (net transfers), 💰↑ / 💸↓ (price), 📈 form. Exported from `src.analytics`. Surfaced as a
  **Trends** column + **Form** / **ICT** columns on the **Players** tab, and a **Trends** column on
  **Build · Analyse · My Squad** (rows built from full player dicts). **Display-only** — a test mutates
  every crowd field to wild values and asserts **`decision_xp` is byte-for-byte unchanged**. Tests (+8 →
  **499**): the flag thresholds (template/differential/price/trending/form), empty-safety, `net_transfers`,
  the xP-invariance, and the Players tab showing the lens columns. Smoke on live data: Haaland (74.9%) →
  🟦 template, Truffert (4.7%) → 💎 differential; momentum/form flags correctly absent preseason (live at
  GW1). `ruff` clean.

---

### 🏁 Sprint Review & Retrospective

_(to be completed at sprint close)_
