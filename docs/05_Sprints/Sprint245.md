# Sprint 245: Sweep for the claim (ADR-184)

**Dates:** 2026-09-12
**Status:** ✅ Complete — ADR-184. **1738 → 1740 tests, ruff clean.**

> **Owner**, reading the Lab: *"Note the model note: 'The recommendation is data-driven; **AI explains the
> reasoning**. Confidence is a heuristic from the signals, not a probability.'"*

---

### 🔴 A claim retired in August, still on six surfaces

`MODEL_NOTE` in `src/ui/explain.py` renders on the Lab, the captain card, the chip advice, the gameweek plan
and three `ask` intents. It has been saying *"AI explains the reasoning"* since before ADR-168 retired that
claim on 2026-08-29.

**It is false for every tester.** No Ollama on Cloud, Ask behind `FPL_ADMIN_KEY`, and the Edge / Risk /
Confidence block it annotates is rule-based Python in the very module that defines the note.

Now:

> *"Analytics decide the recommendation; logic explains it. Confidence is a heuristic from the signals, not a
> probability."*

ADR-182's two halves, with the heuristic caveat kept word for word — it was the one part of the old sentence
that was always true.

---

### ⭐ The lesson — why two ADRs walked past it

ADR-168 removed the claim from the mantra. ADR-182 rewrote the mantra's successor. **Both shipped a guard,
and both guards checked the same two places:**

```python
assert "AI explains" not in brand.MANTRA
for page in ("7_Help.py",):
    assert "The AI explains. You make the call." not in src
```

That is a guard against *a regression in two files*. It is not a guard against a false promise.

> **A guard against a claim must sweep for the claim, not check the places you thought of.**

The claim survived fourteen days three modules away, on more surfaces than the mantra ever had — and ADR-182
walked past it while rewriting the exact sentence it came from.

**The rule for next time: when retiring a claim, grep for the claim and make the grep the test.**

---

### 🔬 The guard was wrong twice before it worked

**v1 had an escape hatch keyed on proximity** — any line with an ADR number within ±5 lines was exempt. A
mutation stripping Help's local-run caveat **passed**, because an unrelated `ADR-168` comment sat four lines
below the claim.

> **An escape hatch keyed on proximity exempts whatever happens to be nearby.**

Replaced with a structural rule: **a comment may say it** (that is how history is recorded); **a string may
not**, unless the copy around it names the condition. Help's *"available when you run it yourself… the hosted
app runs data-only"* earns its exemption by scoping, not by being on a list.

**And one of my own mutations was invalid.** Testing that exemption I changed *"The hosted app runs"* →
*"The app runs"* and read the survival as a guard failure. It was not — both scoping phrases were still
there, so the copy was still honest and the guard was right to pass.

> **A mutation that does not break the property proves nothing about the test.** Check the mutation actually
> breaks the thing before believing what its result tells you.

---

### 🧪 Tests

**+2.** A sweep over `src/` for the claim, and a guard that `MODEL_NOTE` names logic and keeps *"not a
probability"*. Mutation-checked: the claim returning · the caveat dropped · Help losing its scoping.
