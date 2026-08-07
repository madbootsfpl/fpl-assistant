# Lessons Learned

**Sprint:** Sprint 098 — Club-shirt image fallback + captain double-points (next-GW only)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

(1) Every player card/table shows an image — the **photo when it exists, else the club shirt**; (2) the My
Squad **Projected XI** total reflects the **captain's ×2 for the next GW**, with a clear note that the double
counts for one GW when a longer horizon is selected.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Verify the data path before choosing an approach** — the design hinged on *how* photos are missing.
- **Reuse existing computed data** — the captain's next-GW figure was already in `by_gameweek` (ADR-032).

### New Skills Acquired

- The FPL bootstrap **`photo` field is `{code}.jpg` for everyone** — it does *not* flag a missing image; all
  573 players have a code yet ~25% of photo files **403**. So the only reliable signal is an **existence
  check** against the CDN.
- **Keeping network out of the test suite:** a render-time sweep would fire on every page AppTest. An **autouse
  `conftest.py` fixture** that patches the sweep to "nothing missing" keeps the suite offline + fast, while the
  real app still does the check (a unit test overrides the patch to cover the fallback logic).
- **Captaincy is a weekly decision** — doubling a fixed captain across N horizon GWs overstates it; adding the
  captain's *next-GW* xP once is the honest model, made explicit with a one-GW caption.
- The Streamlit squad **session key is `"squad"`** (not `"active_squad"`) — the picker defaults to that; a
  smoke test that set the wrong key silently loaded the saved (captain-less) squad.

---

# What Went Well ✅

- **Real-data de-risking** — proving the `photo` field is useless + the 403 rate made the existence-check
  decision obvious and the honest scope clear.
- **Offline, fast suite** — the conftest patch kept 663 tests at ~45s with no network.
- **Honest answer to the tester's question** — next-GW-only doubling + an explicit caption.
- **Pure helpers** — `captain_bonus` (and the shirt resolver) are unit-tested; the engine never moved.
- 659 → 663 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| How to know a photo is missing? | bootstrap `photo` is `{code}.jpg` for all; codes exist yet 403 | A cached CDN existence sweep (HEAD), degrade to "all present" |
| A network sweep in the test suite | every page AppTest calls `photo_url_by_id` | An autouse conftest fixture patches the sweep out |
| Smoke showed no captain bonus | set `session_state['active_squad']`; the key is `"squad"` | Set `session_state['squad']`; the bonus + caption then appeared |
| Mixed-horizon number | XI over N GW + captain's next-GW bonus | An explicit caption: the ×2 is next-GW only |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| `photo` field | `{code}.jpg` for everyone — not a missing-photo signal |
| Existence check | HEAD the CDN, cache it, degrade to "present" on error |
| Test-safety | An autouse conftest patch keeps a render-time network call out of the suite |
| Captain scope | Next-GW-only double is honest; whole-horizon overstates |
| Session key | The active squad lives under `st.session_state["squad"]` |

---

# Development Lessons 💻

- Decide *how* something fails (missing photo = 403, not null code) before picking the fix.
- When adding a render-time side effect (network), guard the tests centrally (conftest) rather than per-test.
- Fold a new number into a headline metric, but caption the assumptions so it can't be misread.

---

# AI Collaboration Lessons 🤖

- The tester raised a genuine modelling question ("next GW or all selected?"). Surfacing it as a decision
  (with real numbers: 242.5 vs 263.9) let the owner steer, and the ADR records *why* next-GW-only won.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-083 | **Captain double-points in the My Squad projection (next-GW only)** — Projected XI = XI over N GW + the captain's *next-GW* xP (one extra copy), only when the captain is set + in the XI; a caption states the ×2 is a one-week thing (owner steer); "Captain (2×)" reframed to next-GW. Display-only; `decision_xp` unchanged. Whole-horizon doubling rejected (unrealistic). Chips deferred to the Chips tab | Accepted |

_US-255 (image fallback) needed no ADR — display mechanics; the render-time-network choice is documented in the sprint doc._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **AI Chat Assistant** (owner intake) — still needs a grounded-vs-free-form design/ADR + a willing LLM.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + mini-league position (leagues API, GW1).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor lights up.
- Backlog still open: persisted chat context; season countdown / deadline banner; server-side squad
  persistence; (optional) a refresh-time precompute of photo existence if the first-load sweep ever bites.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep de-risking on real data before the gate — it turned two vague asks into concrete, honest scopes.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # missing-photo players now show their club shirt (GK variant for keepers);
                              # My Squad → set a captain → Projected XI includes the ×2 for next GW only
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Existence sweep | A cached HEAD check of which player photos the CDN actually serves |
| Club-shirt fallback | The FPL kit image (`shirt_{team_code}[_1]-66.png`) shown when a photo is missing |
| Next-GW captain double | Adding the captain's next-gameweek xP once (the ×2 bonus, one week) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-083 | The captain-doubling scope decision + the numbers behind it |
| `src/web_streamlit/badges.py` | The photo-or-shirt resolver + the cached existence sweep |
| `src/web_streamlit/squads.py` (`captain_bonus`) | The pure next-GW captain-bonus helper |
| `conftest.py` | The autouse fixture that keeps the sweep offline in tests |

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

- US-255 Club-shirt image fallback — photo when served, else the club shirt (GK variant); cached, degrading
- US-256 Captain double-points (next-GW only) — Projected XI includes the ×2 for next GW, with a one-GW note (ADR-083)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
