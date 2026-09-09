# Sprint 243: Name the two halves (ADR-182)

**Dates:** 2026-09-09
**Status:** ✅ Complete — ADR-182. **1733 tests, ruff clean.**
⏳ One owner action: the **Cloudflare deploy** of `~/madboots-site/index.html` (edited, not deployed).

> **Owner, relaying testers:** *"They're asking what this means. When you explain it it's OK, but that should
> not be necessary: 'the Fantasy Premier League assistant that shows its working.'"*

---

### 🔴 Why the line failed

**Copy that needs a gloss has already failed** — the gloss is not there when someone reads it.

Three faults, and the third is decisive:

1. *"Show your working"* is a **British schoolroom idiom**. Americans say *"show your work"*.
2. **"Working" as a noun** barely exists outside maths homework, so a reader has to realise it *is* a noun
   before the sentence can mean anything.
3. ⭐ **Spoken aloud it is a different sentence:**

```
"Every answer shows its working."     ← what we meant
"Every answer shows it's working."    ← what a listener hears
```

Identical in speech, and the second parse arrives first. It claims only that *the app functions*.

**The mantra is the spoken close of all ten videos.** The most distinctive claim in the product was going to
be delivered ten times in a form whose default hearing is banal — and only §0 had been shot, so the fix cost
nothing.

---

### 🔬 The rejected alternative, checked rather than assumed

The owner asked whether *"AI explains"* could come back: *"you could argue that AI explains the data in human
readable form? (maybe)"*

**No — and the check was in the code, not in memory.** `explain_captain` is plain Python appending
hand-written strings:

```python
if top.get("penalty_taker"):
    reasons.append(_penalty_reason(...))
```

The one place an LLM could speak is gated on `llm.reachable()`, a socket probe that fails on Cloud, and Ask
is behind `FPL_ADMIN_KEY`. **No tester has ever seen AI output.** ADR-168 stands.

It would also be **weaker if true**: the hero script's hook is *"AI that just… guesses"*, so closing on
*"AI explains"* would climb back into the bucket it just climbed out of. **Everyone claims AI. Almost nobody
claims you can check it.**

---

### 💡 The lesson

The owner's line — **"Analytics decide. Logic explains. You make the call."** — is better than the one I
proposed (*"Every answer shows why"*), and for a reason I did not anticipate:

> ⭐ **It names the two halves of the system, in the order they run.**

`decision_xp` decides (ADR-041, one recipe). `explain.py` explains (ADR-089, Edge · Risk · Confidence). **Two
modules, two jobs**, and the line names them. It is a description of the architecture rather than a metaphor
about it.

That is why it will not drift. **"The AI explains" died when the AI turned out not to be deployed. "Shows its
working" died because it named nothing checkable**, so nobody could tell it was vague until a tester said so.
The third names two things that exist and will be exactly as true tomorrow.

> **A slogan that describes the architecture cannot drift; one that describes a feeling always will.**

And the process point: **the tester's confusion was the whole measurement.** *"When you explain it it's OK"*
is not a partial success — it is the failure, stated precisely.

---

### 🧪 Guards — assert the requirement, not the sentence

The mantra has now changed **twice**, and both times a test had to be edited that had no opinion about
anything except the wording. So the guards were rewritten to assert what the line must *do*: no *"working"*,
*"explains"* present, three beats, and a descriptor carrying both halves.

Seven mutations, all caught: the old line returning · *"AI explains"* returning · the middle beat dropped ·
the middle beat no longer naming what explains · the three beats collapsed into one sentence · the descriptor
reverting · the descriptor losing a half.

---

### ⚠️ §0 now differs from its own script, deliberately

The intro is the one video already rendered, and **both its opening line and its close speak the retired
wording**. The script is updated; the video is not.

It is **not** worth re-rendering for this alone — its stills also show a UI that ADR-175→181 has moved past.
The re-cut is one job: new stills, new mantra, Maddie's bookends re-voiced, sequenced **after** the other
nine so the app has stopped moving (`Screenshot_Capture_List.md`).
