# Sprint 208: A reported departure is a dead slot we know about first (ADR-153)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-153. 1456 → 1460 tests, ruff clean.

> **Owner, on Cloud:** *"Watkins is flagged as expected — however it points to another issue. We have the data
> that he is to be sold. However AI Tips doesn't know that… it's suggesting to start him. Should be
> recommending a transfer for him."*

---

### 🔍 Two faults, and the second is the real one

**The flag asserted ignorance it no longer had.** `gameweek_plan` built its reason as a hardcoded string —
*"167,825 sold him this week — nothing in the data says why"* — while the Romano headline sat in the same
database, already being read by two other surfaces. The one place the cause was available and unused.

**And knowing changed nothing about the advice.** The plan flagged Watkins, then recommended **starting** him
and transferring out somebody else, because FPL still reports `status = 'a'` and `decision_xp` still credits
him a full horizon of points he will not be here to score.

### 🔬 The measurement that decided the design

The obvious approach — ask the model whether a transfer is *out of* the league — is one more thing for it to
get wrong. The data answered for free. Of five transfer headlines in the live seed, **exactly one** carried a
heavy unexplained sell-off: Watkins (−167,825). Pinnock, Disasi, Baleba and Hadjam had none — they are moves
**within or into** the league, the player stays playable, and the crowd knows it.

> **The exodus is what separates "leaving the football we can see" from "changed shirts".**

### 🔧 What shipped

Two signals must agree. It reaches the advice through **ADR-136's existing dead-slot machinery** rather than a
new path — a confirmed departure *is* a dead slot; FPL's status just lags. FPL's own status still wins when it
has something to say.

And a reported leaver is measured against **zero**, not his paper xP — which is fiction while FPL calls him
available. Comparing against it produced *"recovers **−8.6** xP"*: a negative recovery, which is not a
sentence about anything.

```
Replace:  ⛔ Watkins (AVL) is reported to be leaving — per Romano.
             → Welbeck (CHE, £6.0) is worth 15.5 xP over 5 GW
Flags:    Watkins (167,825 sold him this week — Romano reports a move — "[Romano] Hilal have now agreed…")
```

---

### 💡 The lesson

> **A signal is only worth what the surfaces do with it.**

ADR-151 extracted the Watkins story correctly, stored it correctly and displayed it correctly — and the app
went on advising he start. The extraction was finished; the *feature* was not, because nothing downstream had
been taught to act on the new fact.

The generalisation worth keeping: **when you add a new fact, list every decision that would change if it were
true.** Here there were two — the flag's wording and the transfer advice — and only the first was obvious,
because it was the one already showing the fact. The second needed a user to notice.

### ⚠️ Left open, deliberately

**The lineup still starts him.** `best_legal_xi` ranks on `decision_xp`, which still rates Watkins 4.3. So we
recommend replacing him *and* would start him until you do. Coherent — he is in the squad until transferred —
but odd to read. **Zeroing his xP for lineup purposes would be a decision taken from a headline**, which is a
bigger step than this sprint should take on its own. Flagged for the owner rather than quietly done.

### 🧪 Tests

**+4.** Two signals must agree, with the five-headline table in the docstring so the reasoning travels with
it; a reported departure is a dead slot before FPL says so; FPL's own status still wins; and a reported leaver
is measured against zero so a recovery can never read as negative.
