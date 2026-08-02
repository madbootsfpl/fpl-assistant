# Architectural Decision Record: Expected Goals (xG / xA / xGI)

**Decision ID:** ADR-015
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-011; supersedes the backlog "FBref xG/xA")
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The backlog's big prize was per-player **expected goals** (xG/xA) to sharpen analysis —
sourced from **FBref**. A feasibility probe changed the plan:

- **FBref is not usable here** — `fbref.com` returns **403** (scraping blocked), and it
  would need a heavy dependency (`soccerdata`) plus fragile FPL↔FBref **name-matching**.
- **FPL's own API already carries the data** — every element has `expected_goals`,
  `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded` (+ per-90
  variants), keyed by FPL id. **No new dependency, no scraping, no name-matching.**

Verified live: 564 players, **376 (66%) have xGI > 0**; values are strings (`'25.50'`);
**xGI = xG + xA exactly**; xGC populated for GK/DEF. Same preseason caveat as every FPL
number — last-season totals that auto-update on `refresh`.

#### Decision Drivers
- **Least risk** — reuse the source and path we already have.
- **Reuse the seams** — model `_to_float`, the generic storage migration, the pluggable
  objective (ADR-011).
- **Honesty** — state what the numbers are (last-season) and what the xGI objective favours.

---

### 💡 Decisions

**1. Source: FPL, not FBref.** Ingest the expected-* fields from the FPL bootstrap. FBref
is **rejected** — 403-blocked, and a scraping dependency + name-matching for data FPL
already gives us by id. (Recorded so the dead end isn't re-attempted.)

**2. Fields (four).** `expected_goals` (xG), `expected_assists` (xA),
`expected_goal_involvements` (xGI = xG + xA), `expected_goals_conceded` (xGC). The per-90
variants are deferred.

**3. Ingest & store.** `Player.from_api` parses the four via the existing `_to_float`
(missing/blank → 0.0). Storage adds four `REAL` columns through the generic `_migrate()`
(`ALTER TABLE ADD COLUMN`), so existing databases upgrade in place; `save` upserts them.

**4. View.** A new `xg` command ranks players by xGI (desc), showing xG / xA / xGI / xGC,
with `--pos` and `--limit` — mirroring the `xp` command.

**5. Objective.** `--objective xgi` adds **one entry** to `objective_scores` returning xGI
per player. Per ADR-011 the optimiser is unchanged — it maximises whatever score it's
handed. This is the promised "a 4th objective is a new dict entry, not a solver change".

**6. Stated bias.** xGI is an *attacking* measure — GK and most DEF are ≈ 0, so
`--objective xgi` fills the outfield with the highest-involvement attackers the formation
allows. That's the intended lens, not a defect; the output notes it.

**Out of scope:** rebuilding the **xP model** on xG (bigger, more season-dependent — a
later sprint); per-90 / minutes-adjusted views; historical gameweek xG.

---

### 🧪 Worked example (pressure-testing — run on real data)

**The `xg` view** (top by xGI):

```
Haaland      xG 25.5  xA  2.7  xGI 28.2
B.Fernandes  xG 10.8  xA 12.3  xGI 23.1
Thiago       xG 20.6  xA  1.8  xGI 22.4
```

**`--objective xgi` vs `--objective points`** (same £80m): the two XIs differ in **9 of 11
players** — xgi pulls in the highest-involvement attackers (e.g. Haaland). The new field
flows all the way through to a different *decision*, before the view or objective are
written. (Both landed on a 4-4-2 under the fixed default here — the bias shows in *who* is
picked, not necessarily the shape.)

---

### ⚖️ Consequences & Trade-offs

* **Positive:** Real underlying attacking data enters the tool with zero new dependency; a
  new ranking lens and a new squad objective, both reusing existing seams; the full
  ingest→store→surface pipeline is exercised (good end-to-end learning).
* **Negative / Trade-offs:** Preseason values are last-season (like every FPL number). The
  xGI objective is attack-biased (stated). Defensive expected value (xGC) is stored but not
  yet turned into a metric.
* **Risks & Mitigations:**
  - *String / blank fields* → `_to_float` → 0.0 (a test covers it).
  - *Old DBs lack columns* → generic `_migrate()` adds them (a migration test).
  - *Scope creep to xP-on-xG* → explicitly out of scope; expose now, model later.

---

### 🛠 Implementation & Migration
* **Components Affected:** `Player` model (+4 fields), storage (migration + save +
  get_players), analytics (`objective_scores` + xgi), CLI (`xg` view, `--objective xgi`),
  Docs. **No new dependency.**
* **Action Items:**
  - [x] Record the design + worked example + the FBref rejection (US-044)
  - [ ] Ingest & store xG/xA/xGI/xGC + migration (US-045)
  - [ ] `xg` view + `--objective xgi` (US-046)
  - [ ] (Backlog) xP v2 on xG; per-90 views; a defensive (xGC) metric

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts and the numbers become live-form.
* **Triggers for Reconsideration:**
  - [ ] Want expected points built on xG → an xP-v2 sprint.
  - [ ] Want per-90 / minutes-adjusted involvement → add the per-90 fields.
  - [ ] Want a defensive lens → turn xGC into a metric.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-044 (this), US-045/046
- **External Docs:** [ADR-011 (pluggable objective)](./ADR-011-squad-objective.md) · [ADR-006 (xP v0)](./ADR-006-expected-points-v0.md) · [Sprint 014](../05_Sprints/Sprint14.md)
