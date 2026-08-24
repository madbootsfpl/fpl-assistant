# Sprint 173: "Upcoming" means the gameweeks you can still act on (ADR-123)

**Dates:** 2026-08-23
**Status:** ✅ Complete — ADR-123. A live GW1 correctness fix, found while checking the first real data refresh.
1105 → 1115 tests. Ruff clean.

> **Owner:** approved the kickoff-time fix ("yes do (a)"), then the whole-gameweek refinement ("do a'") once
> building the first version showed why it was wrong.

---

### 🐛 The bug — the engine did not know GW1 had happened

GW1 was played 21–23 Aug and the data was refreshed on the evening of the 23rd. Every fixture-forward
calculation still treated GW1 as upcoming.

`Storage.get_upcoming_fixtures` filtered on `WHERE f.finished = 0`, assuming FPL flips `finished` when a match
ends. Checked live against `/api/fixtures/?event=1`, two days after the opening match:

```
ARS 3-0 COV  (Fri 21st)   finished=False  finished_provisional=True  started=True
NEW 2-2 LIV  (Sun 23rd)   finished=False  finished_provisional=True  started=True
```

FPL sets `finished_provisional` at full-time and holds `finished` back until the gameweek's bonus is confirmed.
So for the two-to-three days a gameweek is in flight, **every played match reads as upcoming** — and all 380
fixtures came back. A "next 3 gameweeks" projection was spending one of them on football already played, across
~18 call sites (xP horizon, fixture ticker, transfer planner, captain pick). `next_deadline` (ADR-086) was
unaffected — it derives from `kickoff_time` — so the countdown banner was right while the engine beneath it was a
gameweek behind.

---

### 🔁 The mid-build correction — fixtures → gameweeks

The approved fix filtered **per fixture**: drop a match once its own kickoff passes. Built, and it exposed why
that is the wrong unit. A gameweek is played over several days, so cutting fixture by fixture leaves a **stub
gameweek** at the head of the horizon — GW1 with one match left, belonging to CHE and FUL:

```
upcoming GWs:  [(1, 1), (2, 10), (3, 10), (4, 10)]
```

Two callers broke immediately, both from the same root cause — *"the next gameweek" ≠ "every team's next
fixture"* once teams are out of sync:

- **The player card's per-GW row** counts 3 fixtures *per team*; the horizon counts gameweeks *globally*. A team
  that had played was on GW2–4 while a 3-gameweek horizon reached only GW3 → the third cell rendered `0.0`.
- **The captain double** applies to `gameweeks[0]` = GW1, whose deadline went on the Friday. Every captain whose
  team had played earned a **0.0 double**, and the "next gameweek only" caption vanished.

The second is the tell: you cannot transfer, captain or bench for a gameweek whose deadline has passed, so
patching each consumer to route around it treats the symptom. **The deadline is the honest line** — it is exactly
the line between "still deciding" and "already decided". Whole gameweeks in or out; every team stays on the same
one; both defects disappear instead of needing a patch each.

---

### 🔧 What shipped

**`Storage.get_upcoming_fixtures` (ADR-123).** Keeps `finished = 0` (still authoritative once FPL sets it) and
adds a deadline cutoff that admits or excludes a gameweek whole — `event NOT IN (gameweeks whose earliest kickoff
is at or before now + 90 min)`. `now` is injected, defaulting to current UTC, so the boundary is unit-testable
(the `next_deadline` convention). Unscheduled fixtures (null `event` / `kickoff_time`) stay upcoming.

The comparison is a **string** comparison on purpose: kickoffs are stored exactly as the API sends them
(`YYYY-MM-DDTHH:MM:SSZ`, all UTC — verified across all 380 rows), and for a fixed-width UTC format lexicographic
order *is* chronological order, so SQLite compares in-query with no date parsing. A string cannot have 90 minutes
subtracted from it, so the lead is added to `now` instead.

**`DEADLINE_LEAD` moved to `fpl_rules.py`.** The 90 minutes was written down in `analytics/deadline.py`; storage
now needs the same rule. Two copies of a number is how this class of bug starts, so it lives once, in the rules
module both can depend on without either depending on the other.

**`_card_horizon` in the My Squad view.** Sizes the card's fallback xP horizon by the furthest gameweek any team's
next-3 actually reaches, rather than a flat 3. The stub gameweek is what exposed it, but it keeps earning its
place at **blank gameweeks** — a team sitting one out has its next 3 fixtures spread over 4.

---

### ✅ Definition of Done

- **Automated:** 1105 → **1115 tests**, all green. 7 on the storage cutoff (played gameweek dropped; the whole
  gameweek including its straggler; the deadline boundary either side; deadline set by the *earliest* kickoff;
  unscheduled kept; `finished` still honoured; the team filter still binding alongside the new subquery), 3 on
  `_card_horizon` (blank gameweek, every-team-plays, empty). Ruff clean.
- **Manual smoke:** on the live GW1 data — upcoming now starts at GW2 for all 20 teams; next deadline
  2026-08-28 17:30 UTC; CHE's next 3 = BHA (H) · ARS (A) · HUL (H); `decision_xp` horizon gameweeks `[2, 3, 4]`.
- **Docs:** ADR-123, this sprint doc, PROJECT_STATUS.

---

### 📝 Lessons

**An API flag is a claim about the vendor's workflow, not about the world.** `finished` does not mean "the match
has been played" — it means "we have finished processing this match", which is a different event, days later. The
fix that lasts uses a fact about the world (kickoff time) over a flag whose semantics the vendor controls.

**Building the approved design is a legitimate way to discover it is wrong.** The per-fixture cut looked right on
paper and only revealed the stub-gameweek problem once two unrelated callers broke. The second break (a 0.0
captain double) was the one that reframed it — a bug in *two* places from *one* assumption is a sign the
assumption is the bug, not the two places.

**Ask what unit the domain actually uses.** FPL manages in gameweeks: one deadline, one captain, one set of
transfers. Filtering in fixtures imported a unit the rest of the system does not think in, and every boundary
between the two units leaked.

---

### 🔭 Found, not fixed (separate gates)

- **⚠️ The xP cold-start now inverts the ranking.** With one game played, `points_per_game` *is* that game's
  score, and the cold-start rate tier takes `max(ep_next, ppg)` (ADR-104). So M.Sangaré's 14-point opener becomes
  a 14 pts/GW rate (43.4 xP over 3 GWs) while Haaland's 2-point opener projects 2/GW — and the cold-start
  players now top the whole board. 44 players sit on that tier; 5 are badly inflated. Preseason this was safe
  (`ppg` was 0, so `ep_next` floored it); one gameweek of data is what breaks it. Needs its own ADR — a
  minutes/sample-size guard on the `ppg` tier is the obvious shape.
- **The season-to-date boards stay empty until ~GW10**, not GW4–6: over/under, DefCon and clean sheets all gate
  at `MIN_MINUTES = 900`. The 🌱 note (US-430) is honest but will sit there for ten weeks.
- **`player_history` is empty (0 rows)** — the per-GW sparklines and W-D-L form dots have nothing to draw, and
  the ADR-060 form blend stays dormant. Needs the throttled `backfill`, which `refresh` does not do.
