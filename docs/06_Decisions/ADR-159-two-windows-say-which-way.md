# Architectural Decision Record: Two rolling form windows — and the refusal to draw a direction we can't measure

**Decision ID:** ADR-159
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-gated, built, preview signed off** (Sprint 214, 2026-08-27).
**1504 → 1515 tests, ruff clean.**
**Superseded By / Replaces:** Delivers the roadmap's *"rolling 3-/6-GW form windows + trend views"*, unblocked by
ADR-128's widened per-GW table. **No `decision_xp` change; `FORM_WEIGHT` stays 0.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`form_rate` (ADR-060) already computes one rolling points-per-90 over the last `FORM_GAMEWEEKS` gameweeks. It
feeds xP and is dormant. What it cannot do, at any window size, is say **which way a player is going** — a
single number has no direction. That is the question managers actually ask, and the roadmap item for it.

**Measured before designing anything, which changed the design:**

```
distinct PLAYED gameweeks in the data : [1]
players with >=1 played row           : 548
players with >=3 played rows          : 0
players with >=6 played rows          : 0
```

One gameweek. So today a 3-GW window and a 6-GW window are **the same single match** for every player in the
game, and the gap between them is exactly `0.0`. A naive implementation reports that as *level* — a flat,
confident-looking arrow on no evidence at all. This card already refuses to draw a line through one point for
exactly that reason; the same discipline applies one level up.

---

### ✅ Decision

**1. `form_windows(rows, short=3, long=6)`** returns both rates, the signed delta, and a direction.

**2. Both windows are `form_rate` called twice.** Not a second rate written beside it: identical recency and
minutes weighting is what makes the two numbers *comparable*, and a parallel implementation would drift into
subtracting apples from pears. A test pins that identical windows give bit-identical numbers.

**3. `direction` is `None` unless the long window covers strictly more played gameweeks than the short one.**
This is the whole design. It correctly refuses at one gameweek, and it keeps refusing in a case that survives
into a full season: a player back from a three-week injury has six rows and three matches, so the long window
holds nothing the short one doesn't. **Counting rows would get that wrong; counting played matches gets it
right.**

**4. No "meaningfully different" threshold.** Setting one needs a distribution of real gameweek-to-gameweek
swings, which does not exist. The sign and the size are reported and the reader judges. If a cut-off is ever
wanted it is a GW4-6 calibration job, like every other constant here — and inventing one now would be the
failure this project has named repeatedly: **a threshold carries its population with it.**

**5. One home: the Performance trend card.** It answers the same question the rest of that card answers, and
the owner's standing constraint is to cut clutter rather than repeat a fact everywhere it would fit.

**6. The caption ends "not in xP".** `FORM_WEIGHT` is 0, so this informs without implying it moves the
projection. The moment that weight is raised, this sentence must change — noted here because it is exactly the
kind of caption that quietly goes stale.

### 🧪 Definition of Done

1. **Tests: +11.** Rising and fading players; one gameweek refusing a direction; **windows covering the same
   matches refusing one late in a season too**; a player with no minutes having no windows; both windows using
   the same rate; window sizes as arguments. Plus the view: both windows and the gap when there is one, the
   refusal rendered as words with no arrow at all, nothing rendered without minutes, and the trend panel
   degrading to byte-identical output when `windows` is absent.
2. **Manual smoke** — a preview built from the app's own card: today's real state on live data (Haaland,
   68% owned) beside the two states that appear later, from synthetic gameweeks. Owner approved before commit.
3. **Docs** — this ADR, the roadmap item closed, PROJECT_STATUS, a sprint retro.

⚠️ **Honestly stated at sign-off: this is the first thing built this session that cannot be verified on real
data.** The analytics is exercised against synthetic gameweeks; nobody sees the populated state until ~GW4.
That was the accepted trade for having the machinery ready when `calibrate` clears its ≥4-GW guard.

---

### 💡 The lesson

**The data check came before the design, and it *was* the design.** Six lines of counting turned this from
"add a second window" into "add a second window and a rule for when the two are the same thing" — and that
rule is the only part with any subtlety in it. Had the view been built first, it would have shipped a level
arrow on every player in the game and looked entirely correct while doing it.

The generalisable form: **when a feature compares two windows, the first question is not how to compare them
but when they are the same window.** Early seasons, injury returns and new signings all produce that case, and
it does not announce itself — the arithmetic works perfectly and returns zero.
