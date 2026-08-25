# Architectural Decision Record: Split the IA by level — team things on one tab, player things on another

**Decision ID:** ADR-134
**Date:** 2026-08-24
**Status:** ✅ **Accepted — built** (Sprint 187, 2026-08-25). The direction was agreed 2026-08-19
(Feedback_Log) and parked pending this gate. **The reservation below was resolved rather than overruled** — see
the follow-ups.
**Superseded By / Replaces:** Reorganises the Fixtures page (ADR-063 ticker · ADR-119 Team DNA · the 🎯 Radar).
No analytics change.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner's note, 2026-08-19:

> **Restructure the Fixtures tab around Team DNA.** Team DNA is the unique value; FDR is *"handy but available
> in every tool"*; the Radar is player-discovery. **(a)** rename the tab **"🧬 Team DNA & FDR"** (keep "FDR" for
> discoverability — "Fixtures" is a term people scan for); **(b)** reorder **Team DNA first, FDR ticker
> second**; **(c)** move the **🎯 Radar** to a view on the **Players** tab. *Agreed direction (player-level vs
> team-level IA split).*

The page today runs: **ticker → 🎯 Radar → 🧬 Team DNA** — which is roughly the reverse of the value order, with
a player-discovery tool wedged in the middle of two team-level ones.

---

### ✅ Proposed Decision

**Organise by *level*: the team tab holds team things, the Players tab holds player things.**

1. **Rename** `📅 Fixtures` → **`🧬 Team DNA & FDR`**. Keeping "FDR" is deliberate: it is the term people scan a
   sidebar for, and the differentiator alone would not be recognised.
2. **Reorder** — Team DNA first, the ticker second.
3. **Move the 🎯 Radar** to a Players view. It ranks *players*; it belongs where players live.

This is almost entirely **moving existing renders**. The Radar needs `upcoming` and `decision_xp`, both of which
the Players page already loads.

---

### ⚠️ The risk that note flagged, sized

Moving the Radar makes Players' sub-nav **nine** entries. Measured at an iPhone-ish 358px column:

```
now (8 labels, 89 chars)        → 3 rows of pills
with Radar (9 labels, 94 chars) → 4 rows
shortened (9 labels, 65 chars)  → 3 rows
```

So it costs a row on mobile — on a page whose density was already a tester complaint (US-423). **Shortening the
labels absorbs it entirely**: `Over / under-perf → Over/under`, `Defensive Contribution → DefCon`,
`xG / xA / xGI → xG · xA`. Nine views then fit in the same three rows eight occupy today.

That is the recommendation: **move the Radar *and* shorten the labels in the same change**, since the move is
what makes the shortening necessary.

---

### 🤔 One reservation, for the owner to overrule or accept

The agreed order puts **Team DNA first**. There is a competing principle worth naming: the ticker is the
**scan** (all 20 runs at a glance) and Team DNA is the **drill** (one team, in depth) — and the natural flow is
scan → drill. Leading with the drill means every visit opens on a selectbox showing one team, when the common
job is "who has a good run?".

Both principles are legitimate. The owner's is *value order* (lead with what is ours); mine is *task order*
(lead with the entry point). **I would defer to the owner's**, for a reason that survives my own objection: FDR
is genuinely commodity, and a tool that opens on its commodity feature teaches people it is a commodity tool.
The scan-then-drill flow still works from second position — the ticker is one scroll away, and the Team DNA
card names the team you drilled into.

**If the reservation lands, the cheap compromise** is to keep the order as agreed but have the Team DNA section
open on a **league-wide grade strip** (all 20 clubs, graded) rather than a single-team selectbox — that is a
scan *and* it leads with the differentiator.

> ⚠️ **This paragraph was wrong about the cost and that changed the outcome.** It called the strip *"new build
> rather than moving renders"*. It is not: `your_teams_rows` + `your_teams_strip_html` already existed for the
> My Squad ▸ Health strip, so the league-wide version is the same renderer over 20 clubs instead of the owned
> ones. Once the cost was checked rather than assumed, the compromise became the obvious answer and the
> reservation did not need overruling at all. **The owner picked it.**

---

### 🔀 Alternatives Considered

- **Leave the Radar on the team tab.** It *is* fixture-derived ("best players from the easiest-run teams"), so
  there is an argument it is a fixtures output. Rejected: it returns a list of players to buy, and a user
  looking for players will look under Players. Derivation is not the same as belonging.
- **Collapse the Radar into an expander in place.** Solves page length without a move, but leaves
  player-discovery on a team tab and forfeits the IA principle for a cosmetic gain.
- **Keep the page name "Fixtures".** Rejected per the owner's own reasoning — but note the name should follow
  whatever ends up first; `🧬 Team DNA & FDR` reads wrong if the ticker leads.
- **A grouped or dropdown sub-nav on Players.** The right answer if the view list keeps growing (the 2026-08-19
  note anticipated this). Not yet: shortened labels buy the room this change needs, and a dropdown is worse to
  scan than pills while they still fit.

---

### 🧭 Consequences

**Positive** — one legible rule (team level vs player level) instead of a page that mixes both; the
differentiator leads; the Radar becomes findable by people looking for players; almost entirely a move of
existing renders, so the risk is low.

**Negative / risks (mitigations)** — a page rename changes the sidebar label and the URL slug, so any signpost
saying "the Radar's on Fixtures" goes stale (*mitigation:* repoint Help and the in-app signposts in the same
change — they are grep-able); nine views on Players is at the segmented control's comfortable ceiling
(*mitigation:* shortened labels keep it to today's three rows, and a grouped nav is the recorded next step if it
grows again); a returning tester will not find "Fixtures" where they left it (*mitigation:* "FDR" stays in the
name precisely for that, and it is a beta).

---

### 🧾 Status & follow-ups

- **✅ Built (Sprint 187), with the reservation resolved.** The Team DNA section now opens on a **league scan**
  — all 20 clubs as grade · ATT/DEF/FIX · next opponent, sortable by **Grade** or **Fixtures** — with the
  single-team card beneath it and the ticker below that. So the page leads with a scan, the scan is *ours*
  rather than commodity, and scan → drill still works because the drill sits directly under what you scanned.
  The ticker keeps the detailed week-by-week job a grade strip cannot do.
- **The scan earns its place on evidence, not symmetry.** Sorted by fixtures it reads
  `NEW C(100) · LIV B(89) · EVE B(89) · COV D(89) · BHA A(61)` — a fixture scan **and** a quality read at once,
  which the ticker structurally cannot give: it shows runs without saying how good the teams having them are.
- **`your_teams_strip_html` gained a `title` argument** and that is the entire cost of sharing it between the
  squad strip and the league scan. The trailing column is *your players* in one and *next opponent* in the
  other; nothing else differs, which is why there is no second renderer.
- **One deviation from the agreed name.** The sidebar label comes from the filename and Streamlit turns
  underscores into spaces, so a literal `&` would land in a URL where it is a query delimiter. The file is
  `3_Team_DNA_and_FDR.py` (sidebar: *"Team DNA and FDR"*); the **page title keeps the agreed `🧬 Team DNA &
  FDR`**. Renaming also changes the URL slug, so any bookmark to `/Fixtures` breaks — acceptable in a beta, and
  "FDR" stays in the name for exactly the discoverability reason the owner gave.
- **The Players sub-nav went to nine and stayed at three rows**, as measured: `Over / under-perf → Over/under`,
  `Defensive Contribution → DefCon`, `xG / xA / xGI → xG · xA`.
- **Signposts repointed** — the Players page caption that read *"the Radar (on the Fixtures tab)"* and two Help
  entries. That stale-signpost risk was called out above and it was real.
- **Follow-up (owner, same day): the scan shows the next THREE fixtures, not one.** One opponent says who is
  next; three say whether the run the FIX percentile is claiming actually looks like one. It cost nothing,
  because the format changed with it: `CHE (A) · LEE (H) · ARS (A)` would be ~162px and ellipsised on a phone,
  while **FDR-tinted chips** (`CHE`ᵃ `LEE`ʰ `ARS`ᵃ, reusing the card's own fixture idiom at strip scale) are
  ~102px — *shorter than one text pair and carrying difficulty as well*. Three gameweeks therefore fit the
  column one opponent used, and the row gained information rather than losing width.
- **Naming: `Team DNA & FDR` reads clunky (owner) — left as-is pending more tester feedback.** No better
  candidate yet that keeps "FDR" discoverable, which was the reason for including it.
- **Not this ADR:** the league-wide grade strip sketched above, and a grouped/dropdown sub-nav for Players.
