# ADR-251 — The run, the form, and who to buy

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"DNA — need all of the features"*, with screenshots of the web page
**Builds on:** ADR-126 (last season when this one cannot rank), ADR-128 (form), ADR-247 (Team DNA)

---

## Context

ADR-247 shipped the fingerprint. The owner's screenshots showed what sits beside it on the web and does
not on the phone: the **next six fixtures**, the **W/D/L form**, and the **key-players table**.

⭐ They are the reason a manager opens a club page at all: *where is it going, how has it been going, and
who do I buy.* The fingerprint answers what a side **is**; these answer what to **do** about it.

## Decision

`team-dna` now carries `fixtures` (six), `form`, and `key_players` per club.

### ⭐⭐ Six, where the pitch card shows three

`DNA_RUN = 6` sits beside `RUN = 3` as a separate constant. ⚠️ *They are separate because they answer
separate questions, not because one of them was forgotten* — a club's run is a longer horizon than a
player's next card.

### ⚠️⚠️ The key-players table names its season

The ranking needs ~900 minutes. It is September, and the board's best player has **450**. So the table is
**last season's** (ADR-126) — and it says so, with the reason: *"Ranking needs ~900 minutes, so this
season's table fills from about GW10."*

⭐ **A table from a different season that does not say so is the most quietly wrong thing on a page.** A
manager reads it as current form and buys on it. Everything else on the screen would be right.

### The helpers moved out of the Streamlit package

`team_key_players` and `key_players_this_or_last` lived in `web_streamlit/team_dna_card.py`, which imports
Streamlit — so the API could not reach them. They are pure analytics and are in `analytics/team_dna.py`
now, **re-exported** from the card so the page and its tests are untouched.

⚠️ **Moved verbatim, not retyped.** This project has paid for retyping a moved thing once: a shirt-URL
template lost its `-66` suffix in transit and every kit on the pitch broke. ⭐ *A move is a cut and a
paste; anything else is a rewrite wearing a move's name.* There is a test asserting the web's names are the
**same objects**, not a second copy.

## What building it found

⚠️⚠️ **A mutation that blanked every season label passed the first test**, because that test asserted the
clubs **agreed** with each other — and "all unlabelled" is perfectly consistent. ⭐ *An assertion about
agreement says nothing about truth.* It now decides from the board whether this season can rank anyone,
and requires the label to match.

⚠️ **I patched the wrong `fromJson`.** `ClubDna` and `PlayerDna` have byte-identical insight-parsing
blocks, so an anchor that looked unique was not. ⭐ *In a file of parallel models, the safe anchor is the
line that differs, not the line that reads like the one you want.*

⚠️ The payload ceiling moved from 40 KB to 80 — **16 KB → 41 KB** with the new content. ⭐ *Raising a
threshold to make a test pass is how a limit stops being one*, so the number that prompted it is written
into the failure message: the next person to hit it should ask whether the page should still be one fetch.

## Consequences

📌 **Still owed:** the **radar**, the **grade ring**, and **club-vs-club compare**.

⚠️ On the radar, the evidence is the owner's own screenshot of the web page **on his phone**: "FPL Output"
is clipped to `'PL Output` at the left edge. ⭐ *A layout that fails on the device you are porting it to is
not a layout to port* — the proposal is radar **plus** the bars, as the web does, not radar instead.

## Verification

* **13 tests**, including one that fails if the clubs disagree about the season **and** one that fails if
  the label is wrong rather than merely uniform.
* **5/5 mutations killed**: the season label dropped; the run cut to nothing; form inventing a result
  letter; the tables emptied; and the re-export replaced by a second implementation in the web package.
