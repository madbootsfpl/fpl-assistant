# Lessons Learned

**Sprint:** Sprint 107 — Ask readability + a "fit" ✅ emoji

**Dates:** 2026-08-08

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two small, honest display fixes from tester feedback: the **Ask** tab should read well (long answers wrap; the
newest answer scrolls into view), and the **Fit** column should show a positive **✅** for a fit player rather
than a blank cell. Display-only — the analytics/engine untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Separating display from meaning** — a value used both as a UI flag *and* as a truthiness test needs a
  second, display-only helper rather than a change to the shared one.
- **Small Streamlit affordances** — `st.code(wrap_lines=True)` for readable prose; a same-origin iframe for a
  scroll nudge.

### New Skills Acquired

- **Don't overload a value that carries logic.** `availability_flag` returns `""` for a fit player, and that
  emptiness *is* the "is this player a concern?" test (My Squad's who's-flagged caption, the gameweek flags).
  A positive ✅ had to come from a **separate** `fit_flag = availability_flag(...) or "✅"`, leaving the
  truthiness untouched. Changing the original would have silently marked every fit player as "flagged".
- **`wrap_lines=True` keeps alignment.** It wraps long sentences but leaves short lines alone, so the aligned
  squad tables / plan / Why-Risk blocks inside the same mono block stay readable.
- **`st.iframe` height must be positive** — `0` raises `StreamlitInvalidHeightError`; `1` is the invisible
  minimum.

---

# What Went Well ✅

- **Both fixes were tiny and low-risk** — a one-word `wrap_lines`, a small scroll script, and a five-line
  display helper. Fast to build, fast to verify, no engine change.
- **The `fit_flag` split kept two behaviours honest at once** — a positive Fit column *and* an unchanged
  flagged-player detection.
- **Reused a known trick** — the same-origin `window.parent` iframe from the countdown clock (Sprint 101/103).
- 707 → 708 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A fit ✅ would break flagged-detection | `availability_flag`'s `""` doubles as a truthiness test | A **separate** `fit_flag` for display; `availability_flag` unchanged |
| `st.iframe(height=0)` crashed | Streamlit requires a positive height | `height=1` (invisible) |
| The newest Ask answer sat off-screen | history replays oldest-first, appends at the bottom | A same-origin `window.parent.scrollTo(…, smooth)` nudge after the loop |
| Long answers overflowed the mono block | `st.code` doesn't wrap by default | `wrap_lines=True` (keeps table alignment) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Overloaded values | If a value carries logic (a truthiness test), add a display-only sibling — don't mutate it |
| `st.code(wrap_lines=True)` | Wraps prose, preserves aligned/short lines |
| `st.iframe` height | Must be positive; `1` for "invisible" |
| Same-origin scroll | The app can scroll its host via `window.parent` (best-effort, try/catch) |

---

# Development Lessons 💻

- Before "improving" a shared helper, check whether anything relies on its *current* return (here, the empty
  string) as a signal. Add a sibling instead.
- Best-effort browser affordances (scroll, focus) belong in a `try/catch` that no-ops — never assume the host
  frame is same-origin forever.
- Strengthen the existing test rather than only adding one: the Fit-column tests now assert ✅ is present (and
  no blank cells), which pins the new behaviour in place.

---

# AI Collaboration Lessons 🤖

- Tester feedback that names a *specific annoyance* ("sentences don't wrap", "Fit is blank") maps almost
  directly to a one-line fix — the value is in translating the annoyance to the exact Streamlit affordance.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-275 extends **ADR-052** (the Ask chat display), US-276 extends **ADR-074** (the Fit column).
New: `analytics/crowd.fit_flag(player)` (display-only, `availability_flag(...) or "✅"`); `AVAILABILITY_LEGEND`
now leads with "✅ available". `availability_flag` is unchanged (still `""` for fit)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A richer web-native Ask render** (markdown chat bubbles instead of a monospace block) — the standing UI
  polish item, now that wrapping has patched the worst of the readability.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated "why" signals light up (form · % of team goals · opponent xGC); Data
  Hardening + xP calibration; the Price Change Predictor.
- Flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep folding tester feedback into small, single-purpose display sprints — they're cheap and keep the app
  feeling responsive to real use.

---

# Key Commands Learned

```text
python -m pytest tests/test_crowd.py -q -k fit_flag   # the new display-helper test
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `fit_flag` | Display-only Fit flag — ✅ when fit, else the availability concern flag |
| `wrap_lines` | `st.code` option that wraps long lines while keeping short ones aligned |
| Same-origin nudge | An iframe script that scrolls its parent (best-effort) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/crowd.py` (`fit_flag` / `availability_flag`) | The display-vs-truthiness split |
| `src/web_streamlit/pages/4_Ask.py` | `wrap_lines` + the scroll nudge |
| ADR-074 | The Fit column the ✅ extends |

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

- US-275 Ask readability + auto-scroll — `wrap_lines=True` + a same-origin scroll-to-bottom nudge (ADR-052)
- US-276 A "fit" ✅ emoji — a `fit_flag` display helper on the Fit columns; legend updated (ADR-074)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
