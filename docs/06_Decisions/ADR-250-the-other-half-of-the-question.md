# ADR-250 — The other half of the question

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"Need Player DNA too — there's real estate on the More tab."*
**Builds on:** ADR-118 (the eight axes), ADR-247 (Team DNA), ADR-249 (the glossary)

---

## Context

ADR-247 shipped Team DNA and said Player DNA was *"the obvious next home."* The owner agreed before the ink
dried, and spotted the room himself.

⭐ They are the two halves of one question: **what kind of player is he**, and **what kind of side is he
in**. A club's fingerprint decides between two players from different teams; a player's decides between two
players in the same one.

## Decision

**`POST /api/v1/player-dna`** — the eight axes, insights, and the last five appearances, for one player.

### ⭐⭐ Ranked within his position, never across the league

A defender's attacking threat and a forward's are not the same question. Ranked together, **every defender
would look poor at a thing defenders are not asked to do** — ⚠️ *a single scale across incomparable roles
is a ranking that flatters and punishes by position.*

### ⭐⭐⭐ The field travels with the place in it

`pool_size`, `min_minutes` and `low_minutes` come back with every fingerprint, and the screen prints them:
*"Percentile among 10 MID with 450+ minutes."*

⚠️ **On this board that pool is ten players.** *"84th percentile"* alone invites a reader to believe a
great deal more than ten midfielders can support — and a percentile is only as meaningful as the field it
was measured in.

⭐ A player **below** the minutes floor is ranked anyway and captioned, rather than excluded (ADR-118).
Dropping him would lose exactly the player a manager is actively considering; *the honest move is to answer
and caption the answer.*

### It opens on your captain

⭐ Not an empty picker. *A screen that asks a question before it has said anything* wastes the one thing a
phone has less of than a desktop — and the captain is the pick a manager is least willing to be wrong
about.

### The bars are shared

`DnaBars` moved out of `team_dna_view.dart` **the moment there was a second caller**, not before. ⚠️ A
private copy in each view is how two screens showing the same eight numbers start colouring them
differently — and the colours carry meaning here (top quartile, middle, bottom), so a divergence would be a
divergence in *what the app says*, not just how it looks.

## What building it found

⚠️ **A player search was half-written on this screen and cut rather than left in.** It needs the whole
board fetched — a second round trip on a screen that already makes one — and the question *"what kind of
player is he?"* is asked about someone you are already deciding on. ⭐ *Shipping the half that works beats a
picker that loads twice to answer the same question.* 📌 Search is owed when this screen can be reached
from the Players tab.

⭐⭐ **`test_player_shape.py` caught the new endpoint again**, as it did for Team DNA one ADR ago. This one
goes into the sweep **proper** rather than into `NO_PLAYERS`: a fingerprint comes with its player, and that
summary is exactly the sort of field a raw 45-column database row leaks through.

## Consequences

📌 **Still owed from this round of feedback:** Team DNA parity — the radar, the grade ring, club-vs-club
compare, next-6 fixtures with form, and the key-players table.

⚠️ **On the radar specifically**: the phone draws bars deliberately, and the owner's own screenshot of the
web page *on his phone* shows "FPL Output" clipped to "'PL Output" at the left edge. The proposal on the
table is **radar plus bars**, the way the web does it — not radar instead of them.

## Verification

* **7 tests**: all eight axes present and in range; the pool reported; **peers counted against the board**
  per position rather than trusted from a label; a fringe player ranked and captioned; the run included;
  and an unknown or absent id refused by name.
* **5/5 mutations killed**: the pool hidden; a thin sample not captioned; the run dropped; an unknown id
  quietly answered about someone else; and the fingerprint truncated to four axes.
