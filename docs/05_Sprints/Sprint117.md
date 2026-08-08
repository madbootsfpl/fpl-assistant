# Sprint 117: A `history <player>` view — past seasons now, per-GW at GW1

**Dates:** 2026-08-18 (planned)
**Status:** 🟢 In progress (2/2 stories built — retro pending)
**Capacity:** ~1 session (a read-view + a grounded `ask` intent over data we already ingest)
**Carried Over:** none

> **Direction (owner):** keep going on the backlog. The open half of **ADR-027/060**: a **`history <player>`
> season-trend / rolling-form view** over the per-GW + past-season data already ingested. *"Still open"* in the
> Backlog.

---

### 🔎 Verified at planning (on real data)

- **Past-season history is real *now*.** `player_history_past` holds **2019** rows — per-**season** summaries
  (`season_name` · `total_points` · `minutes` · the xG family · `starts` · start/end cost). e.g. **Haaland**:
  *2023/24 → 217 pts · 2024/25 → 181 · 2025/26 → 239* (with minutes + xGI). So a history view has **real data
  today** — not dormant — and the accessor already exists (`Storage.get_history_past(code)`).
- **Per-GW is the GW1 half.** `player_history` (this-season per-GW) is **0** rows preseason → fills at GW1 via
  `history --backfill` (ADR-060); `Storage.get_by_code(code)` already reads it. So the view shows **past seasons
  now** and gains a **this-season per-GW trend** at GW1 — the wired-dormant pattern.
- **Only the ingest exists today.** `history --backfill` fetches the data; there is **no view** over it. The
  positional `history <player>` slot is free (the command currently only takes `--backfill`/`--limit`).
- **A price caveat:** the stored `start_cost`/`end_cost` need a units check (a raw value read as `£1.4m` for
  Haaland) — the view leads with the reliable **points · minutes · xGI** and shows price only once verified.

---

### 🎯 Sprint Goal

**Objective:** *"how did this player do?"* is answerable — `history <player>` shows a player's **season-by-season**
line (points · minutes · xGI · …) now, plus a **this-season per-GW** trend once the season runs — on the CLI and
via a grounded `ask`/`chat` intent. A read-view over existing data; the analytics/xP untouched, every number
verified (✓).

#### Success Criteria
- [x] **US-295 (the `history <player>` view — analytics + CLI)** — a pure `analytics/history.py::player_history`
      (assemble `get_history_past` + `get_by_code` into a display shape: past-season rows + any per-GW rows) +
      `ui/history.py::render_player_history` (a season table — season · Pts · Mins · xGI · … — + a per-GW trend
      block, or a "per-GW fills from GW1" note); a CLI **`history <player>`** command (the positional player
      resolves a name → the view; `history --backfill` still ingests; bare `history` keeps its help). Empty-safe
      (unknown player → a clear message).
- [x] **US-296 (a grounded `history` ask/chat intent)** — a `history` intent + `_decide_history` that reuses the
      analytics + renderer → narrated + **verified** (✓, ADR-037), degrading to the facts block without Ollama;
      routed on distinctive cues (*"history"*, *"last season"*, *"how did X do"*, *"X's record"*) placed so it
      doesn't steal squad/worth commands. Inherited by the **Ask** tab + CLI `chat`; the player resolves or asks.
- [x] **No drift** — a read-view/lens only; `decision_xp`/the analytics unchanged; the read-only web guardrail
      holds; **762** green (751 → +11: view + CLI + intent tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help (extends **ADR-027/060** (history) +
      **ADR-037** (grounded ask) — noted; a short **ADR-094** only if we want the intent recorded, agreed at
      the gate).

---

### 🧭 Design sketch

**US-295.** `analytics/history.py::player_history(store, player_row)` → `{"player": …, "seasons": [rows],
"gameweeks": [rows]}` (pure over the two accessors; empty-safe). `ui/history.py::render_player_history` — a
season table (Season · Pts · Mins · xGI · xGC · Starts, most recent last) built on the shared `_table`
renderer, then a per-GW mini-trend (round · Pts · Mins) when present, else *"per-GW form fills from GW1"*. The
CLI `history` parser gains an optional positional `player`; `cmd_history` branches: a player → resolve
(`_match_players`) → render the view; `--backfill` → the ingest; neither → the current help.

**US-296.** `ask._decide_history(store, question)` — resolve the named player (reuse `_match_players`, ADR-039),
build `player_history`, set a `detail` (the rendered view) + `facts` (last-season pts/mins/xGI, the season
count) so a narrated number verifies; a `history` intent in `_INTENT_KEYWORDS` with specific cues (before the
squad intents, after `worth`, so *"is X worth it"* still routes to worth). `ui/ask.render_ask` shows it like the
other intents; the web Ask tab + CLI `chat` inherit it.

**Deferred:** rolling-form charts / a web History tab (the season table + trend read well; a visual pass can
follow); the price column until the cost units are verified; cross-player comparison of histories.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-295 | **`history <player>` view (analytics + CLI)** — past-season line + a per-GW trend; empty-safe. | High | ⬜ To do | ~½ session |
| US-296 | **A grounded `history` ask/chat intent** — "how did X do?" → the view, narrated + verified. | High | ✅ Done | ~½ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `player_history` assembles past-season + per-GW rows for a known player and is empty-safe
   (unknown → empty); `render_player_history` shows the season table (Pts/Mins/xGI) + the "fills from GW1" note
   when per-GW is empty; the CLI `history <player>` resolves a name and renders (a real-DB smoke, skip if no
   data); `route("how did Haaland do last season?")` → `history` (and *"is Haaland worth it"* still → `worth`);
   `_decide_history` returns a `detail` + facts that verify (✓). Existing **751** stay green. No `.save(` / no
   analytics change.
2. **Manual smoke** — `python app.py history Haaland` shows his past seasons; `ask "Haaland's history"` narrates
   it with the ✓ trust line.
3. **Docs updated** — PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help.

---

### 📝 Session Progress Log

**US-295 — the `history <player>` view (analytics + CLI).** ✅ Done.
- New pure `analytics/history.py::player_history(player, seasons, gameweeks)` → a display shape: normalised
  past-season rows (season · Pts · Mins · Starts · **Pts/90** · xGI · xGC) + this-season per-GW rows (round ·
  Pts · Mins). Empty-safe (None/[] → empty; 0 minutes → pp90 0, no divide-by-zero). A read-view lens — never xP.
- New `ui/history.py::render_player_history` — a season table + a per-GW trend, or a *"per-GW form fills once the
  season starts (GW1)"* note; degrades cleanly (no player → a nudge; no backfill → "run `history --backfill`").
- The CLI **`history`** command gained a positional **`<player>`**: `history Haaland` resolves the name
  (`_resolve_player`: exact web_name wins, else a unique substring; ambiguous/none → a clear message) and prints
  the view; `history --backfill` still ingests; bare `history` keeps its help.
- **Real data now** — `history Haaland` shows 4 seasons (272/217/181/239 pts with minutes · starts · pp90 · xGI
  · xGC); the per-GW trend lights up at GW1. (The stored `start_cost`/`end_cost` are already £m — price is a
  clean follow-up; the view leads with the reliable rate metrics.)
- **Tests (+8):** `player_history` assembly + pp90 + empty-safety; `render_player_history` season table / GW1
  note / per-GW trend / degrade; the CLI parser (positional + `--backfill`) + a real-DB `history Haaland` smoke
  + the unknown-player message. **759** green, ruff clean.
- **Note:** my first `Write` accidentally overwrote the existing `tests/test_history.py` (history *ingestion*
  tests) — caught it (the suite count dropped), restored the original from git, and moved the new view tests to
  `tests/test_history_view.py`.

**US-296 — a grounded `history` ask/chat intent.** ✅ Done.
- A **`history`** intent in `_INTENT_KEYWORDS` (cues: *history · last season · last year · how did · track
  record · past seasons · season by season · season record*), placed **after `worth`** so *"is X worth it"*
  still routes to worth and *"who should I captain?"* stays captain — verified by a routing test.
- `ask._decide_history(store, question)` resolves the named player (`_match_players`, ADR-039), builds
  `player_history`, renders the view as `detail`, and puts the **last season's pts/mins/xGI + the season count**
  into `facts` — so a narrated number **verifies (✓, ADR-037)**; degrades on an ambiguous/absent player or one
  with no backfill. Wired into `_dispatch`; the **Ask** tab + CLI `chat` inherit it.
- **Verified on real data:** *"Haaland's history"* → the season table, `facts.last_season` = *"2025/26: 239
  pts over 2953 mins, 28.17 xGI"*; *"how did Haaland do last season?"* also routes to `history`.
- **Tests (+3):** routing (history vs worth vs captain); `_decide_history` grounds the seasons + facts (verifies
  ✓); degrades without a named player. **762** green, ruff clean.
- **Manual smoke:** `ask "Haaland's history"` narrates his recent seasons with the ✓ trust line (degrades to the
  facts block without Ollama).

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
