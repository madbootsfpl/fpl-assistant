# ADR-317 — A chip you have already played

**Date:** 2026-09-27
**Status:** ✅ **Built** (the wrong answer). ⏳ **Gate** for the two that follow.
**From:** the owner — *"We need to improve the Ask Question / Answer — its not really credible if multiple
questions give the same answer… and note i already have used my bench boost."*

---

## What was actually wrong

The owner's complaint was **repetition**: four questions, one answer. The repetition is real. But it was
hiding something worse, which the parenthesis at the end of his message named:

🔴 **Ask was recommending a chip he had already played.** FPL's own record for his team:

```
wildcard    ✅ available        3xc       🔴 PLAYED in GW3
bboost      ✅ available        freehit   ✅ available
```

…and Ask recommended **Triple Captain for GW7**.

⭐⭐⭐ **The repetition was the only visible symptom of the wrong answer.** Four identically-worded replies
are what made him look closely enough to notice. Had each been phrased differently — which is what an LLM
would have done — there would have been four plausible answers and no reason to check any of them.

## ⚠️⚠️⚠️ The capability existed, on the other path

`get_entry_history` has returned the played-chips list since **ADR-234**, and its docstring says why:

> *"Without it, a chip advisor recommends a wildcard that has already been spent — which is not a rough
> edge, it is a wrong answer delivered confidently."*

The **Chips screen** calls `_chip_status(manager_id)` and marks spent chips. `AskRequest` had no
`manager_id` at all:

```
['question', 'player_ids', 'bench_ids', 'squad_name', 'free', 'bank', 'horizon']
```

⭐ **The same engine was blind on one path and sighted on the other** — and the blind one is the one that
answers in words. 📌 The **sixth** capability this month that was built and unreachable.

## What shipped

- `AskRequest.manager_id`, optional, threaded to the chips decision through `answer → _fresh → _dispatch`.
- ⚠️ **The service fetches it, never the engine.** `src/ask.py` decides; it does not call FPL — *an engine
  that reaches the network is an engine that cannot be tested without one.*
- ⭐ **A spent chip keeps its timing advice and is marked, not removed.** *When it would have been best* is
  still true, and hiding the line would leave a reader wondering whether the app knew about the chip at
  all. The recommendation stops being an instruction:

  ```
  Triple Captain: GW7 — Haaland (MCI), xP 7.6 …  ⚠ ALREADY PLAYED — GW3
  ```

- ⚠️⚠️⚠️ **Unknown is never read as available.** A failed lookup prints **nothing** — never a mark, and
  never an implication that a chip is in hand. *"We could not check" and "you still hold it" are different
  facts and only one is safe to act on.* Mutation-tested by making unknown optimistic.

## ⏳ The gate — the repetition itself

Four questions still route to one intent, and **two of them are not chip-strategy questions at all**:

| asked | should | today |
|---|---|---|
| *"best way to use chips **before they expire**"* | strategy over **chips you still hold**, ordered by expiry | generic strategy |
| *"best chip strategy"* | that | ✅ |
| 🔴 *"**what's a chip?**"* | a **rules** answer (ADR-085's KB) | strategy |
| 🔴 *"**what chips have I played?**"* | a **fact**: *"Triple Captain, GW3"* | strategy |

⭐⭐ This is ADR-308's captaincy finding, one intent along: **the qualifier is the question.** Proposed, and
needing agreement before building:

**A — lenses on the chips intent.** *which chip next* · *have I played X* · *before they expire* · *can I
still play X*. The data is now in hand for all four, because `manager_id` arrived above.

**B — route *"what's a chip"* to `rules`.** ⚠️ A vocabulary fix, and the routing corpus is the place to
prove it: *"chips"* currently wins over the rules cues, and the fix must not steal *"which chip should I
play"* in the other direction.

**C — plumb `converse()`** so *"what about GW9?"* works (ADR-309 item 3, already built and unreachable).

🔴 **Explicitly not proposed: an LLM.** The owner asked whether Ask should be more like a chatbot. ⭐ This
ADR is the argument against it — *a model would have paraphrased the same computed block four ways and
removed the only signal that it was wrong.* ADR-309 measured the ceiling as the router, and ADR-168 tested
an LLM router and lost to four keywords.

## Consequences

- ⭐ The credibility fix is in. **A wrong answer is a different class of problem from a repetitive one**,
  and it is the one that was shipping.
- 📌 A, B and C are cheap and need no AI decision; the inference host stays gated (ADR-309).
- ⚠️ The same blindness may exist elsewhere `AskRequest` is thinner than the screen's request — 📌 worth a
  sweep of what the other intents cannot see.
