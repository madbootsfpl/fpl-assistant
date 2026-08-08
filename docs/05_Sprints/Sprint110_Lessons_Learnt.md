# Lessons Learned

**Sprint:** Sprint 110 — Chat robustness (remembered context + a bigger rules KB)

**Dates:** 2026-08-11

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the Ask/chat assistant sturdier before wider testing: (1) **remember the conversation across runs** so a
follow-up works after the process exits, and (2) **grow the curated rules KB** so it answers more FPL-rules
questions — still grounded + verified (✓). No analytics change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **A pure core pays off.** Because `converse` was already context-in / context-out, persisting across runs was
  a thin CLI wrapper, not a refactor.
- **Designing within a hard constraint** — the read-only, multi-user web — turned into a clean architectural
  split (persistence is CLI-only).

### New Skills Acquired

- **Persist at the edge, keep the core pure.** `ask.answer`/`converse` stay side-effect-free (used by the web +
  tests); only `cmd_ask`/`cmd_chat` load/save. The pure function is reusable; the stateful behaviour is opt-in
  at the CLI.
- **Best-effort state never crashes the feature.** Save/load swallow errors, and a TTL bounds staleness — so a
  corrupt or ancient context returns `None`, and a failed write is silent. Continuity is a nice-to-have.
- **Growing a KB needs routing, not just facts.** A new rules entry only helps if the question *routes* to the
  rules intent — otherwise it falls to free-form (ℹ), ungrounded. The real work was the specific routing cues
  that win over the squad intents without hijacking them.
- **String-scan guardrails need precise anchors.** The web names a `session_state` key `chat_context`, so a
  substring scan false-flagged it; anchoring on the module import + its calls fixed it.

---

# What Went Well ✅

- **Small, low-risk edges** — a ~60-line store + a CLI wrapper + curated content; no analytics touched.
- **The read-only web stayed read-only** — a guardrail test asserts it never imports the store.
- **All 8 new rules verify ✓** — grounded from the KB, never the LLM's memory.
- 716 → 726 tests; ruff + CI-parity green; ADR-091 records the persistence decision.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Persisting for the web would break read-only | multi-user, no server writes | Keep the store CLI-only; web keeps `session_state`; a guardrail test |
| A stale "why?" could resurface an old turn | persistence has no natural expiry | A 2h TTL in `load_context`; `forget` for explicit control |
| New rules answered ℹ (free-form), not ✓ | the questions didn't route to the rules intent | Add specific rules cues that win first without hijacking squad commands |
| Guardrail false-positive | the web's `session_state` key is named `chat_context` | Anchor the scan on `import chat_context` + its calls |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Pure core, stateful edge | Keep the API side-effect-free; persist in the CLI handler |
| Best-effort persistence | Swallow errors + TTL — a nice-to-have must never crash a turn |
| KB + routing | A curated fact is only useful if the question reaches its intent |
| Guardrail anchors | Scan for the precise signal (import/call), not a shared name |

---

# Development Lessons 💻

- Put side effects at the edge so the core stays testable and reusable.
- When adding data to a keyword-routed system, check the *routing*, not just the data.
- Verify a "grounded" feature end-to-end (does it show ✓?), not just the unit that produces the fact.

---

# AI Collaboration Lessons 🤖

- The KB is the antidote to LLM rule-hallucination: curated facts + verification (✓) mean the assistant answers
  rules from *these* strings, and the narration is checked against them — so growing coverage is safe.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-091** (new) — persist one conversational `Context` across CLI runs to a local, git-ignored, TTL'd JSON
file; the pure `ask` API is unchanged and the multi-user web keeps `session_state` (never the file). US-282
extends **ADR-085** (the rules KB) — 8 new entries + routing cues; no ADR needed._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A hosted LLM for the deploy** so the free-form tail + prose work on the cloud (it degrades to rules +
  grounded facts without one).
- **An LLM/intent classifier** — the substring routing works but the cue list is growing.
- **Web-native captain card** — the standing visual follow-up.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the Price Change Predictor; the gated captain
  "why" signals light up.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying grounded features end-to-end (the ✓ line), not just the unit under test.

---

# Key Commands Learned

```text
python app.py ask "who should I captain?"   # then, separately:
python app.py ask "why?"                     # remembered across runs (ADR-091)
python app.py ask "forget"                   # clears the memory
python app.py ask "how many wildcards do I get?"   # a new rules topic, verified ✓
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Persisted context | The last turn saved to a local file so a follow-up works across runs (ADR-091) |
| TTL guard | Ignore a saved context older than the limit — a stale "why?" shouldn't resurface |
| Routing cue | A phrase that sends a question to an intent (a rules fact needs one to verify ✓) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/chat_context.py` | The local, TTL'd context store (ADR-091) |
| `docs/06_Decisions/ADR-091-persisted-chat-context.md` | Why CLI-only + the TTL |
| `src/fpl_rules.py` | The curated, verified rules KB (21 topics) |

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

- US-281 Remember the conversation across runs — a local, TTL'd `chat_context` store; CLI `ask`/`chat` load+save; web session-only (ADR-091)
- US-282 Grow the curated rules KB — 8 new grounded entries + routing cues; still verified (extends ADR-085)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
