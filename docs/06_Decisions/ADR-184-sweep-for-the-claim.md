# Architectural Decision Record: Sweep for the claim, not the places you remember

**Decision ID:** ADR-184
**Date:** 2026-09-12
**Status:** ✅ **Accepted — built** (Sprint 245). **1738 → 1740 tests, ruff clean.**
**Superseded By / Replaces:** Completes [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md) and
[ADR-182](./ADR-182-name-the-two-halves.md), **both of which missed this**. No behaviour change; one
user-facing sentence and the guard that should have caught it.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner, reading the Lab:

> *"Note the model note: **'The recommendation is data-driven; AI explains the reasoning.** Confidence is a
> heuristic from the signals, not a probability.'"*

That is the claim **ADR-168 retired on 2026-08-29**, still rendering. It lives in `MODEL_NOTE`
(`src/ui/explain.py`) and appears on **six surfaces**: the Lab, the captain card, the chip advice, the
gameweek plan, and three `ask` intents.

**It is false for every tester.** There is no Ollama on Streamlit Cloud, Ask is behind `FPL_ADMIN_KEY`, and
the Edge / Risk / Confidence block this note annotates is rule-based Python in `explain.py`. Nothing about it
involves a model.

#### Why two ADRs missed it

ADR-168 removed the claim from the mantra. ADR-182 replaced the mantra's successor wording. Each shipped a
guard, and **both guards checked the same two places**: `brand.MANTRA` and `7_Help.py`.

```python
assert "AI explains" not in brand.MANTRA
for page in ("7_Help.py",):
    assert "The AI explains. You make the call." not in src
```

Neither looked for the *claim*. They asserted the absence of a sentence in the files their author happened to
be editing — which is a guard against **a regression in two files**, not against a false promise.

> ⭐ **A guard against a claim must sweep for the claim, not check the places you thought of.**

---

### 🎯 Decision & Justification

**1. `MODEL_NOTE` says what actually explains.**

> *"Analytics decide the recommendation; logic explains it. Confidence is a heuristic from the signals, not a
> probability."*

The same two halves as ADR-182's mantra, for the same reason: `decision_xp` decides, `explain.py` explains.
The heuristic caveat is kept verbatim — it is the honest half of the brand and the one part of the old
sentence that was always true.

**2. A sweep guard over `src/`,** failing on `AI explains|clarifies|decides|narrates|tells|writes` wherever
it appears.

**3. One mention is allowed, and the rule is why rather than where.** Help's **Local AI** bullet is honest:
it says a local Ollama model can narrate *"available when you run it yourself"* and that *"the hosted app
runs **data-only**"*. The guard permits a mention **only when the surrounding copy names the condition** —
so the exemption is earned by the scoping, not granted to a filename. Delete the caveat and the guard fires.

**4. A code comment may say it; a string may not.** Comments are how the history is recorded (`player_dna.py`
still referred to *"the AI explains panel"*, now corrected). A string is what a reader sees.

---

### 🔬 The guard was wrong twice before it worked

**First version — an escape hatch keyed on proximity.** It exempted any line with an ADR number within ±5
lines. A mutation that stripped Help's scoping *passed*, because an unrelated `ADR-168` comment sat four
lines below the claim.

> ⭐ **An escape hatch keyed on proximity exempts whatever happens to be nearby.**

Replaced with a structural rule: comment lines are skipped; string lines must carry the caveat in their
block.

**And one of my mutations was wrong**, which is worth recording separately. Testing the Help exemption, I
changed *"The hosted app runs"* → *"The app runs"* and called the survival a guard failure. It was not — both
scoping phrases were still present, so the copy was still honest and the guard was right to pass. **A
mutation that does not actually break the property proves nothing about the test.** The real mutation
removes the caveat entirely, and that one does fire.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** a promise the app cannot keep leaves six surfaces; the claim is now checkable
  anywhere in `src/`, not in two remembered files; the note reinforces the mantra instead of contradicting it.
* **Negative Impact / Trade-offs:** the sweep is a text scan, so it reasons about how a claim is *written*.
  A paraphrase (*"the model writes your reasons"*) would slip past. Stated rather than implied; the phrase
  list is extensible and cheap.
* **Risks & Mitigations:**
  - **Risk:** a legitimate future AI feature is blocked by the guard. **Mitigation:** it is not — scope the
    copy to when it is true, which is exactly what Help already does, and the guard passes.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`ui/explain.py`, `analytics/player_dna.py`), Tests, Docs
* **Action Items:**
  - [x] `MODEL_NOTE` rewritten; the heuristic caveat kept
  - [x] `player_dna.py`'s stale *"the AI explains panel"* comment corrected
  - [x] Guard: no string in `src/` claims an AI explains, unless the copy scopes it to a local run
  - [x] Guard: `MODEL_NOTE` names logic and keeps *"not a probability"*
  - [x] Mutation-tested: the claim returning · the caveat dropped · Help losing its scoping
  - [x] Update PROJECT_STATUS, the Roadmap, and a sprint retro

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
**Not applicable** — no surface moves. One sentence changes on six surfaces, toward what the app does.

---

### 💡 The lesson

> **A retired claim outlives the place you retired it.**

ADR-168 removed *"The AI explains"* from the mantra and recorded the reasoning carefully. It survived
fourteen days in a constant three modules away, on more surfaces than the mantra ever had — and ADR-182 walked
straight past it while rewriting the very sentence it came from.

The generalisable form, and the thing to do next time: **when retiring a claim, grep for the claim and make
the grep the test.** Both previous guards encoded *"this file must not say this"*. The useful guard says
*"nothing may say this, unless it says when."*

---

### 🔗 References & Related Artifacts
- **Completes:** [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md) ·
  [ADR-182](./ADR-182-name-the-two-halves.md)
- **Found by:** the owner, reading a model note on the Lab — the seventh fault this month found by using
  the product
