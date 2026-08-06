# Architectural Decision Record: Sidebar consolidation — Players & Squads

**Decision ID:** ADR-069
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** re-groups the Streamlit multipage sidebar (ADR-052/063 named/ordered the
pages). No analytics change. Triggered by owner request.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The sidebar has grown to 12 tabs. The owner wants fewer, clearer top-level tabs: merge **Players + Player
Stats** → **Players**, and **Build Squad + My Squad + Squad Health + Transfer + Captain** → **Squads** —
leaving `Players · Fixtures · Squads · Ask · News · Trending · Help` (7).

**Verified in code:** `st.segmented_control` is AppTest-drivable and renders **only the selected option** —
so a 5-tool Squads page won't recompute the ILP build + transfer + captain + health each interaction (which
`st.tabs` would, executing every tab body). The current pages are top-level scripts, so consolidating means
**extracting each view's body into a `render_*()` function**.

#### Decision Drivers
- **Cleaner IA** — fewer top-level tabs, grouped by the natural workflow.
- **Fast** — the merged Squads page must not re-run 5 heavy tools per render.
- **No behaviour change** — each tool behaves + renders exactly as before (same engine, same outputs).
- **No server writes** — the read-only guardrail holds.

---

### ✅ Decision

**1. Two consolidated pages behind a lazy segmented control.** Merge Players+Player Stats and the five
squad tools into two pages, each with an `st.segmented_control` sub-nav that renders **only the selected
view** (tab-like look, lazy compute). Ask · Fixtures · News · Trending · Help stay top-level. Final sidebar:
`1 Players · 2 Fixtures · 3 Squads · 4 Ask · 5 News · 6 Trending · 7 Help`.

**2. Extract view bodies into `render_*()` functions** (a `web_streamlit/views/` package) that take
already-loaded data + shared helpers. The merged page: page-config → `render_data_status()` → the shared
control → `segmented_control(...)` → call the chosen `render_*`.

**3. Players (US-216).** A shared `filter_controls(rows, key="players", with_price=True)` above the control
(one filter serves the Pool — players have a price — *and* the stat boards, where the price check is a
no-op on price-less analytic rows); views: **Pool · Over/under · DefCon · Clean sheets · xG**.

**4. Squads (US-217).** `render_sidebar()` + the control; views **Build · My Squad · Health · Transfer ·
Captain**. **Build** creates (no picker); the four **manage** views share one `squad_picker()`. Order = the
workflow the Help tab teaches.

**5. Tests + copy.** Rewire the ~38 AppTest references to the merged pages (drive
`segmented_control.set_value(view)` to reach a tool); **keep every prior assertion** (behaviour unchanged).
Update `test_help_tooltips._COVERED`; the segmented control + filter/picker carry `help=`. Update **Home**
and the **Help** guide to the 7-tab nav.

---

### 🔀 Alternatives Considered

- **`st.tabs` for the sub-nav.** Rejected — it executes every tab body, so the Squads page would recompute
  all 5 heavy tools each render (slow, esp. on the Cloud). The segmented control is tab-like but lazy.
- **`st.navigation` sidebar sections.** Rejected — that groups *separate* sidebar entries under a header;
  the owner wants **one** top-level tab per group with in-page sub-nav.
- **Leave the 12 tabs.** Rejected — the owner wants a cleaner IA; the workflow groups are natural.
- **Radio/dropdown sub-nav.** Rejected in favour of the tab-like segmented control (same laziness, better
  look).

---

### 🧭 Consequences

**Positive**
- 12 → 7 tabs, grouped by workflow; the Squads page stays fast (only the shown tool computes).
- View bodies become reusable `render_*` functions (a cleaner edge; easier to test in isolation).
- No behaviour/output change; no server writes.

**Negative / risks (mitigations)**
- **Big test rewire** (~38 refs) → rewired, not weakened; every prior assertion kept, reached via the
  segmented control. A green suite is the proof of no behaviour change.
- **Another nav reshuffle** → intended as the settling point; Home + Help updated so users re-orient.
- **A shared picker across the manage views** → one pick feeds My Squad/Health/Transfer/Captain (nicer);
  Build still sets the session squad the others read.

---

### 📊 Validation

Verified: `st.segmented_control` renders only the selected view (lazy) and AppTest can switch it. Acceptance:
the merged Players + Squads pages render each view via the control; **every prior assertion survives**
(tables, bars, filters, build/transfer/captain/health, session-squad edits); the sidebar shows 7 tabs; the
web writes nothing server-side; the tooltip coverage holds; the existing 585 tests stay green (rewired).
