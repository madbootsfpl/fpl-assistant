# Sprint 172: Team DNA — engine, Fixtures browse card & the My Squad "Your teams" strip (US-418/419/420, ADR-119)

**Dates:** 2026-08-18
**Status:** ✅ Complete — ADR-119 + US-418/419/420. A lean, reuse-heavy sprint: the team-level DNA, on data we
hold, defence-led. 1069 → 1087 tests. Real-data design verified up front; live cards + strip verified after.

> **Owner:** approved ADR-119 ("good call" · "excellent"); "plan Sprint 172".

---

### 🎯 Scope — three stories, heavy reuse of the Player-DNA engine (S168–S171)

**US-418 — the pure engine (`src/analytics/team_dna.py`).** Mirrors `player_dna`; **reuses its `Axis` + `Insight`
dataclasses**.
- `team_dna_all(players, fixtures, *, next_n=5)` → `{team_short: TeamDNA}` — aggregate the pool + fixtures to
  per-team metrics, then rank each as a **percentile across the 20 teams**. `team_dna(team, players, fixtures)` =
  the single-team convenience. Efficient for the strip (compute once, read many).
- **8 axes** (ADR-119), on data we hold via labelled proxies: Attacking Threat (team xG) · Chance Creation (team
  xA) · Defensive Strength (team xGA ← keeper xGC, lower=better) · Clean-Sheet Potential (blend of defence +
  fixture-ease) · Fixture Strength (next-5 FDR via **`team_fdr`**, lower=better) · Set-Piece Threat (Σ SP takers) ·
  FPL Output (team pts) · Squad Depth (regulars, minutes ≥ 1500).
- `TeamDNA(team, name, axes, grade, grade_score)` — a **grade** (A+…D) from the key axes (attack · defence ·
  fixtures · output); `team_insights(dna, metrics)` → grounded `Insight`s (elite axes · fixture swing · miserly
  defence · set-piece load), reusing the player insight kinds.
- Pure, dict + `sqlite3.Row` safe, empty-safe; **works preseason** on last-season aggregates. **No `decision_xp`
  / FDR-model change.**

**US-419 — the Fixtures browse card (`src/web_streamlit/team_dna_card.py`) + wire into Fixtures.** A self-contained
dark card: the **radar** (reuse — *generalise `dna_card.radar_svg` to take `axes` + a label* so player & team share
one SVG builder) + a **grade gauge** + grounded **insights** + **next-N fixtures** (`team_schedule`, FDR-tinted) +
a **Key-players-to-target** table (xGI/90 · pts/90 · minutes% · ownership — all from player rows). Wired into the
**Fixtures page** as a **"🧬 Team DNA"** section: a team selectbox → the card. Reuses the page's `players` +
`upcoming`; **no new store read**.

**US-420 — the My Squad "Your teams" strip (into `render_health`).** The **lead**. In **My Squad ▸ Health**, a
compact **"Your teams"** strip — one row per club you own players in: a **grade** + **Attack / Defence / Fixture**
band-dots + **your players** there — then a **"View a team's DNA"** selectbox that **drills into the same
`team_dna_card`**. Reuses Health's `players` + `upcoming`; scoped to the squad's clubs.

---

### ✅ Definition of Done (3-part)
- **Tests (~+16):** engine — MCI-style team tops attack/output, a tough-fixture team scores low on the fixture
  axis, defence proxy inverts (low xGA → high percentile), the grade thresholds, insights (elite + fixture-swing),
  empty/`Row`-safe; card — HTML has radar + grade + fixtures + key-players; strip — a row per squad team + drill-in;
  2 AppTest e2e (Fixtures Team DNA view · My Squad Health strip).
- **Manual smoke:** Fixtures ▸ Team DNA ▸ Arsenal (A, elite attack, tough-fixture insight) · Liverpool (easy run) ·
  My Squad ▸ Health (the strip lists your clubs + drills in).
- **Docs:** ADR-119 build-progress; PROJECT_STATUS; Roadmap; this doc + lessons.

### ⚠️ Watch-items
- **Label the proxies** — xGA (keeper xGC), Clean-Sheet (blend), Depth (regular count) are honest proxies, not
  Opta; caption them. Upgrade the 🟡 ones (real clean-sheet rate · team form) at GW1 as a follow-up.
- **Don't duplicate Fixtures/Radar** — lead with the strip + the defensive angle; the card **links** to the Radar.
- **One radar builder** — refactor `radar_svg` to take `axes` so player & team can't drift (repoint the S168 test).
- **No engine change** — `decision_xp` + the FDR model untouched; Team DNA is a display lens.

---

### 🎯 Delivered

- **`analytics/team_dna.py` (US-418)** — `team_dna_all(players, fixtures)` → `{team: TeamDNA}`, an 8-axis
  percentile-across-the-league fingerprint + an A+…D **grade** + grounded `team_insights`. Reuses `player_dna`'s
  `Axis`/`Insight`/`_set_piece_score` + `team_fdr`; labelled proxies (xGA ← keeper xGC, clean-sheet = defence +
  fixture blend, depth = regulars). dict/`Row`/empty/preseason safe; **no `decision_xp`/FDR change**.
- **`web_streamlit/team_dna_card.py` (US-419)** — the Fixtures browse card: grade header (reusing the verdict
  `gauge_svg`) + radar + chips + `team_key_players` table, composed with the **reused `insights_card`** + an
  FDR-tinted fixtures row. **Generalised `dna_card.radar_svg` to take `axes`** so Player & Team DNA share one SVG
  builder. Wired into **Fixtures ▸ 🧬 Team DNA** (team picker).
- **The "Your teams" strip (US-420)** — `your_teams_rows`/`your_teams_strip_html`/`render_your_teams`: one row per
  owned club (grade + Attack/Defence/Fixture dots + your players, best grade first) → drills into the full card.
  Wired into **My Squad ▸ Health** (`team_names` threaded from the page).
- **Tests: +18** (9 engine · 6 card+strip · 3 AppTest incl. Fixtures + Health e2e). **1087 green**; ruff clean.
  Live-verified (Fixtures cards ARS/LIV; the strip on a demo squad, 11 clubs graded A–D).

**Tracked GW1 follow-ups:** real clean-sheet rate (vs the fixture blend) + team form. **Deferred:** the event-data
viz (metric bars / zones / shot map) → a future `soccerdata` ADR.

### 🧠 Lessons

- **The DNA engine generalised almost for free.** Team DNA reused `Axis`/`Insight`/`_set_piece_score`/`radar_svg`/
  `gauge_svg`/`insights_card` — the marginal cost was the aggregation + the strip, exactly the "cheap because the
  infra exists" bet from ADR-119.
- **Generalise the shared bit once.** Making `radar_svg` take `axes` (not a `PlayerDNA`) stopped player & team
  radars from drifting — one builder, repointed the S168 test.
- **Lead with the actionable surface.** The "Your teams" strip (your clubs graded, fixture dots = transfer signal)
  is the value; the browse card is the drill-down — building both from one component kept them consistent.
- **Honest proxies, labelled.** xGA-via-keeper / clean-sheet-blend / depth-count are captioned as proxies; the
  real defensive metrics wait for GW1 data (build + verify then), not faked now.
