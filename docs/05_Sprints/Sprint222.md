# Sprint 222: The tap that couldn't work, and a strip that reflowed instead of shrinking (US-444 · US-449 rev)

**Dates:** 2026-08-28
**Status:** ✅ Complete. 1563 → 1565 tests, ruff clean.

> **Owner, on iPhone:** *"the player double click and then release does not work"* · *"the banner is great but
> still some wrapping"* (three screenshots).

Two follow-ups on yesterday's fixes. **Both of mine were wrong in the same way: I fixed what I could see and
never checked the mechanism underneath.**

---

### 🐛 US-444 — the toggle could never have worked

I made a second tap on the same shirt clear the selection, and it passed a test. The test only passed because
it *manually deleted the replay-guard key* between taps — I had written the workaround into the test without
noticing it was a workaround.

`st_click_detector` reports the id of the **last element clicked**. Tap the same shirt again and the value is
byte-identical, so Streamlit sees no state change, **does not rerun, and Python never hears about it.** No
amount of code on our side can recover a gesture the browser never sends. Even when a rerun happens for some
other reason, the replay guard swallows it — correctly, because it cannot distinguish a real second tap from
the replay it exists to suppress.

**The fix is the other half of the ask.** The owner said *"click pitch **or** the player again"* — the grass
behind the shirts is a different anchor, so it always returns a different id and always gets through. A
full-bleed `<a id="sel:clear">` sits behind the kits at `z-index:0`. The caption now promises the gesture that
exists rather than the one that doesn't.

### 🐛 US-449 — reflowing is not shrinking

The screenshots showed the strip working exactly as designed and still looking wrong: three items became
**two-and-one with a full-width orphan**, *taller* than the row it replaced. The ask was for something that
*shrinks on a small screen*; free `flex-wrap` does the opposite.

Now an explicit grid: `--n` columns wide, `--m` narrow, both passed from Python because CSS cannot count
items. Three stay side by side on a phone; four become 2×2 rather than a cramped row or a 3+1 orphan. And the
**labels are short**, because a long label is what forced a column wide in the first place — *"Points spent on
hits"* became **Hits** with the detail in the `sub` line and the tooltip.

---

### 💡 The lesson

> **A test that passes because you wrote the workaround into it is a test that proves nothing.**

`st.session_state.pop("pitch_tap__seen")` sat in the middle of my US-444 test, simulating a fresh click. I put
it there to make the test pass and did not ask *why the guard was in the way* — which was the entire answer:
the platform cannot deliver that gesture. The owner found in one tap what the test was written to hide.

> **"It behaves as designed" and "it works" are different claims.**

The strip reflowed perfectly. It was still wrong, because reflowing was never the goal — *taking less space*
was, and I had verified the mechanism instead of the outcome.

### 🧪 Tests

**+2, three repaired.** A background tap clears the selection; it does nothing where there is no "none"
option; the column count is the item count until four, when a phone gets 2×2. Repaired: the toggle test that
faked a fresh click is gone, the flex-wrap assertions became grid assertions, and three horizon tests now
assert the label and its `sub` separately.
