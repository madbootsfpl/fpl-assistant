# Sprint 264: The blocker was mine, not the repo's

**Dates:** 2026-09-17
**Status:** ✅ **ADR-205 — finding established, Phase 1's data constraint lifted. No code changed.**

---

## The job

The owner asked for instructions on resolving the `vaastav/Fantasy-Premier-League` licence — the item that
had sat on *"needs you"* blocking ML Phase 1, described across four documents as:

> **NOASSERTION** — the absence of a grant, not a permissive one.

The instructions turned out to be: read the file.

---

## ⚠️ It is MIT-licensed

The repo has a `LICENSE` containing the standard MIT text and `Copyright (c) 2017-19 Vaastav Anand`.

GitHub's API reports `"spdx_id": "NOASSERTION"` because its detector does a near-exact template match, and
this file has **two sentences appended**:

> The data provided is property of `fantasy.premierleague.com` and `understat.com` — *"I don't own any of the
> data"*

That is enough to defeat the classifier.

⭐⭐ **I read a detector's failure to classify as the author's failure to grant.** `NOASSERTION` means *"this
tool could not determine a licence"*, not *"no licence was asserted"* — and ⭐ **a field whose name states a
conclusion will be read as that conclusion.**

It gated Phase 1 for a month and cost **one HTTP request** to dissolve — the same length as the request that
produced the flag I trusted instead. ⭐ *A metadata field about a document is not the document.*

---

## The question that actually remained

The maintainer raises it himself: **he cannot license data he does not own.** It splits cleanly.

**FPL-derived data — no new question.** The same source the live app already calls every refresh.
⭐ *Importing it changes the age of the data, not its provenance.* Whatever position the project holds for the
live app applies unchanged — and if it did not, that would already be a live problem, not a future one.

**Understat — real, and avoidable.** Quarantined in `data/<season>/understat/`. Don't import it.

⚠️ **And the obvious way it could leak was tested rather than assumed.** `expected_goals` and friends look
exactly like the columns Understat is famous for. They appear in `merged_gw.csv` **only from 2022-23** —
absent in 2016-17, 2019-20, 2021-22 — which is precisely when **FPL's own API began serving expected stats**.
*The column that would have been the leak is the column that proves there isn't one.*

---

## 👤 What is still the owner's call

**FPL's own terms.** The archive does not create that question — it already applies to every refresh. What
changed is the stakes: AGPL-3.0, and an open question about donations.

⭐ **Treating it as a blocker on the archive confuses a decision about the project with a decision about a
dependency.** It is worth a qualified view if donations go ahead; it is not a reason to leave eleven seasons
on the shelf.

---

## ⚠️ What the archive is not

- One maintainer's scrape, with its own documented caveats — `xP` is taken from `ep_this` **after** the
  gameweek, on a cadence the `DATA_DICTIONARY` says is undocumented.
- **Six of eleven seasons carry no expected stats at all**, so anything built on them is unavailable for most
  of the history. `defcon` exists in exactly one season.
- ⭐ **Eleven seasons of data is not eleven seasons of the same game.** FPL's scoring rules changed repeatedly
  across that span, and the archive is silent about it — being a record, not an explanation.

---

## 💡 The lesson

⭐⭐ **A blocker recorded four times was dissolved by reading the file it was about.** It survived *because*
it was written down: each repetition cited the last, and a claim appearing in four documents reads as
established rather than as repeated.

⭐ **Provenance is a property of the first assertion, not of the count** — and the place that is most
misleading is your own notes. Third sighting of this shape, after ADR-157 (a remembered number that turned
out to be 13-vs-13, not 16-vs-7) and ADR-184 (a retired claim surviving on six surfaces).

---

## Definition of Done

- ✅ **Tests** — no code changed; 1832 passed, ruff clean
- ✅ **Manual smoke** — licence, directory layout and per-season column sets all read directly from the
  source rather than from metadata
- ✅ **Docs** — ADR-205 + index row; **the wrong claim corrected at all three sites it reached** (ADR-201's
  consequences, the Roadmap's owner-blocker row, the Roadmap's Phase 1 gate), PROJECT_STATUS, this sprint doc

**Next:** unchanged — nothing on the ML track until GW8. The archive is now available when Phase 1 needs it.
