# Lessons Learned

**Sprint:** Sprint 063 — Tester-feedback polish: centre the My Squad pitch photos

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Act on the first tester-feedback item: **centre the player photos** on the My Squad pitch (they were
left-aligned), using a robust native fix — no custom CSS, no core change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Running a small feedback item through the loop: log → triage → fix → close.
- Verifying a UI approach (nested columns) *before* committing to it.

### New Skills Acquired

- Centring content in a Streamlit card with a nested `st.columns([1, 2, 1])` middle column — a native
  alternative to custom CSS (one level of nesting is allowed inside a row column).

---

# What Went Well ✅

- **The feedback loop worked end-to-end** — logged + triaged in `Feedback_Log.md`, then fixed the same day.
- **Robust-by-verification** — probed nested columns under `AppTest` first, so "no custom CSS" held without
  guessing whether Streamlit would allow the nesting.
- **Tiny, contained change** — one helper edit, no regressions, 504 tests unchanged.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `st.image` left-aligns in a card | Streamlit default | Place it in the middle of a nested `st.columns([1,2,1])` |
| Alignment isn't unit-testable | `AppTest` can't assert visual centring | Verify by headless render (no error) + a live eyeball |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Centre without CSS | A nested `[1,2,1]` column centres content natively (within the one-level nesting limit) |
| Verify then plan | Probing the framework's behaviour up front keeps a "robustness first" constraint honest |
| Some things are smoke-only | Visual details (alignment) are verified by render + eyeball, not unit tests |

---

# Development Lessons 💻

- For a UI micro-fix, prefer the native primitive (columns) over injecting CSS.
- Keep small feedback turns small — log, fix, close; don't over-engineer a one-line polish.

---

# AI Collaboration Lessons 🤖

- A precise piece of feedback ("centre the images, currently left-aligned") is trivially actionable — the
  loop's value is turning that into a logged, fixed, closed item quickly.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No ADR — a UI polish over the settled edge (Sprint 054/055/062 precedent)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Keep gathering tester feedback (the Sprint 059 loop) → triage into `Feedback_Log.md`. Standing markers:
  **GW1 (2026-08-21)** — the trends `ask` intent (US-185) + threshold calibration + Data Hardening.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the feedback loop turning: small items logged + fixed promptly; larger ones batched into a sprint.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -q   # the My Squad pitch render test
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Nested-column centring | Using `st.columns([1,2,1])` and the middle column to centre content natively |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/pitch.py` | The pitch card renderer (now with centred photos) |
| `docs/00_Project/Feedback_Log.md` | The tester-feedback triage log |

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

- US-188 Centre the My Squad pitch photos (nested-column, native)

**Stories Carried Forward:**

- None (GW1 markers stand: US-185 trends intent + calibration + Data Hardening)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
