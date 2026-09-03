# Architectural Decision Record: One week on the pitch, every week in the Lab

**Decision ID:** ADR-179
**Date:** 2026-09-03
**Status:** ✅ **Accepted — built** (Sprint 240, 2026-09-03). **1722 → 1725 tests, ruff clean.**
The defect fix shipped **on its own** (`e32a56b`) ahead of the three changes, as planned.
**Superseded By / Replaces:** **Closes [ADR-178](./ADR-178-plan-in-the-lab-play-on-the-pitch.md)'s gate** and
**reverses [ADR-175](./ADR-175-value-above-the-fold.md)'s `GW1 | GW1–3` control** — which ADR-175 itself
introduced as a compromise, cutting the pitch from `1/2/3/4/5/10`. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner feedback after ADR-178 shipped, four items:

> *"Let's remove GW1-3 from My Squad. Lab — My Team: Bruno Fernandes was Vice Captain on My Squad but not
> shown in Lab. Lab should show all Emojis, not just Set Pieces. Lab should show all GW scores rather than
> totaling, maybe limit 3 — not sure how you would do that, but it's important to see that info; maybe this
> is a variant of the GW1-3 that we are removing on the My Squad page."*

The last clause is the shape of the whole thing, and it is the owner's, not mine:

> **The multi-week view is not being deleted. It is being moved — off the page you read minutes before a
> deadline, onto the page you sit with while choosing players.**

Which makes the title of ADR-178 finally true rather than aspirational: *plan in the Lab, play on the pitch.*

#### Decision Drivers

- **Driver 1 — a defect first.** One of the four is not a preference; it is a crash. It should not wait behind
  three design changes, and it should not be bundled with them in a commit.
- **Driver 2 — the surfaces differ in purpose, so they may differ in density.** ADR-178 applied one rule to
  both pitches. That was one generalisation too far (see §Correction).
- **Driver 3 — each surface's cap should come from that surface's real limit**, not from one number applied
  to both. A 104px card and a scrollable table do not have the same budget.

---

### 🔬 The defect, found from a one-line observation

The owner reported a missing badge. The cause is worse:

```
>>> render_pitch([], [], captain_id=1, vice_captain_id=2, …)
TypeError: render_pitch() got an unexpected keyword argument 'vice_captain_id'
```

**`render_pitch` has no `vice_captain_id` parameter at all.** `_kit_html` draws the badge and `pitch_html`
forwards it, but the plain renderer in between never took it. My Squad shows the V only because it draws
through `render_tappable_pitch`, which builds its HTML by a different route.

Two consequences, and the second is the serious one:

1. **Every surface using `render_pitch` silently loses the vice-captain** — which is what the owner saw in
   the Lab. ADR-178's new plan view is simply the first place a squad with a vice-captain reached it.
2. **The ADR-133 degrade path raises.** `render_tappable_pitch` falls back to `render_pitch(**kw)` when the
   click-detector component is absent — forwarding `vice_captain_id` straight into a function that does not
   accept it. So on any deploy without that component, **My Squad crashes instead of degrading**, and only
   when a vice-captain is set. The fallback exists precisely so *"a missing component never takes the page
   down"*, and it did the opposite.

⚠️ **This is the third time in two days that a small owner observation has opened onto something larger**
(ADR-177's chip, ADR-178's missing key, this). The pattern is worth naming: **a reported symptom is a place
to start looking, not the size of the problem.**

---

### 🧭 Correction — ADR-178 over-generalised, one day old

ADR-178 concluded *"the pitch is a team sheet, the table is a reference"* and applied it to **both** pitches.
The owner is right that the Lab wants its market flags back, and the reason my rule failed is worth recording
rather than quietly patching:

> **The justification was about page purpose, and I generalised it into a rule about widget type.**

The flags left My Squad because it is read *on a phone, minutes before a deadline*, where anything not about
this gameweek competes with something that is. **None of that is true of the Lab**, where you are choosing
players and *differential-vs-template is the question*. Same evidence, different page, different answer.

So the rule is restated one level down, where it actually holds:

> **Both pitches render glyphs with a key. Which glyphs depends on what the page is for.**

And the flag-mode argument that ADR-178 was pleased to delete comes back. It was deleted for a real reason —
it was redundant *given the rule as stated* — but the rule was wrong, so the simplification was too.

---

### 💡 Options Considered — the Lab's flags

#### Option 1: All glyphs, with a grouped key *(Chosen)*
* **Description:** the Lab pitch shows role **and** market glyphs; its key groups them by kind, with
  ownership written as an **ordered scale**.
* **Pros:**
  - ✅ Same visual language on both pitches — only the set differs, so nothing new has to be learned.
  - ✅ **The ordered scale answers my own objection to glyphs.** ADR-178 argued 💎 ⭐ 🟦 👑 was *"a four-point
    ordinal scale drawn as four unrelated pictures"*. Written `💎 → ⭐ → 🟦 → 👑` the key teaches the
    ranking, which is the thing that was unlearnable.
  - ✅ The Lab's table sits directly below with the same facts **in words**, so the key is a reminder, not the
    only explanation.
* **Cons:**
  - ❌ The key grows to ~12 symbols over three lines. Real cost, and the reason it must be grouped.

#### Option 2: Words on the Lab pitch (what shipped before ADR-178)
* **Pros:** ✅ No key needed at all.
* **Cons:** ❌ Six worded flags wrap to three lines under a 104px name — the density the owner objected to in
  the first place, and he asked for *"all Emojis"*, which settles it.

---

### 🎯 Decision & Justification

**Change 1 — `render_pitch` takes and forwards `vice_captain_id` (defect).** Lands **on its own**, before the
rest. A guard drives the ADR-133 degrade path *with* a vice-captain set, which is the case that raises today.

**Change 2 — `GW1 | GW1–3` comes off My Squad; the horizon is fixed at the next gameweek.** The gate ADR-178
opened, closed by the owner. It removes **two** controls, because the *Cumulative / GW-only* switch only
renders when the horizon exceeds 1. What is not lost, and why this is safe:

- the **player card** under a shirt already shows 3 gameweeks, sized per team so a blank leaves no hole;
- **transfers keep their long view** — ADR-173's *"Longer view: +X over the next 5 GWs"* fires whenever the
  horizon is under 5, so at a fixed one week it now fires *always*;
- and the multi-week read moves to the Lab, which is the point of changes 3 and 4.

Recorded plainly: this **reverses ADR-175's own compromise four days on**, and ADR-175 had already reversed
ADR-171. The owner's standing steer applies — *on the golden page, arriving at the right layout beats holding
a settled one.*

**Change 3 — the Lab pitch shows all glyphs, with a grouped key.** Per Option 1.

**Change 4 — per-gameweek numbers on the Lab's shirts, capped at three.**

⚠️ **Half of this shipped in ADR-178 and may not have been seen yet:** the Lab's *tables* already carry a
column per gameweek (GW3…GW7 at horizon 5), with a blank rendered empty rather than as a zero. What is still
a single total is **the number on each shirt**, and that is what this change addresses.

**Two surfaces, two caps, each from its own limit:**

| surface | cap | why |
|---|---|---|
| the shirt | **3** | the card is 104px wide; a fourth figure wraps |
| the table | **5** | a table scrolls, and ADR-178 already capped it there against false precision (ADR-173) |

One number applied to both would have been arbitrary for at least one of them.

---

### 🔬 Found at build time

**1. Four tests pinned the removed control**, and each was rewritten to assert the requirement rather than
the widget:

| test | what it pinned | what it asserts now |
|---|---|---|
| `…quick_stats_summary` | the control's options are `GW1 · GW1–3` | there is **no** `gw_pitch` control |
| `…captain_next_gw_double` | set the horizon to 3, expect the *"next gameweek only"* caption | the strip is XI **+ the captain's double**, computed at the same one-week window the page uses |
| `…per_gw_card_is_horizon_independent` | the card is the same at horizons 1 and 5 | **the card shows 3 gameweeks at a one-gameweek page horizon** — which is now *the evidence that removing the control was safe* |
| `…offers_this_week_or_the_short_run_only` | the options and the default | renamed `…has_no_horizon_control_at_all`, and asserts **both** controls are gone |

The second is worth spelling out: its expectation was computed at `horizon=3`, so left alone it would have
compared the page's number against a **different window's** sum. Realigning it was not cosmetic.

**2. A caption pointed at a control that no longer exists.** The Captain panel read *"…the **Gameweeks
ahead** selector doesn't change it"* — a reassurance about a widget this page no longer carries, sending the
reader to look for something that is not there.

⚠️ **Deliberately not handled through `RETIRED`.** That list is for phrases retired *everywhere*, and
*"Gameweeks ahead"* is still the live label of the **Lab's** horizon control. A blanket entry would have
failed on a page where the phrase is correct — so the guard is scoped to the page whose *claim* changed.
**The mechanism has to match the scope of the change; a global list cannot express a page-local retirement.**

**3. A fixture could not express the thing under test — again.** The new Lab-glyph guard was written with
`selected_by_percent`; `ownership_tier` reads **`selected_by`**. With the wrong key the fixture produced *no
ownership tier at all*, so the glyph the test is named after could not have appeared however the code
behaved. Fifth occurrence of this root cause; it is now the single most common way a guard here goes blind.

#### ✅ Mutation results — nine guards, each reverted alone, restore verified between every run

| mutation | caught |
|---|---|
| the Lab loses its market glyphs | ✅ |
| My Squad **gains** the market glyphs | ✅ |
| the shirt cap widens from 3 to 5 | ✅ |
| a blank week on the shirt reads as `0.0` | ✅ |
| the price glyph titles itself (`💰↑` explaining `💰↑`) | ✅ |
| the Lab key drops the ownership/momentum lines | ✅ |
| **ownership stops being an ordered scale** (`→` becomes `·`) | ✅ |
| the horizon control returns to My Squad | ✅ *(two tests)* |
| the stale *"Gameweeks ahead selector"* caption returns | ✅ |

Plus the two from the defect fix, one of which **was wrong first**: asserting `"v-badge" in blob` also
matched the **CSS block** every pitch emits, so it passed with the fix reverted. **A selector is not a
rendered element.**

⚠️ Per ADR-178's harness lesson, the sweep re-ran the clean suite after every restore and compared it to a
recorded baseline, rather than trusting the copy-back.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:**
  - A crash on the documented degrade path is removed, and the badge appears wherever a squad has one.
  - My Squad drops to a single question — *what do I do this week?* — with two fewer controls.
  - The Lab becomes the multi-week surface in fact, not just in the ADR title.
* **Negative Impact / Trade-offs:**
  - Someone who has not found the Lab loses the three-week view entirely. Accepted with evidence:
    ADR-178 measured the GW1–3 XI as costing **0.32 xP** in the week you play it, inside ADR-161's sd 3.51.
  - The Lab pitch gets denser — deliberately, and only there.
  - A ~12-symbol key is a lot of legend. Grouped and ordered, but still the largest key in the app.
* **Risks & Mitigations:**
  - **Risk:** testers miss GW1–3 on My Squad. **Mitigation:** it is one control to restore, and the reasoning
    is here rather than lost.
  - **Risk:** three numbers on a shirt re-create the density the glyphs just removed. **Mitigation:** the
    Lab only, and the preview is the check — as it was for ADR-175/176/178.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`pitch.py`, `views/squads.py`, `pages/1_My_Squad.py`), Tests, Docs
* **Action Items — change 1, landing first:**
  - [x] `render_pitch` accepts and forwards `vice_captain_id`
  - [x] `render_plan` passes the squad's vice-captain
  - [x] Guard: the **ADR-133 degrade path with a vice-captain set** renders instead of raising
  - [x] Guard: a vice-captain reaches the badge on a plain `render_pitch`, not only the tappable one
* **Action Items — changes 2-4:**
  - [x] Remove the `GW1 | GW1–3` control; My Squad's horizon is fixed at the next gameweek
  - [x] Guard: no horizon control on My Squad, and the *Cumulative / GW-only* switch goes with it
  - [x] Guard: the answer panels still read a one-week window, and ADR-173's *Longer view* line still appears
  - [x] The Lab pitch renders market **and** role glyphs; My Squad still role-only
  - [x] A grouped key for the Lab, ownership written as an ordered scale
  - [x] Up to 3 per-gameweek figures on the Lab's shirts; table stays at 5
  - [x] Guard: the shirt breakout is capped at 3 and the table's at 5 — **two caps, asserted separately**
  - [x] **Mutation-test every new guard**, and re-run the clean suite between mutants (ADR-178's harness bug)
  - [x] Preview → owner sign-off before build

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
**A control is retired**: My Squad's *"Gameweeks ahead"* (`GW1 | GW1–3`) and the *Projected xP*
*Cumulative / GW-only* switch.
- [x] Swept — **one hit**, the Captain panel's *"the Gameweeks ahead selector doesn't change it"*, now
      corrected and guarded. Home and Help make no multi-week promise about My Squad.
- [x] **Nothing added to `RETIRED`** — *"Gameweeks ahead"* is still the Lab's live control label, so a
      global entry would fail where the phrase is correct. Scoped guard instead; reasoning in §Found at build time.
- [x] Checked `docs/08_Marketing/Video_Scripts.md` — no mention of the horizon control.
- [x] Four did. All four rewritten to assert the requirement — table in §Found at build time.

---

### 🔄 Review & Reconsideration
* **Review Date:** 2026-10 (with tester feedback)
* **Triggers for Reconsideration:**
  - [ ] Testers ask for a multi-week view on My Squad — one control restores it
  - [ ] The Lab's key proves unreadable at 12 symbols — words on the Lab pitch is Option 2, still open
  - [ ] A blank or double gameweek arrives, and the per-GW figures are read in anger for the first time

---

### 🔗 References & Related Artifacts
- **Closes the gate in:** [ADR-178](./ADR-178-plan-in-the-lab-play-on-the-pitch.md)
- **Reverses:** [ADR-175](./ADR-175-value-above-the-fold.md)'s `GW1 | GW1–3` compromise
- **Evidence relied on:** ADR-178 (the XI costs 0.32 xP), [ADR-161](./ADR-161-head-to-head.md) (sd 3.51),
  [ADR-173](./ADR-173-minutes-you-have-actually-played.md) (a longer window multiplies a suppressed rate)
- **Degrade path:** ADR-133 (tap to select, and its fallback)
