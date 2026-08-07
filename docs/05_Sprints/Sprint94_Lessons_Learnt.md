# Lessons Learned

**Sprint:** Sprint 094 — Pronoun-aware chat

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

In chat, a pronoun that refers to the last-mentioned player resolves to that player — *"is Haaland worth
it?"* → *"compare him to Isak"* just works — in both the CLI `chat` and the web **Ask** tab.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Deterministic NL resolution** — a text rewrite before routing, so the LLM stays out of the decision and
  grounding is untouched.
- Threading conversational state (`Context`) through a stateless web page via `session_state`.

### New Skills Acquired

- Pronoun resolution belongs **before routing** (in `_fresh`), and only when the antecedent is
  **unambiguous** (exactly one subject) — otherwise leave the question alone.
- Substituting the player's *name* for the user's pronoun sidesteps any pronoun-assignment concern — we never
  infer or assign a pronoun for anyone.
- The web Ask was one-shot (`answer`); switching it to `converse` + a `session_state` `Context` made it
  conversational (follow-ups + pronouns) with the first turn unchanged.

---

# What Went Well ✅

- **Rewrite-then-route kept the contract** — analytics decide, LLM narrates, every turn verified; resolution
  is pure and testable.
- **Safe by construction** — name-substitution, single-antecedent-only; no misgendering, no guessing.
- **A free bonus** — US-248 gave the web Ask the why/next/what-about follow-ups it never had.
- 636 → 640 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Which player does a pronoun mean? | multi-subject turns are ambiguous | Resolve only when there's exactly one subject; else no-op |
| Pronoun assignment / misgendering risk | assigning a pronoun would be wrong | Substitute the *name* for the pronoun the user typed; never assign |
| The web Ask had no memory | it called one-shot `answer` | Thread `Context` via `session_state` + `converse` |
| `_decide_worth` "has no subjects"? | a mis-grep | It does set `subjects=[player]` — the antecedent chain works |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Resolve before routing | A pronoun rewrite in `_fresh` lets the normal router do the rest |
| Unambiguous only | One subject → resolve; two → leave it (don't guess) |
| Name-substitution | Replacing the pronoun with a name avoids assigning a pronoun |
| Stateless → stateful | A `session_state` `Context` + `converse` makes a one-shot page conversational |

---

# Development Lessons 💻

- Do NL resolution deterministically before the model sees anything — keeps grounding auditable.
- Prefer the honest no-op (leave the question) over guessing an ambiguous antecedent.
- A small state addition (`session_state` context) can unlock a whole conversational surface.

---

# AI Collaboration Lessons 🤖

- "Pronoun-aware chat" mapped to a tiny pure helper + a one-line wire — and threading the same context to the
  web made it visible to the (web-focused) tester, follow-ups included.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-080 | **Pronoun-aware chat** (refines ADR-047) — `_resolve_pronoun` rewrites a pronoun → the last turn's sole subject (unambiguous only; possessives → `name's`), wired into `_fresh`; US-248 threads `Context` through the web Ask (`converse`) so pronouns + follow-ups work there. Name-substitution (never assigns a pronoun); analytics decide, LLM narrates, verified; no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Persist the chat context** across runs (the other half of the backlog "persisted / pronoun-aware chat").
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Backlog still open (season-timely): season countdown / deadline banner; GW1 readiness dry-run; server-side
  squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep NL features deterministic + verifiable — resolve/rewrite before the model, not with it.

---

# Key Commands Learned

```text
python app.py chat            # "is Haaland worth it?" → "compare him to Isak" resolves 'him'
python -m src.web_streamlit   # Ask tab: follow-ups ("why?") + pronouns now work in the browser
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Antecedent | The player a pronoun refers back to (the last turn's sole subject) |
| Rewrite-then-route | Substitute the pronoun with the name, then route as a fresh question |
| Conversational context | The `Context` threaded across turns (CLI `converse`, now the web too) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-080 | The pronoun-resolution decision + the unambiguous-only / name-substitution rationale |
| `src/ask.py` (`_resolve_pronoun`, `_fresh`) | The resolution helper + wiring |
| `src/web_streamlit/pages/4_Ask.py` | The conversational web Ask (`converse` + `session_state`) |

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

- US-247 Pronoun resolution — `_resolve_pronoun` rewrites a pronoun → the last turn's sole subject (ADR-080)
- US-248 Conversational web Ask — thread `Context` + `converse` so pronouns + follow-ups work in the browser

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
