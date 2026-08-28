# Architectural Decision Record: The pitch and player panel rerun on their own

**Decision ID:** ADR-165
**Date:** 2026-08-28
**Status:** ✅ **Accepted — owner-verified on device** (Sprint 224, 2026-08-28). **1568 → 1569 tests, ruff clean.**
Owner, on an iPhone against the live deploy: *"feels a little quicker on the phone."*
**Superseded By / Replaces:** Follows the declined `decision_xp` cache (Backlog, 2026-08-28). **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on Cloud: *"works, it's a little laggy."*

My first idea — cache `decision_xp` — was **measured and declined**: 7 ms of a 56 ms render, and a stale entry
would show wrong xP. What the measurement did establish is that the cost is not any one computation but the
**shape of the interaction**: Streamlit reruns the *entire page script* on every widget change, so tapping a
shirt re-executed the xP strip, the pitch, the panel, the Boot Battle and the Player DNA card — to move one
selection.

`st.fragment` exists for exactly this: a widget inside a fragment reruns only that fragment.

---

### ✅ Decision

**The pitch + player panel is one fragment** — the tappable pitch, the picker, the card, Boot Battle, the
captain button, the substitute controls and the DNA card.

**The boundary is the decision, not the decorator.** Everything inside either *reads* the squad or *selects*
within it, so a partial rerun is correct. The two things that **mutate** it — Make captain, Substitute — call
`st.rerun()`, which defaults to `scope="app"` and reruns the whole page. That is required: the xP strip sits
**above** the fragment and must change when the captain does, and a fragment cannot repaint anything outside
itself. A test pins that `scope="fragment"` never appears, because that is the edit that would silently leave
the strip showing the previous captain's numbers.

The closure is deliberate too: a fragment rerun does not re-execute the parent, so its locals hold the last
full run's values — correct for selection (the squad has not changed) and irrelevant for mutation (which
forces a full rerun anyway).

### ✅ Verified the only way it could be, and ⚠️ here is why the local number was worthless

`AppTest` **does not simulate fragment-scoped reruns.** Proved with a probe app — a counter outside the
fragment incremented on every interaction with a widget *inside* it:

```
after load        : outer=1 inner=1
after a selection : outer=2 inner=2      ← a real fragment rerun would leave outer at 1
```

So the local benchmark (64 ms with, 61 ms without) **measured nothing** — it is blind to the feature by
construction. Reporting it as evidence either way would be worse than reporting no number at all.

**What that left** was a change that is architecturally correct, low-risk, and of unproven benefit — so it
shipped as unproven and the owner checked it on the device that had the complaint. Verdict: *"feels a little
quicker on the phone."*

That is a **subjective** report, and it is worth being precise about why it is nonetheless the right evidence:
the thing being optimised *is* how an interaction feels to the person using it, and the only instrument that
can read it is a person on a phone against the live deploy. A stopwatch on this machine would have been
objective and about a different question.

**"A little"** is also the honest size. The remaining latency is the websocket round-trip plus the custom
component re-mounting — neither of which is ours, and no further Python-side work will move them. **This
closes the performance thread** rather than inviting another pass.

### 🧪 Definition of Done

1. **Tests: +1**, and all 207 web tests still pass. The new one pins the boundary: a fragment exists, the
   mutating controls are inside it, and no rerun is fragment-scoped.
2. **Manual smoke** — the page renders and every control still works headlessly. ⚠️ **The performance claim
   is NOT smoke-tested**, for the reason above.
3. **Docs** — this ADR, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A harness that cannot observe the thing you changed will report success.** The benchmark ran, produced
plausible numbers to two significant figures, and was meaningless — and nothing about the output said so. It
took a five-line probe to find out, and only because the numbers were *suspiciously* flat rather than wrong.

The rule this earns, which is the same one that caught the toothless Home guard and the tap test that faked a
fresh click: **before trusting a measurement, prove the harness can see a difference.** Break the thing on
purpose and check the number moves. If it doesn't, the measurement was never evidence.
