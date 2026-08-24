# Architectural Decision Record: "Upcoming" means the gameweeks you can still act on

**Decision ID:** ADR-123
**Date:** 2026-08-23
**Status:** Accepted — owner-approved, **built** (live GW1 bug).
**Superseded By / Replaces:** Corrects the `finished = 0` filter in `Storage.get_upcoming_fixtures` that has been
there since the fixtures table shipped. Shares its deadline rule with ADR-086 (`next_deadline`).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

GW1 was played on 2026-08-21/22/23 and the data was refreshed on the evening of the 23rd. After the refresh, the
whole fixture-forward engine still believed **GW1 had not happened**.

The cause is an assumption about the FPL API. `Storage.get_upcoming_fixtures` selects `WHERE f.finished = 0`, on
the reading that FPL flips `finished` as soon as a match ends. It does not. Checked live against
`/api/fixtures/?event=1` at 18:46 on 2026-08-23 — two days after the opening match:

```
ARS 3-0 COV  (Fri 21st)   finished=False  finished_provisional=True  started=True
NEW 2-2 LIV  (Sun 23rd)   finished=False  finished_provisional=True  started=True
FUL  -  CHE  (Mon 24th)   finished=False  finished_provisional=False started=False
```

FPL sets `finished_provisional` when the whistle goes and holds `finished` back until the gameweek's bonus points
are confirmed. So for the two-to-three days a gameweek is in flight, **every played match still reads as
upcoming**.

The blast radius is the whole decision engine: `get_upcoming_fixtures` has ~18 call sites across `cli.py` and
`ask.py`, feeding the xP horizon, the fixture ticker, the transfer planner and the captain pick. With all 380
fixtures returned as upcoming, a "next 3 gameweeks" projection was quietly spending one of its three gameweeks on
football that had already been played. `next_deadline` (ADR-086) was unaffected — it derives from `kickoff_time`
and correctly pointed at GW2 — so the countdown banner was right while the engine beneath it was a gameweek
behind.

#### Decision Drivers
- **Live correctness bug** — it is wrong *right now*, on real data, on the pages testers are using.
- **Recurs every gameweek** — this is not a season-rollover artefact; it reappears for ~48h of every GW.
- **Don't add data we don't need** — the fix should use what is already stored if it can.

---

### ✅ Decision *(owner-approved, built)*

**A gameweek is "upcoming" until its deadline passes.** `get_upcoming_fixtures` keeps the `finished = 0` clause
and adds a deadline cutoff that admits or excludes a gameweek **whole**:

```sql
WHERE f.finished = 0
  AND (f.event IS NULL OR f.event NOT IN (
        SELECT event FROM fixtures
        WHERE event IS NOT NULL AND kickoff_time IS NOT NULL
        GROUP BY event HAVING MIN(kickoff_time) <= ?))
```

A gameweek's deadline is its **earliest kickoff minus 90 minutes** — the same rule the countdown already uses.
That 90 minutes now lives once, as `DEADLINE_LEAD` in `fpl_rules.py`, which both `analytics.deadline` and
`storage` import; two copies of the number was exactly the sort of drift that produced this bug.

`now` is an **injected parameter** (`now: datetime | None = None`), defaulting to the current UTC time so the ~18
existing call sites need no change, and passable explicitly so the boundary is unit-testable — the convention
`next_deadline` already uses (ADR-086).

Three details worth recording:

- **Whole gameweeks, not individual fixtures.** See below — this is the crux, and it was a mid-build correction.
- **Unscheduled fixtures stay upcoming.** FPL leaves `event` and `kickoff_time` null until a match is dated.
  Undated is not played, so excluding it would lose real future football.
- **The comparison is a string comparison, deliberately.** Kickoffs are stored exactly as the FPL API sends
  them — `YYYY-MM-DDTHH:MM:SSZ`, all UTC, verified across all 380 stored rows. For a fixed-width UTC format,
  lexicographic order *is* chronological order, so SQLite can compare in-query with no date parsing. A string
  cannot have 90 minutes subtracted from it, so the lead is **added to `now`** instead: a deadline has passed
  exactly when the gameweek's earliest kickoff is at or before `now + DEADLINE_LEAD`.

Both clauses are kept: `finished` is still authoritative once FPL does set it, and the deadline covers the window
where it hasn't yet.

#### Why whole gameweeks — the mid-build correction

The first cut of this ADR filtered **per fixture**: drop a match once its own kickoff has passed. That is the
more literal reading of "upcoming", it was approved, and it was built. It was wrong, and building it is what
showed why.

A gameweek is played over several days. Cutting fixture by fixture leaves a **stub gameweek** at the head of the
horizon — mid-Sunday, GW1 with one match left, belonging to two teams:

```
upcoming GWs:  [(1, 1), (2, 10), (3, 10), (4, 10)]
teams with GW1 still to play:  ['CHE', 'FUL']
```

Every caller that reasonably assumes *"the next gameweek" means "every team's next fixture"* then quietly
disagrees with itself. Two broke immediately:

- **The player card's per-GW row** counts 3 fixtures *per team* while the horizon counts gameweeks *globally*. A
  team that had played was looking at GW2–4 while a 3-gameweek horizon only reached GW3, so the third cell
  rendered `0.0`.
- **The captain double** applies to `gameweeks[0]`, the first global upcoming gameweek — GW1. Any captain whose
  team had already played earned a **0.0 double**, and the "doubled for the next gameweek only" caption vanished.

The second one is the tell. GW1's deadline passed on the Friday: you cannot transfer, captain or bench for it.
Patching each consumer to route around a gameweek nobody can act on is treating the symptom. The deadline is the
honest line, because it is the line that *matters* — once it passes, that gameweek is no longer something you are
deciding about. Whole gameweeks in or out keeps every team on the same one, and both defects disappear rather
than needing a patch each.

---

### 🔀 Alternatives Considered

- **Per-fixture kickoff cutoff.** Approved, built, then withdrawn — see above. More literal, but it leaves a stub
  gameweek at the head of the horizon and breaks every per-team-vs-global assumption downstream.
- **Ingest `finished_provisional` and treat played as `finished OR finished_provisional`.** Truer to the source,
  and the first instinct. Rejected: it needs a schema migration, an ingest change and a reseed, to recover a fact
  the stored `kickoff_time` already tells us. It also swaps one API-flag assumption for another — and this ADR
  exists precisely because an API-flag assumption failed. Kickoff time is a fact about the world, not a flag
  whose semantics FPL can change. It would also still leave the stub-gameweek problem.
- **Filter in the analytics layer instead.** Rejected: ~18 call sites would each need to remember to do it, and
  "which fixtures are upcoming?" is a stored-column question — the storage layer's job (Architecture §3, §6).
- **Do nothing until FPL sets `finished`.** Rejected: it self-heals a few days after each deadline, but the
  window where the engine is wrong is exactly the window where people are making transfer decisions.

---

### 🧭 Consequences

**Positive** — the xP horizon, ticker, transfer planner and captain pick move to the next *actionable* gameweek
the moment its predecessor locks, instead of lagging until bonus is confirmed; every team stays on the same
gameweek, so per-team and global reasoning agree; no schema change, no reseed, no new API dependency; the
90-minute rule exists once; `now` injection makes the boundary testable without freezing the clock.

**Negative / risks (mitigations)** — an in-flight gameweek's unplayed fixtures disappear from "upcoming", so the
Fixtures ticker and an `ask` query like *"who do Chelsea play next?"* will answer with the next gameweek rather
than tonight's match (*mitigation:* correct for decision support, which is what the tool is for — you cannot act
on that match; `get_fixtures_by_event` already serves the true per-gameweek picture if a live "this gameweek"
view is ever built, and that is the natural home for it); the string comparison relies on the stored ISO-Z format
(*mitigation:* it comes straight from the API unmodified, is asserted across all stored rows, and a malformed
value would fail loudly in the ingest long before this query); the `NOT IN` subquery runs per call on a
380-row table (*mitigation:* negligible, and `get_upcoming_fixtures` is already called once per page render).

---

### 🧾 Status & follow-ups

- **Accepted — built:** the deadline cutoff + injected `now`; `DEADLINE_LEAD` shared from `fpl_rules`;
  `_card_horizon` in the My Squad view sizing the card's fallback horizon by the furthest gameweek any team's
  next-3 reaches (which the per-fixture cut exposed, and which still earns its place at **blank gameweeks** —
  a team sitting one out has its next 3 fixtures spread over 4); 10 tests; 3-part DoD.
- **Not this ADR / follow-ups:** a live "this gameweek" view showing in-flight fixtures and results (scores are
  fetched but not stored); the season-to-date boards still gated at 900 minutes until ~GW10 (a separate, open
  decision).
