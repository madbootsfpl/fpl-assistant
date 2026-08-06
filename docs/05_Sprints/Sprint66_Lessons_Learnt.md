# Lessons Learned

**Sprint:** Sprint 066 — Fix: make `ask` see the session active squad (tester bug)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix a 🔴 tester bug: the web **Ask** tab ignored the squad loaded into the session — captain/analyse fell
back to "(all players)" because `ask` read only server-side `SquadStore`, not `st.session_state["squad"]`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Tracing a UI symptom ("(all players)") back to a layer boundary (`ask` ↔ the session-squad model).
- Threading an optional, backward-compatible parameter through a call graph without breaking callers.

### New Skills Acquired

- A clean resolver seam (`_load_squad` / `_known_squad_names`) so *one* place decides "active squad vs
  saved", instead of scattering the check across every decider.

---

# What Went Well ✅

- **A small seam contained the change** — two helpers + threading one optional `active_squad`.
- **Backward-compatible defaults** — `active_squad=None` meant the CLI and most tests were untouched.
- **The feedback loop delivered** — reported → triaged (🔴) → fixed the same session; the fix threads
  *which* squad, so `decision_xp`/the engine stayed put.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `ask` couldn't see the loaded team | `ask` resolved squads only via `SquadStore` (server-side) | Thread an optional `active_squad`; resolve it first via `_load_squad` |
| A few `ask` tests broke | They monkeypatch internal `ask` functions with old-signature lambdas | Update the lambdas to accept `active_squad` (a signal that internal-monkeypatch tests are brittle) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Resolve at one seam | Centralising "active vs saved" in two helpers keeps every decider consistent |
| Backward-compatible threading | An optional trailing param (default None) adds behaviour without breaking callers |
| Monkeypatching internals is brittle | Tests that replace internal functions must track their signatures — prefer public seams |

---

# Development Lessons 💻

- When a symptom crosses a layer boundary, fix the seam, not the symptom.
- Thread request-scoped context explicitly with safe defaults; let existing callers keep working.

---

# AI Collaboration Lessons 🤖

- A precise, reproducible bug report (the "(all players)" headline + "RoboTS lacks B.Fernandes") pinpointed
  the layer instantly — good feedback shortens diagnosis dramatically.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No ADR — a bug fix that connects `ask` to the existing session-squad model (ADR-054/055)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Small future polish: when a user names a squad that's neither loaded nor saved, say "I don't know a squad
  called X" instead of silently answering for all players. Back to the hold / GW1 markers otherwise.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Prefer public seams over monkeypatching internals in tests, so refactors don't ripple into test signatures.

---

# Key Commands Learned

```text
python -m pytest tests/test_ask.py -q     # the ask brain + the new session-squad tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Active squad (in `ask`) | The session squad passed into `ask.answer`, preferred over saved squads |
| Resolver seam | One place (`_load_squad`) that decides active-vs-saved for every squad load |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/ask.py` (`_load_squad` / `_known_squad_names`) | The squad-resolution seam |
| `docs/00_Project/Feedback_Log.md` | The triage trail (this bug → Sprint 066) |

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

- US-192 `ask` reads the session active squad (captain / analyse / transfer / start-bench / fixtures / "my team")

**Stories Carried Forward:**

- None (GW1 markers stand; a "unknown squad name" message is an optional future polish)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
