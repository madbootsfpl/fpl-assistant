# Lessons Learned

**Sprint:** Sprint 103 — Deadline countdown (urgency · context · nudge · a live clock)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the static deadline line into a real experience — a countdown that **escalates in urgency**, shows
**what's coming** (matches · first kick-off), **nudges** the pre-deadline actions, and (on Home) **ticks
live**. All derived from data we already have; `now`-injected so the logic stays deterministically tested.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Pure, `now`-injected time logic** — urgency/context/clock-HTML all unit-tested without a live clock.
- **Graceful degradation** — server-fill + client-tick, with a text fallback beneath.

### New Skills Acquired

- **A live tick needs client-side JS** — `st.iframe` embeds our own HTML in a JS-enabled sandboxed iframe, so
  a `setInterval` ticks in the browser with **no server reruns** (the modern replacement for the deprecated
  `st.components.v1.html`).
- **Fill the cells server-side + tick client-side** — so the clock is readable even if the JS/iframe is
  blocked; keep the static text line as the accessible truth beneath.
- **Escalation is a pure function** — `deadline_urgency(time_left)` (calm/today/imminent) drives both the
  copy and the widget/clock colour; the page just maps urgency → `st.info`/`warning`/`error`.
- An Artifact preview of **pure HTML/JS** actually runs (no CDN/CSP blockers) — so a ticking clock demos live.

---

# What Went Well ✅

- **Everything testable** — urgency thresholds, context (matches/first-kickoff), the escalating banner, and
  the clock HTML (ISO + tick + server-filled cells) are all pinned deterministically.
- **Never a blank box** — server-filled cells + the text fallback mean the countdown always reads.
- **Caught the deprecation** — swapped `components.v1.html` → `st.iframe`; no warning, no looming removal.
- **A real preview** — the pure-HTML/JS clock ticked live in the Artifact — a genuine sign-off.
- 686 → 693 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A live tick without hammering the server | Streamlit reruns server-side | Client-side JS in an `st.iframe` (`setInterval`) |
| `components.v1.html` deprecation warning | slated for removal | Switch to `st.iframe` (JS-enabled inline HTML) |
| The Home deadline moved off `st.info` | now a clock + caption | Update the Home test to read the caption |
| `deadline_line` needed gw + deadline too | the clock needs them | Return `(gameweek, deadline, text, urgency)` |
| Testing an iframe's JS | AppTest doesn't run it | Test the pure `countdown_html` string instead |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Live tick | `st.iframe(our_html)` runs JS client-side; no server reruns |
| Degrade | Server-fill the cells + a text fallback → never blank |
| Urgency | One pure `deadline_urgency` drives copy + colour |
| Testable JS block | Split a pure `countdown_html` from the render call |

---

# Development Lessons 💻

- Put the whole computation in a pure function (`countdown_html`, `deadline_line`) and keep the Streamlit call
  a one-liner — then the logic is unit-tested and the page is thin.
- When a feature moves content between widgets (info → caption), chase the test that reads the old widget.
- Prefer the current API over a deprecated one the moment a smoke surfaces it.

---

# AI Collaboration Lessons 🤖

- Four enhancements split cleanly by layer: three pure/server-side (urgency · context · nudge) in one story,
  the JS clock in another behind its own ADR — so each commit was green and the risky bit (first JS) was
  isolated + documented.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-088 | **A live client-side countdown clock** — `countdown_html` builds a self-contained Days:Hrs:Mins:Secs clock (urgency-coloured, cells server-filled) that ticks via `setInterval`, embedded with `st.iframe` (JS-enabled). The first JS in the app: one self-contained block, no external scripts, only our own ISO/int embedded, display-only; the static text line remains the no-JS fallback. Revisits ADR-086's "no live tick" deferral | Accepted |
| — | US-267 (urgency + context + nudge) needed no ADR — it extends ADR-086. | — |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **"N of your players play first"** on Squads (a per-squad join) — the deferred context nicety.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + mini-league position (GW1).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor.
- Flip the **beta** on when ready (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep splitting a pure builder from the render call so UI logic stays testable.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Home: a live ticking deadline clock that escalates ⏳ → 🟠 → 🔴
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Urgency | How close a deadline is: calm (>24h) · today (<24h) · imminent (<2h) |
| Server-fill + client-tick | Fill the clock server-side, keep it live with browser JS |
| GW context | The gameweek's match count + first kick-off, from the fixtures |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-088 | The live-clock decision (first JS; `st.iframe`; degrade) |
| `src/web_streamlit/countdown.py` | The pure `countdown_html` + `render_countdown` |
| `src/analytics/deadline.py` | `deadline_urgency` + `gameweek_context` |

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

- US-267 Urgency + context + action nudge — the banner escalates + shows what's coming + nudges (extends ADR-086)
- US-268 A live ticking clock — `countdown_html` via `st.iframe`, urgency-coloured, on Home (ADR-088)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
