# Architectural Decision Record: A shared player filter (Players & Player Stats)

**Decision ID:** ADR-064
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — extends the Streamlit edge (ADR-052/063) with one reusable filter.
No analytics change. Triggered by tester feedback (Feedback_Log, 2026-08-06).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Two tester gaps: (1) the new **Player Stats** page has no filter; (2) the **Players** page filters only by
position + max-price, and its price-vs-points **scatter isn't adding value**. Both want a richer filter —
by **player(s) / team / position**, or any combination (multi-select) — over data the pages already load.

**Verified on real data (2026-08-06):** 20 teams; Players rows carry `team`/`position`/`web_name`/`price`,
the stat-analytic rows carry `team`/`position`/`web_name` (no `price`). So one shared filter serves both,
with max-price a Players-only extra.

#### Decision Drivers
- **One filter, two pages** — the same control on Players and Player Stats (DRY, consistent UX).
- **Combinable** — teams ∧ positions ∧ players (AND); an empty dimension means "any".
- **No analytics change** — the filter is a display predicate over rows the pages already have.
- **Replace the dead graph with a live one** — a filter-responsive top-15 bar, not a static scatter.

---

### ✅ Decision

**1. A shared filter — `web_streamlit/filters.py` (built in US-206).**
```
filter_controls(players, *, key, with_price=False) -> dict     # renders the multiselects; returns `sel`
apply(rows, sel) -> list                                       # keep rows matching every non-empty dim (AND)
```
`filter_controls` renders **Team** (options = distinct `team` short names), **Position** (GK/DEF/MID/FWD),
**Player** (options = `web_name`s) multiselects — each keyed off `key` so two pages don't collide — plus an
optional **Max price** slider (`with_price`). `apply` keeps a row when it matches **every non-empty**
dimension: `(not teams or team ∈ teams) ∧ (not positions or position ∈ positions) ∧ (not players or
web_name ∈ players)`, and (if a `max_price` is set and the row has a price) `price ≤ max_price`. Field reads
tolerate both `sqlite3.Row` (Players) and `dict` (stat analytics) rows.

**2. Player Stats gets the filter (US-206).** `sel = filter_controls(players, key="stats")` once above the
four tabs; each tab runs `apply(analytic_rows, sel)` before paginating. The "season-to-date" caption stays.

**3. Players gets the filter + a live bar (US-207).** The filter (with `with_price=True`) replaces the
position multiselect + the max-price slider; the **scatter is removed** and replaced by a **top-15
horizontal bar** (Altair, `sort="-x"`) of the **filtered** players by the current sort metric
(points → Pts, value → Val/£m). The table, pagination and team/position sort are unchanged. Altair ships
with Streamlit (web-only; no new dependency).

---

### 🔀 Alternatives Considered

- **Per-page bespoke filters.** Rejected — duplicates the same three multiselects; a shared helper is DRY
  and keeps the two pages consistent.
- **OR semantics across dimensions.** Rejected — AND (narrowing) is what "team **and** position" means and
  is the intuitive combination; an empty dimension already means "any".
- **Team-scoped player list** (only show players from the chosen teams). Deferred — the flat searchable
  `web_name` list is simple and Streamlit's multiselect is searchable; revisit if it feels unwieldy.
- **`st.bar_chart` for the top-15.** Rejected — it doesn't guarantee value ordering; Altair with `sort="-x"`
  gives a properly rank-ordered bar.
- **Keep the scatter (filtered only).** Rejected (owner's call) — a ranked bar that responds to the filter
  earns its place better than a cloud.

---

### 🧭 Consequences

**Positive**
- One filter on both pages — filter by any mix of player/team/position; combinations narrow.
- The Players graph now *does something* (a live, ranked top-15 of the filtered set).
- No analytics/engine change; the web stays read-only.

**Negative / risks (mitigations)**
- **A ~570-name player multiselect** → Streamlit's multiselect is searchable; a team-scoped variant is a
  noted follow-up if needed.
- **Mixed row types** (Row vs dict) → a tolerant field read in `apply`.
- **Altair** in a web page → it's a Streamlit dependency (web-only); the core imports nothing from here
  (the guardrail test still holds).

---

### 📊 Validation

Probed live: 20 teams; both surfaces expose team/position/web_name (Players also price). Acceptance:
`filter_controls` renders the three multiselects (+ price on Players); `apply` narrows by any combination
(AND); Player Stats narrows every tab when a team/position is chosen; Players filters by team/player and
shows a top-15 **bar** (not the scatter); pagination + sort still work; the web writes nothing server-side;
the existing 571 tests stay green.
