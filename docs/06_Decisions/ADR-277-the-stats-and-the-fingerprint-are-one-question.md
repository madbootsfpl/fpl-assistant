# ADR-277 — The stats and the fingerprint are one question

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"can we merge Players and Player DNA, just put the DNA under the player stat when
selected in player tab & remove the Player DNA from the 'More' tab"*
**Merges:** ADR-247 (Player DNA) into ADR-236 (the player card)

---

## Context

Two screens, two directory entries, one subject. ⭐ **The stats say what he has done; the fingerprint says
what kind of player does that** — and reaching the second meant leaving the first.

⚠️ *Two places to learn about one player is one place too many*, and the app was asking a reader to hold
a stat line in their head while navigating away from it.

## Decisions

**The fingerprint renders under the stats when a row is expanded**, and **Player DNA leaves More.**

**⚠️ Fetched separately, and deliberately not folded into `/player`.** The card is fetched on **every**
expand; the fingerprint ranks him against a whole position pool. ⭐ *Widening an endpoint everyone calls
to serve a panel below the fold is how a fast list becomes a slow one.*

**⚠️ No header inside the card.** The row above has already named him — ⭐ *a screen that names a player
twice has two headings and one subject.* `PlayerFingerprint` became public with a `showHeader` flag
rather than being copied, because ⚠️ *two renderings of one fingerprint drift apart* (ADR-184).

**⭐ A failed fingerprint loses the fingerprint, never the card.** The stats are the reason the row was
expanded.

📌 **Team DNA stays in More.** It is a different question about a different subject — *which club a player
belongs to* is not *what kind of player he is* — and it has no row to live under.

## ⚠️ The widget had no fixture

Rendered in one place and tested through that screen, `PlayerFingerprint` had **no committed sample**.
Shown in two places that becomes a real gap: ⭐ *a widget shown in two places needs a fixture, or only one
of them is ever tested.* `player-dna.json` now ships with the others.

## Verification

* **5 widget tests** — the header appears on its own screen and **not** inside a card, the axes draw
  either way, an **unranked** player is explained rather than shown as an empty shape (*an empty radar
  reads as "he is bad at everything", a claim nobody made*), and More no longer offers the row while
  keeping Team DNA.
* **4/4 mutations killed.**
* ⚠️ The test helper had to be split: `MoreView` is **itself a `ListView`**, so a scrolling wrapper nests
  two unbounded scrollables — ⭐ *a test helper that suits one widget is not a test helper.*
* 2,572 Python · 254 Dart.
