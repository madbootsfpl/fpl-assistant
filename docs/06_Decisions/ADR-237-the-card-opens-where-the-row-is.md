# ADR-237 — The card opens where the row is

**Date:** 2026-09-22
**Status:** Accepted
**Completes:** the audit's §6 *"search, compare, the card"*
**Builds on:** ADR-109/110, ADR-236

---

## Context

The Hub's Predictions and Price-change lists expand **in place**: tap a row and it unfolds into position,
price, ownership, per-game and a fixture strip.

⭐ **That is the right shape.** A list you can interrogate without leaving it beats one that sends you
somewhere and loses your place in it — which is what a separate card screen does, and what makes a browse
list feel like a filing cabinet.

Our Players tab had search and nothing behind a tap. The audit has owed *"the card"* since §6.

## Decision

**`POST /api/v1/player`, expanding inside the row.** Three blocks, because a reader has three different
questions about a name on a list:

* **the run** — first, and with **fixture difficulty**, because *"is he good, or is this an easy month?"* is
  usually what a row is opened to ask, and a projection alone cannot answer it
* **the last five** — points **and minutes**
* **the season stats**, in two columns

⭐ Fetched **on expand**, never with the list. The market is 481 players; carrying every stat for all of
them so that one can be opened is the opposite of the trade the list was built on (ADR-230).

### ⭐⭐ The stats are ordered for the position

A defender's card leads with **expected goals conceded** and **DefCon**; a forward's with **goals** and
**xG involvement**. That ordering has existed since ADR-084 and had never reached a phone.

⚠️ *The same twelve numbers in the same order for everyone is a table, not a card* — and it buries the one
the reader opened the row for.

### Difficulty colours the fixture, not the player

The fixture chips use the FDR palette. ⭐ **This is not ADR-179 reversed**: that declined colouring the
*player card* by points, and this colours an *opponent* by difficulty. A hue about the fixture, sitting
beside a number about the player, is the distinction ADR-179 was protecting rather than the one it refused.

---

## ⚠️⚠️ The branch this snapshot cannot reach

`stat_rows` drops a stat with no value, so a card never shows a dash. A mutation removing that filter
**survived** — and the reason is worth recording.

**Measured: no stat is missing for any player in the snapshot.** The store fills every numeric column, so
the filter is unreachable through the API and the mutation was behaviourally identical.

⭐ *An unreachable branch is not a safe branch; it is an untested one.* And it is **not dead code** — FPL
returns nulls for a player who has yet to play; this snapshot simply has none. Pinned with a direct,
constructed test instead.

That is the **eighth** time this project has been caught by *does the population contain the case?*

## Verification

* **5/5 mutations killed**, including *every position gets the same card* and *the card loses fixture
  difficulty*.
* The position test is constructed by position rather than sampled: whether the first two players in the
  seed differ in position is an accident.

## Consequences

**Good:** the audit's first release is complete — *This week · My squad · Transfers · Players*, with search
**and** the card. One stat catalogue serves the web card, Boot Battle and the phone.

**Costs:** ⚠️ `/player` needs the raw history for the form strip, so it is not a cheap call. It runs once
per expansion.

**Open:** ⭐ **tap two rows to battle them.** Boot Battle is now an endpoint and the Players list has
selection-shaped rows; that is the audit's *"compare"*, and the last piece of §6 still missing.
