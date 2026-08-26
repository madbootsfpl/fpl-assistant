# Sprint 201: The compact card comes back, bound to the selection (ADR-139 rev)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-139 revision. 1415 → 1416 tests, ruff clean.

> **Owner:** *"Previously we had a hover that showed a smaller, condensed version on the pitch under the
> player — this has disappeared. I'd like it back when you click, as well as the more detailed version in the
> panel below."*

---

### 🔍 I removed too much

ADR-139 (yesterday) correctly diagnosed that the hover popover was misbehaving — and then threw away the card
along with the trigger. Re-reading the original complaint makes the mistake plain:

> *"the hover is following the players around, so now I can see one player whom I am going to captain, and
> stats on another"*

**Every clause describes when the card appeared. None describes what it contained.** The compact card under
the shirt was never the problem; it is the thing you glance at while looking at the pitch, without leaving the
pitch. The panel card below is a different job — fuller, further away, for after you have chosen.

### 🔧 The fix

Bind it to the **selection** instead of the cursor. On a clickable pitch only the selected kit carries a
`kit-pop` at all:

| state | result |
|---|---|
| clickable + selected | one card, in place, under the player you chose |
| clickable + nothing selected | **no card exists** — nothing can collide |
| not clickable | hover, unchanged (Squad Lab preview · ADR-133 fallback) |

No extra round-trip — the selection already happened; this only changes what it renders. And **exactly one
card is ever open**, which is the guarantee hover could not make.

So a tap now gives all three: the teal outline, the compact card in place, and the detailed card in the panel.

---

### 💡 The lesson

> **When something misbehaves, separate the thing from its trigger before removing either.**

The hover card had two properties: *a compact card under the shirt* (wanted) and *fires on whatever the cursor
touches* (broken). ADR-139 treated them as one feature, deleted both, and had to be asked for half of it back
a day later.

The tell was in the original complaint and I walked past it — **every clause named the timing, none named the
content**. Feedback usually describes the symptom precisely; it is worth checking which noun the complaint
actually attaches to before deciding what to cut.

Related, and worth noting as a pattern now: this is the second time in two days that a removal went one step
too far. ADR-146 was the same shape in reverse — I concluded a signal did not exist without checking which
input was actually missing. **Both were failures of precision about scope rather than of implementation.**

### 🧪 Tests

**+1, and two rewritten.** `test_the_compact_card_follows_the_SELECTION_not_the_cursor` pins the whole pair —
one card when selected, none when not, and shown by a `.kit.selected` rule rather than a hover rule, because a
hover rule would bring the original bug straight back. `test_a_pitch_you_cannot_tap_keeps_its_hover` pins the
fallback that the whole design leans on.
