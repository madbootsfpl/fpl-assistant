# Architectural Decision Record: Player Stats page + shared pagination

**Decision ID:** ADR-063
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — extends the Streamlit edge (ADR-052) with a stats view + a reusable
paginator. No analytics change (reuses `over_under`/`defcon_reliability`/`defensive_solidity` + the `xg`
ranking of ADR-015/017/018/019). Triggered by tester feedback (Feedback_Log, 2026-08-06).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Three tester gaps: (1) the CLI's **Overperf · DefCon · Cleansheet** (and xG) stat views have no web home;
(2) the **Players** table caps at 50 with no way to page through the rest, and can't sort by team/position;
(3) the **Trending** boards cap at 30. All three are display limits over data the web already loads.

**Verified on real data (2026-08-06):** the stat commands print full tables now — they read **season-to-
date** fields, which preseason are **last season's carryover** (the bootstrap keeps prior aggregates until
the new season overwrites them). So a stats page is useful immediately; no GW1 gating.

#### Decision Drivers
- **Reuse the analytics** — the web must call the same `over_under`/`defcon_reliability`/`defensive_solidity`
  the CLI does (no drift, no engine change).
- **One paginator** — Players, Trending and Player Stats share the same see-everything control.
- **Honest labelling** — the stats are season-to-date (last season's totals preseason); say so.
- **No server writes** — read-only, like every page.

---

### ✅ Decision

**1. A Player Stats page (US-203).** A new `pages/2_Player_Stats.py` with `st.tabs(["Over/under", "DefCon",
"Clean sheets", "xG"])`. Each tab runs the analytic (`over_under` / `defcon_reliability` /
`defensive_solidity`; xG = `sorted(players, key=xgi)`) and renders an st.dataframe with the CLI's columns +
a **team badge** (the analytics rows carry `team` but no player `id`, so badges — not per-player photos —
keep it uniform and change no analytics). Paginated (below). A caption: *"Season-to-date — preseason these
are last season's totals; ≥900 mins."* Placed at **sidebar position 2** (reference views grouped with
Players); the other pages renumber via `git mv`.

**2. A shared paginator (US-203) — `web_streamlit/paginate.py`.**
```
paginate(rows, *, key, per_page=50) -> list      # renders a page control, returns the page's slice
page_labels(total, per_page) -> list[str]         # pure: ["1–50", "51–100", …]  (unit-tested)
```
≤ `per_page` rows → a count caption, return all. Else a **page selectbox** (range labels) + a
"Showing X–Y of N" caption; return the slice. Each caller passes a unique `key` (tab-safe). Display-only.

**3. Players — pagination + sort (US-204).** Replace the `How many` (5–50) slider with
`paginate(ranked, key="players", per_page=50)` — page through **all** matches. Add **team** and
**position** to the *Sort by* selectbox (points/value via `rank_players`; team/position via a plain sort
key). The scatter still spans all matches; st.dataframe headers stay click-sortable.

**4. Trending — pagination (US-205).** Fetch each of the four boards with a large limit
(`trending(players, by, limit=len(players))`) and `paginate(rows, key=f"trend_{by}", per_page=30)` — page
past 30 on every board. The GW1-empty note and the (already-uncapped) buzz board are unchanged.

---

### 🔀 Alternatives Considered

- **Stats as tabs inside the Players page.** Rejected — a dedicated page is clearer and keeps Players about
  the picking table; the tester asked for a "Stats / Player Stats tab".
- **A "show top N" slider with a bigger max.** Rejected — the tester wants to page through *all*; a paginator
  is the see-everything answer and reuses across three pages.
- **Show-all + rely on st.dataframe's internal scroll.** Rejected as the primary — works, but "1–50 →
  next 50" is the explicit ask; the paginator also bounds the rendered rows.
- **Add player photos to the stat tables.** Deferred — the analytics rows lack `id`; adding it is an
  engine change for a cosmetic gain. Team badges suffice.
- **Append Player Stats at the end (no renumber).** Rejected (owner's call) — logical grouping with Players
  is worth the mechanical renumber.

---

### 🧭 Consequences

**Positive**
- Full stat-view parity in the web, reusing the analytics (no drift, no engine change).
- One paginator across Players / Trending / Player Stats — see everything, consistent UX.
- Players sorts by team/position; Trending pages past 30.

**Negative / risks (mitigations)**
- **Placing Player Stats at 2 renumbers 9 pages** → mechanical `git mv`; update the AppTest refs + Home copy
  together; a full test run catches a miss.
- **Season-to-date = last season preseason** → a caption makes the provenance explicit (as the momentum
  boards do for their fields).
- **Pagination + tabs** → each caller passes a unique `key` so page state doesn't collide.

---

### 📊 Validation

Probed live: `overperf`/`defcon`/`cleansheet`/`xg` all return full tables (267 / 248 / 117 / all rows) from
season-to-date fields. Acceptance: the Player Stats page renders each tab + paginates; `page_labels` is
unit-tested; Players pages through all + sorts by team/position; a Trending board pages past 30; the
renumbered pages resolve under their new refs; the web writes nothing server-side; the existing 565 tests
stay green.
