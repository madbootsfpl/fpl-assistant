# Sprint 087: "Talked about" — count mentions across a bigger sample

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (a larger RSS sample + paginate the now-longer board)
**Carried Over:** none

> **Direction (owner, tester feedback):**
> Trending → **💬 Talked about**: *"only showing 1 mention regardless of the number of mentions — can we add
> all mentions?"*

---

### 🔎 Verified at planning (real data — a live fetch)

- **The counter is NOT capped at 1.** A live `r/FantasyPL/.rss` fetch + `community_buzz` gave a distribution
  of **{1: 35, 2: 8, 3: 3, 4: 5}** across 51 mentioned players (Foden / Sánchez / Baleba / Trafford each
  **4**). The display already shows the true count (`r['mentions']`).
- **The real cause is the sample size.** Reddit's default `.rss` returns only **25 posts**, so most players
  are naturally mentioned once → **35 of 51 sit at "1 mention"**, and the board *reads* as "everyone's just
  1." So "add all mentions" = **count across a much bigger sample**.
- **Reddit RSS supports `?limit` (up to 100).** A second fetch to confirm the exact numbers **429'd** (rate
  limited after the first call) — which is exactly the *degrade-gracefully* path (ADR-059) doing its job, and
  a reminder the board is button-gated + cached ~30 min. `?limit=100` is Reddit's documented RSS max; the
  live count is a **DoD manual smoke** (when Reddit isn't throttling).
- **Consequence:** a 100-post sample mentions **many** more players, so the board (currently one expander per
  player, *un*paginated — unlike the other Trending boards, which page at 30) will get long → **paginate it**.

---

### 🎯 Sprint Goal

**Objective:** the "Talked about" board counts mentions across the latest **~100** posts (not 25), so the
counts are meaningful and differentiated; and the now-longer board is **paginated** like the others. Still a
best-effort **buzz lens** (ADR-059) — cached, button-gated, degrades on failure; never touches xP.

#### Success Criteria
- [x] **US-232 (bigger sample, ADR-076)** — the Reddit RSS client requests **`?limit=100`** (a `limit`
      param, default 100), so `community_buzz` counts mentions across ~100 posts. `community_buzz` already
      sums every match across every entry — a test pins that a player mentioned in **N** entries counts **N**
      (not 1). The caption says "across the latest ~100 r/FantasyPL posts". Degrade-gracefully unchanged
      (429/403/timeout → the existing "unavailable" note).
- [x] **US-233 (paginate the board)** — the "Talked about" list is **paginated** (reuse `paginate`,
      per_page=30, like the other Trending boards), still sorted by mentions desc, so a 100-post sample's
      long list stays navigable.
- [ ] **No drift** — it stays a display-only buzz lens (a test still asserts `decision_xp` is untouched);
      existing **619** stay green; ruff clean.
- [ ] Docs: ADR-076 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-232 | **Bigger RSS sample** — request `?limit=100` so "Talked about" counts mentions across ~100 posts (not 25); confirm the count is the true total. ADR-076 (refines ADR-059). | High | ✅ Done | ~¼ session |
| US-233 | **Paginate the board** — page the (now longer) "Talked about" list at 30, sorted by mentions desc. | Medium | ✅ Done | ~¼ session |

---

### 🧭 Design sketch

**US-232 (ADR-076).** `RedditRssClient.get_subreddit_rss(subreddit, *, limit=config.REDDIT_RSS_LIMIT)` adds a
`?limit=` query (new `config.REDDIT_RSS_LIMIT = 100`). The URL template stays; the limit is appended
(`f"{url}?limit={limit}"`). `community_buzz` is unchanged — it already does `hits += len(findall(...))` per
entry, summed across all entries (a test makes this explicit: 3 entries mentioning a player → 3). The
Trending caption + the button help note "the latest ~100 posts". Failure handling unchanged (ADR-059).

**US-233.** In `pages/6_Trending.py`, before the `for r in buzz` render, `page = paginate(buzz, key="buzz",
per_page=30)` and iterate `page` (buzz is already sorted by mentions desc). The per-player expander +
photo/badge rows are unchanged; the count line reads "N players mentioned across the latest ~100 posts".

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `community_buzz` counts N for a player mentioned in N feed entries (a fixture RSS with
   repeats); the Reddit client appends `?limit=100` to the URL; the board paginates (a 40-mention fixture →
   a page control, ≤30 shown). `decision_xp` untouched. Existing **619** stay green.
2. **Manual smoke** (Reddit not throttling) — Trending → Talked about → counts now range well above 1
   (popular players in double figures), the list pages at 30, and it still degrades to the "unavailable"
   note when Reddit 429s.
3. **Docs updated** — ADR-076 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-232 (bigger sample, ADR-076).** Diagnosed on a live fetch: the counter is fine (it produced 1–4); the
board looked uniform only because the default `.rss` is **25 posts** (35/51 players at "1"). Fix:
- **`config.REDDIT_RSS_LIMIT = 100`**; `RedditRssClient.get_subreddit_rss(..., *, limit=…)` now appends
  `?limit={limit}` to the URL → ~100 posts. The counter (`community_buzz`) is untouched — it already sums
  every match across every entry.
- Trending captions + the button help now say *"across the latest ~100 posts."*
- The fake clients in the tests use a no-arg `get_subreddit_rss(self)`, so the defaulted `limit` param is
  backward-compatible; `community_signals` still calls it with no args.
Tests: +2 (a player in 4 posts counts **4**, not 1; the client requests `…/.rss?limit=100`). ruff clean,
full suite **621** green. (Live re-verify is a DoD smoke — Reddit 429'd during planning, which is the
degrade path.)

**US-233 (paginate the board).** The "Talked about" list now pages via the shared `paginate(buzz,
key="buzz", per_page=30)` (like the other Trending boards) — `for r in paginate(buzz, …)` — still sorted by
mentions desc; ≤30 → a count caption, >30 → a "Page" selectbox + "Showing X–Y of N". +1 test
(`test_talked_about_board_paginates`: a 35-player fixture → the page control appears; monkeypatched RSS +
`st.cache_data.clear()` so it's deterministic). ruff clean, full suite **622** green.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **619 → 622** (+3); ruff clean; CI-parity green.

**Delivered**
- **US-232 — bigger sample (ADR-076).** The Reddit RSS client now requests `?limit=100`
  (`config.REDDIT_RSS_LIMIT`), so "Talked about" counts mentions across ~100 posts instead of 25 — the
  counter (`community_buzz`) was already correct.
- **US-233 — paginate the board.** The (now longer) buzz list pages at 30 via the shared `paginate`.

**What went well**
- **Diagnosed before fixing.** A live fetch showed the counter produced 1–4 (not 1) — the real cause was the
  25-post sample (35/51 players at "1"). The fix targeted the sample size, not the (correct) maths.
- **Reused what worked** — the counter and `paginate` were untouched/reused; the change is one URL param +
  one wiring line.
- **The 429 during planning was informative** — it confirmed the degrade-gracefully path (ADR-059) and why
  the board is cached + button-gated.

**Watch-outs / follow-ups**
- **Live re-verify pending** — Reddit throttled during planning, so the higher counts are a manual smoke
  when Reddit isn't rate-limiting. The unit tests pin the count logic + the `?limit=100` request.
- The Cloud IP may still be blocked (unchanged) → it degrades to the "unavailable" note.
- Preseason buzz is thin (megathreads dominate); it sharpens in-season.

See `Sprint87_Lessons_Learnt.md` for the detailed retro.
