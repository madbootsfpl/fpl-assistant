# Sprint 239: Plan in the Lab, play on the pitch (ADR-178)

**Dates:** 2026-09-03
**Status:** ✅ Complete — ADR-178, three of four changes. **1713 → 1720 tests, ruff clean.**
⏳ **GW1–3 on My Squad remains gated** at the owner's request.

> **Owner:** *"The players on the pitch have a lot of emojis under them in some cases which can become too
> much… and in the Lab have them all for planning purposes."*
> Then, at the preview: *"Would it be cleaner to use just the emoji and have a key at the bottom of the pitch,
> for both My Squad and the Lab?"*

---

### 🔧 What shipped

**The pitch carries set-piece glyphs and nothing else** — `⚽ 🚩 🎯`, no words — with one key beneath it, on
both My Squad and the Lab. **The Lab starts from a squad you already own**, not only from nothing. **Every
Lab table shows a score per gameweek**, not one cumulative total.

---

### 💡 The lesson

> **Surveying the counter-proposal made the change smaller.**

ADR-178 first said *"set pieces on the pitch, all the flags in the Lab."* The owner's *"why not glyphs plus a
key, on both?"* prompted a look at what the Lab actually renders — and **it already had every flag, in a
table, with words**, a few inches under its own pitch. So the Lab pitch carrying market flags was redundant
with the table beneath it, and the line was never between the two pages:

> **The pitch is a team sheet. The table is a reference.** Glyphs on one, words on the other.

That deleted an argument from the design — `_kit_html` needs no flag mode. **One rule, one renderer, both
pages.** The counter-proposal was cheaper than the proposal, and only because it was checked against the code
before being answered.

The narrower craft point: **glyphs work here only because the set was already three.** Applied to the
original seven they would have been worse — 💰↑ and 💸↓ are near-identical at 10px, and 💎 ⭐ 🟦 👑 is a
four-point ordinal scale drawn as four unrelated pictures. Three role glyphs are memorable; seven market
glyphs are a rebus.

---

### 🔬 Guards that were wrong — the real story of this sprint

**Removing the market flags from every shirt broke no existing test.** A visible feature came off the golden
page and 1,713 tests stayed green. Everything below follows from that.

**The key never reached My Squad.** It was added to `render_pitch`; My Squad draws through
`render_tappable_pitch`, which builds its own HTML. The only pitch without a key would have been the only one
that mattered — **found by mutation-testing, not by reading.**

And three guards written *for this ADR* passed while protecting nothing:

- **A blacklist of words is not a test that no word appears.** `">pens<" not in html` passed against a mutant
  rendering `⚽ pens`. Now the span content must contain no letters at all.
- **A source-scanning test asserts that code was written, not that it runs.** Replacing the whole condition
  with `if False:` left every string it grepped for. `set_piece_key` was extracted so the branch itself is
  assertable.
- **A test that skips is not a test that passes.** A fresh AppTest has no active squad, so the page hit its
  empty state and the guard returned before asserting anything — and **the skip is invisible in a green run,
  which makes it worse than a failure.**

Two more found by tightening: **a union asks "does any table have this?" when the requirement is "do all of
them?"** — which exposed a third Lab table left cumulative. And `_fixture_gameweeks` was keyed on
`team_h`/`team_a`, FPL's **numeric ids**, then looked up by short name: an empty set for every team, i.e.
*"nobody plays"*, **blanking the whole breakout while looking like a real answer.**

---

### ⚠️ A harness bug worth not repeating

Two mutation sweeps produced meaningless output before the real one: the restore step was `for f in $FILES`,
and **zsh does not word-split unquoted parameters**. Nothing was ever restored, mutations accumulated, and
the second sweep's "failures" were the first sweep's damage. The tree was repaired from backups and
re-verified.

**A mutation harness needs its own check that the restore worked.** Every sweep now re-runs the clean suite
between mutants.

---

### 🧭 Still gated: GW1–3 on My Squad

Held at the owner's request. He is *"leaning heavily on putting it in the Lab"* — and one clarification
narrows what is actually open: **there is nothing to move.** The Lab has offered 1 · 2 · 3 · 4 · 5 · 10 since
US-374. What it lacked was the ability to hold your current squad, which shipped today.

So the lean is already satisfied. The only open question is the narrower one — **does My Squad keep its own
GW1–3 as well?** — and the measurement says it cannot be settled by measuring the model: the XI differs in
**63.7%** of squads, but fielding the GW1–3 XI costs **0.32 xP**, an order of magnitude inside the model's
own noise. A judgement about page cost, best made with a tester in front of the built thing.
