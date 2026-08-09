# Lessons Learned

**Sprint:** Sprint 127 — A Gameweeks box-select + the DefCon magnifier design gate

**Dates:** 2026-08-28

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Respond to owner feedback: (1) turn the "Gameweeks ahead" dropdown into a box-select (1·2·3·4·5·10); (2) answer
"why can't we use in-app email?"; (3) record the **DefCon opposition magnifier** idea as a design gate (ADR-097)
so a GW1 sprint builds against an agreed plan. No analytics change ships.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Engage a big idea with a gate** — capture the design + the traps before building, especially when calibration
  waits for data.
- **Answer "why can't we…" precisely** — often the honest answer is "we can, here's how", not "we can't".

### New Skills Acquired

- **A user's framing may point at data we already have.** The owner framed the DefCon magnifier in *betting
  odds*; the FDR/xGC/Elo strength model already gives the same opposition signal, so the feature needs **no
  auth-walled odds** (which ADR-093 deferred). Translate the ask into the data we own.
- **Name the traps in the gate, not in the post-mortem.** Two non-obvious pitfalls — clean-sheet and DefCon
  points move **oppositely** vs opponent strength, and a transferred player's `defcon_per90` reflects the *old*
  team — belong in the ADR so the eventual build avoids them by design.
- **Reuse a hard-won insight across features.** The transferred-player problem is the same "history doesn't
  capture the new context" issue solved by the set-piece tier guard (ADR-096) — spotting the pattern early saves
  the DefCon build from re-learning it.
- **Gate what you can't calibrate.** DefCon is a new-season signal; magnitudes need in-season returns, so the
  build is genuinely GW1-work — a design gate now is the honest deliverable.

---

# What Went Well ✅

- **A clean quick win** (the box-select) + **a serious gate** for the big idea in one small sprint.
- **The in-app-email question got a precise answer** — already possible (the relay), the blocker is Proton SMTP,
  the fix is config.
- **The proxy insight** — no betting odds needed; the strength model suffices.
- 804 → 805 tests; ruff + CI-parity green; no analytics change.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Old tests referenced a selectbox | the control became a segmented control | Updated both to `at.segmented_control` |
| The magnifier has nothing to scale | DefCon xP isn't in `decision_xp` | Record it as a prerequisite in the gate |
| Clean-sheet vs DefCon direction | they respond oppositely to opponent strength | Separate multipliers; noted in the ADR |
| Transferred player mis-priced | `defcon_per90` reflects the old team | A deferred team-share adjustment (cf. ADR-096) |
| Can't calibrate preseason | DefCon is a new-season signal | Gate now, build + calibrate at GW1 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Proxy over odds | The FDR/xGC/Elo strength model gives the opposition signal without betting data |
| Opposite signals | Clean-sheet and DefCon points scale inversely vs opponent strength |
| Gate the uncalibratable | A new-season modelling feature is a design gate until its data lands |
| Pattern reuse | The transferred-player nuance = the set-piece "new context" guard |

---

# Development Lessons 💻

- When a control changes type, update every test that selected it by its old widget kind.
- Translate a user's ask into the data you already own before assuming you need a new source.
- Put the non-obvious pitfalls in the ADR so the build is designed around them, not surprised by them.

---

# AI Collaboration Lessons 🤖

- A DefCon-xP magnifier would change `decision_xp`, so — like set-pieces/form — it's a **modelling** term (an
  ADR + wired-dormant + auditable), not a lens; the grounded/read-only posture decides the shape.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-097** (design gate, no code) — a fixture-context DefCon magnifier: a DefCon-xP component (from
`defcon_per90` → `P(clear)`) scaled by a magnifier **inverse** to a clean-sheet-probability proxy (FDR/xGC/Elo,
no odds), clamped ~0.5–1.5; separate from clean-sheet points (opposite direction); the transferred-player
baseline flagged (a deferred team-share adjustment); wired-dormant; a modelling change (not a lens); build +
calibrate at GW1. US-315: the Squads "Gameweeks ahead" box-select. No new analytics code._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 (2026-08-21+): build the DefCon magnifier** (ADR-097) — a DefCon-xP component + the fixture magnifier +
  a team-share adjustment for transfers; calibrate on real DefCon returns. Alongside the set-piece + form
  calibrations (the Data Hardening flip).
- **Owner:** set the FormSubmit **relay** so in-app feedback emails your inbox (BETA.md §1B — config, no build).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep recording big/uncalibratable modelling ideas as ADR gates with the traps named; build when the data lands.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → "Gameweeks ahead" box-select (1·2·3·4·5·10)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Clean-sheet proxy | Opposition-strength → clean-sheet probability from FDR/xGC/Elo (no odds) |
| DefCon magnifier | A fixture multiplier on DefCon xP, inverse to the clean-sheet proxy |
| Opposite signals | Clean-sheet vs DefCon points scale in opposite directions vs opponent strength |
| Design gate | An agreed design recorded before building (build waits for GW1 data) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-097-…` | The DefCon-magnifier design + the traps |
| `src/analytics/defcon.py` / `cleansheet.py` | The DefCon reliability + clean-sheet solidity lenses |
| `src/web_streamlit/pages/3_Squads.py` | The Gameweeks box-select |

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

- US-315 A Gameweeks box-select (1·2·3·4·5·10) on the Squads tab
- ADR-097 A fixture-context DefCon magnifier — the design gate (build at GW1)

**Stories Carried Forward:**

- The DefCon magnifier **build** (GW1, gated by ADR-097).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
