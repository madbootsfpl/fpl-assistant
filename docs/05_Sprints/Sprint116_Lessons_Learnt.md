# Lessons Learned

**Sprint:** Sprint 116 — Two feedback fixes + a web-native Captain Pick card

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix two tester-feedback items (tooltips "stopped working"; `reseed` "no longer calls ClubElo") and pick up a
backlog item — a **web-native Captain Pick card** on the Captain tab. Fixes + display only; the analytics
untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Diagnose to a cause before fixing** — rule out the code (tests pass, CSS scoped), then find the real
  suspect.
- **Reuse an established visual pattern** — the pitch's scoped-CSS + escape-everything + one `st.markdown` block.

### New Skills Acquired

- **An unpinned dependency is a silent regression risk.** The Community Cloud auto-upgrades Streamlit, so the
  deploy can drift past the tested version and change rendering (tooltips) with no code change. Pinning makes
  dev == deploy.
- **"It stopped calling X" can be a reporting bug.** `reseed` *did* still call ClubElo — a one-word `_`
  discarded the count so the printout looked silent. Read the code before assuming the behaviour changed.
- **Split pure from Streamlit for testability.** `captain_card_html` (pure string) unit-tests the tokens /
  escaping / band / empty-safety with no Streamlit context; `render_captain_card` just `st.markdown`s it.
- **Anchor HTML assertions on the applied attribute, not a class name.** The CSS block defines every pill class,
  so `"cc-med" not in html` was wrong — assert `'cc-conf cc-high'` (the class the span actually carries).

---

# What Went Well ✅

- **Both feedback items pinned to a precise cause** → two small, confident fixes.
- **The card was pure presentation** — reused the pitch pattern + the existing explanation/picks.
- **Sign-off before finalising** — a faithful Artifact preview (both themes) got approved.
- 746 → 751 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Tooltips "stopped working" | unpinned Streamlit → deploy drifted past 1.61.1 | Pin `streamlit==1.61.1` (dev == deploy) |
| "reseed no longer calls ClubElo" | `cmd_reseed` discarded `n_elo` (`…, _ = …`) | Capture + report the Elo count / kept-last-known |
| A CSS-block false-positive in a test | the block defines all pill classes | Assert the applied `class="cc-conf cc-high"` |
| Testing HTML without Streamlit | render fn needs a script context | A pure `captain_card_html` + a thin render wrapper |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Pin your deploy deps | Silent auto-upgrades drift the deploy from the tested build |
| Read before assuming | "stopped X" was a dropped print, not a dropped call |
| Pure vs Streamlit | Split the string builder from the render for unit tests |
| HTML assertions | Anchor on the applied attribute, not a name the CSS also defines |

---

# Development Lessons 💻

- Rule out the code (tests + scoped CSS) before blaming it; the real cause is often the environment.
- Keep visual components pure-string at the core so they're testable and escape-safe.
- Get visual sign-off with a faithful preview before committing the look.

---

# AI Collaboration Lessons 🤖

- The card changes *how* the grounded decision is shown, not *what* it decides — `explain_captain` still
  computes every reason + the number; the card only presents them, escaped.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-293 is fixes (pin Streamlit; report ClubElo in `reseed`); US-294 extends **ADR-084**
(the self-contained HTML/CSS pattern) + **ADR-089** (explainability). New: `web_streamlit/captain_card.py`
(`captain_card_html` + `render_captain_card`); the web Captain tab renders it in place of the mono block._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Verify the tooltip fix on the live deploy** after the pin redeploys; chase a Streamlit-version regression if
  it persists.
- **A web-native worth card** (same pattern) as the visual follow-up.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the price/form/ownership signals sharpen;
  calibrate the price-predictor thresholds; wire a YouTube creator into `MEDIA_FEEDS`.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Pin deploy dependencies and bump them deliberately (test → re-pin), not by silent drift.

---

# Key Commands Learned

```text
python app.py reseed          # now prints "…and N Elo ratings (ClubElo)"
python -m src.web_streamlit   # Squads → Captain: the styled Captain Pick card
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Captain Pick card | The web-native styled captaincy card (medal · confidence pill · Why/Risks · alternatives) |
| Dep pinning | Fixing a dependency version so the deploy matches the tested build |
| Reporting bug | The behaviour was right; only the printed summary was missing a value |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/captain_card.py` | The card (pure builder + render) |
| `src/web_streamlit/pitch.py` | The self-contained HTML/CSS pattern it reuses (ADR-084) |
| `requirements.txt` | The Streamlit pin (dev == deploy) |

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

- US-293 Two feedback fixes — pin Streamlit (tooltips) + report ClubElo in `reseed`
- US-294 Web-native Captain Pick card — a styled HTML/CSS card on the Captain tab (extends ADR-084/089)

**Stories Carried Forward:**

- None. (Verify the tooltip fix on the live deploy; a worth card is a follow-up.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
