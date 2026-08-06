# Architectural Decision Record: Interpretable stat boards — quality ratings + clearer captions

**Decision ID:** ADR-071
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** new capability, **display-only**. Adds a rating/legend layer on top of the
existing stat analytics (`defensive_solidity` ADR-018, `over_under`, `defcon_reliability`, xGI ranking) and
the shared web boards (ADR-063). No analytics change. Triggered by tester question.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback on the Players stat boards: *"what does xGI 9.72 mean — or is it just relative to others in
the table?"* They correctly derived `xGC/90 = xGC × 90 ÷ mins` (Calafiori 0.52) but asked how a **casual
user** should read it, and suggested a **colour graphic beside the score** (sharing a ChatGPT band table:
0.5 = excellent … 2.0+ = very poor).

The raw `xGI`/`xGC` numbers are **absolute season totals** (a model's expected goals, last-season carryover
preseason), and `xGC/90` normalises by minutes — but *whether a value is good* is only meaningful **relative
to peers**, which is exactly the tester's uncertainty. A colour rating answers it — **if** it's calibrated
correctly.

**Verified in code (real data, this sprint):** the ChatGPT band table is **miscalibrated for FPL**. On 117
DEF/GK with ≥900 mins, xGC/90 has **median 1.36**, p25–p75 **1.22–1.40**, min 0.52, max 2.04. Applying
ChatGPT's fixed bands buckets **91/117 as "poor"** and only **1 as "excellent"** — almost everyone red.
ChatGPT's scale is *team goals-per-match* (≈1.1 average); FPL's *player xGC/90* attribution sits higher. A
fixed absolute band copied from ChatGPT would actively mislead. Also verified: `st.dataframe` has **no
per-cell hover tooltip** primitive, so a percentile must ride **inline** in the rating cell.

#### Decision Drivers
- **Casual-readable** — a colour + a plain word ("excellent" … "very poor") at a glance.
- **Honest / self-calibrating** — the rating must reflect the real field, not a wrong fixed scale; it must
  answer "is 0.52 good, or just relative?" truthfully.
- **Display-only** — no change to the analytics or the sort order; the raw number stays the source of truth.
- **Reusable** — one helper, applied where a metric has a clear "good direction".

---

### ✅ Decision

**1. A relative, quintile quality rating (hybrid: band + percentile).** New display helper
`src/web_streamlit/ratings.py::quality_band(value, pool, *, higher_is_better)` → `{emoji, label,
percentile}`. `pool` is the finite set of the metric's values **currently shown**; a value's rank within it
picks a **quintile** — 🟢 excellent · 🟢 good · 🟡 average · 🟠 poor · 🔴 very poor — and the **percentile**
("top N%", the share of the field it beats) is returned alongside. `rating_cell(...)` formats
`"{emoji} {label} ({percentile})"`. Relative (not fixed) because the real distribution is narrow and
fixed bands mislead; it self-calibrates as the field changes (incl. GW1) with no threshold maintenance.

**2. A Rating column on the two "clear-direction" boards.** In `views/players.py`, **Clean sheets**
(xGC/90, lower = better) and **xG** (xGI, higher = better) gain a **Rating** column via `rating_cell`, plus a
one-line **legend** caption ("rated vs the players shown — 🟢 best 20% … 🔴 worst 20%"). The rating is
computed over the **filtered** board (all pages), so a player's rating is stable across pagination and
re-scales only when the filter changes (the legend says "vs the players shown"). The **over/under-perf** and
**DefCon** boards are *signed* (they already show +/- direction), so they get **no** colour rating — a band
would add noise, not clarity.

**3. Clearer captions + per-column tooltips on all four boards.** `_board` accepts an optional
`col_help` map → `st.column_config.Column(head, help=...)`, so each metric column carries a plain-English
tooltip (absolute season total vs per-90; higher/lower = better). Captions restated to say what the number
*is*, not just how it's ranked.

**4. Scope + placement.** Web edge only (the tester's context); the CLI stat commands are unchanged (could
adopt later). The helper lives in `web_streamlit/` (display policy at the edge) — analytics stays pure. No
server writes.

---

### 🔀 Alternatives Considered

- **Fixed absolute bands (ChatGPT's table).** Rejected on real-data evidence — mislabels 91/117 "poor". Even
  re-calibrated fixed thresholds need re-checking every data refresh; relative bands don't.
- **A true per-cell hover tooltip for the percentile.** Not available in `st.dataframe`; the percentile
  rides inline in the rating cell instead (colour + number, both visible).
- **Rating on all four boards.** Rejected — the signed over/under and DefCon metrics already communicate
  direction; a quintile band there competes with the +/- sign.
- **A numeric 1–5 / letter grade.** Rejected — a colour + a word is more scannable for a casual user; the
  percentile gives the precise anchor.
- **Move the helper into analytics.** Rejected — it's a *display* concern (pool-relative, presentation
  vocabulary); keeping it web-side preserves the pure, one-way analytics core.

---

### 🧭 Consequences

**Positive**
- A casual user reads each defensive/attacking metric at a glance, with an honest "vs peers" anchor.
- Self-calibrating — no fixed thresholds to maintain; correct today (carryover) and at GW1 with no change.
- Zero analytics drift; the raw numbers + sort order are untouched; no server writes.

**Negative / risks (mitigations)**
- **"Relative" can confuse** ("excellent vs whom?") → the legend states "rated vs the players shown", and the
  percentile makes the field size explicit.
- **A narrow filter → a tiny pool → coarse quintiles** (e.g. 3 players) → acceptable and honest; the legend's
  "vs the players shown" covers it.
- **Preseason values are last-season carryover** → the rating reads correctly now and sharpens at GW1 with no
  code change.

---

### 📊 Validation

Verified: the ChatGPT fixed bands fail on real data (the evidence above); quintiles over the real pool place
Calafiori 🟢 excellent (top ~1%) and Dubravka near 🔴 very poor. Acceptance: `quality_band` returns the right
quintile + percentile for lower- and higher-is-better metrics (ties, a 1-element pool, the extremes); Clean
sheets + xG render a Rating column + a legend; all four boards show a clarifying caption + column tooltips;
the analytics + existing 598 tests are unchanged (new tests added for the helper + the boards).
