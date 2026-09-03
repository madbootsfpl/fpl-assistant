# Sprint 240: One week on the pitch, every week in the Lab (ADR-179)

**Dates:** 2026-09-03
**Status:** ✅ Complete — ADR-179. **1722 → 1725 tests, ruff clean.**
The defect fix shipped **on its own** (`e32a56b`) ahead of the three design changes.

> **Owner:** *"Let's remove GW1-3 from My Squad. Lab — My Team: Bruno Fernandes was Vice Captain on My Squad
> but not shown in Lab. Lab should show all Emojis, not just Set Pieces. Lab should show all GW scores rather
> than totaling, maybe limit 3… maybe this is a variant of the GW1-3 that we are removing on the My Squad
> page."*

That last clause is the sprint. **The multi-week view was not deleted — it was moved**, off the page you read
minutes before a deadline, onto the page you sit with while choosing players.

---

### 🔴 The defect, and why it shipped alone

He reported a missing badge. **`render_pitch` had no `vice_captain_id` parameter at all** — `_kit_html` drew
the V, `pitch_html` forwarded it, and the plain renderer between them never took it. Every surface drawing
through it lost the badge; ADR-178's new Lab plan view was simply the first place a squad *with* a
vice-captain reached it.

The half he could not see is the reason it did not wait behind three design changes:

```
render_tappable_pitch → render_pitch(**kw)
TypeError: render_pitch() got an unexpected keyword argument 'vice_captain_id'
```

That is **ADR-133's degrade path** — the fallback taken when the click-detector component is absent. On any
deploy without it, My Squad **raised** instead of degrading, and only when a vice-captain was set. The
fallback exists so *"a missing component never takes the page down"*. It did the opposite.

> **A reported symptom is a place to start looking, not the size of the problem.** Third time in two days
> (ADR-177's chip, ADR-178's missing key, this).

---

### 🔧 The three changes

**My Squad lost its horizon** — and **two** controls, since the *Cumulative / GW-only* switch only rendered
above a horizon of 1. Nothing the page needs went with them: the player card still shows 3 gameweeks, and
ADR-173's *"Longer view: +X over the next 5 GWs"* fires whenever the horizon is under 5, so at a fixed week
it now fires **always**.

**The Lab pitch carries every glyph**, with a grouped key. **The Lab's shirts show up to three per-gameweek
figures**; the tables keep five.

> **Two surfaces, two caps, each from that surface's own limit.** A 104px card and a scrollable table do not
> have the same budget, and one number applied to both would have been arbitrary for at least one of them.

---

### 🧭 The lesson — I generalised the justification, not the finding

ADR-178, one day old, concluded *"the pitch is a team sheet, the table is a reference"* and applied it to
**both** pitches. The owner was right that the Lab wants its market flags back, and the reason my rule failed
is the keeper:

> **The justification was about page purpose, and I generalised it into a rule about widget type.**

The flags left My Squad because it is read *on a phone, minutes before a deadline*. None of that is true of
the Lab. Same evidence, different page, different answer. Restated where it actually holds: **both pitches
render glyphs with a key; which glyphs depends on what the page is for.**

And the simplification ADR-178 was pleased to make — *"`_kit_html` needs no flag mode"* — came back, because
it was only redundant *given the rule as stated*, and the rule was too broad.

One thing that survived and improved: ADR-178 argued against market glyphs partly because 💎 ⭐ 🟦 👑 is *"a
four-point ordinal scale drawn as four unrelated pictures"*. Written in the key as **💎 → ⭐ → 🟦 → 👑** it
teaches the ranking. A guard asserts the arrow, because replacing it with a separator is exactly the tidy-up
someone would make.

---

### 🧪 Guards, and what they caught

**Four tests pinned the removed control**, each rewritten to assert the requirement rather than the widget.
The subtle one: `…captain_next_gw_double` computed its expectation at `horizon=3`, so left alone it would
have compared the page's number against **a different window's sum**.

The best of them is now inverted into evidence: a test that used to prove *"the card is independent of the
horizon"* now proves *"the card shows 3 gameweeks at a one-gameweek page horizon"* — **which is the reason
removing the control was safe.**

**A caption pointed at a control that no longer exists** — *"…the Gameweeks ahead selector doesn't change
it"*. Deliberately **not** put through `RETIRED`: that list is for phrases retired *everywhere*, and
"Gameweeks ahead" is still the Lab's live label, so a global entry would fail where the phrase is right.

> **The mechanism has to match the scope of the change. A global list cannot express a page-local
> retirement.**

**And a fixture that could not express the thing under test — the fifth time.** The Lab-glyph guard was
written with `selected_by_percent`; `ownership_tier` reads **`selected_by`**, so the fixture produced no
ownership tier at all and the glyph the test is named after could not have appeared however the code behaved.

Nine mutations, all caught, with the clean suite re-run against a recorded baseline after every restore —
ADR-178's harness bug, not repeated. One guard from the defect fix **was wrong first**: `"v-badge" in blob`
also matched the CSS block every pitch emits, so it passed with the fix reverted. **A selector is not a
rendered element.**
