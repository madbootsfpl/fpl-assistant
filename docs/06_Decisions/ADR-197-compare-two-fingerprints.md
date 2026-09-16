# Architectural Decision Record: Compare two fingerprints, and give it no verdict

**Decision ID:** ADR-197
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built** (2026-09-16). **1798 → 1803 tests, ruff clean.**
**Superseded By / Replaces:** Extends [ADR-118](./ADR-118-player-dna-page.md)'s DNA radar and ADR-110/111's
Boot Battle. **No `decision_xp` change** — display only, reusing the axes both pages already compute.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> **Owner:** *"Could we do a compare DNA for both Team & a Player. For Player it's an extension of Boot Battle
> and should include Performance trend too."*

Boot Battle answers *which of these two is better at each stat*, row by row, with the winner tinted. It cannot
answer the two questions a manager choosing between two players actually has next:

- **what shape is each player** — a 90th-percentile creator and a 90th-percentile finisher both look like
  "good" in a stat table, and nothing like each other on a radar
- **which way is each one going** — the trend the single DNA page has carried since ADR-159 and the
  comparison never had

---

### 🎯 Decision

**1. Two polygons on one octagon, not two radars side by side.** The value of a fingerprint comparison is the
*shape difference*; two charts make the reader do the overlay in their head, which is precisely the work Boot
Battle already does for them stat by stat. One builder (`radar_compare_svg`) serves Player and Team, as
`radar_svg` already does.

**2. A performance trend per player**, under the radar — the half Boot Battle never had.

**3. ⭐ No second verdict. This was the design decision, agreed before building.**

Each player carries a MADBOOTS Verdict on his own DNA page. Two side by side would read as a **ranking**, and
the model has not earned one: a verdict is a heuristic 0–99 assembled from signals deliberately kept **out** of
`decision_xp` (ADR-118). Putting two next to each other invites a subtraction nobody measured — the same
overclaim [ADR-194](./ADR-194-a-start-bench-call-gets-a-margin.md) had removed from the lineup the day before,
where a 0.1 xP gap was being stated as an instruction.

> **The shapes compare; the reader concludes.**

The team compare drops its **grade gauge** for the same reason: two grades side by side read as a league table
of two.

#### ⚠️ The case that only exists with two shapes

A single radar declines to draw below three rankable axes, and sits an unranked axis on the mid ring with a
hollow dot — *absent evidence is not a zero* (ADR-118/126). With two fingerprints there is a case that cannot
arise on one: **each may be unranked on a different axis.** Drawing both plainly would silently imply they were
level there.

So the pair **declines together** if either side is too thin — a radar where one shape is real and the other is
guesswork is worse than no radar, because it looks like a comparison — and each unranked vertex is drawn hollow
**in its own colour**, so a reader can see which side is short of evidence and where. ⭐ *That is a decision
taken at the gate rather than discovered on camera, which is what the gate is for.*

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the two questions Boot Battle could not answer now have a surface; the Team DNA page
  gains a club-vs-club view it has wanted since ADR-169 split it out; and both reuse the existing axes, so
  there is no second definition of a fingerprint to drift.
* **Negative Impact / Trade-offs:** two more panels on surfaces that have been cut for density twice (ADR-135,
  ADR-174). **Both sit behind an expander** — the stat card and the single-club view are what most visits want.
* **Risks & Mitigations:**
  - **Risk:** someone later adds the "missing" verdict, reasonably, because every other card has one.
    **Mitigation:** a test asserts neither compare calls `build_verdict`, `render_verdict_card` or `gauge_svg`,
    and says why in the docstring rather than only in this file.
  - **Risk:** a name collision — Boot Battle's stat card is already `render_player_compare`.
    **Mitigation:** the new one is `render_dna_compare`. ⭐ *Two functions called the same thing on one panel is
    how the wrong one gets called in six months.*

---

### 🛠 Implementation & Migration
* **Components Affected:** `web_streamlit/dna_card.py` (`radar_compare_svg`, `COMPARE_CSS`),
  `player_dna_view.py` (`render_dna_compare`), `team_dna_card.py` (`render_team_compare`),
  `views/squads.py` (under Boot Battle), `pages/4_Team_DNA.py` (under the club picker)
* **Action Items:**
  - [x] One builder for both, reusing the shared axis geometry
  - [x] Trend per player; no verdict either side; no grade gauge on the team compare
  - [x] The unranked-axis rule decided for two shapes, not inherited from one
  - [x] Guards: both drawn on one radar · hollow-in-own-colour per side · declines when **either** is thin ·
        **no verdict on either compare** · a trend per player
  - [x] Mutation-test every guard — four mutants, all red, including a verdict creeping back in

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

### 🔧 Owner feedback, same day — three fixes

**1. The radar did not match the one above it.** Shipped at size 380 / `R−78` / 2.5px stroke against the
single card's 360 / `R−74` / 2px. The compare sits one expander below the single view, so the mismatch was
directly visible. ⭐ *Two charts of the same thing at different scales read as two different charts.* Now
identical, with a test that compares both sources rather than pinning numbers in one place.

**2. The table became chips.** Owner: *"rather than a table could we use the legend as used in single club
with the comparing club data alongside it."* The markdown table was a **second reading order for the eight
facts the chart had already shown**, and on a phone every cell wrapped onto three lines. It is now the single
card's chip grid carrying **two values per axis**, tinted by **shape colour** rather than by band — in a
comparison the question is *whose is this*, and the radar already answers *how good* by position on the ring.

**3. ⚠️ The phone bug, and it was a real one.** The radar's furniture is hard-coded for a dark ground —
`rgba(255,255,255,.10)` rings, `#cdd6e2` labels, `#0c121a` dot outlines. The single card supplies that ground
itself via `.dna-card`; **the compare rendered the bare `<svg>`**, so on a light-themed phone it sat on white
with near-invisible axis labels while everything around it stayed dark.

⭐ **A component that hard-codes one theme's colours is not portable to a container that does not supply
them** — and it looks perfect on the developer's machine, because the developer is in dark mode. The same
trap the theme work hit in ADR-180, one layer down: there it was a colour the theme should own, here it is a
*ground* the component assumed. Both compares now render inside the same card, including when they decline to
draw — otherwise the refusal renders on white too.

---

### 💡 The lesson

> **The interesting part of a comparison feature is what it refuses to conclude.**

Building two radars on one chart is an afternoon. The decision that matters took one exchange: *does the
comparison get a verdict?* Every instinct says yes — each card has one, the reader is asking "which?", and the
number already exists. And it would have been the third overclaim of the week, after a lineup instructing on
0.1 xP and two cards crediting an AI that is not there.

⭐ **A number that is honest alone can become a claim when you put it next to another one.** The verdict is a
fair heuristic for one player; place two on a screen and you have published a ranking, using signals the engine
deliberately refuses to rank with.

---

### 🔗 References & Related Artifacts
- **The radar and the verdict:** [ADR-118](./ADR-118-player-dna-page.md) · the unranked rule, ADR-126
- **What it extends:** ADR-110/111 (Boot Battle) · ADR-159 (form windows) · ADR-169 (the Team DNA split)
- **The same overclaim, a day earlier:** [ADR-194](./ADR-194-a-start-bench-call-gets-a-margin.md)
- **Asked for by:** the owner, in the same message that caught the AI labels (ADR-196)
