# ADR-358 — The match timeline we cannot build

**Date:** 2026-10-18
**Status:** Parked — *a decision recorded, not work deferred*
**Raised by:** tester feedback — more match stats, *"like flashscore"*
**Owner's call:** *"park the stats slice and gate it properly"*

---

## The request

A tester sent two screenshots of Flashscore's match summary: a minute-by-minute timeline — *44'
Lewis-Potter (Thiago)*, *45+8' red card*, *46' Schade for Ouattara*, *41' Penalty overturned (VAR)* —
behind tabs for **Summary · Report · Stats · Lineups · Player Stats**.

## 🔴 The finding that settles it: our data has no timeline in it

FPL's per-fixture `stats` is **aggregate counts per player**, and nothing else:

```
goals_scored     away: id156×2
assists          away: id148×1
yellow_cards     home: id21×1, id229×1, id244×1      away: id40×1, id151×1, …
saves            home: id226×4
bonus            away: id156×3, id148×2, id28×1
bps              away: id156×64, id148×35, …
defensive_contribution …
```

⚠️⚠️ **No minute markers. No substitutions at all. No VAR. No lineups.** Every single element of the
screenshots is absent — not hard, *absent*. Flashscore pays a sports-data provider for that feed.

⭐⭐ So this is not a question of effort or taste. **Matching that screen means buying and maintaining a
second data source**, to reproduce what a free app already does better, funded by the advertising visible
in the tester's own screenshot. 🔴 That is a business decision with a recurring cost, and it is the one
thing this ADR rules out rather than parks.

## 📌 What we have that Flashscore does not

Two fields, and they are the two that decide an FPL manager's weekend:

* **`bonus`** — the 3/2/1 awarded after the match
* **`bps`** — the underlying score that decides it, visible *before* the bonus settles

No general livescore app carries either. ⭐ *The asymmetry runs the other way from the request.*

## The parked slice

ADR-346 already states the strategy — ***"the join is the feature.** A scoreline is a commodity; what
nobody else can print is 'CHE 5-1 BOU — your João Pedro scored twice'."* The on-strategy move is to
**deepen that join**, not to add a timeline beside it: per match, for **your** players only, what they
actually did — goals, assists, cards, saves, **bonus and BPS**.

Free, from a payload already fetched every tick, and the one thing a tester genuinely cannot get on
Flashscore.

## ⏳ Why it is parked rather than built

⚠️ It is a **card-layout change to the screen rebuilt twice in a week**, and both rounds needed the
owner's eye — *"its duplicated and not well laid out"* was the verdict on the first attempt, and the
chosen design came from three mocked options, not from the first thing built.

📌 So the gate is: **a mock before any code**, and a decision on where it lives — inside the match card,
or behind a tap. ⭐ *The last two layout rounds were settled by looking, and nothing about this one is
different.*

## Explicitly not decided here

- whether a second data provider is ever worth it (ruled out **for this**, not forever)
- whether bonus/BPS belong on the Scores card or the player sheet
