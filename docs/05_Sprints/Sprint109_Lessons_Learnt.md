# Lessons Learned

**Sprint:** Sprint 109 — Captaincy scopes to *your* squad (+ a clear "best overall")

**Dates:** 2026-08-10

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix the reported bug — *"who should I captain from my-team?"* answered from **all** players, not the loaded
squad — and turn it into a clear pair of questions: a squad-scoped pick (the default when a team is loaded) and
a first-class **global** "best captain picks this GW". Routing + display only; the analytics untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reproduce before you plan.** A five-minute real-data reproduction turned a vague "it ignores my squad" into
  a one-character root cause (space vs hyphen).
- **One rule, two outcomes.** Designing the fix so a single check both repairs the bug and delivers the chosen
  default behaviour.

### New Skills Acquired

- **A default beats a phrase-match.** The old code matched the literal phrase "my team"; brittle to punctuation
  and wording. Replacing it with "*with a squad loaded, default squad questions to it unless explicitly
  global*" is robust to any phrasing — the hyphen stops mattering entirely.
- **Gate a broad default by intent.** "Default to the loaded squad" is only safe for squad-shaped intents;
  scoping a global *fixtures* question would be wrong. The gate (`_SQUAD_DEFAULT_INTENTS`) is what makes the
  broad rule safe.
- **A silent default needs a visible label.** Changing behaviour (bare question → your squad) is only honest if
  the answer *shows* its scope — hence the reframed heading + nudge (US-280).
- **Default arguments bind at import.** `SquadStore(path=config.SQUADS_PATH)` captures the path once, so a test
  can't isolate the store by monkeypatching `config` — it must patch where `SquadStore` is constructed.

---

# What Went Well ✅

- **Small, precise fix** — one rule in `_fresh`; no analytics touched; the grounding + verification held.
- **The global question stayed first-class** — reachable on purpose via an explicit cue, and clearly labelled.
- **The gate was validated on real data** before the test — a global "best fixtures" stayed global.
- 713 → 716 tests; ruff + CI-parity green; ADR-090 records the semantics.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "my-team" answered globally | `\bmy (team|…)\b` matches a space, not a hyphen; examples use the hyphen | Replace with a default-to-loaded-squad rule (no phrase-match) |
| A broad default could scope global questions | the rule fired for any intent | Gate to `_SQUAD_DEFAULT_INTENTS` (captain/transfer/analyse/…); exclude fixtures/compare |
| Keeping the global "best picks" reachable | the default would swallow it | An explicit-global cue (`all players` / `best overall` / …) escapes |
| A flaky end-to-end test | ambient saved squads (RoboTS/TS) leak into routing; `SquadStore` default path binds at import | Isolate the store to a temp file via `monkeypatch.setattr(ask, "SquadStore", …)` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Defaults > phrase-matching | A behavioural default is robust to phrasing/punctuation a regex can't anticipate |
| Gate broad rules | Restrict a broad default to the intents it's safe for |
| Honest defaults | A changed default must be visible in the answer (heading + nudge) |
| Import-time defaults | Default-arg paths bind at import — patch the construction site, not the config |

---

# Development Lessons 💻

- Reproduce a reported bug on real data before designing — the root cause often shrinks the work.
- When a fix changes behaviour, pair it with a display change so users can see what changed.
- Make routing tests hermetic — ambient user-state (saved squads) makes them order-sensitive otherwise.

---

# AI Collaboration Lessons 🤖

- The tester's phrasing ("returns the same answer regardless of my players") named the symptom precisely enough
  to reproduce in one step — and their aside ("that global question is a great one") shaped the design into
  *two* questions rather than a single "always scope" fix.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-090** (new) — `ask` defaults squad questions to the loaded squad when a squad is active, no squad was
named, and there's no explicit-global cue; captaincy's global mode is reachable via that cue. Refines Sprint 066
("my team" → session squad) + ADR-047/080 routing. New: `_SQUAD_DEFAULT_INTENTS`, `_EXPLICIT_GLOBAL` in
`ask.py`; `render_captain_pick` gained `heading` + `nudge` (US-280). Routing/display only._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A web-native styled captain card** — the standing visual follow-up.
- **Extend explicit-global synonyms** if testers phrase it other ways ("league-wide", "any team").
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the gated captain "why" signals light up (form · % of team goals · opponent xGC);
  Data Hardening + xP calibration; the Price Change Predictor.
- Flip the beta on (`docs/BETA.md`); a hosted LLM for the deploy (free-form chat).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "reproduce on real data → then plan" habit — it right-sized this whole sprint.

---

# Key Commands Learned

```text
python app.py ask "who should I captain from my-team?"     # now scopes to your loaded squad
python app.py ask "who should I captain from all players?" # the explicit global "best picks"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Default squad-scoping | With a squad loaded, squad questions use it unless explicitly global (ADR-090) |
| Explicit-global cue | A phrase ("all players", "best overall") that forces the global answer |
| Best Captain Picks | The global captaincy answer's heading, distinct from the scoped "Captain Pick" |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/ask.py` (`_fresh`, `_SQUAD_DEFAULT_INTENTS`, `_EXPLICIT_GLOBAL`) | The default-scoping rule |
| `docs/06_Decisions/ADR-090-default-squad-scoping.md` | Why the default + the global escape |
| `src/ui/captain.py` (`render_captain_pick`) | The heading/nudge that make scope visible |

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

- US-279 Scope captaincy to the loaded squad by default — the hyphen fix + the default, with a global escape (ADR-090)
- US-280 Global vs scoped, unmistakable — reframed "Best Captain Picks" + a nudge + personalised example prompts

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
