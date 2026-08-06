# Sprint 068: Community Signals — Reddit RSS buzz (no auth)

**Dates:** 2026-08-06
**Status:** ✅ Complete (1/1 story; retro done)
**Capacity:** ~1 session (a gate + a best-effort RSS adapter + a buzz counter + a board)
**Carried Over:** US-195 (the Reddit spike, from Sprint 067) — reframed to RSS after the JSON API 403'd

> **Direction (owner):** genuine community sentiment — *who the community is talking about* — **without**
> applying for Reddit Developer access (the rules changed). Owner's call: use the **public RSS feed** and
> name it **"Community Signals"**. A probe confirmed `r/FantasyPL/.rss` works (no auth) while the `.json`
> API 403s.

---

### 🔎 Verified at planning

- **`.json` → 403** (all User-Agents / `old.reddit` — an IP/access block, not the header); **`.rss` → 200**
  (25 posts, 50 KB). Parsing titles + counting player `web_name` mentions gave a live buzz list
  (Cunha/Mbeumo/Wirtz…). So **no OAuth, no secret** needed.
- **Rate-limited** — the `/hot/.rss` variant 429'd on rapid repeats → **cache + button-gate**.
- **Cloud-IP caveat** — worked from a normal IP; Streamlit Cloud's datacenter IP may be blocked → the board
  **degrades to "unavailable"** (accepted, best-effort like ClubElo).
- **Buzz, not sentiment** — mention *frequency*, framed honestly as "most talked about".

---

### 🎯 Sprint Goal

**Objective:** ship **Community Signals** — a best-effort, no-auth Reddit **RSS** buzz counter surfaced as a
Trending "💬 Talked about" board — degrade-gracefully, cached, button-gated. Display-only; xP untouched. A
gate (ADR-059) settled the RSS-not-OAuth approach.

#### Success Criteria
- [x] Approach agreed (**ADR-059**) — RSS (no auth/secret); degrade-gracefully; cached + button-gated;
      buzz ≠ sentiment; cloud-IP may block → degrades
- [x] A self-contained **Reddit RSS client** (`src/api/reddit.py`, best-effort, retry-then-`RedditError`)
- [x] A pure **`community_buzz(rss, players, limit)`** (parse Atom + count `web_name` mentions; empty-safe)
      + an orchestrator **`community_signals`** that degrades to `(None, message)`
- [x] A Trending **"💬 Talked about"** board — **button-gated** (no fetch on load), `@st.cache_data`
      (~30 min), degrades to "unavailable"; player · team · **Mentions** · flags
- [x] **No xP change** — display-only; `decision_xp` untouched
- [x] Tests — `community_buzz` (rank + empty-safe + short-name skip); `community_signals` (degrade + ok, fake
      client); the board button present (no network on load); existing **523** stay green
- [x] Docs: ADR-059 + index, Architecture, Roadmap (Tier-2), Home, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-195 | **Community Signals (Reddit RSS)** — a best-effort RSS client + a pure buzz counter + a Trending "Talked about" board; ADR-059; degrade-gracefully, cached, button-gated; no auth/secret | High | ✅ Done | 1 session |

---

### ✅ Definition of Done

1. **Tests pass** — `community_buzz` ranks mentions + is empty-safe + skips short names; `community_signals`
   degrades on a failing client and returns the buzz on success (fake client, no network); the Trending
   board button is present without a fetch on load; a test still asserts `decision_xp` unchanged. **528**
   green.
2. **Manual smoke done** — the counter ranks a sample RSS (Haaland 3 / Saka 2 / Isak 1); the orchestrator
   degrades to "unavailable" on a boom client; the page loads with the button, no network until clicked.
3. **Docs updated** — ADR-059 + index, Architecture, Roadmap, Home, PROJECT_STATUS.

---

### 📝 Session Progress Log

- **US-195 ✅ (gate + build)** — Recorded **ADR-059** (RSS-not-OAuth). New `src/api/reddit.py`
  `RedditRssClient` (best-effort, ClubElo pattern — retry then `RedditError`); new `src/community.py` —
  pure **`community_buzz(rss, players, limit)`** (parse Atom titles/content, count `web_name` mentions,
  ≥4 chars, empty-safe) + **`community_signals`** (fetch + count, degrade to `(None, message)`). A Trending
  **"💬 Talked about"** tab: **button-gated** (no fetch on load) + `@st.cache_data(ttl=1800)` on the RSS,
  degrading to "buzz unavailable"; shows player · team · **Mentions** · flags. Config `REDDIT_RSS_URL` /
  `REDDIT_SUBREDDIT` / `REDDIT_TIMEOUT`. Tests (+5 → **528**): the counter (rank / empty-safe / short-name
  skip); the orchestrator (degrade + ok via a fake client); the board button (no network on load). Smoke
  confirmed. No auth, no secret; `decision_xp` untouched. **Cloud-IP caveat:** may degrade to "unavailable"
  on the live datacenter IP — accepted (best-effort).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — genuine "community buzz" shipped **without Developer access or a secret**, by
using the public RSS feed the owner suggested. Degrade-gracefully, cached, button-gated.

**What went well** — probing feasibility first turned a blocked OAuth plan into a no-auth RSS one; mirroring
the ClubElo best-effort pattern made it robust by construction; button-gating + caching keeps it a good
Reddit citizen *and* kept the network out of tests (a fake client covers every branch).

**What to watch** — the **cloud datacenter IP may be blocked** (403/429), so on the live app the board may
often show "unavailable" — honest, best-effort, and exactly what the degrade path is for; verify on the
live site after redeploy. Buzz is mention-frequency, not sentiment (a later NLP step if wanted).

**Lessons captured:** `docs/05_Sprints/Sprint68_Lessons_Learnt.md`.
