# Architectural Decision Record: A Help guide tab

**Decision ID:** ADR-068
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — a new onboarding page on the Streamlit edge (ADR-052). No analytics
change. Triggered by tester feedback (Feedback_Log, 2026-08-06).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

A new user can't easily tell *how to use the tool end-to-end* — Home lists the tabs, but there's no
step-by-step "here's how you build and manage your team with the assistant". The tester asked for a **Help**
tab giving that walkthrough.

#### Decision Drivers
- **Onboarding** — a clear, ordered path from a blank slate to a saved, tweaked team.
- **Complement, don't duplicate** — Home has the short overview; Help goes deeper (a recipe, not a list).
- **Robust + low-maintenance** — static content, no data dependency (renders even before `refresh`).
- **No churn** — don't renumber the sidebar again.

---

### ✅ Decision

**1. A static step-by-step Help page.** `pages/12_Help.py` — a numbered walkthrough with **one
`st.expander` per step** (the first expanded), copy-paste `ask` examples, and a pointer from each step to
the right tab: *build → make it yours → check health → improve (transfer/captain) → research → ask → save*.
Markdown only — **no analytics/data dependency** (so it renders before any refresh) and **no input
controls** (so it's outside the help-tooltip coverage test, ADR-065). It closes with an honest note on data
freshness + what lights up at **GW1 (2026-08-21)** and the crowd-signals *lens-not-truth* principle.

**2. Placed last (owner's call).** `12_Help.py` sorts after Trending, so **no other page files move**
(Streamlit orders the sidebar by the numeric prefix). A one-line pointer to Help is added on **Home**.

---

### 🔀 Alternatives Considered

- **An interactive stepper/wizard** (Next/Back, session-state progress). Rejected (owner's call) — more code
  + state to maintain; a static guide is clearer and easier to keep accurate.
- **Placed first (before Players).** Rejected (owner's call) — would renumber all 11 pages again (a third
  reorder); Home already carries the overview + will point to Help, so it isn't hidden at the end.
- **Only expand Home's overview.** Rejected — the ask is a *step-by-step recipe*, which is more than a tab
  list belongs on the landing.

---

### 🧭 Consequences

**Positive**
- A new user has a clear path to building + managing a team with the assistant.
- Static + no data dependency → robust, renders anytime, trivial to keep accurate.
- Zero renumber churn; Home points to it.

**Negative / risks (mitigations)**
- **The guide can drift from the app** → keep it a *recipe* (tabs + `ask` examples), not a spec; a
  key-content test flags if the core steps/examples vanish; reviews catch wording.
- **Discoverability at the end** → the Home pointer + the literal label "Help" mitigate it.

---

### 📊 Validation

Acceptance: `pages/12_Help.py` renders with **no data** (no exception) and contains the key steps + at least
one `ask` example (a test asserts it); Home gains a one-line Help pointer; no input widgets (so the
tooltip-coverage test is unaffected); the web writes nothing server-side; the existing 584 tests stay green.
