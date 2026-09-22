# ADR-238 — A directory holds more than a menu, and a hidden filter has to say what it is set to

**Date:** 2026-09-22
**Status:** Accepted
**Completes:** the last of the five changes drawn from the competitor review
**Builds on:** ADR-166 (the sidebar, cut 12 → 9 by frequency), ADR-228 (More), ADR-230 (the bottom bar)

---

## Context

Two things from the Hub's app, which the testers use as their benchmark.

**Their More screen carries six destinations without feeling like a junk drawer.** The owner spotted why
before I did — *"very smart way of cramming a lot more functionality into the app without clutter."*

⭐⭐⭐ **The mechanism is the one-line description under each name.** It is not a menu, it is a *directory*.
A menu asks you to guess what a noun means; a directory tells you, so it can hold more entries without
costing more to read. You scan four sentences instead of gambling on four words.

Ours could not do that, because half of it was not destinations. `MoreView` mixed a text field, a
free-transfer stepper and a feedback box in among two links. ⭐ **A row you *change* reads nothing like a
row you *enter***, and interleaving them means neither reads as anything.

**Their filter chips state their value** — `Position: Any`, `Gameweek: 6–11`. Ours showed the options and
highlighted one.

## Decision

### 1. More becomes a directory; the controls move one tap deeper

Four rows, each an icon, a name, a sentence and a chevron: **Signals · Chips · Tell us something ·
Settings**. Everything that was a control is now behind **Settings**; feedback got its own destination.

⭐ **Frequency decides depth** — the same rule that ordered the bottom bar in ADR-230. Free transfers change
at most weekly; the screens they affect are opened daily. Paying one extra tap for the weekly thing to
un-clutter the daily one is the trade the whole navigation is built on.

⭐ **Feedback is a row of its own and is deliberately *not* also inside Settings.** Settings is where you go
having decided to change something; feedback is where you go having just seen something. Two doors to one
room drift apart — ADR-184 is that lesson with six surfaces.

⭐⭐ **The Settings row states its own current value** — `Manager 2885974 · 2 free transfers · this
gameweek's numbers`. A directory entry that answers the question most people open it to check has done its
job without being opened. *Showing the state beats offering the options*, which is the same idea as §2.

### 2. A value-showing filter, where a value-showing filter earns its place

⭐⭐ **Not everywhere.** Position has five options, they all fit on the row, and highlighting one of five
already says what is on — turning that into `Position: Any` would trade one tap for two and buy nothing.

**Price is the opposite case**: sixty values, so it *has* to hide behind a tap — and the moment a filter is
hidden, the chip is the only place its setting can live. A list silently showing a third of the market
while its controls look untouched is the failure this prevents.

So: the position chips stay as they are, and a new `Price: any` / `Price: under £8.0m` chip opens a sheet.
⭐ *The lesson is not "copy the pattern", it is that the pattern is true where the options do not fit.*

**The empty state names the filters that emptied it** — *"Nobody matches "sal" + MID + under £5.0m."*
"Nobody matches that" makes a reader hunt for what *that* was.

## What building it found

⭐⭐ **Splitting the screen introduced a bug that looked like nothing.** A pushed route is built from values
captured when it was pushed, so the stepper — reading `freeTransfers` straight off its constructor — told
the parent and **redrew nothing**. The highlight stayed where it was while every number underneath was
correct. *A control one route away from its state has no way to hear that the state changed.* Settings owns
its copy now, and a widget test asserts the tapped number lights up.

⚠️⚠️ **The price sheet clipped its most expensive options on a short screen.** Eight rows in a fixed
`Column` fit the phone I was picturing and overflow a bottom sheet capped at a fraction of a smaller one —
and the rows that fall off the bottom are `under £10m` and `under £12m`, so the filter would have quietly
lost premiums for exactly the managers browsing them. ⭐ **Found by a widget test running at 800×600**,
which is smaller than any phone I had in mind and therefore the only size that asked the question.

⚠️ **`null` is a legitimate answer here**, so *"chose Any price"* and *"tapped outside the sheet"* pop the
same value. Without a sentinel a dismissal silently clears the filter; there is a test for the dismissal,
because that is the half nobody tries by hand.

### ⭐⭐⭐ The measurement was of the wrong artefact, and it was confidently wrong

`players_view.dart` tells a reader the board is fetched once because it is small enough to be — *"the whole
ranked market is ~110 KB."* ⭐ **A number in prose is an untested claim** (ADR-212, learned on a README
claiming 121 ADRs against 212), so this change put the sample on disk and wrote the guard.

The sample was **168.7 KB**. I corrected the comment to ~120 KB.

**The test I had just written then failed my correction**: the wire carries **96 KB**. The committed sample
is indented and key-sorted for a human to read, which makes the *file* 76% larger than the *response* it
documents. ⚠️ **The original ~110 KB had been right, and I replaced it with a worse number using a
measurement of the wrong thing.**

⭐⭐ **A measurement of the wrong artefact is confidently wrong, not noisily wrong** — nothing about
`stat().st_size` looks approximate. It is the same shape as ADR-183 (*a measurement of a nondeterministic
process is not a measurement*) and the `chmod 444` probe that broke the fix it was testing: **the
instrument was the fault, and the reading looked fine.** Both size tests now measure the compact encoding,
and say in the code why.

## Consequences

* Free transfers are two taps from the pitch instead of one. Accepted, and stated above rather than
  discovered later.
* `players.json` joins the committed samples at 169 KB on disk — the biggest by a factor of ten, which is
  the point: the size of that response is a fact the app's design depends on, so it is now under test.
* More has room to grow. ⚠️ **That is a hazard as much as a feature** — ADR-228's argument that this is not
  a drawer for everything the web app can do does not weaken because the rows now scroll nicely.

## Verification

* **9 widget tests** across the directory, the Settings state and the filters — widget tests because the
  claims are about what a reader *sees*, and a model-layer test would leave ADR-238's whole argument
  unguarded.
* **9/9 mutations killed**: a description downgraded to a label; every row sharing one destination; the
  Settings row hiding its value; the stepper never updating its copy; the chip rendering no value; the
  sentinel removed so a dismissal clears the filter; the price filter never applied; the empty state
  omitting one active filter; and the empty state naming nothing.
* ⚠️⚠️ **Three mutations first reported SURVIVED and had never applied** — `dart format` had reflowed the
  indentation my patches matched on, and the patches carried no assert. Two more reported *broken harness*
  because the gate treated an `info`-level style lint as a compile error. ⭐ **Four of nine results in the
  first sweep were about my harness rather than my tests**, which is the third time this pattern has cost a
  sweep: *a mutation run that cannot detect its own no-ops reports confidence.*
* **3 mutations** against the Python size guards, including the exact instrument error above.
