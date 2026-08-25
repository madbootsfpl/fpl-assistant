# Sprint 192: The value frontier — and the error it magnified (ADR-138)

**Dates:** 2026-08-25
**Status:** ✅ Complete — ADR-138. 1341 → 1347 tests, ruff clean. Owner-approved after two review rounds.

> **Owner:** ⭐-flagged this on the Roadmap as the last open competitive gap, then reviewed the live-data
> preview twice. Both notes changed the build — the second one changed the analytics.

---

### 🔍 Why this sprint exists

The competitive review left one row unclosed: **aceanalyst's pool-wide value scatter**, noted as *"the one
clear remaining gap — data all exists."* True, and exactly the kind of claim this project checks before
building on. So the chart was justified with measurements first:

- **The frontier is not "the best players".** Only **4 of 8** frontier players are also top-8 by raw xP. The
  other half is invisible to every ranking in the app.
- **Choosing well at one price rivals moving up a bracket.** The best £4.5 player is **+11.9 xP** over the
  median £4.5 player across five gameweeks; £4.5 → £8.0 buys ~19.1 xP for £3.5m. Same decision, two forms,
  never shown together before.
- **The existing value number looks backwards.** Pool's `Val/£m` is *last season's* points ÷ price — at GW1 it
  describes a squad since rebuilt in the transfer market. The frontier runs on `decision_xp`.

---

### 👀 What the review changed

**"Dots look blurred." Said twice** — because the first fix (smaller, stroked, more opaque dots) was a guess.
Only after the second note was the cause actually measured:

| price band | players | share of dots | share of x-axis | over-dense |
|---|---:|---:|---:|---:|
| £4.0–5.5 | 312 | 60% | 12% | **5.0×** |
| £5.5–7.0 | 177 | 34% | 12% | 2.8× |
| £9.0–15.5 | 5 | 1% | **57%** | 0.0× |

**94% of players in 24% of the width, and half the canvas spent on five people.** Never a dot-size problem.
Four readings went back as one page (linear/log × all/decision-set); the owner picked **linear price, decision
set**. Money stays linear; the fix is to stop plotting non-decisions. Default is the **256** who have featured
*and* project above a point a week, with **Plot everyone** to restore the rest — and *measured* stays separate
from *plotted*, so no number moves when the filter does.

**"Dubravka will not be first choice keeper."** Spurs' keepers:

| | mins this season | xP | xMins weight |
|---|---:|---:|---:|
| Dubravka £4.0 | **0** | **9.9** | 0.64 |
| Kinsky £4.5 | **90** | **2.3** | 0.18 |

**Exactly backwards.** Dubravka made 35 starts last season; the in-season minutes share is deferred to ~GW4-6
(ADR-125) because one gameweek is thin evidence. So a new function, `minutes.yet_to_play`, asks the one
question the weight cannot: *has his team completed a gameweek he played no part in?* — carefully, since a
gameweek only counts when it has a **scoreline** (the ADR-125/129 trap: FPL writes the row when the fixture is
*scheduled*, so Leno reads 0 minutes only because Fulham have not kicked off).

An unproven player now **cannot hold the frontier and cannot block anyone dearer**. Dubravka → O'Shea,
Watkins → Mbeumo; all eight have played. He keeps his score and his peer-median place, because the number is
not wrong — it is unsupported.

---

### 💡 The lesson

> **A frontier is an error magnifier, and that is a feature if you let it be.**

Ranking by xP buries a bad number mid-list. A frontier *promotes* it, because cheap-and-high is precisely what
it selects for. So the very first real user look found a model weakness that had been sitting quietly in every
other surface in the app. Uncomfortable, and useful — provided the chart also says what its numbers stand on.

Two smaller ones:

- **Guessing twice cost more than measuring once.** "Blurred" got two speculative fixes before anyone counted
  dots per unit of axis. The count took one command and produced the answer immediately — and it was not the
  thing being adjusted. *When a visual complaint repeats, stop tuning and go measure the distribution.*
- **Marking beat modelling, and the owner's third comment proved it.** Watkins looks Saudi-bound; nothing in
  the FPL data says so, and nothing was built for it. Yet both flagged frontier players were genuinely
  un-buyable — for reasons the flag cannot see and reliably points at. The app supplied the suspicion, a human
  supplied the reason. That is the right division of labour when the model provably cannot know.

### 🧪 Tests

**+15 (1341 → 1347).** `value_frontier` — the definition and why it is not points-per-£m, ties at one price,
the peer median, float-safe price grouping, a missing xP, and unproven-excluded-but-still-scored.
`frontier_verdict` — the sentence itself, including the only-player-at-this-price case that would otherwise
read "exactly the median" about a group of one. `minutes.yet_to_play` — all three states plus the
not-kicked-off trap. An AppTest pins measured-vs-plotted and the **Plot everyone** escape hatch.
