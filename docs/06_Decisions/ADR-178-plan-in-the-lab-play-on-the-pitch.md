# Architectural Decision Record: Plan in the Lab, play on the pitch

**Decision ID:** ADR-178
**Date:** 2026-09-03
**Status:** ✅ **Accepted — built** (Sprint 239, 2026-09-03). **1713 → 1720 tests, ruff clean.**
⏳ **GW1–3 remains GATED, not built** — the owner: *"let's think through the GW1-3 a bit more before dropping
it… I am leaning heavily on putting it in the Lab."*
🔧 **Revised at preview** (2026-09-03) — the owner: *"would it be cleaner to use just the emoji under the
player and have a key at the bottom of the pitch, for both My Squad and the Lab?"* Yes, and it made the
change **smaller**. See §Revision 1.
**Superseded By / Replaces:** Continues [ADR-175](./ADR-175-value-above-the-fold.md)'s division of labour
between the pitch and the Lab. **No `decision_xp` change** — every number here already exists.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner UX + functional feedback on My Squad and the Lab, after ADR-175/176 shipped:

> *"We currently have the option to look at one GW or up to 3 GWs on that screen — now questioning the
> usefulness of that… It is used for planning your squad for the future, should this be done in the Lab? Then
> the Lab becomes more useful… instead of having just a new squad, use the drop down that currently has
> 'Squad name' and select your Current Squad or a New Squad."*
>
> *"The MySquad players on the pitch have a lot of Emojis under them in some cases which can become too much,
> maybe reduce to corners, pens, FKs — and in the Lab have them all for planning purposes. I also think in
> planning it should show each score for up to 3 weeks, not a combined."*

One principle underneath all of it, and it is worth naming because it decides each case:

> **The pitch is where you play this week. The Lab is where you plan a season.**

ADR-175 drew that line once already, on the owner's steer — *"I don't think this analysis will be done here —
yes in the Lab when you're creating your team, but not now when active."* This carries the same line through
three surfaces that had not been re-read against it.

#### Decision Drivers

- **Driver 1 — the golden page is scanned, not studied.** It is read on a phone, minutes before a deadline.
  Anything that is not about *this* gameweek is competing with something that is.
- **Driver 2 — the Lab is under-used because it only does one thing.** It builds from scratch. That is a
  few-times-a-season job, so a page that can only do it is closed the rest of the time.
- **Driver 3 — nothing may be lost in between.** Two of these changes move a capability rather than removing
  it, so the destination has to exist before the origin is cut. This is what makes the ordering part of the
  decision rather than an implementation detail.
- **Driver 4 — no new model work.** Every number needed here already exists (`by_gameweek`, ADR-032).

---

### 🔬 Measured first

#### 1. The emoji load, across all 651 players

```
1 flag:  478 (73.4%)          3 or more:  64 (9.8%)
2 flags: 109 (16.7%)          6 flags:     5

Szoboszlai   🟦 template ❄️ out 📈 form ⚽ pens 🚩 corners 🎯 FK
Groß         ⭐ popular 🔥 in 📈 form ⚽ pens 🚩 corners 🎯 FK
Palmer       ⭐ popular 🔥 in 💰↑ 📈 form ⚽ pens
```

Two findings the average hides:

**Every player carries at least one flag** — the ownership tier always fires, so the pitch is *never* clean.
And the six-flag players are Palmer, Szoboszlai, Groß, Gibbs-White: **the clutter concentrates on exactly the
players a good squad owns.** The owner is seeing it because his squad is good.

Set pieces only: **94% of players show nothing**, and a fifteen would carry two or three marked shirts.

**And the crowd flags are a third copy of things that already have better homes on the same page.** Price is
on the line directly beneath the pitch, *by name* (*"Isak may drop"*). Availability is on the Flagged line,
by name, linked to News. Ownership and momentum are what 📈 Trending and 📡 Signals exist for. The shirt is
the least readable of the three, and the only one that cannot say *why*.

Set pieces survive that cut **on merit, not preference**: they are a fact about the player's *role*, not
about the market, so they are the one group with no better home.

#### 2. Does the GW1–3 view actually change anything? — the gate evidence

589 legal fifteens sampled from the top-150 pool (≤3 per club, ≤£100.0m), each priced at both horizons:

```
best XI differs, GW1 vs GW1–3 : 375  (63.7%)
```

**Which looked decisive, and on its own is misleading.** The XI you field is a *one-week* commitment — you
re-pick it free next week — so the question is not whether the two differ but **what the GW1–3 XI costs you
in the week you actually play it**:

```
cost of fielding the GW1-3 XI next gameweek (n = 375 squads where they differ)
  mean 0.32 · median 0.30 · p90 0.60 · max 1.30 xP
  ≥ 1.0 xP:  4 squads  (1%)
```

**A third of a point.** ADR-161 measured one starter's single-gameweek spread at **sd 3.51**. So the
difference this control makes is an order of magnitude inside the model's own noise — it changes the answer
constantly and changes the *outcome* essentially never.

⚠️ **A correction to my own first reading, recorded because it nearly became the recommendation.** I also
measured the captain differing in 32% of squads and started to write that up as a fault. It is not: `captain.py`
hard-codes `horizon=1`, so the captain recommendation is **already** a next-gameweek decision at every setting.
The 32% was a property of the *ranking*, not of anything the app advises. **A measurement is not a finding
until you have checked which code path consumes it.**

---

### 💡 Options Considered — the flags

#### Option 1: Set pieces on the pitch, everything in the Lab *(Chosen)*
* **Pros:** ✅ 94% of shirts go clean; ✅ removes the only copy that cannot explain itself, keeping the two
  that name the player; ✅ the cut has a *reason* (role vs market), not a taste.
* **Cons:** ❌ a differential you would have spotted from 💎 on the shirt now needs Trending — which is the
  page that exists to say it, with the number attached.

#### Option 2: Cap the flags at two, most important first
* **Pros:** ✅ keeps everything reachable.
* **Cons:** ❌ requires a priority order nobody has agreed, and it would silently drop a *different* flag per
  player — the worst kind of inconsistency, because it looks like data.

---

### 🎯 Decision & Justification

**Three changes, and one thing deliberately not decided.**

**1. The pitch shows set-piece flags as bare glyphs, with one legend line beneath — on My Squad *and*
the Lab.** Revised from *"set pieces on the pitch, everything in the Lab"* — see §Revision 1, which is both
cleaner and less code.

**2. The Lab's "Squad name" becomes a squad *picker* — Current squad · New squad · a saved one.** Today that
field only *labels the output*; making it an input is what turns the Lab from a from-scratch optimiser into
the place you plan from where you actually are.

⚠️ **This is where scope has to be held.** *Loading* your current squad and reading it over 5-10 gameweeks is
cheap and honest. **Searching a transfer path from it is [ADR-132](./ADR-132-transfer-timing.md), which was
declined on evidence** — the best sell was the same player in all six gameweeks and the market yielded one
beneficial move, *a tree with one branch*. This ADR ships the read and does **not** reopen the search.

**3. The Lab shows per-gameweek xP, not one cumulative total.** The data already exists (`by_gameweek`,
ADR-032; it sums to `xp`). The reason it is better is not tidiness:

> **A cumulative number hides a blank gameweek.** 15 points over three weeks reads identically whether it is
> 5·5·5 or 15·0·0 — and blanks and doubles are precisely what multi-week planning is *for*. The total does
> not merely omit them; it conceals them.

**The breakout is capped at the first 3-5 gameweeks, with anything beyond as a single total.** Ten individual
weekly numbers would display a precision the model does not have — ADR-173 caught exactly this, where a longer
window multiplied a suppressed rate instead of correcting it.

#### ⏳ GATED — dropping GW1–3 from My Squad (owner's call, evidence above)

The owner asked to think this through rather than ship it, and the measurement is why that was right: **both
of the obvious arguments fail.**

- *"It is decorative, so drop it"* — **no.** It changes the suggested XI in 64% of squads.
- *"It changes the answer, so keep it"* — **also no.** The change is worth 0.32 xP, an order of magnitude
  inside the model's own noise.

So it cannot be settled by measuring the model. What is left is a genuine judgement about **page cost against
purpose**, and these are the facts that bear on it:

| in favour of dropping | in favour of keeping |
|---|---|
| It removes **two** controls, not one — the *Cumulative / GW-only* switch renders only when the horizon is >1 | The Lab is a page people rarely open; the pitch is the page they always open |
| The three-week view **does not leave** — the player card under a shirt already shows 3 GWs, sized per team so a blank leaves no hole | A user who has not found the Lab loses the capability entirely |
| Transfers keep their long view regardless — ADR-173's *"Longer view: +X over the next 5 GWs"* fires whenever the horizon is < 5 | The XI xP strip becomes a one-week number, and *"can I afford a −4 hit?"* is a multi-week question |
| The owner has now stated the principle twice, and ADR-175 recorded it | Testers have not yet seen either version |

**Recommendation: decide it after changes 1-3 are live**, not before. Once the Lab can hold your current
squad and show it week by week, dropping GW1–3 costs nothing; today it would strand the capability. That
sequencing is the decision this ADR *is* making — the removal itself stays open.

🧭 **Owner's lean, recorded 2026-09-03:** *"Let's hold on dropping the GW1-3, I am leaning heavily on putting
it in the Lab."*

⚠️ **One clarification that narrows the open question considerably: there is nothing to move.** The Lab
**already offers 1 · 2 · 3 · 4 · 5 · 10** (US-374, unchanged by ADR-175) — the long horizons have lived there
all along. What the Lab lacks is the ability to hold *your current squad*, which is change 2 of this ADR.

So once changes 1-3 ship, the owner's lean is **already satisfied**, and the only thing still undecided is
the narrower question: **does My Squad keep its own GW1–3 as well?** That is a question about one page's
cost, not about where planning lives — and it can be answered with testers in front of the built thing
rather than in advance.

---

### 🔧 Revision 1 — the owner's counter-proposal, and the finding that settled it

> *"Would it be cleaner to use just the emoji under the player and have a key at the bottom of the pitch to
> remind users what they mean, for both My Squad and the Lab?"*

**Yes — and surveying it before answering made the change smaller, not bigger.**

#### The finding: the split is pitch-vs-table, not My-Squad-vs-Lab

The original decision said *"the Lab shows all the flags"*. **The Lab already does — in a table, with
words.** `render_player_table` in the Lab carries a **`Trends`** column (`crowd_flags`) and a **`Set`**
column (`set_piece_flags`), sortable, already wired to `SET_PIECE_LEGEND` via `help=`, sitting a few inches
below the pitch.

So the Lab pitch carrying the market flags was **redundant with the table directly beneath it**, and the real
line was never between the two pages:

> **The pitch is a team sheet. The table is a reference.** Glyphs belong on one, words on the other — and
> that rule reads the same on both pages, so there is no per-page mode at all.

That deletes an argument from the design: `_kit_html` does not need a flag mode. **The pitch always renders
set-piece glyphs. One rule, one renderer, both pages.**

#### Why bare glyphs, and why only these three

Emoji-only is the right call *because the set was already cut to three*. Applied to today's seven it would
have been worse, not better: 💰↑ and 💸↓ are near-identical at 10px on a phone, and 💎 ⭐ 🟦 👑 is a
**four-point ordinal scale drawn as four unrelated pictures** — a reader would have to memorise an order, not
a meaning. Three role glyphs are memorable; seven market glyphs are a rebus.

`SET_PIECE_LEGEND` already exists and is already the exact copy:

> *Set pieces: ⚽ penalties · 🚩 corners · 🎯 free-kicks — shown for the **first-choice** taker (blank = not
> on set pieces).*

So the key costs one caption and no new words.

⚠️ **The honest cost, stated because it is real: on a phone, a key at the bottom of the pitch is off-screen
while you are looking at a shirt.** Three mitigations, in order of how much they actually help: the legend
sits *directly* under the pitch rather than at the page foot; each glyph carries a `title` so a desktop hover
explains it; and — the one that matters — **three is a memorisable number.** This design would not survive
seven.

---

### 🔬 Found at build time

Every one of these was found by a guard, and four of them were found by guards that were **wrong first**.

**1. The key never reached the golden page.** `set_piece_key` was added to `render_pitch` — and **My Squad
does not call it.** It draws through `render_tappable_pitch` (ADR-133), which builds the HTML itself, so the
one pitch with no key would have been the only one that mattered. The whole test suite stayed green.
**Found by mutation-testing:** deleting the caption from `render_pitch` broke nothing.

**2. Two dropdowns labelled "Squad" on one tab.** The Lab's new picker collided with the page's existing
`squad_picker` (ADR-054). A guard addressing it by label grabbed the wrong one — which is the test noticing
an ambiguity a *reader* has too. Renamed **"Start from"**.

**3. One Lab table was left cumulative.** Tightening the table guard from *"the union of all tables carries
the words"* to *"every table does"* exposed that the formation-preview table had no per-gameweek columns.
**A union asks "does any table have this?" when the requirement is "do all of them?"** — and one table
quietly answering a different question than the two above it is how a reader learns not to trust any of them.

**4. `_fixture_gameweeks` keyed by the wrong field.** Written against `team_h`/`team_a` — FPL's **numeric
ids** — then looked up by short name, so it returned an empty set for every team. That reads as *"nobody
plays"*, which would have blanked the entire breakout **while looking like a real answer**.

#### ⚠️ Three guards that were wrong, and what each got wrong

This is the part worth keeping. Each passed, each protected nothing.

| the guard | what it asserted | why a mutation walked through it |
|---|---|---|
| no words on a shirt | `">pens<" not in html` | the mutant rendered `⚽ pens` — the word *was* there, just not after `>`. **A blacklist of the words you thought of is not a test that no word appears.** Now: the span content must contain no letters at all |
| the key is printed | the source contains `"Set pieces: "` and one `st.caption` | replacing the whole condition with `if False:` leaves every string in the file. **Source-scanning tests assert that code was written, not that it runs.** `set_piece_key` was extracted so the branch is assertable, and the render is checked on the page |
| the key reaches My Squad | rendered the page, then `if no pitch: return` | a fresh AppTest has no active squad, so it hit the empty state and **returned before asserting anything**. A squad is injected now. **A test that skips is not a test that passes — and the skip is invisible in a green run, which makes it worse than a failure** |

#### 📋 The coverage gap that made this necessary

**Removing `crowd_flags` from every shirt broke no existing test.** A visible feature came off the golden
page and 1,713 tests stayed green. That is the honest measure of how much of this was protected before, and
the reason the seven new guards were each mutation-tested rather than trusted.

#### ✅ Mutation results — every guard, reverted one at a time

| mutation | caught |
|---|---|
| market flags back on the shirt | ✅ |
| words back on the glyphs | ✅ |
| the key removed from the **tappable** pitch (My Squad) | ✅ |
| the key removed from `render_pitch` (the Lab) | ✅ *(only after a second, Lab-specific assertion — two render paths need two)* |
| the key printed when nothing is flagged | ✅ |
| a blank gameweek reads as `0.0` | ✅ |
| the breakout uncapped | ✅ |
| fixtures keyed by numeric id | ✅ |
| a saved squad falls through to the optimiser | ✅ |
| each of the **three** Lab tables loses its worded columns | ✅ ✅ ✅ *(the plan table needed its own guard — it only renders in the mode the other test never enters)* |

⚠️ **A process note, recorded because it cost real time.** Two mutation sweeps produced meaningless results
before this one: the restore loop was written as `for f in $FILES`, and **zsh does not word-split unquoted
parameters**, so nothing was ever restored and mutations accumulated. The tree was repaired from backups and
re-verified. **A mutation harness needs its own check that the restore worked** — every sweep here now
re-runs the clean suite between mutants.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:**
  - The pitch reads as a team sheet again; the market lens moves to the pages built for it.
  - The Lab becomes useful between wildcards, which is the difference between a page and a feature.
  - Blanks and doubles become visible where planning happens, instead of being averaged away.
* **Negative Impact / Trade-offs:**
  - A flag someone used on the pitch now costs a page change. Mitigated: every one of them is *named* on
    Trending/Signals rather than shown as a glyph.
  - The Lab gains a mode, and a page that does two things is harder to explain than one that does one.
  - Per-gameweek columns are wider than a total — they must scroll on a phone, not wrap.
* **Risks & Mitigations:**
  - **Risk:** "Current squad" in the Lab drifts toward the declined path-search. **Mitigation:** it is stated
    here as a read; any optimiser over it needs new evidence and its own ADR.
  - **Risk:** per-gameweek columns invite over-reading week 5. **Mitigation:** the breakout is capped, and
    labelled with the gameweek, so a blank shows as a blank rather than a zero.
  - **Risk:** removing crowd flags from the pitch is judged wrong by testers. **Mitigation:** it is one
    argument to the kit renderer — reversible in a line, and the Lab keeps the full set as the reference.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`pitch.py`, `views/squads.py`, `pages/1_My_Squad.py`), Tests, Docs
* **Action Items:**
  - [x] `_kit_html` renders set-piece **glyphs only** — one rule, both pages, **no flag mode argument**
  - [x] `SET_PIECE_LEGEND` as one caption under the pitch on both pages (the constant already exists)
  - [x] A `title` on each glyph, so a desktop hover explains without the key
  - [x] Guard: no crowd/market flag reaches **any** pitch, and no flag renders its word on a shirt
  - [x] Guard: the Lab's `Trends` + `Set` **table columns keep their words** — the reference copy stays
  - [x] Lab squad picker — Current squad · New squad · saved squads
  - [x] Guard: picking "Current squad" reads the stored squad and does **not** run the optimiser over it
  - [x] Per-gameweek xP columns in the Lab, breakout capped, blanks shown as blanks not zeros
  - [x] Guard: the per-GW columns sum to the cumulative total (ADR-032's invariant, asserted on the surface)
  - [x] **Mutation-test every new guard** — revert each one at a time, confirm red
  - [x] Preview → owner sign-off before build (the ADR-175/176 loop)
  - [ ] ⏳ **GW1–3: leave in place.** Revisit once 1-3 are live and testers have used them
  - [x] Update PROJECT_STATUS, the Roadmap, and a sprint retro

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
The Lab's **"Squad name"** field changes from a text input to a picker — a control a person could be told to
go and find, so it is in scope.
- [x] Checked Home, Help and the marketing scripts — **no hit**. The only other `"Squad name"` is My
      Squad's **Rename** field, a different control, and its two tests were verified still to target
      it (both run; neither silently skips).
- [x] Nothing added to `RETIRED` — no *user-facing* phrase was retired. The Lab's field was relabelled
      **Name this squad** and gained a sibling **Start from**; no doc or script names either.
- [x] Checked — the two tests matching `"Squad name"` target My Squad's Rename field, unaffected.

---

### 🔄 Review & Reconsideration
* **Review Date:** 2026-10 (after tester feedback on the Lab)
* **Triggers for Reconsideration:**
  - [ ] Testers report missing the crowd flags on the pitch — one argument reverses it
  - [ ] The GW1–3 gate is decided either way (this ADR is amended, not superseded)
  - [ ] A double/blank gameweek arrives and the per-GW columns are read in anger for the first time

---

### 🔗 References & Related Artifacts
- **Continues:** [ADR-175](./ADR-175-value-above-the-fold.md) (the pitch/Lab division of labour)
- **Holds the line drawn by:** [ADR-132](./ADR-132-transfer-timing.md) (path search declined on evidence)
- **Data from:** ADR-032 (`by_gameweek`), ADR-081 (set-piece flags), ADR-057 (crowd flags)
- **Noise baseline:** [ADR-161](./ADR-161-head-to-head.md) — one starter's single-GW spread, sd 3.51
