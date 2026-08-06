# Sprint 070: Differentials / value `ask` intent

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1–2 sessions (a gate + a differential lens on the shortlist + a single-player value verdict)
**Carried Over:** none

> **Direction (owner):** extend the natural-language layer with the two lenses the backlog flagged —
> **"best differentials"** (low-owned, good players) and **"is X worth the money?"** (a single-player value
> verdict). Owner's calls: **build both**; the value verdict shows **rank among position peers *and* vs the
> position median**. Value (xP/£m) already exists on the shortlist (ADR-042) — this adds the *ownership* lens
> and the *single-player* judgment.

---

### 🔎 Verified at planning (real data)

Probed the live DB (2026-08-06):

- **Ownership is live now** — all 570 players carry `selected_by` (median **0.4%**, max **74.9%**). The
  existing **`DIFFERENTIAL_OWN = 5.0`** constant (`analytics/crowd.py`, ADR-044) is the natural threshold.
- **The differential shortlist already works** — *"best differential MID ≤£8m"* (≤5% owned, xP-ranked)
  returns a genuinely useful list: **Stach** (£6.0, 1.3%, xP 18.4), Gakpo (3.5%), Zubimendi (1.5%), Eze
  (3.3%). xP ranking keeps it relevant — no junk.
- **Preseason honesty:** ownership hasn't concentrated yet, so **497/570 players are ≤5% owned** — the
  differential filter is *weakly discriminating now* (it removes ~73 template picks) and **sharpens at GW1**
  as ownership concentrates. Same "lights up at GW1" story as the momentum boards; it still works today.
- **Value (xP/£m) is already the shortlist's `by_value` path** (ADR-042) — reused for both the differential
  ranking (when "value" is asked) and the single-player verdict.

---

### 🎯 Sprint Goal

**Objective:** two new natural-language capabilities, grounded + verified like every `ask` (ADR-037),
reusing the unified xP + the existing ownership/value analytics:
1. **Differential shortlist (US-198)** — *"best differentials [position] [under £X]"* → the shortlist,
   filtered to **≤ `DIFFERENTIAL_OWN`** owned, xP-ranked (or xP/£m with "value"), with an **Own%** column.
2. **Single-player value verdict (US-199)** — *"is X worth the money?"* → a grounded verdict: the player's
   **xP/£m**, its **rank among position peers**, and how it sits **vs the position median**.

#### Success Criteria
- [x] Approach agreed (**ADR-061**) — a differential *filter* on the shortlist (reuse `DIFFERENTIAL_OWN`,
      add Own%); a new single-player **value** intent (rank + median, grounded); both preseason-honest
- [x] **US-198** — `_shortlist_query` also parses a **differential** cue; `_decide_shortlist` filters to
      `selected_by ≤ DIFFERENTIAL_OWN`; `render_shortlist` shows **Own%** (differential mode); routes in
      `ask` **and** `chat`; paging ("who else?") still works; grounded facts include ownership
- [x] **US-199** — a `_decide_worth` handler: match a player, compute xP/£m, **rank among available
      same-position players** + the **position median**, and a tiered **verdict** (above / near / below);
      degrades to a helpful message when no player is matched (or flagged/ambiguous)
- [x] **Routing** — "differentials" → shortlist (not trends); "worth …" / "good value" / "value for money"
      → the value intent (not the "best value" shortlist, not transfer via "buy"); precedence tested
- [x] **Grounded** — every number in the narration traces to the facts (the ✓/⚠ trust line, ADR-037);
      analytics decide, the LLM only narrates
- [x] Tests green (existing stay green; + query-parse, filter, verdict-tiers, routing, no-match) — **556**
- [ ] Docs: ADR-061 + index ✅; Architecture, Roadmap/Backlog, PROJECT_STATUS, README _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-198 | **Differential shortlist lens** — "best differentials [position] [under £X]": filter the shortlist to ≤`DIFFERENTIAL_OWN` owned, xP- (or value-) ranked, +Own% column; ask + chat. ADR-061. | High | ✅ Done | ~1 session |
| US-199 | **Single-player value verdict** — "is X worth the money?": one player's xP/£m + rank among position peers + vs the position median + a tiered verdict; grounded, degrades on no match. ADR-061. | High | ✅ Done | ~1 session |

---

### 🧭 Design sketch (to settle in ADR-061)

**Differential lens (US-198).** Extend `_shortlist_query` → `(position, cap, by_value, differential)`;
`differential` true on `differential(s)` / `off-template` / `low-owned`. Add `differential`/`differentials`
to the shortlist **intent keywords** (so routing catches "best differentials" — trends doesn't match it).
In `_decide_shortlist`, when `differential`, keep only `(p["selected_by"] or 0) <= DIFFERENTIAL_OWN` —
**including 0%** (maximally differential; xP ranking keeps it relevant, unlike the *flag* which means "owned
but rare"). `render_shortlist(rows, title, *, show_own=False)` adds an **Own%** column in differential mode
(the normal shortlist is byte-unchanged). Facts note the ≤5% filter; the caption says it sharpens at GW1.

**Value verdict (US-199).** A new `worth` intent (keywords: `worth`, `value for money`, `good value`) →
`_decide_worth`: match a player (reuse the compare matcher). Compute `value = xP / £m` (unified xP). Among
**available** same-position players, rank the player by value and take the **median**. Verdict tiers:
`value ≥ 1.15 × median` → *"good value"*, `≥ 0.9 ×` → *"fair"*, else *"pricey for the output"*. Facts:
price · xP · xP/£m · rank / N · position median · verdict. No player matched → a helpful message (never a
guess). Grounded: the verdict word is derived from the facts, the LLM only phrases it.

**Precedence.** `worth` before `shortlist` (a single-player "is X worth …" must not fall into "best value");
"differentials" routes to `shortlist`; "most owned" stays with `trends` (Sprint 067). A routing test pins it.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — differential query-parse + the ≤5% filter + Own% render; the value verdict's rank +
   median + each verdict tier + the no-match message; routing precedence (differentials→shortlist,
   worth→value, most-owned→trends); grounding holds. Existing **546** stay green.
2. **Manual smoke** — `ask "best differential forwards under £7m"` (low-owned, xP-ranked, Own% shown);
   `ask "is <player> worth the money?"` (rank + median + verdict); a chat follow-up "who else?" pages the
   differential shortlist; a nonsense player name degrades cleanly.
3. **Docs updated** — ADR-061 + index, Architecture, Roadmap/Backlog, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

- **US-198 ✅ (gate + build)** — Recorded **ADR-061** (+ index; covers US-199 too). `DIFFERENTIAL_OWN`
  exported from `analytics/crowd.py`. `_shortlist_query` → a 4-tuple with a **differential** cue
  (`differential(s)` / off-template / low-owned); `differential`/`differentials` added to the shortlist
  **intent keywords**. `_decide_shortlist` filters `cands` to `(selected_by or 0) ≤ DIFFERENTIAL_OWN`
  (0% included — maximally differential), keeps the xP/value ranking + paging, and sets a differential
  title/caption + ownership in the facts. `render_shortlist(rows, title, *, show_own=False)` adds an
  **Own%** column only in differential mode — the **plain shortlist is byte-identical** (a test asserts no
  `Own%` leaks). Tests (+5): the differential query-parse, the ownership filter (template dropped, Own%
  shown), routing (`differentials`→shortlist, `most owned`→trends), the Own% render, and the unchanged
  plain render. **Smoke (real DB):** `ask "best differential forwards under £7m"` → Welbeck (2.7%, xP 15.5),
  Igor Jesus, Evanilson… with the Own% column, the "sharpens at GW1" caption, grounded narration + the ✓
  trust line; `ask "best forwards"` shows **no** Own% column. 550 tests green, ruff clean. _Cross-cutting
  docs (Architecture / PROJECT_STATUS / README / Backlog) batched to the sprint close after US-199._

- **US-199 ✅ (build)** — A new **`worth`** intent (keywords `worth the money` / `worth it` / `good value` /
  `value for money` / `worth buying` …), placed **before captain/transfer** so "worth buying" isn't caught
  by "buy" (the phrases are value-specific, so "worth captaining" still routes to captain). `_decide_worth`
  reuses the compare **player-matcher**: matches one player, computes **xP/£m** (unified xP), ranks it among
  **available same-position** players, takes the **position median**, and a tiered **`_value_verdict`**
  (`≥1.15×` → good · `≥0.9×` → fair · else pricey) — the verdict is fact-derived, the LLM only phrases it.
  Degrades on an ambiguous name, no player, or a **flagged** target. Wired into `_dispatch`; `_FALLBACK`
  updated. Tests (+6): routing precedence (worth vs transfer/captain), the verdict tiers, the rank + median
  + value facts (good-value + pricey cases), and the two degrade paths. **Bug caught in smoke:** sorting
  `(value, row)` tuples crashed on a value tie (rows aren't orderable) → switched to a `key=` sort. **Smoke
  (real DB):** *is Haaland worth the money?* → "good value — 1.87 xP/£m, 19 of 61 FWDs; median 1.00";
  *is Stach good value?* → "good value — 3.07 xP/£m, 3 of 231 MIDs; median 1.11" — grounded, ✓ trust line;
  "is it worth the money?" → "Name a player". 556 tests green, ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both lenses shipped, grounded + verified, by **reusing** the shortlist, the one
xP, the `DIFFERENTIAL_OWN` threshold, and the compare player-matcher. No new data, no new dependency; the
plain shortlist and every other intent are byte-unchanged.

**What went well** — verifying on **real data first** confirmed the differential shortlist returns genuinely
useful picks *and* surfaced the honest preseason caveat (ownership is flat, so the filter is weakly
discriminating now and sharpens at GW1 — captioned, not hidden). Threading `show_own` into the renderer kept
the plain shortlist byte-identical (a test pins it). Placing `worth` **before** transfer stopped "worth
buying" leaking into the "buy" intent — a small routing-precedence call that a test now guards.

**What to watch** — the differential lens only bites once ownership concentrates (GW1); the value verdict's
tier thresholds (1.15× / 0.9× the median) are a reasonable first cut worth revisiting once real form moves
prices. The **smoke caught a real bug** the unit tests missed — sorting `(value, row)` tuples crashes on a
value *tie* (rows aren't orderable) — a reminder that the manual smoke earns its place in the DoD.

**Lessons captured:** `docs/05_Sprints/Sprint70_Lessons_Learnt.md`.
