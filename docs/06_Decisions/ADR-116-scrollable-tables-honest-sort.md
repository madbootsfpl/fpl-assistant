# Architectural Decision Record: One scrollable table (honest column-sort), replacing pagination

**Decision ID:** ADR-116
**Date:** 2026-08-17
**Status:** Accepted — owner-approved (option A). Build = the header-sort honesty fix (UX audit carry-over).
**Superseded By / Replaces:** **Supersedes ADR-063** (the 50/30-per-page pagination). Extends ADR-057/064 (the
pool + shared filters). Display-only.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The UX audit flagged an **interaction-honesty** bug: the browse tables (Players pool · the stat boards · Trending)
sort the **full** filtered list via an explicit **"Sort by"** selectbox, then `paginate()` slices to 50/30 rows
before `st.dataframe`. Clicking a **native column header** re-sorts only the **visible page**, not the whole
result set — the header *looks* like a global sort but silently isn't. Same class as the Your-team card chips
(US-388) and the Ask-markdown table.

**Verified constraint:** **Streamlit 1.61.1 cannot disable native column sorting** on `st.dataframe` (no
`sortable` flag; `column_config` can't turn it off), and the sort state isn't reported back to Python — so the
header-sort can neither be removed nor intercepted. The only honest options are **(A)** show the whole set so the
native sort operates on everything, or **(B)** disclose the page-only behaviour in a caption. The owner chose **A**.

#### Decision Drivers
- **Honesty** — no control that looks like it does one thing and does another.
- **Simpler UX** — a single scrollable, sorted grid beats page-hopping.
- **Perf** — Streamlit's dataframe (glide-data-grid) **virtualises rows** (only visible rows render/load images),
  so showing all ~600 players in one grid is fine.

---

### ✅ Decision

**Show the full filtered+sorted list in one scrollable `st.dataframe`; remove pagination.** Each browse table
passes its **entire** sorted list to `st.dataframe` (with a fixed `height` so it's a predictable scrollable box) —
so the **native column-header sort now sorts the whole set** (honest), while the explicit **"Sort by"** selectbox
sets the default order. `paginate()` (the page selectbox + slice) is retired; a thin **`show_count(rows)`** helper
renders the "N shown" caption and returns the rows unchanged. Applies to the **Players pool**, the **stat boards**
(`_board`), and **Trending** (incl. the buzz board).

**What this is *not*.** Not an analytics/engine change. Not a change to the filters (ADR-064) or the sort logic —
only pagination is removed. `page_labels` and its unit test go with the retired paging.

---

### 🔀 Alternatives Considered

- **B — keep pagination + a disclosure caption** ("header sorts this page; use Sort by for the whole list").
  Rejected by the owner — honest, but it *discloses* the lie rather than removing it, and keeps the page-hop.
- **Disable native sort / intercept it.** Impossible in Streamlit 1.61.1 (verified).
- **`st.table` (static, no sort).** Rejected — no `column_config`/images, renders all rows untruncated (no scroll).

---

### 🧭 Consequences

**Positive**
- The column-header sort is **honest** — it sorts the full result set.
- **Simpler** — one scrollable grid, no page selectbox; the explicit "Sort by" remains the default order.

**Negative / risks (mitigations)**
- **All rows in one grid.** *Mitigation:* row virtualisation (only visible rows render/load images) + a fixed
  `height` cap; the count caption shows the total.
- **Reverses ADR-063.** *Mitigation:* recorded here as a supersede; the pagination helper/test are removed cleanly.

---

### 🧾 Status & follow-ups

- **Accepted.** Build: retire `paginate()`/`page_labels` → a `show_count` helper; pass the full list + a `height` to
  each browse `st.dataframe`; update the pagination tests (assert the full row-set is shown, no "Page" selectbox).
- **Not this ADR:** the incremental token retro-fit (Sprint B carry-over).
