# Sprint 015 — soccerdata evaluation: findings

> Evidence for the ADR-016 decision. All numbers are reproducible with the scripts in
> this folder, run in a throwaway venv (`pip install soccerdata`). Nothing here touches
> the app.

## Environment probe (planning)

- `soccerdata` 1.9.1 installs cleanly in a fresh venv.
- Sources reachable: **Understat** 570 players / **3.4s**; **FBref** 580 / **36s** (it
  downloads a TLS-client `.dylib` to get past FBref's 403 anti-bot).
- Understat 2024/25 (`read_player_season_stats`) gives: `player`, `team`, `player_id`,
  `xg`, **`np_xg` (npXG)**, `xa`, `np_goals`, `key_passes`, `shots`, `xg_chain`,
  `xg_buildup` — several fields FPL does **not** provide.

---

## US-047 — Name-matching (FPL ↔ Understat, 2024/25)

**Method.** Match FPL's current roster (players with minutes > 0) to Understat 2024/25 via
`match_fpl_understat.py`: normalise (accent-fold, lowercase), then two layers —
(1) exact **formal** full-name, (2) FPL **`web_name`** (the *common* name) as a token in an
Understat name — with **team** as the tiebreaker for duplicates. Misses are split into
"name-form" (the player IS in Understat, we just couldn't confirm) vs "absent" (not in
Understat 2024/25 at all — roster drift).

**Results.**

| Outcome | Count | % of FPL-played (400) |
|---|---|---|
| Confident match | 259 | 64% |
| Name-form miss (present, unresolved) | 12 | 3% |
| Absent (roster drift) | 129 | 32% |
| **Match rate among those actually in both** (259 / 271) | | **95%** |

**Interpretation.**

- **Matching is tractable.** 95% confident automatic match with a simple two-layer
  matcher. The first naive pass (formal name only) got 88%; adding the common-name
  (`web_name`) layer — because FPL stores full legal names (`david raya martin`) while
  Understat uses common ones (`David Raya`) — recovered most of the gap.
- **The residual ~3–5% is a known, bounded problem.** The misses are ambiguous common
  names (`gabriel` — two Gabriels at Arsenal; `rodrigo`; `daniel james`) that need a small
  **hand-maintained override map** — exactly the pattern we already ship for teams
  (`CLUBELO_TO_FPL`). So it degrades to a finite, reviewable list, not silent wrong matches.
- **The real coverage ceiling is roster drift, not matching.** 32% of FPL-played players
  aren't in Understat 2024/25 — new signings, promoted-club players, anyone who didn't
  feature in the PL last season. They simply have no last-season Understat data and would
  get `None` — **the same graceful degradation as FPL's own xG for newcomers**, not a bug.

**Verdict (rubric #1 — matching reliable?):** ✅ **Yes.** ~95% automatic + a small override
table for ambiguous names, with graceful `None` for the genuinely-absent. Comparable to the
ClubElo integration we already run, and with no silent wrong matches.

---

## US-048 — Unique value (npXG) & operational cost

**The unique field: npXG.** FPL gives total `expected_goals` (**penalties included**);
Understat gives `np_xg` (**non-penalty xG**), which FPL does not. For penalty-takers the two
diverge sharply — npXG is the truer measure of *open-play* threat.

Top attackers, FPL xG vs Understat xG vs npXG (2025/26, matched, `compare_npxg.py`):

| Player | FPL xG | US xG | npXG | penalty gap |
|---|--:|--:|--:|--:|
| Haaland | 25.5 | 28.8 | 25.8 | 3.0 |
| Thiago | 20.6 | 24.7 | 17.8 | **6.9** |
| Calvert-Lewin | 15.6 | 18.7 | 14.9 | 3.8 |
| **Palmer** | 10.6 | 10.3 | **5.7** | **4.6** |

- **FPL xG and Understat xG agree** once seasons align (a cross-source sanity check) — the
  match is real, and the small gaps are model differences.
- **npXG changes decisions.** Penalty inflation is 3–7 xG for takers; **Palmer's open-play
  threat is barely half his raw xG** (5.7 vs 10.6). Ranking the top-10 by npXG instead of
  FPL xG swaps **~3 of 10** (Sesko/Ekitike/Evanilson in; Welbeck/Schade/Enzo out). FPL
  cannot produce this — **rubric #2 (unique value real?) → ✅ Yes**, though the value is
  *narrow* (one field, mattering mostly for a handful of penalty-takers).

**A real integration gotcha — season alignment.** FPL's `expected_goals` reflects the *last
completed* season (2025/26 here). Pulling the wrong Understat season silently joins
mismatched data: at Understat 2024/25, Thiago showed **0.1 xG / 148 mins** (injured) vs
FPL's **20.6 / 3282** — a 200× error that *looked* like a bad match but was a one-season
offset (also masking transfers: Calvert-Lewin Everton→Leeds). FPL doesn't label its season,
so a production join must infer it and guard against misalignment. **Aligning seasons also
raised the match count 231 → 316** — so it matters for coverage too.

**Operational cost (rubric #3 inputs).**

| Dimension | Finding |
|---|---|
| Dependency weight | project venv **14 packages** → soccerdata venv **72** (5×), incl. **pandas, numpy, lxml, beautifulsoup4, selenium + seleniumbase** (a full browser-automation stack) |
| Speed | Understat ~3.4s (fine, best-effort like ClubElo); FBref ~36s (too slow) |
| Fragility | web scraping + anti-bot bypass (a downloaded TLS `.dylib`); breaks when sites change |
| Offline tests | the project's tests are 100% offline; soccerdata scrapes + caches to `~/soccerdata` — an integration needs a DI'd client wrapper + cached fixtures (rework) |
| Season alignment | must infer FPL's season and pull the matching Understat one, or silently mis-join |

**Verdict (rubric #3 — cost acceptable?):** ⚠️ **High.** 14 → 72 packages (browser
automation + scientific stack), scraping fragility, a season-alignment trap, and
offline-testing rework — heavy against the charter's *"prefer simple, avoid unnecessary
complexity"*, for one narrow (if real) field.
