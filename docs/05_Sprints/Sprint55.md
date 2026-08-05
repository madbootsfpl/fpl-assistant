# Sprint 055: Streamlit visual polish — Home, player photos, team badges

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2 working sessions (a Home fix + player photos + a small `team.code` ingest for badges + docs)
**Carried Over:** None (Sprint 054 closed clean)

> **Direction (owner, from the Sprint-54 review):** make it *look* great. Rename the home tab to **Home**
> and list all six pages; add **player photos** and **team badges** across the Streamlit UI. (The bigger
> asks — deploy & share at `a custom domain`, and Data Hardening — are captured in the Backlog; Data
> Hardening is GW1-gated anyway.)

---

### 🔎 Verified at planning (the image feature is de-risked)

- **The FPL image URLs resolve** (HTTP 200): player photos at
  `resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png` (players already carry
  `code`); team badges at `…/badges/70/t{code}.png`.
- **`team.code` is ingestable** — it's in `bootstrap-static`'s `teams[]` (Arsenal `code` = 3) but not yet
  stored (teams hold only id/name/short_name/elo). A **light migration** adds it — the same pattern as
  earlier field additions.
- **Display is native** — `st.column_config.ImageColumn` renders a URL column as thumbnails inside
  `st.dataframe`; the **browser** fetches the images (not our server), so no new runtime dependency; a
  missing image just shows a broken-thumbnail icon (graceful).
- **Thin, reuses the engine** — the pages already build their tables from stored data; images are one more
  column derived from the stored `code`. Core analytics unchanged; the two-edge guardrail holds.
- Preseason (GW1 2026-08-21).

---

### 🧭 What's new — the UI gets a face

The Streamlit app gets a proper **Home** landing (all six pages described) and **imagery**: **player
photos** on the Players table and **team badges** on Fixtures (and the Players team column). Small,
visual, and it makes the app pleasant to look at (and to share later).

---

### 🎯 Sprint Goal

**Objective:** the Streamlit edge gains a renamed **Home** page (full landing), **player photos** (from
the stored player `code`) and **team badges** (via a light `team.code` ingest) rendered as native image
columns — reusing the stored data, the core unchanged, FastAPI frozen.

#### Success Criteria
- [ ] The home sidebar entry reads **Home**, and the landing lists **all six** pages (incl. Transfer &
      Build descriptions)
- [ ] **Player photos** — a photo column on the Players table (`st.column_config.ImageColumn` from
      `p{code}.png`)
- [ ] **`team.code` ingested** — a light migration (model + storage column + upsert) reading
      `bootstrap-static` `teams[].code`
- [ ] **Team badges** — a badge column on **Fixtures** (and the Players table's team), from `t{code}.png`
- [ ] Images fail gracefully (a missing URL → a broken-thumbnail icon, no crash)
- [ ] Tests — the migration/ingest (get_teams returns `code`); `AppTest` (the image columns are
      configured; pages still render)
- [ ] The core analytics are unchanged; **FastAPI frozen**; the two-edge guardrail passes
- [ ] Docs: Architecture changelog, Handbook Ch 12, README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-162 | **Home + player photos** — rename the home tab to **Home** + list all six pages on the landing (Transfer/Build descriptions); add a **player photo** column to the Players table (`ImageColumn` from `code`). `AppTest` tests | High | ✅ Done | 0.5–1 session |
| US-163 | **Team badges (+ `team.code` ingest)** — a light migration to store `team.code` (model + storage + ingest from `bootstrap-static`); a **badge** column on Fixtures + the Players team. Storage/ingest + `AppTest` tests | High | ✅ Done | 1 session |
| US-164 | **Polish + docs** — image sizing / graceful fallback tidy; docs (Architecture, Handbook Ch 12, README, PROJECT_STATUS). Smoke | High | ✅ Done | 0.5 session |

#### Technical Tasks & Maintenance
- [x] `team.code` migration + ingest (a light schema addition) — _US-163_
- [x] Update Architecture changelog + Handbook Ch 12 + README + PROJECT_STATUS — _US-164_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the `team.code` migration/ingest (storage returns `code`); `AppTest` (the
   image columns configured; pages render with data or the info branch); the existing **439** stay green;
   the core + the FastAPI edge unchanged; the two-edge guardrail passes.
2. **Manual smoke test done** — `python -m src.web_streamlit`: the sidebar shows **Home**; the landing
   lists all six pages; player photos show on Players; team badges show on Fixtures; a `refresh` populates
   `team.code`.
3. **Documentation updated & checked** — Architecture, Handbook Ch 12, README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Home rename + full landing; player photos; team badges | Deploy & share (`a custom domain`) — Backlog (a later gated sprint) |
| A light `team.code` ingest for badge URLs | Any analytics/decision change; a new runtime dependency |
| Native image columns (`ImageColumn`); graceful fallback | Downloading/caching images locally (the browser fetches them) |
| Reuse the stored data + existing pages | Data Hardening (GW1-gated) |

**External Dependencies:** FPL's image CDN (`resources.premierleague.com`) — fetched by the **browser** at
render; a miss degrades to a broken-thumbnail icon. No new Python dependency.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| An image URL 404s (a player/team without a photo) | Low | Native `ImageColumn` shows a broken-thumbnail icon; no crash; verified the URL pattern resolves |
| The `team.code` migration on an existing DB | Low | A light additive migration (nullable column); a `refresh` backfills it; a storage test asserts it |
| Images load slowly / offline | Low | The browser fetches them; the tables still render without them; cosmetic only |
| Scope creep into a player-detail page | Low | Keep it to image *columns* on existing tables this sprint |

---

### 🗝️ No gate this sprint — one call to confirm

UI polish over the settled Streamlit edge (ADR-052) + a **display-only** metadata field (`team.code`). No
new analytics decision, so **no ADR proposed**. *The one call for the owner (confirm at "start US-162"):*
earlier schema additions were ADR-gated when they were **analytics** fields (strengths, xG, ownership);
`team.code` is **display-only** (a badge URL), so I propose **skipping the ADR** — say if you'd rather a
light ADR-053 for the schema touch. Images render via native `ImageColumn`; the browser fetches them.

---

### 📝 Session Progress Log

- **US-162 ✅** — **Home**: renamed the entrypoint `app.py` → **`Home.py`** (in Streamlit's classic
  multipage, the sidebar label is the entrypoint's *filename* — hence the old "app"); the runner
  (`__main__._APP`) + tests now target `Home.py`. The landing lists **all six** pages with Transfer/Build
  descriptions. **Player photos**: the Players table gains a leading image column (`st.column_config.
  ImageColumn`) whose URL is built from the stored player `code`
  (`…/photos/players/110x140/p{code}.png`); the browser fetches it, a missing one degrades to a
  broken-thumbnail icon. No ingest change (player `code` already stored).
  - **Tests (440 total, +1):** the Players table has the photo-URL column when data is present (checked
    via `at.dataframe[0].value[""]`); the runner points at `Home.py`; all pages still render.
  - **Smoke:** `python -m src.web_streamlit` boots clean (entrypoint `Home.py`, 200, no errors).
- **US-163 ✅** — **`team.code` ingest** (a light migration, the same pattern as earlier field additions):
  `Team.code` (model + `from_api`), the `teams.code` column (CREATE + `_MIGRATIONS` + `UPSERT_TEAM` +
  `save_teams` + `get_teams`); `Team.from_api` reads `bootstrap-static` `teams[].code`, so **`refresh`
  backfills it** (ARS=3, AVL=7 …). **Team badges**: a new edge helper `src/web_streamlit/badges.py`
  (`{short_name → …/badges/70/t{code}.png}`, empty for a missing code); a **badge** image column on
  **Fixtures** and the **Players** table (the two `st.dataframe` pages — Squads stays text). Player photo
  key renamed `"" → "photo"` so the two image columns don't collide.
  - **Tests (442 total, +2):** a storage round-trip (`save_teams(code) → get_teams` returns it); the badge
    helper (URL from code; `None → ""`); the Players/Fixtures page tests assert the photo + badge columns.
    The two-edge guardrail still passes (badges.py is *edge*, imported by pages, not the core).
  - **Smoke (`AppTest`, refreshed DB):** Fixtures renders real badge URLs (t14 = LIV); Players shows both
    the player photo and the team badge.
- **US-164 ✅** — Docs wrap + polish. Images already degrade gracefully (`width="small"`; a missing code →
  an empty cell, no crash), so no code change. **Docs:** Architecture §12 (Sprint 055 — Home rename +
  photos/badges + the `team.code` ingest); Handbook Ch 12 (the `Home.py` entrypoint + `ImageColumn`
  photos/badges); README (Home landing + photos/badges in the pages list); PROJECT_STATUS (Tests 442, the
  Web-UI pages with photos/badges).
  - **Final smoke:** `python -m src.web_streamlit` boots clean (Home entrypoint, 200, no errors); 442
    tests green, ruff clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the Streamlit UI got a face. A proper **Home** landing (all six pages),
**player photos** on Players, and **team badges** on Fixtures + Players. **442 tests** (was 439, +3); **52
ADRs** (no new ADR — UI polish + a display-only field). Core analytics unchanged; the two-edge guardrail
holds.

**Delivered**
- **US-162** — Home (entrypoint `app.py` → `Home.py`, full landing) + player photos (`ImageColumn` from
  the stored player `code`).
- **US-163** — a light `team.code` ingest (migration, backfilled by `refresh`) + team badges (an edge
  helper `badges.py`) on Fixtures + Players.
- **US-164** — docs (Architecture, Handbook Ch 12, README, PROJECT_STATUS) + smoke.

**What went well**
- **The URL probe at planning paid off** — verifying the FPL photo/badge URLs (and that `teams[].code`
  existed) meant the images "just worked" first time.
- **A tiny data touch, kept honest** — `team.code` was a nullable, additive migration that `refresh`
  backfills; display-only, so no ADR. The `Team.from_api` reuse meant *zero* ingest-code change.
- **The edge boundary held** — the new `badges.py` helper lives in `src/web_streamlit/`; the guardrail
  test confirmed the core imports no edge.
- **Images degrade gracefully** — the browser fetches them; a missing code → an empty cell, no crash.

**Challenges / how they were handled**
- **Renaming the Home tab** — in Streamlit's classic multipage the sidebar label is the entrypoint
  *filename*, so `app.py` → `Home.py` (+ runner/tests) was the clean fix.
- **Two image columns colliding** — a dict can't have two `""` keys; renamed the photo key to `"photo"`
  and added `"badge"`, each an `ImageColumn`.
- **`AppTest` + a wide table** — pandas truncates the string repr, so the image-column tests inspect the
  DataFrame column directly (`df["photo"]` / `df[""]`).

**Carried forward:** None. *(Backlog for later: deploy & share at `a custom domain`; a Compare/Captain
page; Data Hardening post-GW1.)*
