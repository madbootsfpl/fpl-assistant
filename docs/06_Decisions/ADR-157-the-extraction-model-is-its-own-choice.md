# Architectural Decision Record: Extraction gets its own model — and the resolver stops matching non-players

**Decision ID:** ADR-157
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 212, 2026-08-27). **1485 → 1496 tests, ruff clean.**
**Superseded By / Replaces:** Follow-up to ADR-151 (extraction) and ADR-152 (name resolution). **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

I proposed this sprint to the owner as *"switch `OLLAMA_MODEL` to `qwen3:8b` — it found 16 events on the live
feed where `llama3.2` found 7"*, citing spike 206. He said do it.

**Re-measured on the same 112 headlines, that claim was wrong.** Both models found **13**. The spike number
had compared different runs on different days and I repeated it as if it were a controlled result.

The measurement did settle the question, just not on the axis I predicted:

| | events | speed | correctness |
|---|---|---|---|
| `llama3.2` | 13 | **0.5 s/headline** | 1 false positive, 1 mislabel (a *return* called a *transfer*) |
| `qwen3:8b` | 13 | 1.0 s/headline | both typed correctly, plus one real injury the other missed |

*(A first run reported 9.0 s vs 1.3 s. That was a confound — a full `pytest` run overlapped `llama3.2`'s leg.
Re-run clean, `llama3.2` is the faster of the two. Recorded because I nearly shipped the confounded number.)*

Then the false positives turned out not to be a model problem at all. Checking which players the events
attached to:

* *"€135m **Bradley** Barcola"* → **Conor Bradley**, a Liverpool defender.
* *"**Enzo** Maresca"* → **Enzo Fernández**. A **manager's** first name.
* *"**David** Ornstein"* → a player called David. **The journalist we cite as a source.**

Both models produced these, because our own resolver did. ADR-152's span consumption defeats *"James
Maddison"* vs Reece James **because we hold both names**. It cannot help when the longer name belongs to
someone outside the Premier League, or to someone who is not a player at all.

---

### ✅ Decision

**1. Extraction gets its own model, timeout and budget.** `OLLAMA_EXTRACT_MODEL` / `OLLAMA_EXTRACT_TIMEOUT` /
`EXTRACT_BUDGET_SECONDS`, separate from the narration knobs. One constant was deciding for two jobs that do
not want the same thing: narration runs while a person waits and wants a warm sentence; extraction runs once,
unattended, inside `refresh`, and wants the same answer every time. Set to **`qwen3:8b`** — half the speed and
none of the mislabels, which is the right trade for a job nobody is waiting on.

**2. A bare surname followed by another capitalised word is not a mention.** Only bare `web_name` patterns are
tested; a full-name match is unambiguous, so *"Ollie Watkins, here we go"* must survive — it is the headline
the entire departure feature was built on. **Measured on the corpus: 45 mentions → 40, all five rejected ones
wrong, none of the 40 good ones touched.**

**3. A truncated read says so.** The budget stopped cleanly and **silently**, so a feed that outgrew it read
exactly like a quiet news day. `enrich_headlines` now times the call and names the truncation.

**4. The budget goes 180s → 300s**, from measurement rather than feel: 112 headlines at ~1.0 s median is a
~75 s read, and the old ceiling left too little room for a feed that grows.

**Live, after both changes:** 12 events, none false. Watkins → Al-Hilal still flagged; the Spurs team-news
headline correctly typed as a *return*; Barcola, Maresca and Ornstein gone.

### 🧪 Definition of Done

1. **Tests: +11.** Extraction and narration read different model knobs and different timeouts; an explicit
   model still wins; extraction asks for determinism and no thinking; a missing model costs only the answer;
   a truncated read says so and a complete one doesn't; and five resolver cases — the foreign player's first
   name, the manager, the journalist, a full name surviving a following capital, and an ordinary mention
   untouched.
2. **Manual smoke** — `refresh` on the live feed, 74 s, 12 events, listed and checked one by one.
3. **Docs** — this ADR, PROJECT_STATUS, the sprint retro.

⚠️ **Not yet on Cloud.** `seed.db` still carries the six llama3.2-era events; the app reads the committed
snapshot (ADR-056), so this reaches Cloud on the next **reseed** — which is the owner's call, not mine.

---

### 💡 The lesson

**I pitched this sprint on a number I had not verified, and the owner approved it on my say-so.** "16 vs 7"
came from my own note about a spike, and re-measuring showed 13 vs 13. The work was still worth doing — but
it was worth doing for reasons neither of us knew when it was approved, and if the measurement had gone the
other way we would have spent a sprint on nothing.

The rule this earns: **a remembered measurement is not a measurement.** It is a hypothesis with a number
attached, and it should be re-run before it is used to justify work — especially when quoting it *to the
person deciding whether to fund the work*.

The second lesson is the more useful one for the codebase. **I went looking for a better model and found a
worse resolver.** The most consequential defect in the extraction pipeline was not in the part that guesses —
it was in the deterministic code that decides who the guess is *about*, which had been quietly attributing
transfers to a manager, a journalist and a player at another club. Investigating a suspect component is a good
way to find out that the reliable one next to it was never checked.
