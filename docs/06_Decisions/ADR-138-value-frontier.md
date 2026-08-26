# Architectural Decision Record: The value frontier — position everyone, don't rank fifteen

**Decision ID:** ADR-138
**Date:** 2026-08-25
**Status:** ✅ **Accepted — built and owner-approved** (Sprint 192, 2026-08-25). **1341 → 1347 tests, ruff
clean.** Two rounds of owner review on a live-data preview changed the design materially — see §Review. ⭐ on the Roadmap since the competitive review; listed there
as *"the one clear remaining gap"* against **aceanalyst**. Measured on live data before building.
**Superseded By / Replaces:** Complements the DNA radar (ADR-118) — the radar shows *one* player's shape, this
positions *everyone*. Uses `decision_xp` (ADR-041) unchanged; adds no new metric to the model.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The competitive review left one gap: **aceanalyst's pool-wide value scatter.** Every other rival signature is
either shipped or declined on evidence with the numbers written down. This one was open, and the note said
*"data all exists"* — which is true, and is also exactly the kind of claim this project has learned to check
before building on it.

**So the first question was whether the chart says anything on our data.** A scatter that turns out to be a
blob is a screenshot, not a tool. Measured over 516 available players (£100m squad, 5-GW horizon, xP):

**1. The frontier is not just "the best players".** Taking the efficient frontier — *nobody cheaper scores
more* — and comparing it to a plain top-N by xP:

| | frontier size | also in the top-N by raw xP |
|---|---:|---|
| GK | 4 | 2 of 4 |
| DEF | 5 | 2 of 5 |
| MID | 8 | 5 of 8 |
| FWD | 8 | 5 of 8 |
| **All** | **8** | **4 of 8** |

Half the frontier is invisible to an xP ranking. That half is the entire point of the chart.

**2. Choosing well at one price beats moving up a price bracket.** The spread *within* a single price point:

| price | n | best | median | the best is… |
|---|---:|---:|---:|---|
| £4.0 | 60 | 9.9 | 4.8 | **+5.1 xP** over the median at the same price |
| £4.5 | 116 | 16.9 | 5.0 | **+11.9 xP** |
| £5.0 | 136 | 17.5 | 7.4 | **+10.1 xP** |
| £5.5 | 105 | 20.8 | 8.5 | **+12.3 xP** |
| £8.0 | 6 | 24.1 | 20.9 | +3.2 xP |

**Picking the right £4.5 player is worth ~11.9 xP; upgrading £4.5 → £8.0 buys ~19.1 xP for £3.5m.** Those are
the same decision expressed two ways, and no ranked list in the app puts them side by side. A scatter does it
in one glance. **This is the justification** — not that a rival has one.

**3. And the current "value" number is looking the wrong way.** The Pool's `Val/£m` is *last season's total
points* ÷ price — backward-looking, and at GW1 it is describing a squad that has since been rebuilt in the
transfer market. The frontier is built on `decision_xp`, the same forward number every recommendation in the
app already acts on.

---

### ✅ Decision

**1. A pure `value_frontier(rows, xp_by_id)` in `src/analytics/value.py`**, beside `points_per_million` — the
module that already owns "what is a player worth per pound". Returns each player annotated with their xP,
their price-peer median, and whether they sit on the frontier. Pure, Row/dict safe, no I/O, unit-tested
offline. **The verdict is computed here, not in the view** — a chart's tooltip is a statement about the data
and belongs where it can be tested.

**2. A grounded verdict on hover, not a dot to interpret.** This is the MadBoots difference and it is the only
part a rival cannot copy from a screenshot:

> **Mitchell** · £4.5 DEF · **16.9 xP** over 5 GW
> **+11.9 xP** vs the median £4.5 player
> **On the value frontier** — nobody cheaper scores more

A dot at (4.5, 16.9) is a fact. The sentence is a finding.

**3. Median baselines, as the Roadmap asked** — a horizontal rule at the pool's median xP and a vertical at
the median price, splitting the chart into quadrants. The top-left quadrant (cheaper than median, better than
median) is the one worth reading, and the rules are what make it visible without a legend explaining it.

**4. It lives as a tenth view on Players, `Value`.** It reuses the shared filter (`sel` / `apply_filter`) at no
cost, exactly like the Radar does — the filters are already cross-view, so building it "inside Pool to reuse
the filters" would have bought nothing and made a long function longer.
**⚠️ Ten is the ceiling.** ADR-134 already noted that nine labels stretch three rows. The next view added to
this page needs a **merge** first, not another label, and that is written here so it is not rediscovered.

**5. Price × xP only. The other two axis pairs in the Roadmap line are not built.** *xGI × points* and *DefCon
× points* are different questions, already answered by the `xG · xA` and `DefCon` boards as rankings. Building
three scatters would be building one good one and two duplicates. **Scope reduction, stated rather than
quietly dropped:** if the frontier proves itself with testers, a metric selector is a small follow-on.

**Not in scope:** any `decision_xp` change, any new stored metric, and clickable dots (a tap that selects is
ADR-133's shape and would be a fine follow-on; a tap that opens a menu is ADR-135 and is not).

### ⚠️ Risks

- **The floor blob.** 18% of available players (93) sit under 1.0 xP — backups who do not play. They are a
  dense band along the x-axis. Kept, not filtered: *"most players at your price are not worth buying"* is the
  shape that makes the frontier mean something. De-emphasised visually rather than removed.
- **Early-season xP.** One gameweek in, `decision_xp` is heavily shrunk toward the historical baseline
  (ADR-124). The frontier is therefore mostly a *last-season-plus-fixtures* statement right now, and will
  sharpen as the form term comes in at GW4-6. The caption says so, in the ADR-126 idiom already used by the
  boards that cannot answer from this season yet.
- **Reading a scatter on a phone.** ~516 dots on a narrow screen. Mitigated by the shared filter (position
  alone cuts it to 57-227) and by the frontier being drawn as a line, which survives at any size.

### 🧪 Definition of Done

1. **Tests** — `value_frontier` unit tests (the frontier definition, ties at the same price, the peer median,
   a player with no xP, an empty pool) and an AppTest that the view renders and reacts to the filter.
2. **Manual smoke** — the view on real data; the frontier names match the numbers measured above.
3. **Docs** — this ADR, the Roadmap entry (and the competitive table row it closes), PROJECT_STATUS, a retro.

---

### 👀 Review — two owner notes, and the second one changed the analytics

A faithful preview was published on live data (the memory idiom: real numbers, hand-drawn SVG since the CSP
blocks chart CDNs). Both notes came back on the first look, and both were right.

**1. "Dots look blurred." Twice.** The first fix — smaller, stroked, more opaque dots — did not work, and the
second look said so. Only then was the *cause* measured rather than guessed:

| price band | players | share of dots | share of x-axis | over-dense |
|---|---:|---:|---:|---:|
| £4.0–5.5 | 312 | 60% | 12% | **5.0×** |
| £5.5–7.0 | 177 | 34% | 12% | 2.8× |
| £7.0–9.0 | 22 | 4% | 16% | 0.3× |
| £9.0–15.5 | 5 | 1% | **57%** | 0.0× |

**94% of players sit in 24% of the width, while over half the canvas holds five people.** It was never the dot
size. Four readings were rendered side by side (linear/log × all/decision-set) and the owner chose **linear
price, decision set only**: keep money linear, and stop plotting things that are not decisions. Default is now
the **256** players who have featured *and* project above **a point a week** (`1.0 × horizon`, so it still
means that at any window), with a **Plot everyone** tick restoring the rest.

**Measured and plotted are kept separate**: medians, edges and the frontier are always computed over the full
516, so no number moves when the display filter does.

**2. "Dubravka will not be first choice keeper."** The sharper note, and it moved the analytics rather than the
chart. Spurs' keepers on the live data:

| | mins this season | xP | xMins weight |
|---|---:|---:|---:|
| **Dubravka** £4.0 | **0** | **9.9** | 0.64 |
| **Kinsky** £4.5 | **90** | **2.3** | 0.18 |

**The model had it exactly backwards** — the keeper who played GW1 scored 2.3, the one who did not scored 9.9,
because Dubravka made 35 starts last season and the in-season minutes share is deferred to ~GW4-6 (ADR-125).
The frontier put that error in the most prominent place on the page: **its cheap end is precisely where the
xMins model is weakest**, so a £4.0 backup with a strong history is the ideal false positive.

The first response was a warning label. The owner's point argues for more than that, so:

- **`minutes.yet_to_play`** — has his team completed a gameweek he played no part in? Three states, and telling
  them apart is the function: *he played* → no; *his team played and he did not* → yes; *his team has not
  played* → no, we know nothing. A gameweek counts only when it has a **scoreline** — never row presence,
  never `minutes == 0` alone, which is the ADR-125/129 trap (on this data Leno reads 0 minutes purely because
  Fulham have not kicked off).
- **An unproven player cannot hold the frontier, and cannot block anyone dearer.** *"Nobody cheaper scores
  more"* is a claim about who to **buy**. Dubravka → **O'Shea** (£4.0 DEF), Watkins → **Mbeumo** (£8.0 MID);
  all eight frontier players have now played.
- **He keeps his score and his peer-median place.** The number is not wrong, it is *unsupported* — deleting
  him would hide a player some managers own, and discounting him would invent a minutes correction the
  calibration has not earned. **179 of 516** are in this state one gameweek in.

**A note on the second one that is worth keeping.** The owner also flagged that Watkins looks bound for a Saudi
club. Nothing in the FPL data says so — his status is `a` with empty news — and nothing was built for it.
🔁 **That conclusion was wrong, and ADR-146 corrects it (2026-08-26).** It treated the *news feed* as the
boundary of what the app knows. The app was already computing `net_transfers` = **−96,095** for that player and
already returning a ❄️ out flag — a hundred thousand managers' reading of the same event, rendered three clicks
away from where it mattered. "We don't have that data" is a claim worth checking as hard as any other. But
both flagged frontier players turned out to be genuinely un-buyable, for reasons the flag cannot see and
reliably points at. **That is the argument for marking rather than modelling**: the app supplied the
suspicion, a human supplied the reason.

### 💡 The lesson

**The frontier is an error magnifier, and that is a feature if you let it be.** Ranking by xP buries a bad
number in the middle of a list; a frontier promotes it to the headline, because being *cheap* and *high* is
exactly what it selects for. So the first real user look found a model weakness that had been sitting quietly
in every other surface. A chart that surfaces your worst numbers first is uncomfortable and useful — provided
it also says what they are standing on.

### 🧪 Definition of Done — met

1. **Tests: +15 (1341 → 1347).** `value_frontier` (the definition and why it is not points-per-£m, ties, peer
   median, float-safe price grouping, missing xP, unproven excluded-but-scored), `frontier_verdict` (the
   sentence, and the only-player-at-a-price case), `minutes.yet_to_play` (all three states plus the
   not-kicked-off trap), and an AppTest pinning measured-vs-plotted and the **Plot everyone** escape hatch.
2. **Manual smoke:** the view on live data at both filter settings; two owner review rounds on a preview.
3. **Docs:** this ADR, the Roadmap entry + the competitive-table row it closes, PROJECT_STATUS, Sprint192.
