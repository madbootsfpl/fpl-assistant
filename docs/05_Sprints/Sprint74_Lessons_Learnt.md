# Lessons Learned

**Sprint:** Sprint 074 — Help tooltips (ⓘ) across the web app

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Put a small **ⓘ tooltip** over every feature option in the web app so a new user can tell what each control
does — added consistently, and enforced by a coverage test so it stays that way.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Making a broad, consistent UX change cheaply by editing the **shared components** first.
- Turning a "cover everything" requirement into a **machine-checked** guarantee (a coverage test).

### New Skills Acquired

- Streamlit renders an **ⓘ tooltip** from any widget's `help=` — but **`st.tabs` labels and
  `st.chat_input` don't take it** (captions must cover those).
- **AppTest exposes `.help`** on widgets, so a test can assert every input control carries a tooltip.

---

# What Went Well ✅

- **Leverage** — help on `filters.py` / `paginate.py` / `squads.py` covered Players, Player Stats, Trending
  and every squad page before any page was touched individually.
- **Enforced, not audited** — the coverage test asserts every input widget on all nine pages has non-empty
  `.help`; it grew story-by-story and now guards future controls too.
- **Zero behaviour risk** — help text only; the whole suite stayed green throughout.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Tabs / chat input can't show ⓘ | `st.tabs` labels + `st.chat_input` take no `help=` | Exempt them in the test; keep the existing captions |
| "Cover everything" is easy to miss | many controls across ~10 files | A coverage test over `.help` for every input widget, grown per story |
| Conditional controls (swap-in, apply-swap) don't always render | they depend on state | Add help regardless; the test checks whatever renders |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Shared-component leverage | Put help where controls are *defined once* (filters/paginate/sidebar) to cover many pages |
| Coverage as a test | `.help` via AppTest turns "all options documented" into a CI gate, not a manual pass |
| `help=` reach | Works on inputs + buttons; **not** on tab labels or chat input |
| Presence ≠ accuracy | The test guarantees a tooltip exists; correct wording is still a review concern |

---

# Development Lessons 💻

- For a blanket UX change, edit the shared seam first, then mop up per-page — smaller, safer diff.
- Encode the "all of X" requirement as a test so it can't silently regress.

---

# AI Collaboration Lessons 🤖

- The owner's ask ("ⓘ over all feature options") mapped cleanly to Streamlit's `help=` + a coverage test —
  a small, well-bounded sprint with a durable guarantee.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-065 | **Help tooltips (ⓘ)** — a concise, action-oriented `help=` on every input control across the web (added at the shared components + per page; key buttons too); `st.tabs`/`st.chat_input` exempt (captions); a coverage test (`.help` via AppTest) enforces "all options have a tooltip"; no behaviour change | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- The coverage test guarantees a tooltip *exists*; a periodic read-through keeps the *wording* honest. Open
  items: a team-scoped player multiselect, pronoun-aware chat, a team-level squad-fixtures view, the
  tech-debt sweep (PuLP 4.0 + shared squad renderer), and — post-GW1 — the Data Hardening flip +
  calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Edit shared components first for blanket changes; encode "cover everything" as a test.

---

# Key Commands Learned

```text
python -m pytest tests/test_help_tooltips.py -q   # asserts every input control on every page carries help
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Help tooltip (ⓘ) | Streamlit's `help=` on a widget — a small info icon showing what the control does |
| Coverage test | A test that asserts a property holds across *all* items (here: every input has help) |
| Shared-component leverage | Making a change where a control is defined once, so many pages inherit it |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-065 | The help-tooltip convention + the tabs/chat_input exemption + the coverage test |
| `tests/test_help_tooltips.py` | The guarantee that every option has a tooltip |
| `filters.py` / `paginate.py` / `squads.py` | Where a single `help=` covers many pages |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-208 Help tooltips — shared components (filters/paginate/squads) + browse pages; the coverage test
- US-209 Help tooltips — Build Squad · My Squad · Transfer · Captain; coverage test extended to all pages

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
