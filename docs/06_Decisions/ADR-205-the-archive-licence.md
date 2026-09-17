# Architectural Decision Record: The archive licence — the blocker was mine, not the repo's

**Decision ID:** ADR-205
**Date:** 2026-09-17
**Status:** ✅ **Finding established — the licence question is resolved. One call remains, and it is the owner's.**
**No code changed. No tests changed.**
**Superseded By / Replaces:** ⚠️ **Corrects a factual claim repeated in
[ADR-201](./ADR-201-a-season-is-part-of-the-identity.md), the index and the Roadmap**, where the archive was
described as carrying *"NOASSERTION — the absence of a grant, not a permissive one."* That is wrong.
Unblocks ML Phase 1's data question ([ADR-204](./ADR-204-the-phase-1-gate.md)).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### ⚠️ The correction, first

`vaastav/Fantasy-Premier-League` **is MIT-licensed.** It has a `LICENSE` file containing the standard MIT text
and a copyright line, `Copyright (c) 2017-19 Vaastav Anand`.

GitHub's API reports `"spdx_id": "NOASSERTION"` because its licence detector does a near-exact template match,
and this file has **two extra lines appended**:

> The data provided is property of `fantasy.premierleague.com` and `understat.com` — *"I don't own any of the
> data"*

Those two sentences are why the automated classifier gives up. ⭐⭐ **I READ A DETECTOR'S FAILURE TO CLASSIFY
AS THE AUTHOR'S FAILURE TO GRANT, AND WROTE IT DOWN FOUR TIMES AS THOUGHT IT WERE A FACT ABOUT THE REPOSITORY.**
`NOASSERTION` means *"this tool could not determine a licence"*, not *"no licence was asserted"* — the word
looks like it means the second thing, and it does not.

⭐ **A field whose name states a conclusion will be read as that conclusion.** The check that would have caught
it on day one was **one HTTP request to read the file** — the same length as the request that produced the
flag I trusted instead. ⭐ *A metadata field about a document is not the document.*

---

### 📌 So what is the actual question?

Not the repository's licence — that is settled and permissive. The real question is the one Vaastav himself
raises in the same file: **he cannot license data he does not own.** So it resolves into two, and they have
very different answers.

#### 1. FPL-derived data — **no new question at all**

This is the same source MADBOOTS already calls live, every refresh: `bootstrap-static`, `fixtures`,
`element-summary`. The archive is not a new provider; it is **the same provider's data, older**.

⭐ **Importing it changes the age of the data, not its provenance** — so whatever position the project already
holds on using FPL's API for the live app applies unchanged. There is nothing here to newly decide, and if
there were, it would already be a live problem rather than a future one.

#### 2. Understat-derived data — **real, and entirely avoidable**

Understat is a separate source with separate terms, and the project has never used it (ADR-016 declined
soccerdata). Checked rather than assumed:

- Understat data is **quarantined in its own directory**, `data/<season>/understat/`. Every other file
  (`gws/`, `players/`, `players_raw.csv`, `fixtures.csv`, `teams.csv`, `player_idlist.csv`) is FPL.
- ⚠️ **And the obvious way it could leak was tested**: `expected_goals` and friends look exactly like the
  columns Understat is famous for. They appear in `merged_gw.csv` **only from 2022-23 onward** — 2016-17,
  2019-20 and 2021-22 have none — which is precisely when **FPL's own API began serving expected stats**. They
  are FPL-native, not a backfill. *The column that would have been the leak is the column that proves there
  isn't one.*

**So: import nothing from `understat/`, and the question does not arise.**

---

### 🎯 Decision

**The archive is usable for ML Phase 1, scoped to the FPL-derived files.** Concretely: `gws/merged_gw.csv`
per season, joined to `player_idlist.csv` for the stable `code`. Eleven seasons are present, **2016-17 through
2026-27**, and the columns are a near-exact match for `player_history` — `minutes`, `total_points`, `fixture`,
`kickoff_time`, `round`, `opponent_team`, `was_home`, both scorelines, goals, assists, clean sheets, saves,
bonus, bps, ICT, `value`. (`defcon` is absent — it is a 2025/26 FPL addition — and `element` is the season id,
not the stable code, which is what `player_idlist.csv` is for.)

**Attribution is required and cheap.** MIT requires the copyright notice and permission text to travel with
substantial portions. If the archive is imported, `NOTICE` gains Vaastav's copyright line and his data
disclaimer, verbatim.

---

### 👤 The one call that is still the owner's

⚠️ **This ADR settles the repository licence. It does not settle FPL's own terms for their data**, and that
question is *not* created by the archive — it already applies to every refresh the live app makes. What
changed is the stakes around it: the project is now **AGPL-3.0** and there is an open question about
**accepting donations**, and "personal project reading a public API" and "funded public service redistributing
the same data" are not obviously the same posture.

I am not qualified to answer that, and it is worth a view from someone who is if donations go ahead. What I
can say is what it is *not*: it is not a blocker on the archive specifically, and treating it as one confuses
a decision about the project with a decision about a dependency.

🔧 **Updated the same day — the owner parked donations** (*"we can hold to see if it becomes a reality"*), with
a trigger recorded in the Roadmap. That settles this paragraph too: the FPL-terms question was **elevated** by
donations, not created by them, so parking returns it to the posture it has always had — a personal project
reading a public API, exactly as every refresh has done since day one. ⭐ *It goes back to being a thing to
know rather than a thing to resolve*, and it re-opens automatically if the donations trigger fires.

---

### 📊 Consequences

**Good:** Phase 1's data constraint is lifted. If the GW8 review ships the blend (ADR-204), a learned model
has eleven seasons rather than eight gameweeks. The item leaves the owner's "needs you" list.

**Costs / limits:**
- ⚠️ **Archive data is not identical to ours.** It is one maintainer's scrape, with its own documented caveats
  — the `DATA_DICTIONARY` flags `xP` as scraped from `ep_this` *after* the gameweek with an undocumented update
  cadence. Anything trained on it inherits that, and the archive's own columns should be checked against our
  stored 2026/27 rows where the two overlap before either is trusted.
- Pre-2022/23 seasons have **no expected stats at all**, so any feature built on them is unavailable for six of
  the eleven seasons. A model trained across all eleven cannot use xG uniformly.
- `defcon` exists in exactly one season. Same problem, narrower.
- ⭐ **Eleven seasons of data is not eleven seasons of the same game** — FPL's scoring rules have changed
  repeatedly over that span, and the archive is silent about that because it is a record, not an explanation.

---

### 💡 The lesson

⭐⭐ **A BLOCKER I RECORDED FOUR TIMES WAS DISSOLVED BY READING THE FILE IT WAS ABOUT.** It survived because it
was *written down* — each repetition cited the last one, and a claim that appears in four documents reads as
established rather than as repeated. ⭐ *Provenance is a property of the first assertion, not of the count* —
and the one place the count is most misleading is your own notes.

This is the same shape as ADR-157 (*"I pitched a sprint on an unverified remembered number"*) and ADR-184
(*a retired claim surviving on six surfaces*). Third sighting: ⭐ **re-check the source of a claim before it
blocks work, not after it has blocked work for a month.**

---

### 🔗 Links

- [ADR-201](./ADR-201-a-season-is-part-of-the-identity.md) · [ADR-204](./ADR-204-the-phase-1-gate.md) — where the wrong claim was recorded
- [ADR-016](./ADR-016-soccerdata-evaluation.md) — the standing decline of Understat-family sources
- [ADR-157](./ADR-157-the-extraction-model-is-its-own-choice.md) — the same failure mode, on a number
