# MADBOOTS Roadmap

*Re-cut 2026-08-24 (post-GW1) into a single forward-looking page with an explicit **end-state vision**.
Everything known is pulled in — including things we may well decide **not** to build; a parked idea with a
recorded reason is worth more than a forgotten one. Phase 1 shipped as a **CLI** (ADR-002/003), not the
original web-first plan; that plan and its reconciliation live in git history and the per-sprint docs.
Previous consolidations: 2026-08-05 (Sprint 050), kept current through Sprint 172.*

**Status legend:** ✅ Done · ◑ Partial · ⬜ Not started · ⏳ Gated (waiting on data or a decision) · 🅾️ Declined

---

## Where we are — 2026-08-25, GW1 played

A mature FPL assistant: an analytics + optimisation core, a decision-support suite, a grounded
natural-language layer (`ask` + `chat`), a deployed Streamlit web app, a crowd/signals lens, and the two
differentiators — **Player DNA** (ADR-118) and **Team DNA** (ADR-119).

**1285 tests · 134 ADRs · CI green · live at madboots.streamlit.app / madboots.com.**

**GW1 (2026-08-21) has been played and the season is live.** The data-hardening flip is done: per-GW history is
backfilled (609 players), and the season-to-date surfaces that reset at rollover now fall back to last season
until they can answer for themselves (ADR-126). What remains gated is **calibration** — the weights stay 0 until
`calibrate` clears its ≥4-gameweek guard at ~GW4-6.

GW1 cost us **nine-plus bugs of one species**: code that had shipped correct-looking and had **never executed
under real data** — a flag that only lies mid-gameweek, a `max()` that only misbehaves once `points_per_game`
is non-zero, `.get()` on a `sqlite3.Row` in a loop that had always been empty, a primary key that held until a
double gameweek, and *three separate cases* of a missing value rendering as a confident zero. Preseason green
tests proved much less than they appeared to.

Two habits came out of it and are now standing practice: **audit before a first occurrence** (a deliberate
DGW/BGW pass found three more bugs *ahead* of the event — repeat it before the first blank and the first chip
deadline), and **prototype before building** (it changed or shrank four features — ADR-125, 130, 131, 132 —
each time because a measurement contradicted a plausible assumption).

---

## ✅ Delivered — the condensed trail

*Kept compact on purpose; the full record is in `docs/05_Sprints/` and the [ADR index](../06_Decisions/ADR-000-index.md).*

**Core engine (CLI).** FPL API client + SQLite cache (upsert, generic migrations); ClubElo as a best-effort
second source. Custom FDR (overall + Elo), pts/£m value, **xP over a multi-week horizon**, xG/xA/xGI/xGC,
over/under-performance, DefCon, clean-sheet solidity. **One xP recipe** (`decision_xp`, ADR-041) shared by the
optimiser and the decision layer — so a squad built on xP has no phantom free transfers. **xMins v0** (ADR-038)
weights xP default-on at every decision edge. An **ILP squad selector** (PuLP) — best XI or full 15, formations,
declared bench, include/exclude, archetypes (ADR-043/044), bench-aware builds (ADR-045).

**Decision support.** `captain` (ADR-029) · `transfer` ranked by XI-gain (ADR-046) + a coordinated plan
(ADR-035) · `analyse` with a per-GW breakdown (ADR-032) · a grounded **gameweek plan** (ADR-070) · a v0
**chip-timing advisor** (ADR-082) · a **price-change predictor** (ADR-092) · **set-piece takers** (ADR-081).

**Grounded language layer.** `ask` — eight intents, all *analytics-decide, LLM-narrates*, every answer
**verified** against the data (✓/⚠, ADR-037); `chat` (ADR-047) with follow-ups; an FPL **rules** assistant over a
curated KB (ADR-085). The LLM is optional — absent, it degrades to decision + facts.

**The web edge.** A thin FastAPI slice (ADR-050, now **frozen** as the lean "also-serves-HTTP" reference) → a
measured **Streamlit spike + decision** (ADR-051) → the app we grow (ADR-052), **deployed** to Community Cloud
(ADR-053). A CSS **pitch view** (ADR-084), a **countdown** banner (ADR-086/088), the **My Squad / 🧪 Squad Lab**
IA split (ADR-105), a **player-actions panel** (ADR-108), a **per-GW xP toggle** (ADR-121), **scrollable stat
boards** with honest sort (ADR-116), a ⭐ **Watchlist** (ADR-117), **compare two players** (ADR-110).

**The differentiators.** **Player DNA** (ADR-118, S168-171) — AI Verdict → 8-axis percentile radar → AI Insights
→ performance trend, on Players ▸ Card and My Squad. **Team DNA** (ADR-119, S172) — the same fingerprint for a
club, via Fixtures ▸ 🧬 Team DNA and the My Squad ▸ Health "Your teams" strip.

**Crowd & signals (Phase 6, Tiers 1-2).** Crowd/momentum ingestion + `crowd_flags` (ADR-057), a Trending page,
an FPL **news lens**, **manager-ID import** (ADR-058), Reddit **RSS buzz** (ADR-076), **media headlines**
(ADR-093) — all degrade-gracefully, display-only.

**Product & ops.** MADBOOTS rebrand (ADR-103) · Google auth + per-user persistence (ADR-106) · cross-device
squads (ADR-094) · beta gate, waitlist and self-service unsubscribe (ADR-087/102/122) · anonymous usage
analytics (ADR-100) · the calibration harness (ADR-101).

**Post-GW1 (2026-08-24).** "Upcoming" fixtures cut by **gameweek deadline**, not FPL's `finished` flag
(ADR-123) · the cold-start xP rate shrinks by **evidence, not value** (ADR-124) · the full **per-GW history
backfill** · the gated boards, Team DNA key-players and Player DNA all **fall back to last season** rather than
showing nothing (ADR-126) · in-season xMins **deferred** with its trap recorded (ADR-125).

---

## 🎯 The end state — what MadBoots is trying to be

**A tool that tells you what to do and shows its working — and admits what it doesn't know.**

The market splits into **solvers** (fplapex — optimise hard, explain nothing) and **viz tools** (aceanalyst —
show everything, decide nothing). MadBoots straddles both *and* narrates. The nearest neighbour in philosophy is
**fplanalyser** — grounded and narrative, squad grades, plain-English verdicts, "a plan not a panic".

⚠ **Recalibration (2026-08-19):** *"we explain, they don't"* is a weak claim against fplanalyser — they explain
well too. The real edge is **execution + the DNA visuals + free/honest positioning + the full workflow in one
place.** Own the *explain + DNA + honesty* lane; don't try to out-solver a solver.

### Where we actually stand (2026-08-25)

This stopped being a list of things to borrow. We have now shipped against three of the four, and **twice
declined to copy a rival's feature because our own measurements said it wouldn't work here**:

| rival | their signature | where we are |
|---|---|---|
| **fplanalyser** | Squad Risk Monitor · Squad-grade DNA · forward planner | **all three shipped** (ADR-130/131). The planner is **deliberately different**: their projected-points-vs-average framing is *noise* on our numbers (a squad's per-GW xP varies ±3%), so ours leads with fixture **exposure**, which swings 2→7. |
| **fplapex** | multi-GW transfer path · chip-sequence scan · competitive layer | Path search **declined on evidence** (ADR-132): the best sell was the same player in all six gameweeks and the market yielded *one* beneficial move — a tree with one branch. Shipped the **timing arithmetic** instead. **Chip scan resolved** (ADR-143): the ranking declined on evidence (worth 0.3 xP), the legality defect it hid — two chips advised for one gameweek, 28% of squads — fixed. Competitive layer **partly** shipped as 🏆 Leagues (ADR-141): the *differentials* half is live (effective ownership vs global, captain split, chips, movers). **H2H and the win-probability sim are still open** — see the detailed item. |
| **FFH** | the rich player card · click-a-player menu | Card beaten on our own metrics (xP · value · ownership tier · DefCon · set-pieces — none of which they show). **Tap-the-pitch live and Cloud-verified** (ADR-133). |
| **aceanalyst** | pool-wide value-frontier scatter | **Shipped** (ADR-138) — and made ours: the hover carries a tested *verdict*, not a coordinate. Building it also exposed an xMins blind spot no ranked surface had surfaced, because a frontier promotes cheap-and-high numbers rather than burying them. |

**The divergences are the position, not a shortfall.** Anyone can copy a screenshot; what is hard to copy is
having measured *whether the thing behind the screenshot works on your own data* — and having written down the
answer. Both declines are recorded with the numbers that produced them, and both carry a **checkable trigger**
for revisiting (ADR-132's is explicit: if the best move ever differs by gameweek, or three-plus beneficial moves
co-exist, the tree becomes well-posed).

**The honesty half is no longer a slogan.** When a board can't answer it says so and names the season it is
showing instead (ADR-126). When a pool can't rank a player it says that rather than drawing a shape (ADR-133's
radar guard). When a tester can't be assessed the roster shows "—" rather than 100% risk (ADR-130). When a
projection barely moves, the card says so rather than letting a 3% wobble read as a forecast (ADR-131). That is
**six or so places enforced by tests**, and it is the one lane none of the four compete in.

**In full, the end state is:**
1. **A decision engine** — one xP recipe, calibrated on real returns, with a multi-gameweek transfer path and a
   full chip-sequence plan.
2. **An explanation layer** — every recommendation carries a grounded *why* (Edge / Risk), verified against the
   data, never the model's imagination.
3. **A DNA layer** — player, team and squad fingerprints that make a shape legible at a glance.
4. **A triage layer** — what needs your attention this week, and how much you'd regret ignoring it.
5. **An honest layer** — degrade visibly, label the source, never render a guess as a measurement.
6. **An interaction layer** — tap a shirt, not a dropdown (see *Interaction*, below).

---

## 🥇 Next up (agreed 2026-08-24)

1. ✅ **Player DNA — real sparklines + W-D-L form dots.** Done (ADR-128, Sprint 179). Dots live now; the
   sparklines draw from GW2, by design — a line through one point is not a trend.
2. ✅ **Team DNA — real clean-sheet rate + team form.** Done (ADR-128, Sprint 179). Falls back to the labelled
   proxy per team, so a club yet to kick off keeps the estimate instead of reading 0%.
3. ✅ **`_percentile` midrank fix.** Done (ADR-127, Sprint 178) — shipped as the classic percentile rank. It counts peers "at or below", so in an all-tied pool a zero lands in the
   90s — **A.Becker, a goalkeeper, reads Goal Threat 96th percentile on a raw 0.00**. Pre-existing (ADR-118),
   exposed when the DNA fallback made percentiles visible again. Fix = `(below + 0.5 × equal) / n`, which puts
   an all-tied pool at 50. **Shifts every percentile in Player and Team DNA → needs its own ADR.**

---

## ⏳ Data Hardening — gated on ~GW4-6

Prep is done and dormant (Sprint 069, ADR-060); the harness is built (Sprint 138, ADR-101) and the flip is
scripted in the **[GW1_RUNBOOK](../GW1_RUNBOOK.md)**. `calibrate` prints its own countdown — currently
*"have 1, need ≥4"*. **The harness recommends; the owner commits.** One weight at a time (ADR-101).

- ✅ **Per-GW history ingestion** — done 2026-08-24; re-run after ADR-128 widened the table (609 players,
  2051 season rows + 609 per-GW rows, now 27 columns).
- ⏳ **`FORM_WEIGHT` calibration** — the main season signal; first of the three.
- ⏳ **`SET_PIECE_WEIGHT` calibration** (ADR-096) — then revisit the tier guard against observed returns.
- ⏳ **`DEFCON_MAGNIFIER_WEIGHT` calibration** (ADR-097).
- ⏳ **PARKED QUESTION — should `decision_xp` be more fixture-sensitive?** Two features came back smaller than
  the roadmap described for the same underlying reason: the fixture multiplier is ±20% at its extremes
  (ADR-006), so a squad's per-gameweek projection varies by **±3%** (ADR-131) and one player's best transfer is
  **the same in every gameweek** (ADR-132). That is a deliberate property of a smooth metric, not a bug — but
  it is worth *measuring* rather than assuming. Belongs in this sitting because `calibrate` can answer it:
  sweep the multiplier as a weight and see whether a sharper one improves rank correlation. **Do not change it
  to make a chart look better** — that is the one thing both ADRs refused.
- ⏳ **In-season minutes in the xMins share** (ADR-125) — deliberately paired to the same sitting: same
   threshold, same data. ⚠ Whoever builds it must not infer "played" from a per-GW row's presence — **FPL
   writes the row when the fixture is scheduled, not played**, so a naive minutes share zeroes two whole clubs
   for the two days their gameweek is in flight.
- ⬜ **Rolling 3-/6-GW form windows + trend views** — now unblocked by the widened per-GW table (ADR-128).
- ⬜ **Per-season price sparkline** — long open in the backlog; the per-GW `value` column now exists (ADR-128).
- ✅ **Price-change predictor** — shipped (Sprint 112, ADR-092) and live: 10 🔺 / 9 🔻 flags on GW1 data.
   *(This page listed it as not-started for months; corrected here.)*
- 🅾️ **Attack/Defence FDR split** (ADR-005) — **blocked at source, not by timing.** Checked the live API on
   2026-08-24: `strength_attack_home` and friends are **still 0 after GW1**, and the `teams` table doesn't even
   carry the columns. FPL is not populating them. This dies unless we **derive our own attack/defence strength
   from results** — a different and much bigger piece of work. **Needs a decision, not a wait.**

---

## 🖱 Interaction — the FFH-style click layer

**The thread the owner explicitly did not want lost.** Testers keep describing Fantasy Football Hub's
interaction: *"FFH pops a menu on **clicking** a player — full card · substitute · captain."*

- ✅ **The panel** (ADR-108, Sprint 149) — one selection → card + 👑 captain + 🔁 substitute. Shipped as the
  achievable shape: **click-to-select → an actions panel**, because a static `st.markdown` pitch cannot fire a
  click callback (established the hard way in S139/142). Explicitly built as **a foundation, not a stopgap**.
- ✅ **My Squad v2 — tap-the-pitch** — **shipped** (ADR-133, Sprint 185). Both of the deferral's grounds were
  tested by spike 185 and neither held: a pre-built PyPI component means no build toolchain, and keeping the
  dropdown means the selection path keeps its coverage. ✅ Cloud-verified 2026-08-25. *(original entry:)* A
  custom **Streamlit JS component** so **tapping a shirt** returns the player id → opens the *same* ADR-108
  panel. **~90% is already built** — only the selection *input* changes, dropdown → tap.
  - **Why it was deferred:** it introduces a **front-end build toolchain** to a pure-Python project, and the
    component can't be AppTested — so the golden page loses its coverage. It was also nine days from GW1.
  - **Needs its own spike + ADR**, comparing: a **full custom React component** vs a **lightweight
    click-detector reusing `pitch.py`'s existing HTML with per-kit ids** — plus a **Community Cloud deploy
    check**. The lightweight path could more than halve the cost.
  - **Trigger:** feedback-driven. Ship the panel, watch the testers; if *"I want to tap the shirt"* stays the
    top ask, that's the green light.
- ↩️ **Actions on the entity — a density change** (ADR-135, Sprint 189) — **built, hit its number
  (6-7 widgets → 3), REVERTED the same day.** The tap-to-select half (ADR-133) stays and works; the action
  **menu** on the shirt is gone. Cause: every tap is a full Streamlit rerun with a `decision_xp` recompute, so
  a two-tap flow cost two round-trips — a floating menu advertises client-side responsiveness we cannot
  deliver, and it collided with the neighbouring cards' hover popovers. **Widget count was a bad proxy for
  clutter**; three fast controls beat one slow menu. Read ADR-135 §Outcome before re-opening this.
  ⬜ The league-scan rows should inherit **selection**, not a menu — a row tap that selects is ADR-133's shape
  and is still wanted; a row tap that opens a menu is this ADR again. The density goal stands; the mechanism
  for reaching it does not.
- ✅ **The player card opens on a TAP, not a hover** (ADR-139, Sprint 193, 2026-08-25) — *owner,
  2026-08-25.* Reading the code changed the fix: the panel **already** rendered the full card for whoever is
  selected, and ADR-133's tap already drove that with the teal outline — so the behaviour existed and the
  hover popover was a second, compact, floating copy on a worse trigger (it fires on whatever the cursor is
  over, not on what is selected, which is how one player's stats appeared beside another's selection). The
  rule shipped is **hover exists only where tapping doesn't**: suppressed when `clickable=True`, kept on Squad
  Lab's build preview and on the ADR-133 fallback, which gets it back for free. The card also moved **above**
  the Boot Battle controls — the half that actually delivers the ask. Exposed a test that had asserted nothing
  since ADR-133; see the ADR.
- 🅾️ **Drag-and-drop to reorder the bench** (ADR-084) — rejected; the ⬆/⬇ controls do the job without JS.

---

## 🧭 Interface & information architecture

- ✅ **Fixtures IA restructure** — built (ADR-134, Sprint 187). Team DNA leads, opening on a **league-wide
  scan** of all 20 clubs (which resolved the scan-vs-drill tension rather than trading it off); ticker second;
  🎯 Radar moved to a Players view.
- ⬜ **Squad Lab icon → a lab motif** — swap the 🥾 boot on the Squad Lab header for a flask/test-tube; it fits
  *Lab* and distinguishes it from the boot-branded rest. **Needs the art** (clean transparent PNG).
- ⬜ **Homepage copy is stale** — `madboots.com` still says *"No login to look around · your squad saves across
  devices by a handle"*, untrue since Google auth went live (2026-08-12). ⚠ **The homepage source isn't in this
  repo** (Cloudflare Pages) — owner to point at the file or we rebuild it. Also needs **hello@madboots.com** to
  exist as a real inbox.

---

## 📊 Analysis & decision features

**Competitive-inspired (⭐ = the data already exists, near-term feasible):**

- ⭐ ✅ **Squad Risk Monitor** — done (ADR-130, Sprint 182). *(fplanalyser)* — one row per owned player, sorted by **how much attention he
  needs / how likely you are to regret holding him** — not how good he is. A **driver** (Minutes / Fixtures),
  "% chance he doesn't reach 60", an attention rating. We hold everything needed (xMins → chance-under-60;
  fixture difficulty). A sharp triage the Health tab lacks.
- ⭐ ✅ **Squad-grade DNA** — done (ADR-130, Sprint 182). *(fplanalyser + our engine)* — aggregate the owned 15 into **one graded picture**:
  overall grade + Attack / Defence / DefCon / Fixtures bars + a verdict headline + a grounded edge line
  ("3 penalty takers = a deliberate edge"). A squad-level sibling of Team DNA; reuses the engine.
  **Pairs with Squad Risk Monitor — both aggregate the owned 15 and would share plumbing.**
- ✅ **Pool-wide value-frontier scatter** *(aceanalyst)* — **BUILT** (ADR-138, Sprint 192, 2026-08-25) as
  **Players ▸ Value**. Justified by measurement, not by the rival: only **4 of 8** frontier players are also
  top-8 by raw xP, and the best £4.5 player is **+11.9 xP** clear of the median £4.5 player — nearly what
  £4.5 → £8.0 buys for £3.5m, and no ranked list showed those together. **MadBoots spin delivered:** a hover
  verdict computed in `analytics.value` and unit-tested, not a dot to interpret. Two owner review rounds
  changed it materially — the crowding was the **axis** (94% of players in 24% of the width), fixed by
  plotting only decisions; and **a player who has not featured can no longer hold the frontier** (`yet_to_play`),
  which swapped a backup keeper off it. ⬜ *Not built, deliberately:* the xGI × points and DefCon × points
  axis pairs — different questions the stat boards already rank. A metric selector is the follow-on if asked.
- ◑ **Multi-GW transfer-path planner** — the **timing arithmetic** shipped (ADR-132, Sprint 184: use it /
  bank it / take the hit); the **path search itself is declined on evidence** — the best sell was the same
  player in all six gameweeks and the market yielded one positive-gain move, so the tree had one branch. A
  checkable trigger to revisit is recorded in the ADR. *(original line, for the trail)* — plan several
  gameweeks ahead as a path/tree, pricing **hits (−4 now vs rolling)** against total xPts. **MadBoots spin:** a
  grounded *why* per move (Edge/Risk each step). Reuses `suggest_transfers` + `by_gameweek`. Pairs with the
  per-GW xP toggle (US-422). *(A coordinated greedy plan already shipped, Sprint 033 — this is the real one.)*
- ◑ **Full chip-sequence scan** *(fplapex)* — the **ranking is declined on evidence** (ADR-143, Sprint 197);
  the **legality defect** it would have hidden is fixed. Measured over 200 random legal squads on live data:
  two chips want the same gameweek **28% of the time** (so not a one-branch tree), but resolving it optimally
  is worth **0.3 xP median / 1.5 worst** — the same order as ADR-131's ±3% noise. A precise ordering on
  numbers that cannot carry one. **What was real:** the app was advising two chips in one gameweek, which FPL
  forbids and `fpl_rules` explicitly states — contradicting its own knowledge base. Chips now take distinct
  gameweeks, the one with the least at stake moves, and it says what that cost (0.0 xP median). *Third
  sequence/tree feature killed by a measurement here — our projections are smooth, and smooth projections make
  optimal ordering worthless.* *(A v0 chip-timing advisor shipped — Sprint 096, ADR-082.)*
- ✅ **Forward GW planner — "a plan, not a panic"** — done (ADR-131, Sprint 183), but **built differently
  from this line**: measured on our own data, the per-GW xP spread is ±3% while fixture exposure swings 2→7, so
  it leads with exposure and states the xP range instead of naming a "problem week" out of noise. *(original
  line, for the trail)* — per-GW projected-points-vs-your-average
  bars + *"your problem week is GW6, five weeks out"* + N-hard-fixtures per GW + which players face them.
  Extends the per-GW xP toggle into a multi-GW forward view. Bigger build; needs in-season data.
- 🅾️/✅ **Player clashes** — the **framing rejected on evidence**, the real quantity underneath it **built**
  (ADR-145, Sprint 199, 2026-08-26). Measured: clashes are **universal** (100% of 300 random squads, ~26 pairs
  over 5 GWs; still 7.4 filtered to XI defensive-vs-attacker) so a list is wallpaper — and **a clash costs no
  expected points**, because `decision_xp` already prices each player's own fixture. It changes the *joint*
  distribution, not either marginal: same expected score, **lower variance** — which is good when protecting a
  lead and bad when chasing (ADR-141's logic). Shipped **fixture concentration** instead: how much of a
  gameweek's XI projection rides on one match (live spread: median 29% · p75 34% · p90 40% · max 64%), flagged
  above p75, naming the match and the players. The clash survives as a **qualifier** — players on both sides
  means their returns partly cancel.
- ✅ **Captain margin** (ADR-144, Sprint 198, 2026-08-26) — shipped, and the measurement turned a cosmetic line
  into one with an opinion. Across 300 random legal squads the lead over the runner-up is **p25 0.20 · median
  0.60 · p75 1.00**, and **44% of squads separate their top two by under half a point** — so a medal plus
  "Confidence 91/100" was implying certainty the data mostly doesn't support. The verdict thresholds **are
  those quartiles**, so "a clear pick" means the top quarter of real leads. A whisker now says *"too close to
  call; take the one you fancy"* — a decision tool's job includes knowing when it hasn't decided. The old
  duplicate narrow-lead risk bullet was removed.
- ✅ **Import a league — and compare against it** (ADR-141, Sprint 195, 2026-08-26) — *owner, 2026-08-25.*
  Shipped as **🏆 Leagues**: a classic league by id, or the global Overall league as the **elite** preset (same
  code, different id). **Justified by measurement:** across the top 50 managers in the world, Palmer sat at
  **62% effective ownership against 11.9% global** — every other surface here calls that a differential; among
  the people winning it is template, and global ownership cannot tell them apart. Also the captain split
  (21/8/7) and that **47 of 50 played Bench Boost**. **The cost came in 5× below the estimate** that nearly
  deferred it — the table is ONE call, and the insight layer needs the current gameweek only, not a history.
  **Find a league by your MANAGER id** — nobody knows their league id, and `/entry/{id}/` already lists them (private leagues first; FPL's automatic club/region/Overall ones are 100,000× bigger and would bury them). Affordable because a completed gameweek's picks are **immutable**: cached with no expiry (17.5s first load,
  0.0s after). Insight sits behind a button — *nothing that costs N calls happens because someone opened a
  tab*. ⬜ Not in v1, deliberately: **transfer flow** (one more call per manager) and **H2H leagues** (a
  different endpoint).
- ✅ **Transfer advice names the dead slot** (ADR-136, Sprint 190, 2026-08-25) — *owner, 2026-08-19.*
  `suggest_transfers` ranks by starting-XI gain (ADR-046), so a departed player on the bench moved that number
  by zero and the advice read *"hold"*. Now asked as a separate question: a slot that cannot score for the
  whole horizon is named, with the **reason** (*"gone"* · *"out until 28 Nov"* · *"no return date"*) and the
  best legal replacement. The design turns on telling a **permanent exit from a two-week injury** — 94 players
  are unavailable and `decision_xp` scores all of them 0.00, so the only signal is FPL's news text, parsed
  into *how many of your next N gameweeks he misses*. Doku (back 5 Sep) is held; Minteh (back 28 Nov) is not.
  Surfaces: CLI · `ask` · web ▸ Transfer (one-click Replace). No `decision_xp` change.
- ✅ **Squad Lab's three build modes are really two** (ADR-137, Sprint 191, 2026-08-25) — *owner,
  2026-08-19.* Measured before building, and it was worse than reported: "Bench Boost" produced the same
  fifteen as "Balanced" **even when run with `bench_weight=1.0`**, because maximising the XI plus a
  full-weight bench *is* maximising all 15 — it could never have been a distinct build. The two that exist
  were also named backwards ("Balanced" was the max-15, £23.5m, strong-bench build). Now **All-round (strong
  bench)** and **Strong XI (cheap bench)**, with Bench Boost answered as a caption where the question is
  asked. Default unchanged, deliberately: the XI-first build is +7.2 XI xP but buys a bench with a 4.9-xP
  near-dead slot — a real trade, now honestly labelled. No optimiser change.
- ✅ **A loaded league persists between sessions and across devices** (ADR-147, Sprint 202, 2026-08-26) —
  *owner, 2026-08-26.* New `prefs.py` on the proven per-user pattern (ADR-106/117): keyed by
  `auth.user_key(email)`, **no new secret**, restored once per session, written only when a value changed.
  **Remembers the manager id, not just the league** — a stored league restores one league, a stored manager id
  restores the *list*. Signed out → session-only, i.e. today's behaviour. ⏳ Owner: create `user_prefs` (SQL
  in the ADR, with all three RLS policies) — until then it degrades silently and **Admin ▸ 🔧 says so**, the
  diagnostic shipping *with* the feature rather than after a day of NULLs (the ADR-142 lesson).
  ✅ Follow-up **done same day** (ADR-148): `remove_me` now deletes `user_prefs`, and checking it found that
  ADR-147's own SQL had **no `delete` policy** — so the delete would have been refused *silently*, telling
  someone their data was gone while it was still there. SQL corrected in three places; `remove_me` now returns
  a per-table status so the promise is checkable.
- ✅ **"My squad only" reaches Community Signals** (ADR-149, Sprint 204, 2026-08-26) — *owner,
  2026-08-26.* ⚠️ **My triage of this was wrong in both directions:** the four Trending *boards* have honoured
  the shared filter since US-407b; the one surface that did **not** is the 💬 **Community Signals** tab — which
  is exactly what the owner named, by its on-screen heading. Now filtered too, **after** the scan so the full
  count stays visible (*"6 of 47 players mentioned match your filter"* — six alone says nothing), with an
  empty result telling you how to get back out. *Lesson recorded: a triage note written from memory is a guess
  wearing the clothes of a decision.*
- ✅ **One 📡 Signals page** (ADR-150, Sprint 205, 2026-08-26) — *owner question, 2026-08-26.* Counting them
  properly changed the answer: there were **four** lenses across two pages, not two — News already held
  official news *and* media headlines, while Reddit's discussions and mention counts sat on Trending beside
  ownership percentages. ADR-146's exodus was a fifth with **no browse surface at all**. The axis was never
  *official vs unofficial* but **doing vs saying**: Trending = what the crowd is doing, in numbers; Signals =
  what is being said, in words. Signals descends by **evidentiary strength** (official fact → our exodus
  inference → named outlets → a mention count), each labelled — *a merged page must label its sources or the
  merge becomes the misinformation*. 🐛 Gave the exodus a browse list and found ADR-146's threshold needed an
  **ownership floor**: per-1%-owned divides by a small number, so 0.1%-owned players read as stampedes (17
  players → 8). The floor is the population the p10 was measured on. ⚠️ `/News` → `/Signals` breaks bookmarks.
- ⬜ **Ceiling / "differential" captaincy** — `captain` ranks by *mean* xP; add a variance/ceiling lens for when
  you need a differential rather than the safe pick.
- ◑ **The competitive layer** *(fplapex)* — **partly shipped.** ✅ *Differentials vs your rivals* is live as
  🏆 **Leagues** (ADR-141): league import by manager id, standings + movement, **effective ownership vs
  global** (the number that decides differential-or-template), captain split and chip usage.
  ⬜ **Still open: mini-league H2H** and a **win-probability sim** — *"what do I need to do to catch him?"*,
  which needs per-manager projections rather than per-player ones. Needs the **leagues API**; picks are public
  from the GW1 deadline, so this is **unblocked**. Reinforces the Crowd/Signals track rather than the solver one — it answers *"what do I need to do
  to catch him?"*, which is a different question from *"what's the best squad?"*. **Mini-league position also
  sharpens the chip advisor** (ADR-082): when to burn a Wildcard depends on whether you're chasing or defending.
- ⬜ **DGW/BGW detection** — sharpens the chip advisor; in-season data.
- ⬜ **Probabilistic xMins (the full ML model)** — per-fixture expected-minutes *probabilities* from schedule
  density, European congestion, rotation profiles. Needs in-season per-GW minutes to train, external
  European-fixture data, and a real ML effort. The rigorous successor to xMins v0 — **Phase 5, genuinely far off.**
- ⬜ **Evaluation & feedback loops** — did the suggested captain beat the template? Golden-gameweek regression;
  xP calibration; captain hit-rate; net season points. *Critical before fully trusting recommendations* — and
  the only item that tells us whether any of the above actually helped.

---

## 🗣 Crowd, signals & the language layer

Tiers 1 and 2 shipped (ADR-057/058/059/093) — crowd flags, a Trending page, an FPL news lens, manager-ID
import, Reddit RSS buzz, media headlines. Momentum boards are live now that GW1 has run.

- ⬜ **Tier 3 — the crowd backtest**: does following vs fading the crowd beat xP-only? Ties into *Evaluation*.
- ⬜ **Reddit r/FPL aggregate sentiment** — needs the Reddit API + a Cloud secret (RSS buzz is a *count*, not
  sentiment).
- ⬜ **Pundit / video NLP** — LLM-summarise FPL YouTube / articles into structured signals. Research-heavy.
- ⬜ **More `ask` intents** — differentials; a persisted chat; an LLM intent classifier.
- 🅾️ **X/Twitter signals** — paid/restricted. Skipped.
- 🅾️ **Betting/odds as a lens** (ADR-093) — declined *as a lens*; a possible **Tier-3 modelling input** later,
  never a display.

---

- ✅ **Price arrows use the colour channel: green up, red down** (ADR-140, Sprint 194, 2026-08-25) —
  *owner, 2026-08-25.* Confirmed the bug: 🔺/🔻 are **both red** (U+1F53A is literally "red triangle pointed
  up"), so direction was carried twice and colour carried nothing. Not a one-character swap — no green
  triangle exists in emoji, and an emoji's colour cannot be overridden. Shipped **one plain pair `▲`/`▼`**
  (`PRICE_UP`/`PRICE_DOWN`, imported by the CLI too) that inherits colour, plus a **pandas Styler** for the
  dataframe column and `:green[…]`/`:red[…]` markdown for captions. Dead ends recorded: `TextColumn` has no
  colour, and `MarkdownColumn` renders only in a click-through overlay. The retrospective 💰↑/💸↓ pair stays
  uncoloured on purpose — a Styler paints whole cells, and those share one with four other flags.
  colour is the easy part.
## 🔬 Data sources we've evaluated and declined

Kept so the reasoning isn't re-litigated:

- 🅾️ **soccerdata / npXG** (ADR-016, Sprint 015) — matching works (~95% FPL↔Understat) and npXG is real, **but**
  the value is narrow (penalties score points in FPL, so penalty-inclusive xG is the relevant signal) and the
  cost is high: 14 → 72 packages including a selenium/pandas stack, scraping fragility, a season-alignment trap.
  **Revisit only if a decision-driving need appears that FPL can't meet** — and prefer a *lightweight direct
  Understat fetch* over the full library. Evidence: `spikes/015-soccerdata/`.
- ⬜ **Player-card "advanced" stats — Key Passes + Shots in the Box** — FFH shows them; they're not in the FPL
  API but *are* reachable from a free Understat/FBref fetch (per-shot coords → "in box"; KP direct). Same
  decision as above — **its own sprint and data-source ADR** if the card wants them.
- ⬜ **Shot map / zones / event-data bars** (Player + Team DNA 🔴 deferred) — same dependency, same gate.
- 🅾️ **Big Chances / Big Chances Created** — Opta-proprietary and paid. Not planned.

---

## 🛠 Infrastructure, ops & tech debt

- ✅ Cross-device persistence (ADR-094) · Google auth (ADR-106) · "remember me" (ADR-099) · Log out ·
  anonymous usage analytics (ADR-100) · beta gate + waitlist (ADR-087/102) · self-service unsubscribe (ADR-122).
- ✅ **ADR-120 — Admin tester-activity roster + load watch** — built (Sprint 186). ⏳ Owner smoke outstanding
  (`FPL_ADMIN_KEY` + the anon SELECT policy) before the numbers have been seen.
- ⚠️ **OWNER ACTION — ADR-122's unsubscribe silently no-ops** until a `beta_users` **DELETE policy** is added in
  Supabase (BETA.md §4). The *"remove me = we delete your rows"* promise isn't kept without it. Console work,
  not code.
- ⚠️ **OWNER ACTION — admin-read smoke** (ADR-100): add the anon SELECT policy + set `FPL_ADMIN_KEY`.
- ⬜ **Session/cookie auth for user-specific data** (`/my-team/{id}/`) — unlocks a manager-ID fetch inside
  `analyse`/`transfer`. Native `st.login()` is the product-path upgrade above the current gate.
- ⬜ **Source versioning** — formalise "version all external sources"; confidence scoring on fallback.
- ⬜ **Cache TTLs.**
- ⬜ **Deferred auth polish** — a confirm dialog on Log out; a signed/opaque "remember me" token instead of the
  raw value (deferred as over-engineering for a hobby beta; revisit only if the raw cookie value becomes a
  concern).
- ◑ **PuLP 4.0 migration** (ADR-066) — variables migrated; `PULP_CBC_CMD` deliberately kept (COIN_CMD needs an
  external CBC that fails locally *and* on the read-only Cloud). Revisit only if we adopt `pulp[cbc]`.

---

## 🧯 Standing risks

- **Season-rollover and first-occurrence bugs.** Six in two days at GW1. A deliberate **DGW/BGW audit**
  (2026-08-24) then found three more *before* the event: a primary-key collision that silently halved a double
  gameweek, the fixture ticker hiding a double's second fixture, and the player card double-counting one — all
  three fixed (ADR-129). Auditing ahead of a first occurrence works — worth repeating before the
  first blank gameweek and the first chip deadline.
- **`ep_next` is load-bearing early.** The cold-start rate leans on it (ADR-104/124) until real evidence
  accrues; an FPL quirk in it propagates.
- **Streamlit Cloud can serve a stale build** after a push — Reboot from the ⋮ menu.
- **ClubElo is intermittent** — best-effort by design (ADR-010), degrades to last-known.

---

## Guiding principles (unchanged)

- **The CLI stays the engine** — new surfaces (web) are edges over the same analytics; generic core, policy
  at the edge.
- **Analytics decide; the LLM only narrates** — grounded, verified, optional.
- **FPL is the source of truth**; external sources degrade gracefully.
- **Learn by building, sprint by sprint** — a gate (ADR) per feature; simple over clever.
- **Degrade visibly.** An empty board beats a wrong one; a labelled fallback beats both. Never render a missing
  value as a confident zero — that lesson cost six bugs in two days.
