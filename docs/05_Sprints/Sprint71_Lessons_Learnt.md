# Lessons Learned

**Sprint:** Sprint 071 — Web build parity + squad-tab reorg

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring the web to **full CLI `squad` build parity** — build with any/all options on **Build Squad** (or via
**Ask**), save into the session so **My Squad** picks it up to tweak, then download — and rename/regroup the
squad tabs logically. No engine change: reuse the same optimiser the CLI does.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Exposing an existing engine's options through reliable form widgets (not fragile NL).
- Keeping two edges (CLI + web) in lock-step by calling the *same* functions, not re-implementing.
- Renaming/reordering Streamlit multipage pages (filename-driven) without breaking tests.

### New Skills Acquired

- **`st.page_link` needs the multipage runtime** — it crashes under `AppTest`, so a cross-page link isn't
  headless-testable; a caption pointer is the robust fallback.
- **Additive contract change** — adding one optional field (`squad`) to a decision + `AppResult` extends a
  layer (ask) for a new edge without touching any existing caller.
- Streamlit **expander bodies always execute** (they hide, not defer), so an in-expander build runs every
  render — worth knowing for cost.

---

# What Went Well ✅

- **Real-data-first** confirmed the engine already supported every option (include/exclude/objective/weekly/
  formation), so the sprint was pure UI/edge — low risk, no optimiser changes.
- **Parity by reuse** — the Build Squad page runs the CLI's exact logic (`available_players`,
  `bench_weight`, `archetype_bands`, the score split), so it can't drift.
- **No regressions** — the plain shortlist, the CLI build, and every other page were untouched; the
  page renames tracked as `git mv` (history preserved) and all existing web tests passed under new names.
- **The Ask bridge stayed tiny** — one optional `squad` field threaded through; CLI output byte-unchanged.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `st.page_link` crashed every My Squad test | `AppTest` has no multipage runtime (`url_pathname` KeyError) | Use a caption pointing to the sidebar instead of a click-through link |
| Formation doesn't fit the save flow | `--formation` shapes an XI (11); a saveable squad is a 15 | Make it a display-only "best XI shape" preview that never saves |
| Web can't drift from the CLI | two edges, one behaviour | Both call the *same* `select_squad` / `decision_xp`; the web just supplies widgets |
| Adding "Use this squad" to Ask across reruns | a chat submit + a button click are separate runs | Stash the built squad in `session_state`; the button survives the rerun and clears on click |
| Renaming pages could break AppTest refs | ~26 `from_file` paths hard-code filenames | Update them together; a full test run catches any miss |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| One engine, many edges | Parity is free when the edge *calls* the engine rather than re-implementing its rules |
| Widgets > NL for options | ~10 structured choices belong in form controls, not prose parsing (reliable + self-describing) |
| AppTest limits | `st.page_link` to another page isn't headless-testable — prefer a caption or design around it |
| Additive contracts | A new optional field extends a layer for one edge without disturbing the rest |
| Streamlit expanders execute | Their body runs every render (hidden ≠ deferred) — a second build has a real cost |

---

# Development Lessons 💻

- Probe the engine before building UI — it told me this was a UI-only sprint (no optimiser work).
- Reuse the CLI's exact call, not a paraphrase, so the two surfaces stay identical.
- When a nice widget (page_link) fights the test harness, pick the simpler thing that stays testable.

---

# AI Collaboration Lessons 🤖

- The owner's scoping call — **widgets on Build (not NL), My Squad stays the tweaker, rename + regroup** —
  turned an ambiguous "put it in Ask" request into a clean, maintainable plan.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-062 | **Web build parity + tab reorg** — full CLI `squad` options as **form widgets on Build Squad** feeding the *same* engine (no change); the saveable build stays a **15** (formation = an XI-only display preview); My Squad stays the tweaker + points to Build Squad; rename Squads→**Squad Health**, Build→**Build Squad**, grouped; an optional Ask-build → session-squad bridge (a `squad` field on the decision/`AskResult`); no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- If the Build Squad page feels heavy on the cloud, gate the "best XI shape" preview behind a toggle (it
  builds every render). Related open items: pronoun-aware chat, a team-level squad-fixtures view, the
  tech-debt sweep (PuLP 4.0 API + shared squad renderer), and — post-GW1 — the Data Hardening flip +
  calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the real-data gate before building; keep the web an edge over the one engine; keep new edge-only
  data additive on the decision contract.

---

# Key Commands Learned

```text
python -m src.web_streamlit                    # run the app; Build Squad now has the full option set
python app.py ask "build me a squad for £100m" # CLI unchanged; the web Ask offers "Use this squad →"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Edge parity | Two surfaces (CLI, web) behaving identically because they call the same engine |
| Session active squad | The squad held in the browser session (built/adopted), tweaked in My Squad, never saved server-side |
| Display-only preview | A rendered result (best XI shape) that is shown but not adoptable/saveable |
| Additive contract change | Adding an optional field to a return value so a new consumer benefits without breaking existing ones |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-062 | The web-parity + tab-reorg design and the page_link/AppTest note |
| `pages/3_Build_Squad.py` | The full-option Build page (the widgets → same `select_squad`) |
| `pages/8_Ask.py` + `ask.AskResult.squad` | The Ask-build → session-squad bridge |

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

- US-200 Build Squad — full CLI option parity (include/exclude/bench/objective/no-xmins/weekly/bench-boost/
  include-unavailable as widgets → same `select_squad`; a display-only best-XI-shape preview)
- US-201 Tab rename + reorder (Build Squad · My Squad · Squad Health grouped; My Squad → Build Squad pointer)
- US-202 Ask-build → session-squad bridge ("Use this squad →" after a "build me a squad" answer)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
