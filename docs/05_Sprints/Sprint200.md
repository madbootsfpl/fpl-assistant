# Sprint 200: The crowd knows what the feed does not (ADR-146)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-146. 1407 → 1415 tests, ruff clean.

> **Owner:** *"Watkins is currently looking at a move to Saudi. There is no warning or pickup from AI tips or
> Health — **despite a lot of people transferring him out**."*

---

### 🔍 I had already looked at this case and got it wrong

**ADR-138 examined this exact player two days ago and concluded there was nothing to build.** Its words:
*"Nothing in the FPL data says so — his status is `a` with empty news — and nothing was built for it."*

True, and the wrong conclusion. It treated **the feed** as the boundary of what the app knows. The owner's
own sentence contained the correction: *despite a lot of people transferring him out.*

```
Watkins · status 'a' · news '' · minutes 0
   transfers_out_event  103,678   vs   transfers_in_event  7,583   →  net −96,095
   crowd_flags          ['⭐ popular', '❄️ out']        ← already computed, every refresh
```

`crowd_flags` was **already returning ❄️ out**. It renders in the Pool's Trends column and on the pitch. And
neither of the two surfaces that answer *"what's wrong with my squad?"* ever looked at it — `squad_risk.py`
contained no reference to transfers at all, and `gameweek_plan` built its flags purely from `status`.

**The data was there, computed, and displayed three clicks away from the place it mattered.**

### 🔬 The measurement that made it a feature rather than a nag

A raw exodus is not enough — the crowd dumps underperformers weekly. Across the 199 players owned by ≥1%, the
eight biggest sell-offs split **five explained, three not**:

| | net | our data says |
|---|---:|---|
| Pedro Porro | −227,771 | *"Lack of match fitness"* — explained |
| **Gyökeres** | −115,127 | status `a`, no news — **nothing** |
| **Konsa** | −106,963 | status `a`, no news — **nothing** |
| **Watkins** | −96,095 | status `a`, no news — **nothing** |

**The signal is the discrepancy, not the exodus.** And the three unexplained ones are exactly the players
worth a warning — and exactly the ones the app was silent about.

### 🔧 What shipped

`crowd_exodus` fires only when the sell-off is heavy **and** `status`/`news` cannot account for it. Scaled by
`price_pressure` (net per 1% owned) so template players are not flagged for being popular; threshold is the
measured p10 (−8,000 against p10 −7,996 · median −969 · p90 +11,104).

It reaches both surfaces at the layer they share — the gameweek flags (so `ask`, CLI and web AI tips all
inherit it) and the Risk Monitor (a `Crowd` driver that sorts to the top but stays **out** of the `attention`
score, because it is not a probability and averaging it with one would be ADR-143's units mistake again).

And it never claims to know *what* the news is:

> *"96,095 managers sold Watkins this gameweek and nothing in the data explains it — no injury, no suspension,
> no news. The crowd may be reacting to something we can't see; worth a look before you keep him."*

A test asserts it invents no cause. Saying *"he may be moving to Saudi Arabia"* would be sounding confident
about something we cannot know.

---

### 💡 The lesson

> **"We don't have that data" is a claim worth checking as hard as any other.**

ADR-138 said the app could not know about a Saudi transfer. That was true about the *news feed* and false
about **the app**, which was already computing a hundred thousand people's opinion of the same event and
rendering it in a table. The gap was never data — it was that the signal and the question lived on different
screens.

The general form: **when you conclude a feature is impossible, name precisely which input you are missing.**
"There's no news field for it" is checkable and, here, irrelevant. "We have no way to know" is neither — and
it is the sentence that closed this two days early.

Second: **the owner's throwaway clause was the whole answer.** *"Despite a lot of people transferring him
out"* is not context for the complaint, it is the mechanism for the fix. Worth reading feedback for what it
already knows rather than only for what it asks for.

### 🧪 Tests

**+8.** The Watkins case with its real numbers; an explained exodus — Pedro Porro, the largest of all — *not*
flagged, because the discrepancy is the signal; per-1%-ownership scaling; buys are not an exodus; **the note
asserts no cause it cannot know**; the threshold pinned as the measured p10; and gameweek-flag tests that it
reaches the plan and that a genuine `status` always wins over the inference.
