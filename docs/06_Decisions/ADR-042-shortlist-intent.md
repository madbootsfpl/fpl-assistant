# Architectural Decision Record: A "best players" shortlist `ask` intent

**Decision ID:** ADR-042
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Extends `ask` (ADR-034/039/041) with a seventh intent; reuses `decision_xp`
(ADR-041), the shared table renderer (ADR-025), and `verify_grounding` (ADR-037).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`ask` answers squad-relative questions (captain / transfer / analyse / start-bench) and now builds a
squad — but a manager also asks the open question *"who are the best midfielders under £8m?"*. The
ranking/value views (`xp`, `table`) have no natural-language front. This intent adds one, grounded and
on the unified xP.

#### A planning probe proved the parse + the ranking on real data
- Parse handled every case: "best midfielders under £8m" → MID/£8m; "best forwards" → FWD; "best
  defender under £4m" → DEF/£4m; "best value goalkeepers" → GK (value).
- Ranking by the unified `decision_xp` is sensible: MID ≤£8m → Mbeumo (23.3), Gibbs-White (22.2), Rice
  (20.9)…; GK → Raya (19.4), Pickford (19.2)…; £4m DEF → Furlong (7.1)… (a thin, honest list).
- **"value" ≠ "best":** "best value" should rank by xP *per £m* (Raya £6/19.4 vs Roefs £5/17.5 flips),
  matching FPL vocabulary — a small toggle worth having.

#### Decision Drivers
- **The open target-hunting question**, in plain English.
- **One metric** — rank by the same `decision_xp` everything else uses.
- **Grounded + optional** — reuse the verifier + the shared renderer; degrade without the LLM.

---

### ✅ Decision

**1. Routing.** A `shortlist` intent, keyed on **position words** (`goalkeeper`, `keeper`, `defender`,
`midfielder`, `forward`, `striker`) + `best value` + `best players`, checked **after `build_squad`** (so
"best squad/XI" still builds) and **before `compare`**. First-match-wins as ever.

**2. Parse** (`_shortlist_query(question)` → position, price cap, by_value):
- **position** → `GK`/`DEF`/`MID`/`FWD` (a word maps to a code; absent → all positions);
- **price cap** → from "under £Xm" / "£Xm" (absent → no cap);
- **by_value** → true when "value" appears (rank by xP-per-£m instead of xP).

**3. Decide** (`_decide_shortlist`). Rank the **available** pool (injured/suspended excluded, as
`squad` does) by the unified `decision_xp`; filter to the position and `price ≤ cap`; sort by **xP**
(or **xP / price** when by_value); take the **top ~8**. `subjects` = the listed players; facts = the
top few humanised (name, position, price, xP). A **clear message** when the filter matches nobody
(e.g. "best defender under £3.5m").

**4. Render + ground.** A ranked detail table (Player / Team / Pos / £ / xMins / xP — the shared
`_table` renderer), then narration + the ✓/⚠ trust line; optional (degrades to the table + facts).

---

### 🔀 Alternatives Considered

- **Rank by last-season points.** Rejected — the whole tool speaks xP now; consistency matters.
- **Ownership / differentials** ("best low-owned MID"). Deferred — needs `selected_by`; a later intent.
- **Short position forms as routing keywords** (`def`, `mid`, `gk`). Rejected for *routing* (they match
  inside common words — "definitely"); routing uses full words, the parser may accept more.
- **An intent classifier instead.** Deferred (backlog) — keyword routing still holds at seven intents.
- **No `value` toggle.** Rejected — "best value" is standard FPL phrasing; xP/£m is a one-line addition.

---

### 🧭 Consequences

**Positive**
- The open "best <position> [under £X]" question is answerable, grounded, on the one metric.
- Pure composition — `decision_xp` + a filter/sort + the shared renderer + the verifier; no new data.

**Negative / risks (mitigations)**
- **"forward"/"value" are common words** → a rare mis-route; the intent still returns a sensible list,
  and position/price parsing is forgiving.
- **Thin lists at a low cap** → honest (that's what the budget yields); a message when truly empty.
- **Preseason xP** → the same baseline-driven xP as every view; improves once the season starts.

---

### 📊 Validation

Prototyped on the live DB before code: the parse + rank produced sensible shortlists for MID ≤£8m, FWD,
£4m DEF, and GK, all ordered by the unified xP; "value" flips the order toward cheaper players.
Acceptance for the sprint: `ask "best midfielders under £8m"` returns a ranked table + the ✓ line;
`ask "best defender under £3.5m"` (or similar) gives a clear no-match message; existing intents unchanged.
