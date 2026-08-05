# Chapter 21 — Analytics

**Badges:** 📖 🧪 💻

---

## Purpose

Analytics is where the project *calculates* things, rather than just storing and
showing numbers that came from FPL. The first metric is **Points-per-£m** (value).

---

## Why We Use It — and where it sits in the architecture

Analytics is the first layer that **creates data rather than moving it**. Everything
below it copies FPL's numbers around; analytics turns those into *new* insight. It
**reads from storage, computes, and hands results up to display** — it never touches
the API or the screen.

```
storage (raw rows) → analytics (adds a computed number, ranks) → display
                         ▲ the layer that "thinks"
```

Keeping it in its own layer (`src/analytics/`) means the project's *reasoning* has
one home — as more metrics arrive (form, fixture difficulty, later xP), they all live
together instead of being scattered into queries or formatting code.

---

## Concepts

- **Derived metric:** a number the app computes (points ÷ price), not read from source.
- **Pure function:** numbers in, number out — no side effects; trivial to test.
- **Per-row vs aggregate:** value is per player; fixture difficulty (FDR) is *per team
  across several fixtures* — a summary of a group.
- **Perspective:** the same input can mean different things to different subjects — a
  fixture is easy for one team and hard for its opponent, so each team reads its own side.
- **Undefined results:** some inputs have no sensible answer (divide by zero). Say so
  honestly rather than inventing a value.
- **Cross-domain:** a metric that combines two domains — Expected Points (xP) joins a
  *player's* scoring rate with their *fixture's* difficulty (`points_per_game ×
  multiplier(difficulty)`). The join key is the player's `team_id`.

---

## Examples (from this project)

The value metric in `src/analytics/value.py`:

```python
def points_per_million(total_points, price):
    if total_points is None or not price or price <= 0:
        return None          # undefined — don't invent a number
    return total_points / price
```

Ranking players by value (undefined values sort to the bottom):

```python
enriched.sort(key=lambda d: (d["value"] is not None, d["value"] or 0.0), reverse=True)
```

**The payoff:** sorting by value surfaces cheap high-scorers a points-only list hides
— e.g. a £5.5m defender at 30.0 pts/£m ranking above a £15.5m striker at 15.4.

An *aggregating* metric — Fixture Difficulty (`src/analytics/fdr.py`) — summarises a
group instead of one row. Each fixture is attributed to *both* teams from their own
perspective, then averaged per team over the next N games:

```python
for f in fixtures:
    per_team[f["home"]].append((f["team_h_difficulty"], f["away"]))   # home's view
    per_team[f["away"]].append((f["team_a_difficulty"], f["home"]))   # away's view
# then: average each team's next N, rank easiest-first
```

The boundary from Chapter 10 holds: storage answers "which fixtures are upcoming?";
analytics does the perspective + averaging + ranking.

**Expected Points (xP)** is the first metric to *compose two others*: it multiplies a
player's `points_per_game` by their next fixture's difficulty (reusing FDR's `_view`).
`src/analytics/xp.py` links each player to their team's next fixture via `team_id` —
the first time the player and fixture threads meet. It also carries FPL's own
`ep_next` alongside, so ours can be compared to theirs (ADR-006).

A metric can have more than one **source**. `fdr --type fpl|custom` uses either FPL's
published difficulty or our own (the opponent's overall strength at their venue,
ADR-005) — same averaging/ranking machinery, a different input number. Keeping both
lets us compare our rating against FPL's.

**Enriching a metric's *input*, not its formula (ADR-028).** Sprint 026 improved xP
without touching its formula: instead of the rate being one noisy season's
`points_per_game`, it's a **multi-season baseline** — a recency- and minutes-weighted
points-per-90 over the last ≤3 seasons (from the new past-season history, ADR-027),
falling back to the current season when a player has no history. Two lessons worth
keeping:
- **Gate small samples.** A cameo season (2 pts in 20 mins → pp90 90.0) invents an
  absurd rate. A live smoke test — not the unit tests, which used clean data — caught
  it topping the ranking; the fix was the same ≥900-minute gate the DefCon/over-under
  views use (the Sprint 016 Meslier lesson, again). *Verify metrics on real data.*
- **Use only trustworthy fields.** Older seasons report `0.00` for stats that didn't
  exist yet (xG, DefCon) — a 0 meaning "not tracked", not a real zero. The baseline
  uses only points + minutes, which are reliable across all seasons (ADR-027).
- **Know the boundary.** The baseline is a *"quality when playing"* rate — it doesn't
  model rotation/minutes (that's xMins, a later phase). Stated in the view's footer.

**From ranking to *recommending* (Sprint 027, decision support).** Captain suggestions
(ADR-029) are the first feature that *advises* rather than lists — and the lesson is that a
good recommendation **reuses a trusted metric and explains itself**, rather than inventing a
new score. `captain_picks` ranks by the existing xP, then adds *why* (opponent, venue, penalty
duty) and applies decision-appropriate policy: exclude goalkeepers (captaincy is a ceiling bet;
a keeper ranked 3rd by mean xP gave that away on a live probe) and keep doubtful players but
*flag* them. Two rules worth keeping:
- **Don't double-count.** Penalty takers are shown as context, not given a score bonus — their
  penalty returns are already inside xP. Adding a bonus would count them twice.
- **Explain, then let the human decide.** A recommendation the manager can see the reasons for
  is one they can trust or overrule — better than an unexplained "captain X".

**Recommending a *change* means respecting the rules (Sprint 028, transfers).** `suggest_transfers`
(ADR-030) is the next step up: it proposes swapping a player out, so it must only ever suggest a
*legal* move — same position, ≤3 per club, affordable. Two lessons:
- **Encode the domain constraints, and test each one in isolation.** The ≤3/club rule has a subtle
  case — selling a same-club player frees a slot — that a unit test flushed out (it caught a *bad
  test*, where a legal same-club swap existed after all). A recommendation that breaks the rules is
  worse than none.
- **Be honest about what you can't see.** We don't know the manager's bank (no auth) or who they
  start — so the bank is an input (`--bank`, default £0 = self-funding) and bench players are
  *flagged*, not silently modelled. State the assumptions rather than guessing.

**Rank by the *right* number — the team you actually field (Sprint 046, XI-aware transfers).** The
first version ranked swaps by **raw player-xP gain** (`in.xp − out.xp`), which happily "upgraded" a
cheap bench player: a big paper number that doesn't change your starting XI. ADR-046 switched the
metric to **XI-gain** = `best_xi_points(owned − out + in) − best_xi_points(owned)` — how much the swap
lifts your *best legal XI*. Two lessons:
- **The metric is the recommendation.** Same candidates, same rules — only the *ranking number*
  changed, and the advice went from misleading (*Kusi-Asare → João Pedro +19.3*, a bench swap) to
  useful (*Guéhi → Gabriel +3.0 XI xP*). A bench-only swap now scores **0** and drops out. Getting the
  objective right matters more than any amount of tuning around a wrong one.
- **A fast exact helper beats a slow "proper" one.** Re-solving the XI ILP per candidate would be
  seconds; instead `best_xi_points` enumerates the ~7 legal formations and sums the top-N per position
  — **exactly matching** `best_legal_xi` (pinned by a test) in ~0.02s for ~750 swaps. Default-on, with
  `--raw` preserving the old view.

**A language layer that adds words, not intelligence (Phase 4, `ask`).** `ask` (ADR-034) answers a
question in plain English — but the numbers, decisions and rules stay in the deterministic
analytics. The pattern (proven by a spike, ADR-033) is strict:
- **Analytics decide; the LLM only narrates.** Ask a small model to *rank* and it fabricates (it
  once "recommended" the lower-xP player claiming a higher xP). Hand it a *pre-made decision* + facts
  and it stays honest.
- **Pre-humanise the facts.** The model must not decode `A`/`H` or team codes, and it conflates
  fields in a summary — so we pass self-describing facts (`"availability_problems": "none"`) and
  forbid merging. Grounding is *engineered*, not hoped.
- **The LLM is optional.** It's an *additive narrator*: if Ollama is absent, `ask` degrades to the
  analytics decision + facts. The tool never depends on the model — the honest, transparent contrast
  to a black-box AI companion.

**A recommendation over a *sequence* (Sprint 033, multi-transfer plan).** `suggest_transfer_plan`
(ADR-035) is the first that reasons across several moves: *"which 3 transfers?"*. The lesson is to
**reuse the single-move engine over an evolving state** rather than write a new optimiser — a greedy
loop that, each step, takes the best legal `suggest_transfers` move and updates the state (running
bank, club counts, players used). That makes it correct *by construction*: the bank can't go negative
(the affordability check runs on the running bank), no player is bought twice or a sold one
re-bought, and ≤3/club holds across the set. Greedy (explainable) over ILP (optimal-but-opaque); and
it's honest about what it can't know (your free-transfer count, hits).

**Composing features, and `ask` structured detail (Sprint 034).** The plan table then gained each
incoming player's **per-gameweek xP** — a straight *join* of the plan (ADR-035) and the per-GW
breakdown (ADR-032), no new logic. And `ask` learned to return a **structured table** (a
pre-rendered `detail`) *above* the narration: the table is the exact truth, the LLM prose is the
readable summary. The lesson: mature features compose — reach for a join before a rebuild — and a
natural-language layer can still show hard data, not just words.

**Verify the grounding, don't just instruct it (Sprint 035).** The LLM is *told* not to invent
numbers — `verify_grounding` (ADR-037) then *checks* that it didn't: every number in the prose must
appear in the facts, and any known FPL player named must be a subject of the answer. `ask` shows a
soft **✓/⚠ trust line**, with the facts/table always present. Two lessons: (1) an anti-hallucination
*claim* becomes a *guarantee* only when you check it — instructing is hope, verifying is proof; and
(2) a self-check must itself be trustworthy, so the name check is deliberately conservative
(≥4-letter whole words) to avoid crying wolf. This is what separates a grounded assistant from a
black-box one — the grounding is *visible*.

**A summary that composes and cross-links (Sprint 029, the analyser).** `analyse_squad` (ADR-031)
is the capstone: it adds almost no new computation — it *aggregates* the pieces (xP over a horizon,
availability, the optimiser's XI pick, the club rule) into one health check, and **points at the
other tools** (a weak link → `transfer`, the top XI player → `captain`). Two lessons:
- **Indicators beat a grade.** We show projected XI xP, # issues, weak links — not an invented
  "B+". A concrete number the manager can interpret is more honest than a false-precision score.
- **The dividend of clean layers.** Three Phase-3 features (captain, transfer, analyse) were each
  mostly *wiring* — because xP, availability, saved squads, the optimiser and the renderer were
  already separate, testable pieces. Composability is the pay-off of the one-way-flow architecture.

**Making a metric legible without changing it (Sprint 030, per-GW xP).** A total can hide *when*
the points land. The per-gameweek breakdown (ADR-032) splits xP into its gameweeks — but it's a
**faithful decomposition**, not a new number: the total is the sum of the (unrounded) per-GW parts,
so it's byte-for-byte unchanged and every existing xP test stayed green. Two lessons:
- **Additive beats invasive.** The breakdown was added as extra keys (`by_gameweek`) on the result;
  existing consumers ignore them, and one capability now serves `analyse` *and* `xp`.
- **Round for display, keep the total authoritative.** Per-GW cells are rounded, so a row can read
  ±0.1 off its total — a normal rounding artifact. We footnote it rather than fudge the total (which
  would break the "unchanged" guarantee). Honesty over a tidy-looking-but-wrong sum.

---

## Common Mistakes

- **Dividing by zero / assuming clean data.** Guard undefined inputs; return None.
- **Hiding the metric in SQL or the display.** Then "what counts as value" is smeared
  across layers. Keep it in analytics.
- **Inventing a value for undefined cases** (e.g. 0) — it mixes with real low values.
- **Inventing a new score when a trusted one exists** — captaincy reuses xP + context, not a
  bespoke "captain rating" that would need its own validation.

---

## Best Practices

- Write metrics as pure functions — easy to reason about and test.
- Represent "undefined" explicitly (None → "—", sorted last).
- Analytics reads from storage and returns data; it never fetches or prints.

---

## Lessons Learned

- This is the layer that turns the app from a *viewer* into an *assistant*. Its
  isolation is what will let metrics grow without touching anything else.

---

## Related Documents

- [Architecture v0.1 §4](../03_Architecture/Architecture.md)
- [Chapter 10 — SQLite](./10_SQLite.md) (where the data is read from)
- [Chapter 20 — CLIs](./20_CLIs.md) (how a metric reaches the user)
- Code: `src/analytics/value.py`
