# Architectural Decision Record: Hover exists only where tapping doesn't

**Decision ID:** ADR-139
**Date:** 2026-08-25
**Status:** ✅ **Accepted — built** (Sprint 193, 2026-08-25), **revised 2026-08-26 and Cloud-verified** — the compact card is
back, bound to the selection instead of the cursor. Owner: *"perfect!"* **1415 → 1416 tests, ruff clean.** Owner-reported 2026-08-25, logged to the Roadmap the same
day, built the same day.
**Superseded By / Replaces:** Removes the hover reveal added by US-344 / ADR-109 from the **tappable** pitch
only. Completes ADR-135's revert by dealing with the surface that was actually misbehaving. Keeps ADR-133's
tap-to-select and ADR-108's panel exactly as they are.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, 2026-08-25:

> The current hover on a player is too much, better if it appeared on a click, with the teal highlight.

This is the last loose end from ADR-135. That revert removed the action **menu**, but the screenshot which
triggered it showed a second problem that went unaddressed: *"the hover is following the players around, so
now I can see one player whom I am going to captain, and stats on another."* The **hover popover** is that
problem. It fires on whatever the cursor is over, independently of what is selected, so a selected card and an
unrelated card's stats can be on screen at once.

**Reading the code changed the shape of the fix entirely.** The plan logged on the Roadmap assumed a new
click-to-open card had to be built. It does not: `views/squads.py` **already renders the full player card in
the panel below the pitch** for whoever is selected, and ADR-133's tap already drives that selection with the
teal outline. So the tap-to-reveal behaviour the owner asked for **already exists** — the hover popover is a
*second, compact copy of the same card*, floating, on a different trigger.

The feature was not missing. It was being obscured by a duplicate.

**And the duplicate is desktop-only**, which was always the weaker half: the caption on this very page has read
*"works on phone too (the pitch hover is desktop-only)"* since ADR-108. Half the audience never had it.

---

### ✅ Decision

**1. The rule: hover exists only where tapping doesn't.**

| pitch | tappable? | reveal |
|---|---|---|
| My Squad (`render_tappable_pitch`, component present) | yes | **tap → teal outline + full card in the panel** |
| My Squad (component missing — the ADR-133 fallback) | no | hover, unchanged |
| Squad Lab ▸ Build (`render_pitch`, a preview) | no | hover, unchanged |

The popover is suppressed when, and only when, `clickable=True`. This falls out of one condition rather than a
flag anyone has to remember, and — importantly — **the fallback path gets hover back for free**: when the
click component fails to load, `render_tappable_pitch` already calls plain `render_pitch`, so the page degrades
to exactly its old behaviour. The failure mode stays "the tap stops working", never "there is no way to see a
card".

Squad Lab's Build pitch keeps hover because there is no panel there and no selection to drive one. Different
affordances on the two pitches is not an inconsistency; it is the honest answer to *"can you tap this one?"*.

**2. The card moves to the top of the panel.** It was rendering *below* three Boot Battle widgets (pool ·
club · compare-with), so a tap put the teal outline on the shirt and the card a scroll away, behind controls
for a different question. The card is now the first thing after the selection, which is what makes "tap →
card" feel like one action instead of two. This is the part that actually delivers the request; the removal
alone would have taken something away without putting anything where the eye lands.

**3. Nothing else changes.** No analytics, no `decision_xp`, no change to selection, the outline, the panel's
actions, or the compact-card renderer (still used by the two non-tappable pitches).

**Not in scope:** an *in-place* popover on the shirt itself. It is the shape that runs out of room on a phone,
it is what collided with its neighbours, and the panel already holds a fuller card than a 250px floating box
ever could.

### ⚠️ Risks

- **A desktop user who liked hovering to scan several players quickly.** Real: hover surveys the pitch faster
  than tapping does, because each tap is a Streamlit rerun. Accepted, because the thing being scanned was a
  *compact* card and the panel shows the full one — and because a survey mechanism that shows one player's
  stats beside another player's selection is not a survey mechanism, it is a bug. If scanning turns out to be
  the real want, the answer is a table view, not a floating box.
- **Discoverability.** Hover was self-revealing; a tap has to be advertised. Mitigated by the existing ADR-133
  caption, which already says *"Tap a shirt on the pitch"* whenever the component is live, and is now the only
  instruction rather than one of two.

### 🧪 Definition of Done

1. **Tests** — the popover is absent from clickable pitch HTML and present on both non-clickable paths
   (including the component-missing fallback); an AppTest that the panel's card renders above the Boot Battle
   controls.
2. **Manual smoke** — My Squad on Cloud, desktop and iPhone: tap a shirt, get the outline and the card, and no
   floating card anywhere.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, a sprint retro.

---

### 🔨 Built — and a dead test it exposed

The change itself is two edits: `pop_html` is emitted only when `not clickable`, and the panel's card moved
above the Boot Battle widgets. Verified on the markup directly:

```
tappable pitch — popovers: 0     plain pitch — popovers: 12     teal outline still on the tapped card: True
```

**The smoke found a test that had been passing while asserting nothing.**
`test_my_squad_pitch_popover_shows_per_gameweek_xp` checked ADR-109's per-GW row by reading
`AppTest.markdown` — but **ADR-133 put the pitch inside a click component two sprints ago**, so the pitch
stopped appearing in `at.markdown` at all and the test hit its `if "fpl-pitch" not in blob: return` guard on
every run. It has asserted nothing since, and nothing in `test_pitch_html.py` covered the per-GW row either,
so ADR-109's behaviour was **untested on both paths**.

ADR-139 would have made it worse in a specific way: the test would have kept passing under the name of a
popover that no longer exists on that pitch — a green tick standing guard over a deleted feature.

Fixed on both sides:
- `test_pitch_html.py` gains the per-GW assertion against the **markup**, on a non-clickable pitch, where the
  popover still lives and no component can hide it.
- The AppTest is **renamed and retargeted** to `test_my_squad_panel_card_shows_per_gameweek_xp`, asserting the
  row on the card the *tap* reveals — which is where My Squad actually shows it now. The docstring records why
  it changed, so the next reader does not think it always tested that.

*(The sibling `test_my_squad_pitch_cards_show_set_piece_attributes` has the same shape but was neutered
**knowingly** in ADR-133, with a comment pointing at its replacement. Left alone — it is documented, not
silently empty.)*

### 💡 The lesson

**A test that returns early is not a test, and "the suite is green" will not tell you.** Both of the last two
sprints found something similar — ADR-136's verifier flagging its own recommendation, ADR-137's contradictory
notes — and the shape is the same each time: *an old path kept running beside a new one, and nobody asked what
the old path was still asserting.* ADR-133's write-up did say "coverage moved rather than shrank" and listed
the AppTests affected; what it did not do was check that every moved assertion actually landed somewhere. One
of them did not.

**When a change makes a test unable to see what it was watching, the guard clause that hides it is the danger,
not the failure.** A test that fails loudly gets fixed the same hour.

### 🧪 Definition of Done — met

1. **Tests: +3 (1347 → 1350).** `test_hover_exists_only_where_tapping_does_not` (the rule, both directions),
   `test_the_fallback_pitch_keeps_its_hover` (the ADR-133 join this leans on), the retargeted per-GW test, and
   the new markup-level per-GW assertion, plus an AppTest that the card renders **above** the Boot Battle
   controls.
2. **Manual smoke** — ⏳ owner, on Cloud: tap a shirt on My Squad (desktop and iPhone), confirm the outline
   plus the card in the panel, and no floating card anywhere on that pitch. Squad Lab ▸ Build keeps its hover.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, `docs/05_Sprints/Sprint193.md`.

---

### 🔁 Revision (2026-08-26) — the trigger was broken, not the card

**Owner, after living with it:** *"Previously we had a hover that showed a smaller, condensed version on the
pitch under the player — this has disappeared. I'd like it back when you click, as well as the more detailed
version in the panel below."*

**This ADR removed too much.** It correctly identified that the hover popover was misbehaving, and then threw
away the card along with the trigger. Re-reading the original complaint makes the distinction obvious:

> *"the hover is following the players around, so now I can see one player whom I am going to captain, and
> stats on another"*

Every word of that is about **when** the card appeared, not **what** it contained. A compact card under the
shirt is genuinely useful — it is the thing you glance at while looking at the pitch, without leaving the
pitch. The panel card below is a different job: fuller, further away, for when you have already chosen.

**Bound to the selection, the original failure cannot recur.** On a clickable pitch only the *selected* kit
carries a `kit-pop` at all, so:

| state | result |
|---|---|
| clickable + selected | one card, in place, under the player you chose |
| clickable + nothing selected | **no card exists**, so nothing can collide |
| not clickable | hover, unchanged — Squad Lab's preview and the ADR-133 fallback |

There is no extra round-trip: the selection has already happened, and this only changes what that selection
*renders*. And there is exactly one card on screen at any time — which is precisely what hover could not
guarantee.

### 💡 The lesson

**When something misbehaves, separate the thing from its trigger before removing either.** The hover card had
two properties — *a compact card under the shirt* (wanted) and *fires on whatever the cursor touches*
(broken). ADR-139 treated them as one feature and deleted both, then had to be asked for half of it back a day
later.

The tell was in the original complaint and I walked past it: **every clause described the timing, none
described the content.** Feedback usually names the symptom precisely; it is worth reading which noun the
complaint actually attaches to.