# ADR-269 — A widget that ignores the colour you set

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner's fourth round of phone feedback, with screenshots
**Fixes:** ADR-266 (Trending), ADR-267 (Mini-leagues), ADR-265 (the ticker)

---

## 1. ⚠️⚠️ Four rows of choices shipped invisible

`ChoiceChip` rendered as **blank white blocks**. Material 3 ignores `backgroundColor` for the *unselected*
state and paints its own near-white surface, so a `white54` label sat on white.

⭐ **A widget that ignores the colour you set is worse than one that has none** — it fails only in the
state you are least likely to screenshot, and the *selected* chip looked perfect in every check I made.

⚠️ **The rest of the app had always hand-built these pills, and those rows were the ones that looked
right.** I reached for the framework widget on a new screen and got a different answer to the same
question. So there is now a named `Pill`, used everywhere, and the chips are gone.

📌 The test measures the pill **composited over the page**: `computeLuminance()` ignores alpha, so
`white10` reads as pure white. ⭐ *A test that reads a colour without its background measures a colour
nobody sees* — and it passed against the bug before that was fixed.

## 2. ⭐⭐ Worth a Look leads Trending

*"Missed the 'Worth a Look' analysis — most important information from this section. It should lead,
first tab."*

ADR-167's convergence board — players standing out on **two or more** stat boards at once, each with its
evidence. ⭐ **It is also the only board here that is about the *player*.** The other four are facts about
other managers, and ⚠️ *leading with the crowd taught the screen to be read as a popularity chart* —
exactly the framing ADR-150 ranks last.

⚠️ **It came back empty first, and that was a wrong source rather than an honest null.**
`get_gw_history_by_code` (this season's gameweeks) was read where `get_history_by_code` (past seasons) was
meant. It returned **667 codes and zero last-season rows**, so the rate boards ran on five gameweeks of
minutes, cleared nothing, and the board answered *"nobody stands out"* — ⭐ *a wrong source that returns
plenty of data fails as an empty answer, not as an error*, and this is a board designed to say exactly
that sentence truthfully.

**The reasons are the board.** A convergence list without its evidence is a ranking on a number nobody can
see — and this board deliberately has no such number.

## 3. The ticker promised a tap it did not have

*"Says tap a club to see the run in full — nothing happens when you do. What does the * mean?"*

⚠️ **Both halves are the same defect as ADR-263.** The header advertised an interaction that was never
built, and the asterisk was a mark with nowhere to look it up. ⭐ *A UI claim that is wrong is worse than
a missing feature, because it sends the reader looking.*

Now: the tap opens the club's full run, a **legend** shows the five bands and says `CHE* = away`, and a
blank gameweek is spelled out in words where there is room for them.

⚠️ **And a real bug fell out of testing it.** `TickerCell.label` was built only from the `opponents` list
and returned an **empty string** for a cell carrying the singular `opponent` — a fixture that exists,
rendered as nothing. ⭐ *A derived field that silently returns empty is worse than one that throws*,
because the screen still lays out a row for it.

## 4. More, This Week, and the rival picker

**The "On the web" block is gone** — ⚠️ it had become wrong twice over, advertising the fixture ticker and
Squad Lab as surfaces the web carried when ⭐ *both are now in this app*. Two paragraphs of philosophy were
also pushing the last directory row below the fold: *an option you have to scroll to find is an option
most people never see.* The mantra stays, in the brand's orange.

⚠️ **I over-trimmed the Help row** and took *"Opens madboots.streamlit.app"* with the clause the owner
named. `test_help_link.py` caught it: *tapping a list item and landing in Safari is a surprise unless it
was announced.* ⭐ The guard then had to be repaired itself — its regex assumed no comment between `name:`
and `why:`, so it reported *"the Help row is gone or renamed"* about a row that was present. ⚠️ *A guard
that fails for its own reasons teaches people to edit the guard.*

**This Week's cards are bordered by what they mean.** Confidence gets a **whole** border rather than a
3px left rule — ⭐ *a rule reads as decoration; a border reads as a verdict on the card it encloses*, and
this card's colour **is** the verdict. Edge and Risk gain borders, Lineup/Transfer/Timing gain one always
rather than only when highlighted (⚠️ *transparent-when-not is the same as none*), and **Risk is always
red**: ⭐ *severity belongs in the line — "doubtful, 75%" — not in the frame around it.* Three new glossary
terms so every heading has a (?), generated from `src/glossary.py` as ever.

**The rival picker is a dropdown.** ⚠️ A league holds fifty managers and a swipe strip showed four —
*an option you have to swipe to discover is one most people never learn is there*, which made the
head-to-head look like it only worked against the top of the table.

## Verification

* **12 Dart tests**; **5/5 mutations killed** — ⚠️ one survived and turned out to be **dead code**: the
  `signals` branch of `trendValue` could only differ above a thousand, and a signal count is at most four.
  Deleted rather than tested. ⭐ *Defensive code for a case that cannot arise is untested code that looks
  tested.*
* Two existing Python tests had to name the board they meant, because the **default moved** — ⭐ *a test
  that depends on a default is a test that breaks when the default changes, which is a fact about the
  test.*
* 2,553 Python · 208 Dart.
