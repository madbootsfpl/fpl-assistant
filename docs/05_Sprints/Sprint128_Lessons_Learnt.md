# Lessons Learned

**Sprint:** Sprint 128 — CLI catch-up (a `chips` command + a price "who's about to rise?" intent)

**Dates:** 2026-08-29

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Bring two web/`ask`-only features to the terminal by **surfacing** existing analytics: a standalone CLI `chips`
command and a `price` "who's about to rise?" `ask`/`chat` intent. No new analytics; grounded; degrade honestly
until GW1.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Thin edges over shared analytics** — a new surface reuses the one recipe, so it can't drift.
- **Keyword-router precedence** — place a new intent so it wins its phrases without stealing others'.

### New Skills Acquired

- **Parity is cheap when the analytics + renderer already exist.** `chip_advisor` + `render_chip_advice` were
  built for web/`ask`; the CLI `chips` command is just `cmd_analyse` with a different call + renderer — and it
  **matches `ask`/web by construction** because it's the same `decision_xp` assembly (no separate logic to drift).
- **A new intent needs collision-checking, not just keywords.** "price risers" first routed to *rules* (its
  "price rise" is a substring); placing `price` **before** rules with prediction-specific cues fixed it, and a
  routing test pins that genuine rules/trends questions still win their cases.
- **Reuse the honest-degrade pattern.** The price intent returns a first-class "live at GW1" message on flat
  preseason data — the same shape as trends/momentum — so it never invents movement from zero.
- **Keep a surfaced signal a lens.** The price intent presents `price_prediction`; it never touches
  `decision_xp` (ADR-092), so no invariance is at risk.

---

# What Went Well ✅

- **Two clean parity wins** from reuse — thin edges, no new analytics, no ADR.
- **The CLI chips can't drift** from `ask`/web (same assembly).
- **Routing precedence handled** — the "price risers" collision fixed + tested.
- **Honest preseason degrade** kept (a "live at GW1" message).
- 805 → 811 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "price risers" → rules | rules' "price rise" is a substring | Place `price` first with prediction-specific cues |
| Don't steal rules/trends | shared price/rise words | Prediction phrases only; route tests pin the boundaries |
| Nothing to show preseason | net transfers flat → 0 pressure | A first-class "live at GW1" message |
| Keep the CLI in sync | a separate assembly could drift | Reuse the one `decision_xp` recipe → matches by construction |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Parity via reuse | A CLI edge over shared analytics + renderer can't drift |
| Router precedence | Order + specific cues decide which intent wins a phrase |
| Honest degrade | A dormant-preseason signal returns a clear "live at GW1" answer |
| Lens discipline | Surface `price_prediction`; never touch `decision_xp` |

---

# Development Lessons 💻

- Add a new surface as a thin edge over the shared recipe, not a re-implementation.
- When adding a keyword intent, test the collisions (what it must *not* steal), not only what it should catch.
- Preserve the app's honest-degrade convention for signals that are 0 until the season starts.

---

# AI Collaboration Lessons 🤖

- The price intent is grounded like the rest of `ask`: analytics rank the movers, the facts carry the named
  players + numbers, and the LLM narrates only those (verified ✓) — a surfaced lens, never a new decision.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — surfacing. US-316: `cli.py::cmd_chips` (reuses `chip_advisor`/`render_chip_advice`, ADR-082).
US-317: a `price` `ask`/`chat` intent + `ui/price.py::render_price_movers` over `price_prediction`/`price_pressure`
(ADR-092), a lens; grounded; a "live at GW1" message preseason._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- The **buildable-now backlog is essentially exhausted before GW1 (2026-08-21)**. The meaty work — set-piece +
  DefCon + form calibration, momentum boards, live manager import — unlocks on real in-season data. Sprint 129 is
  a natural point to pause small polish or bank a last tidy item.
- **Deferred:** a CLI price column on `table`/`xg`; an absolute "% to the next price change" (a GW1 counter).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep surfacing shared analytics as thin edges; keep degrade-honestly for pre-GW1 signals.

---

# Key Commands Learned

```text
python app.py chips --squad my-team       # when to play each chip (TC · BB · FH · WC) + confidence
python app.py ask "who's about to rise?"  # likely price risers 🔺 / fallers 🔻 (live at GW1)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Thin edge | A surface (CLI/ask) that reuses the shared analytics + renderer, no new logic |
| Router precedence | The dict order + cue specificity that decides which intent matches |
| Transfer pressure | Net transfers per 1% ownership — the directional price signal (ADR-092) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/cli.py` (`cmd_chips`) | The CLI chips edge (mirrors `cmd_analyse`) |
| `src/ask.py` (`_decide_price`, the `price` intent) | The price intent + routing |
| `src/ui/price.py` | The 🔺/🔻 price-mover renderer |

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

- US-316 A CLI `chips` command (surface `chip_advisor` — reuses the renderer)
- US-317 A price "who's about to rise?" `ask`/`chat` intent (likely risers 🔺 / fallers 🔻; live at GW1)

**Stories Carried Forward:**

- None. (A CLI price column + a "% to next change" are deferred / GW1.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
