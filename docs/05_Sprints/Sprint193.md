# Sprint 193: Hover exists only where tapping doesn't (ADR-139)

**Dates:** 2026-08-25
**Status:** ✅ Complete — ADR-139. 1347 → 1350 tests, ruff clean. ⏳ Owner smoke on Cloud outstanding.

> **Owner:** *"The current hover on a player is too much, better if it appeared on a click, with the teal
> highlight."*

---

### 🔍 The request, and why reading the code changed the answer

This is the last loose end from ADR-135. That revert removed the action **menu**, but the screenshot which
triggered it showed a second fault nobody dealt with: *"the hover is following the players around, so now I
can see one player whom I am going to captain, and stats on another."* The hover popover fires on whatever the
cursor is over, independently of what is selected — so a selected card and an unrelated card's stats sit on
screen together.

The Roadmap entry assumed a click-to-open card had to be **built**. It did not. `views/squads.py` already
renders the **full** player card in the panel for whoever is selected, and ADR-133's tap already drives that
selection with the teal outline. **The behaviour the owner asked for already existed** — the hover popover was
a second, compact, floating copy of the same card on a different trigger, and it was obscuring the real one.

The feature was not missing. It was being duplicated by something worse.

---

### 🔧 What shipped

**The rule: hover exists only where tapping doesn't.**

| pitch | tappable? | reveal |
|---|---|---|
| My Squad (component present) | yes | tap → teal outline + **full card in the panel** |
| My Squad (ADR-133 fallback) | no | hover, unchanged |
| Squad Lab ▸ Build (a preview) | no | hover, unchanged |

Keying the popover off `clickable` rather than a new flag is what makes the fallback correct **for free**: when
the click component fails to load, `render_tappable_pitch` already draws a plain pitch, so the page degrades to
exactly its old behaviour. The failure mode stays *"the tap stops working"*, never *"there is no way to see a
card"*.

**And the card moved to the top of the panel.** It was rendering below three Boot Battle widgets, so a tap put
the outline on the shirt and the card a scroll away, behind controls for a different question. This is the half
that *delivers* the request — removing the popover alone would have taken something away without putting
anything where the eye lands.

One hole closed on the way: with the card above the Boot Battle selectbox, a **stale** comparison label (the
selection moved to another position, so the remembered opponent is not in the new pool) would have skipped the
card *and* rendered no comparison, leaving the panel silent about the player you just tapped.

---

### 🐛 The dead test this exposed

`test_my_squad_pitch_popover_shows_per_gameweek_xp` asserted ADR-109's per-GW row by reading
`AppTest.markdown`. **ADR-133 moved the pitch inside a click component two sprints ago**, so the pitch stopped
appearing there and the test hit its `if "fpl-pitch" not in blob: return` guard on every single run.

It has asserted nothing since. And `test_pitch_html.py` had no per-GW coverage either — so ADR-109's behaviour
was **untested on both paths** while the suite stayed green.

ADR-139 would have made it worse in a precise way: the test would have gone on passing under the name of a
popover that no longer exists on that pitch. A green tick standing guard over a deleted feature.

Fixed on both sides — the markup-level assertion moved into `test_pitch_html.py`, and the AppTest renamed and
retargeted to the panel card, with a docstring recording why, so nobody later assumes it always tested that.

*(Its sibling `test_my_squad_pitch_cards_show_set_piece_attributes` has the same shape but was neutered
**knowingly** in ADR-133, with a comment pointing at its replacement. Left alone: documented, not silently
empty. That difference is the whole point.)*

---

### 💡 The lesson

> **A test that returns early is not a test, and "the suite is green" will not tell you.**

Three sprints running have found the same shape: an old path left running beside a new one, with nobody asking
what the old path still does. ADR-136 — a verifier flagging our own recommendation. ADR-137 — two output lines
contradicting each other. Now ADR-139 — a test watching a thing it can no longer see.

ADR-133's write-up *did* say "coverage moved rather than shrank" and listed the AppTests affected. What it did
not do is check that every moved assertion actually **landed** somewhere. One of them did not, and the honest
prose about the move is exactly what made it feel handled.

**When a change makes a test unable to see what it was watching, the guard clause that hides it is the danger —
not the failure.** A test that fails loudly gets fixed within the hour.

### 🧪 Tests

**+3 (1347 → 1350).** `test_hover_exists_only_where_tapping_does_not` pins the rule in both directions;
`test_the_fallback_pitch_keeps_its_hover` pins the ADR-133 join it leans on; the per-GW assertion now exists
at the markup level *and* on the panel card; and an AppTest checks the card renders **above** the Boot Battle
controls by comparing rendered element order, not source order.
