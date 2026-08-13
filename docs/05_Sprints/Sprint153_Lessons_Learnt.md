# Lessons Learned

**Sprint:** Sprint 153 — P1 quick-wins (2026-08-13 intake)

**Dates:** 2026-08-13

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Four P1 quick-wins from the 2026-08-13 tester intake: **US-373** Home tidy-up (owner's copy); **US-374** default
horizon (My Squad 1 GW · Squad Lab 5 GW); **US-375** hide the dev-only "Start Ollama…" hint from deployed users;
**US-376** make the Set-pieces columns read as *order*, not counts. Display/config only — no analytics change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Answer the question, then fix the confusion.** Two of the "feedback items" were *questions*, not bugs (Ollama is
  local-only; set-piece numbers are the taking *order*). The right response wasn't code — it was an explanation — but
  each still left a **real UX fix**: hide the dev-only Ollama prompt from users, and label the set-piece columns so
  the number can't be misread. A misunderstanding is a signal that the UI wasn't clear enough.
- **Reuse a seam for a context split.** The CLI and web share `render_ask`; a single `ollama_hint` flag (default True)
  lets the CLI keep the local-dev prompt while the web edges pass False — no fork, no duplicated renderer.

### New Skills Acquired

- **A changed default ripples into tests.** Flipping My Squad's horizon 5 → 1 broke **two** pre-existing tests that
  hard-coded the old default — one just needed the new value; the other is *about* the multi-GW captain double, so it
  now sets horizon 5 explicitly. Lesson: when you change a default, grep the tests for the old value AND check which
  tests actually depend on the multi-GW behaviour vs merely assumed the default.
- **A default is a statement of intent.** My Squad = "manage *this* week" → 1 GW; Squad Lab = "build for the run" → 5.
  The default should match what the page is *for*.

---

# What Went Well ✅

- **Four small, independent, low-risk fixes** — display/config only; no `decision_xp`/analytics touched.
- **The owner's Home copy dropped in cleanly** (typos fixed, our icons kept, internal ADR refs stripped from user copy).
- **Green + pinned** — 982 → 983; new tests assert each fix (the new tagline; horizon defaults; no web Ollama hint;
  the "order" headers).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Two tests broke on the horizon default | They hard-coded `default 5` | One → assert 1; the multi-GW-captain test → set horizon 5 explicitly (its "next gameweek only" caption is hidden at horizon 1) |
| Suppress a hint on web but not CLI | `render_ask` is shared | An `ollama_hint` flag — CLI True, web False |
| A number misread as a count | Bare "Corners" header | Rename to "Corner order" + a "not a count" tooltip |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Shared renderers | Split behaviour with a flag, not a fork (`ollama_hint`) |
| Defaults & tests | Changing a default surfaces every test that assumed it — grep for the old value |
| Label clarity | If a value is a *rank*, the header must say so (a caption/tooltip isn't enough — people don't hover) |

---

# Development Lessons 💻

- When feedback is a *question*, the fix is often "make the UI self-explanatory", not new logic.
- A misread number → strengthen the header, not just the tooltip.
- After changing a default, run the full suite — the break is usually a test that hard-coded the old value.

---

# AI Collaboration Lessons 🤖

- Display/config only: no analytics change, the read-only invariant intact. The Ollama fix also clarifies the app's
  honest position — the live app is **data-only** (no cloud LLM); the *cloud-narration* question is parked as a P2
  strategic decision (`docs/Backlog.md`).

### Notes _(for Tony)_

---

# Decisions Made 📋

No new ADR — small copy/config/label fixes. Community Signals source: **keep r/FantasyPL** (owner, 2026-08-13).
Two tester "issues" resolved as **not bugs** (Ollama local-only; set-piece numbers are order) with UX clarity fixes.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** Home reads clean; My Squad opens at 1 GW / Squad Lab at 5; the AI-Tips/Ask output
  has no "Start Ollama" line; Set-pieces headers say "order".
- **Next from the 2026-08-13 intake:** the **Help revamp** (its own workstream — a focused sprint + light ADR + a
  preview); then the gate/decision items — **Boot Battle compare *from the card*** (⚙ panel follow-on) and the
  **cloud-LLM narration** decision. P2 admin graphs later.
- **GW1 (2026-08-21, ~8 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Grep the tests for a default's old value before changing it.

---

# Key Commands Learned

```text
grep -rn "default=5\|== 5\|over 5 GW" tests/     # find tests that hard-code a default before changing it
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `ollama_hint` | `render_ask` flag — CLI shows the "Start Ollama" prompt, the web suppresses it (US-375) |
| Set-piece **order** | The FPL taking priority (1 = first-choice), not a count — now in the column header (US-376) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/Backlog.md` (2026-08-13 intake) | The triage + the "shipped since 2026-08-12" roll-up |
| `src/ui/ask.py` (`render_ask` + `ollama_hint`) | The CLI/web behaviour split |

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
