# Architectural Decision Record: The tap leaves the pitch — league-scan rows select

**Decision ID:** ADR-158
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-gated, built, preview signed off** (Sprint 213, 2026-08-27).
**1496 → 1504 tests, ruff clean.**
**Superseded By / Replaces:** Delivers ADR-134's open follow-up. Reuses ADR-133; **does not** reopen ADR-135.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The roadmap carried this item with its own guard rail already written, from ADR-135's reversal:

> The league-scan rows should inherit **selection**, not a menu — a row tap that selects is ADR-133's shape and
> is still wanted; a row tap that opens a menu is this ADR again. The density goal stands; the mechanism for
> reaching it does not.

The scan (ADR-134) renders 20 clubs as a strip of HTML with a selectbox beneath it. Reading the rows tells you
which club to look at; acting on that reading meant leaving them and finding the same club in a dropdown.

---

### ✅ Decision

**1. A scan row is an anchor, and a tap selects that club.** ADR-133's gesture, unchanged: the tap writes the
same `session_state` the selectbox writes, so the DNA card downstream is reused **entirely** unchanged. Only
the input is new.

**2. The row element *is* the anchor.** `.yt-row` is a four-column grid; an `<a>` *inside* it would become the
single grid item and collapse the layout. A test pins this, because it is the kind of thing that looks fine
until a row has a long value in it.

**3. The picker stays, permanently** — ADR-133's rule, and the reason this stays cheap. `AppTest` drives the
page exactly as before, so the golden page loses no coverage; keyboard and screen-reader users keep a path;
and a missing component degrades to precisely the pre-ADR-158 page.

**4. The caption only offers the gesture when the gesture works.** One sentence that is both the hint and the
deploy check — ADR-133's finding that an invisible fallback is right for users and wrong for diagnosis.

**5. The Health strip taps too.** It is rendered by the same function and looks identical. A gesture that
worked on one and not the other would read as a bug rather than a boundary. Flagged to the owner as a scope
call rather than slipped in; he signed off the preview with both.

**6. The replayed-click guard moved into shared code.** The component hands back its *last* click on every
rerun, so without a guard the picker can never override a tap. That was found while debugging ADR-135 and
lived inside the pitch function; it is a property of the component, not of pitches, so it now sits in `_fresh`
where both callers get it. `select_from_html` is the generalisation — anchors carry `id="team:<short>"`, and
`label_by_id` maps that to the selectbox's label.

**What it deliberately does not do:** open a menu. ADR-135 hit its density target exactly and was still worse
on two devices, because every tap is a full rerun with a `decision_xp` recompute, so a two-tap flow costs two
round-trips. Selection is one tap for one outcome.

### 🧪 Definition of Done

1. **Tests: +8.** A row tap selects that club; a replayed click cannot overwrite the picker; unknown, stale
   and wrong-prefix ids are ignored; a missing component selects nothing and draws nothing; the clickable row
   *is* the anchor and the plain strip has no anchors at all; only the selected row is outlined; and — through
   `AppTest` — the page offers the gesture when the component is live, hides it when it is not, and keeps the
   picker either way.
2. **Manual smoke** — a faithful preview built from the app's own rendered component and live data, tappable,
   signed off by the owner before commit.
3. **Docs** — this ADR, the roadmap item closed, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**The guard rail was written a month before the feature, by the sprint that failed.** ADR-135 did not just get
reverted; it left behind a sentence naming which half of it was worth keeping and which half must never come
back. This sprint was mostly the act of reading that sentence and doing what it said.

That is worth more than the feature: **a reverted sprint is only wasted if it doesn't leave a rule behind.**
ADR-135 cost a day and produced "tap to select, never tap to open" — which has now shaped two surfaces it was
never about.

The smaller lesson is about sharing. Generalising `render_tappable_pitch` surfaced a bug fix that had been
sitting inside it — the replayed-click guard — which was never pitch-specific and would have had to be
rediscovered by whoever built the second tappable surface. **Code that is copied loses its bug fixes; code
that is shared keeps them.**
