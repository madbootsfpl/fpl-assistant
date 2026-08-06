# Architectural Decision Record: Differentials / value `ask` intent

**Decision ID:** ADR-061
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — extends the shortlist intent (ADR-042) with an *ownership* lens and adds
a *single-player value* judgment. Reuses the differential threshold of ADR-044 and the one xP of ADR-041.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The natural-language layer answers "best `<position>` [under £X]" (ADR-042), already with a **value** lens
(xP per £m). Two adjacent, frequently-wanted questions aren't covered: **"best differentials"** (low-owned,
good players) and **"is X worth the money?"** (a value verdict on *one* named player). Ownership
(`selected_by`) is already ingested (ADR-044) and live now; the unified xP (ADR-041) already gives value.

**Verified on real data (2026-08-06):** all 570 players carry `selected_by` (median 0.4%, max 74.9%);
*"best differential MID ≤£8m"* (≤5% owned, xP-ranked) returns a useful list (Stach 1.3% / xP 18.4, Gakpo,
Zubimendi, Eze). **Preseason caveat:** ownership hasn't concentrated (497/570 are ≤5%), so the differential
filter is *weakly discriminating now* and **sharpens at GW1** — it still works today (removes the template
picks, xP-ranks the rest).

#### Decision Drivers
- **Reuse, don't reinvent** — the shortlist, the unified xP, the `DIFFERENTIAL_OWN = 5.0` threshold, and the
  compare player-matcher already exist.
- **Grounded + verified** — analytics decide; the LLM only narrates; every number traces to the facts
  (ADR-037).
- **Preseason-honest** — the differential lens works now but sharpens at GW1; say so.
- **Don't regress the plain shortlist** — its output must stay byte-identical.

---

### ✅ Decision

**1. A differential lens on the shortlist (US-198).** `_shortlist_query` also parses a **differential** cue
(`differential(s)` / `off-template` / `low-owned`); `differential`/`differentials` join the shortlist
**intent keywords** (routing — "best differentials" → shortlist; trends doesn't match it). When set,
`_decide_shortlist` keeps only players with `(selected_by or 0) ≤ DIFFERENTIAL_OWN` — **including 0%**
(maximally differential; xP ranking keeps it relevant — unlike the *flag*, which means "owned but rare").
The ranking is unchanged (xP, or xP/£m with "value"). `render_shortlist(rows, title, *, show_own=False)`
adds an **Own%** column only in differential mode, so the plain shortlist is **byte-unchanged**. The title +
facts note the ≤5% filter; a caption notes it sharpens at GW1. Works in `ask` **and** `chat`, paging intact.

**2. A single-player value verdict (US-199).** A new **`worth`** intent (keywords `worth`, `value for
money`, `good value`) → `_decide_worth`: match a player (reuse the compare matcher); compute `value = xP /
£m` (unified xP). Among **available** same-position players, rank the player by value and take the
**median**. A tiered, fact-derived **verdict**: `value ≥ 1.15 × median` → *"good value"*, `≥ 0.9 ×` →
*"fair"*, else *"pricey for the output"*. Facts: price · xP · xP/£m · rank / N · position median · verdict.
No player matched → a helpful message, never a guess. The verdict word comes from the analytics; the LLM
only phrases it (grounded, ADR-037).

**3. Routing precedence.** `worth` is checked **before** `shortlist` (a single-player "is X worth …" must
not fall into "best value"); "differentials" routes to `shortlist`; "most owned" stays with `trends`
(ADR-057). A routing test pins all three.

---

### 🔀 Alternatives Considered

- **A separate `differential` intent.** Rejected — it *is* a shortlist with an ownership filter; a new
  intent would duplicate the position/price/value/paging logic.
- **Fold "worth the money" into `compare`.** Rejected — compare is two-player; a single-player value verdict
  is a distinct shape (rank + median), and forcing a second player is unnatural.
- **A ceiling/EO differential model.** Deferred — needs variance/effective-ownership data we don't have yet
  (Backlog); ≤5%-owned + xP is the honest first cut.
- **Verdict vs a price-tier expectation (regression).** Rejected as over-engineered — rank + position median
  is simple, grounded, and explains itself.

---

### 🧭 Consequences

**Positive**
- Two wanted questions answered by **reusing** the shortlist, xP, ownership, and the compare matcher — small
  surface, no new data.
- The plain shortlist and every other intent are unchanged (a test pins the byte-identical shortlist).
- Grounded + verified like the rest of `ask`; works in `chat` too.

**Negative / risks (mitigations)**
- **Preseason ownership is flat** → the differential filter is weakly discriminating now; the caption says
  it sharpens at GW1 (like the momentum boards). It still removes template picks + xP-ranks today.
- **"value"/"worth"/"good value" routing could clash** → `worth` before `shortlist`; "best value" stays
  shortlist; a routing test guards precedence.
- **"worth the money" is a judgment** → the verdict is a fact-derived tier (vs the position median), not the
  LLM's opinion; the facts (rank + median) are always shown.

---

### 📊 Validation

Probed live: ownership present for all 570 players; the differential shortlist returns a sensible ≤5%-owned,
xP-ranked list. Acceptance: `_shortlist_query` parses the differential cue; `_decide_shortlist` filters to
≤`DIFFERENTIAL_OWN` and shows Own%; the plain shortlist stays byte-identical; `_decide_worth` computes the
rank + median + each verdict tier and degrades on no match; routing precedence (differentials→shortlist,
worth→value, most-owned→trends) is tested; grounding holds; the existing 546 tests stay green.
