# ADR-265 — A capability with no transport is invisible

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner's feedback — *"Add the Fixture Difficulty ticker to 'More' tab"*
**Follows:** ADR-264 (the same feedback round), ADR-219 (the contract layer)

---

## Context

⭐⭐ **The engine already did every hard part.** `fixture_ticker` has produced a clubs × gameweeks grid —
handling **doubles** and **blank** gameweeks — since Sprint 062. What was missing was a way for a phone to
ask. ⚠️ *A capability with no transport is invisible to every surface that does not share a process.*

The app's own fixture data could not answer it: `my-team` carries the **9 clubs in your squad** over **3**
gameweeks. ⭐ *A ticker is a question about the league, not about you* — and narrowing it to the clubs you
already own would remove the clubs you are thinking of buying, which is the entire point.

## Decisions

**`POST /api/v1/ticker` — no squad at all**, the second endpoint after `players` that takes none.

**⭐ A blank gameweek is a present key holding `null`.** *"They do not play"* is the most actionable thing
this grid says — ⚠️ *a club that cannot play cannot be captained* — and a missing key reads as missing
**data**, so a client would render a gap identical to a bug. The cell is drawn, with a dash.

**⚠️ A double carries both opponents and is shaded by the harder one.** A double is only as easy as its
worse fixture, and ⭐ *shading it by the first match would make the one view people open to find doubles
the view that misrepresents them.*

**Keys are stringified**, because JSON has no integer object keys and `"10"` sorts before `"6"` as text
(ADR-219). The order lives in `gameweeks`, never in the map.

**`source` accepts `fpl` and `custom`, not `elo`.** Elo needs bands the caller would have to supply; ⚠️ *an
option that silently returns undefined difficulties is worse than one that is not offered.*

**The colours are FPL's**, because ⭐ *a familiar scale with unfamiliar colours is a scale you have to
learn twice.* Green easy, red hard.

## ⚠️ Three guards fired, and all three were right

Adding one endpoint tripped three existing tests, each naming a thing that would otherwise have shipped
missing: the **player-shape sweep** (registered under `NO_PLAYERS` — it answers about clubs), the
**contract test** (an endpoint with no committed sample is one a Dart author does not know exists), and a
**widget test**. ⭐ *This is what the guards were built for, and they cost one line each to satisfy.*

## ⚠️ And two of my own tests were wrong

**A property the design does not have.** *"Redness rises monotonically with difficulty"* failed against
**correct** colours: FPL's band 5 is a dark maroon and carries less red than the brighter band 4. ⭐ *A
property the design does not have is not a property worth asserting* — replaced with the direction of
dominance, which is what a reader actually decodes.

**A threshold invented to look strict.** The legibility check used a raw luminance difference, which white
ink on the bright green band passes while being genuinely hard to read — so **forcing every band to white
ink survived the mutation run**. ⭐ *A threshold nobody derived is not a threshold.* Now the WCAG contrast
ratio against the published bar, and the mutation dies.

**A hand-written list of directory rows** meant the new row was covered by nothing. Now derived from the
widget — ⚠️ *a hand-maintained list does not grow when the thing it describes does*, which is the same
fault as ADR-261's `_CORE`, found twice in one day. ⚠️ A `ListView` also does not build off-screen
children, so the extra row silently took the **last** row out of every test looking for it: ⭐ *a test that
cannot see a widget fails identically to one where it is absent.*

## Verification

* **7 Python tests** — every club present, easiest-first ordering, blank keys present for every club,
  stringified keys, and a **constructed** double (⚠️ the seed may hold none, and a test that quietly skips
  when the data is ordinary reads as coverage).
* **11 Dart tests** against the committed 27 KB sample the server actually produced; **5/5 mutations
  killed**, one only after the contrast threshold was made real.
* 2,507 Python · 157 Dart.
