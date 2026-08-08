# Lessons Learned

**Sprint:** Sprint 118 — History on the web (+ a price column)

**Dates:** 2026-08-19

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Complete the Sprint-117 history feature: a per-season **price / price-change** column across the CLI/Ask
renderer, and a **web** History view (a player picker → a season table + a per-GW trend). Display only, reusing
`analytics.player_history`; the analytics/xP untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Build once, surface many** — one pure assembler feeding the CLI, Ask and web.
- **Right-sizing presentation** — native components where they fit; bespoke HTML/CSS only where it earns it.

### New Skills Acquired

- **A shared assembler makes a new surface cheap.** `analytics.player_history` already produced the shape, so
  the web view was a selectbox + a `st.dataframe` + a `st.line_chart` — no new logic, no drift from the CLI.
- **Slot into the existing sub-nav.** A per-player view lives happily as another `st.segmented_control` option
  on the Players page — no new tab, discoverable next to the stat boards.
- **Native vs bespoke is a per-surface call.** The captain card earned custom CSS (a designed card); the
  history table is a data grid → native `st.dataframe`/`st.line_chart` read consistently and skip a sign-off.
- **Resolve a data caveat by reading the test, not re-probing.** The Sprint-117 price "£1.4m" scare was a
  mis-divided debug; the ingestion test (`115 → 11.5`) confirmed the stored cost is £m — trustworthy to show.

---

# What Went Well ✅

- **One history source, three surfaces** (CLI · Ask · web) — no duplication.
- **The web view was small** — reused the assembler + the shared `column_config`.
- **Native + consistent** — no bespoke design, no preview needed.
- 762 → 764 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Was the price safe to show? | a mis-divided Sprint-117 debug read £1.4m | The ingestion test confirms £m (`115 → 11.5`) — add the column |
| History is per-player, not a board | the Players views are all-player boards | A selectbox + an on-demand `Storage` read for the picked player |
| Per-GW chart can't be tested now | per-GW is empty preseason | Test the dataframe + the GW1 caption; the chart lights up at GW1 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Shared assembler | One pure function → CLI + Ask + web with no drift |
| Sub-nav reuse | A per-entity view fits the segmented control |
| Native vs bespoke | Data grids → native; designed cards → HTML/CSS |
| Trust via tests | A pinned conversion in a test resolves a data-units doubt |

---

# Development Lessons 💻

- Add a new surface by reusing the assembler, not re-deriving the data.
- Prefer native Streamlit for tabular/plot data; reserve custom CSS for designed components.
- When a data value looks wrong, check the conversion test before re-probing.

---

# AI Collaboration Lessons 🤖

- History stays a lens across every surface: it reads stored rows, the numbers are the truth, and (in Ask) the
  facts anchor the narration — the web view just presents the same shape.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-297/298 extend **ADR-027/060** (history) + **ADR-069** (the Players sub-nav). New:
`player_history` season rows carry `start_cost`/`end_cost`/`change`; `render_player_history` gains a £ column;
`web_streamlit/views/players.py::render_history` + a "History" option on the Players segmented control._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A coloured up/down on the web `Δ£`** + a rolling-form sparkline once per-GW data lands.
- **A hosted LLM for the deploy** so prose + the free-form tail work on the cloud.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the per-GW history fills → the trend/chart go live; Data Hardening + xP
  calibration; the price/form/ownership signals sharpen.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reusing the pure assembler for each new surface; don't re-implement the data shape.

---

# Key Commands Learned

```text
python app.py history Haaland          # now with a £ start→end column
python -m src.web_streamlit            # Players → History → pick a player
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Sub-nav view | A `st.segmented_control` option on a consolidated page |
| On-demand read | A short-lived `Storage` fetch for the selected item only |
| Native vs bespoke | Data grids use native widgets; designed cards use HTML/CSS |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/views/players.py` (`render_history`) | The web History view |
| `src/analytics/history.py` | The one assembler feeding CLI/Ask/web |
| `src/ui/history.py` | The mono renderer + the £ column |

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

- US-297 A price column in the history (`£start→end` + `Δ£`) — CLI + Ask (ADR-027/060)
- US-298 History on the web — a Players "History" view (season table + per-GW chart + price) (ADR-069)

**Stories Carried Forward:**

- None. (A coloured Δ£ + a rolling-form sparkline are follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
