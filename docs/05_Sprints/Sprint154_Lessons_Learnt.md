# Lessons Learned

**Sprint:** Sprint 154 — Help revamp + Boot Battle everywhere + the MadBoots Explainer

**Dates:** 2026-08-13

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Rewrite the Help page (owner's copy) reconciled against the live app; make **⚔️ Boot Battle** a real feature (My Squad
⚙ panel + rebrand); add the **MadBoots Explainer** glossary (one expander, category subheaders). Mostly content; the
one behaviour add reuses `compare_card_html` (ADR-111).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Docs must be reconciled, not transcribed.** The owner's draft was good, but the *live app* is the source of
  truth — the biggest fix was the Help still claiming *"no accounts, nothing saved on the server"* long after auth +
  persistence went live. Building the copy meant checking **every claim against the code** and correcting drift
  (Save flow, the AI-narration line, feature names) — a stale Help erodes trust as fast as a bug.
- **Make the copy real, don't water it down.** The draft assumed Boot Battle from the card; rather than soften the
  copy, we built the small feature (⚙-panel compare) so the docs are honest *and* the app is better.

### New Skills Acquired

- **Streamlit expanders can't nest** → a long glossary lives in **one** expander with category **subheaders**, all
  visible. For a *lookup* reference that's a feature, not a limitation: Ctrl-F finds any term (a hidden-tab switcher
  would defeat it).
- **The honest framing of a missing capability.** The live app has no cloud LLM; instead of hiding that or telling
  users to "start Ollama", the Help says *"you always get the full data-driven plan; where a local AI is available it
  adds narration"* — accurate for everyone, and the glossary's "Local AI" entry carries the detail.

---

# What Went Well ✅

- **Boot Battle reused everything** — the ⚙-panel compare is just a picker + `render_player_compare`; no analytics.
- **The rewrite is honest** — auth-live save flow, real feature names, no "start Ollama".
- **Green throughout** (983 → 985) — tests pin Boot Battle in both places, the auth-live save copy (+ that the stale
  line is gone), and the glossary.
- **A content preview** (a one-scroll read with the reconciliations marked) for owner sign-off before deploy.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Stale Help claims | Copy predated auth (ADR-106) | Rewrote the Save section for auth-live; removed "no accounts / session-only" |
| The draft over-promised Boot Battle | It assumed compare from the card | Built the ⚙-panel compare (reuses the renderer) so the copy is true |
| A long glossary, no nested expanders | Streamlit limitation | One expander + category subheaders (Ctrl-F-able) |
| The compare-label rebrand broke a test | "🔍 Compare with" → "⚔️ Boot Battle" | Repointed the test to match "Boot Battle" |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Docs as code | Reconcile every user-facing claim against the app; a test can pin "the stale line is gone" |
| Expander limits | Can't nest → subheaders for a long section; better for lookup anyway |
| Reuse for features | A "new feature" (⚙ Boot Battle) can be a picker + an existing renderer |

---

# Development Lessons 💻

- When you touch a docs page, re-verify its claims against the current app — features move faster than the copy.
- Prefer building the small feature that makes the copy honest over softening the copy.
- A test that asserts a *removed* stale string keeps the docs from regressing.

---

# AI Collaboration Lessons 🤖

- Mostly content; the one behaviour add is display-only (reuses the compare renderer). The Help is now honest about
  the app's data-only-on-cloud position — the *cloud-LLM narration* decision stays parked (P2 strategic,
  `docs/Backlog.md`). See [[visual-preview-for-ui-signoff]] (a content preview for sign-off).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-111 — Help revamp + Boot Battle everywhere + the MadBoots Explainer.** Rewrite the Help (owner copy,
reconciled); ⚔️ Boot Battle on the My Squad ⚙ panel + rebrand both controls (reuses `compare_card_html`); the
glossary as one expander with category subheaders. Keep the app's icons over the draft's.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** read through the Help; ⚔️ Boot Battle works from a My Squad player card; the
  glossary is Ctrl-F-able; the Save section reads account/auto-sync.
- **Remaining 2026-08-13 items:** the **cloud-LLM narration** decision (P2 strategic — do we pay for live AI
  narration, or stay data-only?); the **admin usage/logins graphs** (P2, as users grow).
- **GW1 (2026-08-21, ~8 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- When rewriting a docs page, grep it for claims about persistence/accounts/features and re-check each.

---

# Key Commands Learned

```text
python -m pytest tests/ -q -k "help or explainer or boot_battle"   # the Help + Boot Battle sprint
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Boot Battle ⚔️ | The two-player compare feature — now on both Players and the My Squad ⚙ panel |
| MadBoots Explainer | The Help glossary (one expander, category subheaders, Ctrl-F-able) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-111-help-revamp.md` | The revamp decision + the reconciliation principle |
| `src/web_streamlit/pages/8_Help.py` | The rewritten Help + the glossary structure |

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
