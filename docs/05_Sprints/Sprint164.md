# Sprint 164: Honest column-sort — scrollable tables replace pagination (US-407)

**Dates:** 2026-08-17
**Status:** ✅ Complete — ADR-116 + US-407 (owner-approved, option A). Display-only. UX-audit carry-over. 1007 → 1004 tests
(the 3 `page_labels` tests retired with paging).

> **The bug (UX audit, interaction honesty):** the browse tables sorted the full filtered list via a "Sort by"
> selectbox, then `paginate()` sliced to 50/30 rows. Clicking a **native column header** re-sorted only the visible
> page — it *looked* like a global sort but wasn't. **Verified:** Streamlit 1.61.1 can't disable native sort, so the
> honest fix is to show the whole set (owner chose A over a disclosure caption).

---

### 🎯 Delivered (US-407, ADR-116)

- **One scrollable, fully-sorted `st.dataframe` per table** — the Players **pool**, the **stat boards** (`_board`),
  and **Trending** (incl. the buzz board) now pass their **entire** sorted list to `st.dataframe` (with a fixed
  `height` so it's a predictable scrollable box). The **native column-header sort now orders the whole set** —
  honest — and the explicit **"Sort by"** selectbox sets the default order.
- **Retired `paginate()` + `page_labels`** → a thin **`show_count(rows)`** helper (the "N shown" caption); the grid
  scrolls (row virtualisation keeps it light, so ~600 players in one grid is fine). Supersedes ADR-063.
- **Tests:** the pool / talked-about / owned-board pagination tests now assert the **full** list is shown and
  there's **no "Page" control**; `test_paginate.py` (page_labels) removed. **1004 total.**

**Owner smoke:** the Players pool + stat boards + Trending scroll as one table; clicking a column header sorts the
**whole** list; no page selector.

### 🧠 Lessons

- **Verify the platform limit before choosing a fix.** Streamlit 1.61 can't disable native sort — that ruled out
  "just turn it off" and made "show the whole set" the honest path.
- **A misleading affordance is worse than a missing one.** A header that sorts only the page reads as a global sort;
  removing the page (so it *is* global) beats disclosing the caveat.
