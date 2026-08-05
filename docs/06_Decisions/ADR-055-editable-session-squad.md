# Architectural Decision Record: An editable session squad (name · transfers · captain · manual edit)

**Decision ID:** ADR-055
**Date:** 2026-08-05
**Status:** Accepted
**Superseded By / Replaces:** Extends the session "active squad" (ADR-054) from **read-only** to
**editable**; reuses the optimiser/transfer/captain engines (ADR-008/030/029) and the legality idiom of
`legal_xi_issues` (ADR-022).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 057 (ADR-054) gave the web a session **active squad**, but it's **read-only** once set: you can
build/upload it and run Analyse/Transfer/Captain on it, but you can't **change** it. Tony's testing notes
ask for exactly that — and surfaced a bug:

1. **Bug:** the **Build** page renders **xMins 0 / xP 0.0** for every player.
2. Can't **name** a squad (it's hardcoded "My squad").
3. Can't **edit** a squad once built (swap players).
4. Can't **select a captain** that sticks.
5. Can't **apply transfers** to your team (Transfer only *suggests*).

The owner chose the fuller scope: **guided edits *and* a manual player-picker**, with the captain **set &
persisted**. Two design calls were settled with the owner: editing should be available **wherever you spot
an opportunity** (inline on Transfer/Captain) as well as on a dedicated hub; and the £100m budget should be
a **warning, not a block** (prices drift, so blocking is brittle).

#### A planning probe confirmed the pieces
- The Build bug is `p.get("xp", 0)` → 0 because the page never attaches `xp`/`minutes_weight` onto the
  selected players; the CLI does exactly that before rendering (`cli.py:320–323`).
- There is **no** 15-man legality check — `legal_xi_issues` covers the XI only; `SQUAD_15` and
  `MAX_PER_CLUB = 3` exist as constants. A manual edit needs a new validator.
- `captain_id` is a harmless **superset** key on the squad dict — the CLI ignores it; `parse_uploaded`
  tolerates it (and can validate it).

#### Decision Drivers
- **Edit where the opportunity appears** (owner) — inline, not only on a special page.
- **Keep the architecture** — still **no server writes**; mutation is session-only, download = save.
- **One source of truth for legality** — a generic, tested validator, not per-page checks.
- **Simple & robust to price drift** — warn over budget, don't block (matches ADR-022's "warn, not block").

---

### ✅ Decision

**1. The session squad becomes editable — in `session_state`, no server writes.** Every edit mutates
`st.session_state["squad"]` in place (`name`, `player_ids`, `bench_ids`, **`captain_id`**, `cost`). The DB
and `SquadStore` stay **read-only** — the web never calls `SquadStore.save` (the ADR-054 guardrail test
holds). The **Download** button captures the edited squad; that file is the save.

**2. All edits go through mutation helpers (edge).** `src/web_streamlit/squads.py` gains `rename`,
`apply_transfer(out_id, in_id)`, `replace_player(out_id, in_id)`, `set_captain(id)`, `set_bench(ids)`. Each
edits the dict, **recomputes cost** from current prices, re-derives the bench/XI as needed, clears a
`captain_id` that has left the squad, and re-validates. **Pages never edit the dict inline** — so the
mutation logic can't drift across pages.

**3. A generic legality validator (core).** New pure **`squad_15_issues(players,
max_per_club=MAX_PER_CLUB)`** in `src/analytics/optimizer.py`, modelled on `legal_xi_issues`: checks the
**structural** rules — 15 players in the `SQUAD_15` split (2/5/5/3) and ≤`max_per_club` per club — and
returns a list of human-readable issues (empty = legal). These are the **hard** blockers. **Budget is
deliberately kept out of the validator** and handled at the **edge** (the squad's cost vs the £100m
reference): so an over-budget edit is a **soft warning** that never blocks (prices drift), which is
impossible to get wrong when it isn't in the "is this legal?" list at all. Unit-tested; reused by
apply-transfer and the manual editor.

**4. `captain_id` — a schema superset.** Added to the squad dict; ignored by the CLI; included in the
downloaded `squad.json`. `parse_uploaded` validates it when present (`captain_id ∈ player_ids`), and a
transfer/manual swap that removes the captain clears it.

**5. Editing lives wherever the opportunity appears.** Inline **Apply** on **Transfer** (apply a suggested
swap) and **Set as captain** on **Captain** mutate the same session squad — edit where you're already
looking. A new **My Squad** hub page centralises the overview + the heavier controls: the 15 shown with
**(C)**, cost, and a **legality line**; **rename**; the **manual swap** (search any player → replace,
validated); and **bench** adjustment. Build keeps Download/Use and gains the **name** input.

**6. Captain display.** The `captain_id` is marked **(C)** in the squad views (Build/My Squad) and in
`render_squad_analysis`; it travels in the download.

---

### 🔀 Alternatives Considered

- **Fold all editing onto Build (no new page).** Fewer pages, but Build would do double duty
  (optimise *and* edit), and an **uploaded** squad (never built) has no obvious home. Rejected in favour of
  inline edits + a My Squad hub (the owner wants to tweak from wherever the opportunity is).
- **Hard-block over-budget edits** (like the optimiser's constraint). Stricter, but brittle as prices drift
  and you can't stage an over-budget edit then fix it. Rejected → **warn, not block** (ADR-022).
- **Per-page legality checks.** Duplicated, drift-prone. Rejected → one generic `squad_15_issues`.
- **Server-side persistence of edits.** Out of scope — still no server writes; Path 2 (a server DB) remains
  the Backlog follow-up (ADR-054).

---

### 🧭 Consequences

**Positive**
- The squad is genuinely **yours**: name it, transfer, hand-edit, captain — from wherever you spot the
  chance; the download reflects every edit.
- **One legality validator** (`squad_15_issues`) — generic, tested, reused; the core stays policy-free.
- **Architecture intact** — mutation is session-only; no server writes; the guardrail test still holds.
- The Build bug is fixed as a by-product (attach `xp`/`minutes_weight`, mirroring the CLI).

**Negative / risks (mitigations)**
- **A manual edit could be illegal** → `squad_15_issues` gates every edit; illegal → a clear reason, no
  apply (budget is the one soft, always-appliable warning).
- **Mutation scattered → drift** → one set of helpers in `web_squads`; pages never touch the dict directly.
- **A stale `captain_id`** (captain transferred out) → cleared on the mutation; validated on upload.
- **Accidental server write** → still no `SquadStore.save`; the guardrail test holds.
- **Scope is large (5 stories)** → ship the fix + name first; the manual editor (US-174) is the heaviest
  and may carry to Sprint 059.

---

### 📊 Validation

Probed on the live DB: the Build bug reproduces (xP/xMins = 0) and mirrors `cli.py:320–323` for the fix;
`legal_xi_issues` is the template for `squad_15_issues`; `captain_id` is a tolerated superset key.
Acceptance for the sprint: Build renders non-zero xP; a named squad round-trips; **Apply** mutates the
session squad (cost recomputed); a manual swap is legality-validated (illegal refused with a reason,
over-budget warned but appliable); a set captain persists, shows **(C)** in Analyse, and travels in the
download; the web makes **no** server writes; the existing 455 tests stay green.
