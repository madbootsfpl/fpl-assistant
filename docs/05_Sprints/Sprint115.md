# Sprint 115: Signal feeds — a media-headlines lens + sharper "talked about"

**Dates:** 2026-08-16 (planned)
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~1 session (a generic best-effort RSS lens + a Reddit variant — display-only, no xP)
**Carried Over:** none

> **Direction (owner):** *"Review these news/signal feeds and add value to News / Trending if appropriate."*
> After a review (verdict table below), the owner chose to add the four viable, no-auth RSS feeds: **Fantasy
> Football Scout** + **BBC Football** + **YouTube (FPL creators)** → **News**; **Reddit weekly-top** → **Trending**.

---

### 🔎 Verified at planning (fetched each feed from here)

- **Public RSS works, no auth:** Fantasy Football Scout `/feed/` → **12** items; BBC Football
  `feeds.bbci.co.uk/sport/football/rss.xml` → **70**; Reddit `r/FantasyPL/top/.rss?t=week` → **25** (real FPL
  titles, e.g. *"Are Haaland, Fernandes and Gabriel Worth Their Price?"*); YouTube `feeds/videos.xml?channel_id=…`
  is public Atom. The FFS **FPL-tag** feed returned malformed XML → use the **main** `/feed/` (it's FPL-heavy).
- **We already have the pattern.** `api/reddit.py::RedditRssClient` is a self-contained, **best-effort** RSS
  client (tight timeout, retry-once, degrade on 403/429/timeout); Community Signals caches + button-gates it.
  A generic media-feeds client is the same shape — **no new dependency** (stdlib `ElementTree` parses both RSS
  `<item>` and Atom `<entry>`).
- **The rules the review applied:** adopt only **public, no-auth** feeds that are **FPL-relevant**, parse as
  **RSS/Atom** (no HTML scraping), and stay a **display lens** (never xP). That's why we **defer** Reddit `.json`
  (OAuth), Premier League/Sky/club sites & Premier Injuries (HTML scraping; FPL's own `status`/`news` is our
  grounded injury source), Transfermarkt (anti-scrape ToS) and **betting/odds** (auth + it's a modelling input
  that crosses the lens→xP line — a gated Tier-3 effort). Recorded as **ADR-093**.
- **Cloud reality:** any of these may 403/rate-limit from the Streamlit Cloud IP (as Reddit's `.rss` sometimes
  does) — so every feed is **button-gated + cached + degrade-gracefully** (a failed feed is skipped; all-failed
  → "unavailable"), never blocking the page.

---

### 🎯 Sprint Goal

**Objective:** the **News** tab gains an opt-in **Headlines** lens aggregating FPL-relevant public RSS (Fantasy
Football Scout · BBC Football · a YouTube FPL creator), and the **Trending** "talked about" gains the week's
**top discussions** (Reddit weekly-top) — both best-effort, cached, display-only. No scraping, no secret, no xP.

#### Success Criteria
- [x] **US-291 (a media-headlines lens on News)** — a generic best-effort `api/feeds.py::MediaFeedsClient` +
      a pure parser (`title` · `link` · `published`, handling RSS `<item>` and Atom `<entry>`) driven by a
      **`config.MEDIA_FEEDS`** list (Fantasy Football Scout · BBC Football · YouTube). A **Headlines** section
      on the **News** tab — button-gated, **`st.cache_data`** (~30 min), grouped by source (title + link +
      date), each linking back to the source; a per-feed degrade (skip a failed feed; all-failed → a graceful
      note). Display-only, no secret.
- [x] **US-292 (sharper "talked about")** — the Trending **Community Signals** gains a **"🔥 Top discussions
      this week"** list from Reddit **`top/.rss?t=week`** (top N post titles + links) — reusing
      `RedditRssClient` (a URL variant), button-gated + cached + degrade-gracefully, alongside the existing
      buzz counter.
- [x] **No drift** — display/lens only; `decision_xp`/the analytics/grounding unchanged; the read-only web
      guardrail holds (no server writes); the new fetches are best-effort + tested with a **fake/parsed
      fixture** (no live network in tests); **746** green (739 → +7: parse/aggregate/degrade + reddit-top + render checks); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help, ADR-093 (the signal-source policy +
      the media lens).

---

### 🧭 Design sketch

**US-291 — the media lens (the gate writes ADR-093).**
- `config.MEDIA_FEEDS = [{"name": "Fantasy Football Scout", "url": ".../feed/"}, {"name": "BBC Football",
  "url": ".../sport/football/rss.xml"}, {"name": "YouTube — <creator>", "url": ".../videos.xml?channel_id=…"}]`
  (a list, so adding/removing a feed is one line).
- `api/feeds.py::MediaFeedsClient.fetch(url)` — best-effort GET (our UA, tight timeout, retry-once), returns
  the raw XML or raises; a pure `parse_feed(xml, limit)` → `[{title, link, published}]` handling both RSS
  `<item>` (`title`/`link`/`pubDate`) and Atom `<entry>` (`title`/`link href`/`published`). Empty-safe.
- `web_streamlit/media.py::media_headlines(feeds, limit_per_feed)` — fetch + parse each, per-feed try/except so
  one bad feed doesn't sink the rest; cached at the page via `st.cache_data`.
- **News** tab: below the FPL player news, an expander/section **"📰 Headlines (FPL analysis & football news)"**
  — button-gated, grouped by source, each a `st.link_button`/markdown link + the date; degrades to "couldn't
  reach the feeds right now" on total failure. *(YouTube channel-id(s) finalised at build by fetching to verify;
  if none verifies, ship the mechanism + a documented `MEDIA_FEEDS` slot for the owner to fill.)*

**US-292 — weekly-top discussions.** `RedditRssClient.get_top_weekly()` (the `…/top/.rss?t=week` URL) → parsed
titles + links; a **"🔥 Top discussions this week"** list in the Trending Community Signals block (button-gated
+ cached), beside the buzz counter. Reuses the existing parser/degrade path.

**Deferred (recorded in ADR-093):** Reddit `.json` (OAuth); Premier League/Sky/club-site/Premier-Injuries HTML
scraping; Transfermarkt (ToS); betting/odds (auth + crosses lens→xP → a possible Tier-3 modelling item, not a
lens); NLP/sentiment over the headlines (we show titles + links, not analysis).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-291 | **Media-headlines lens (News)** — a generic best-effort RSS/Atom aggregator (FFS · BBC · YouTube) as an opt-in Headlines section; cached, degrade-gracefully (ADR-093). | High | ✅ Done | ~½ session |
| US-292 | **Sharper "talked about" (Trending)** — Reddit weekly-top discussions (titles + links) beside the buzz counter. | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `parse_feed` extracts title/link/date from an RSS `<item>` **and** an Atom `<entry>`
   fixture (empty-safe on junk); `media_headlines` skips a failing feed and returns the others (a fake client);
   `get_top_weekly` parses a Reddit-top fixture; the News Headlines section + the Trending weekly-top render
   (AppTest, no live network — the client is faked/monkeypatched) and degrade to a note on total failure.
   Existing **739** stay green. No `.save(` (guardrail holds); no live network in the suite.
2. **Manual smoke** — News → Headlines shows FFS/BBC/YouTube titles that link out; Trending shows the week's
   top discussions; both degrade cleanly when a feed is unreachable.
3. **Docs updated** — PROJECT_STATUS, Architecture, Roadmap, Backlog, README, Help, ADR-093.

---

### 📝 Session Progress Log

**US-291 — media-headlines lens on News.** ✅ Done. **ADR-093** written first (the gate).
- New `api/feeds.py`: `MediaFeedsClient.fetch(url)` (best-effort — our UA, 5s timeout, retry-once, raise on
  failure) + a pure **`parse_feed(xml, limit)`** that extracts `title`/`link`/`published` from **both** RSS
  `<item>` (title/link/pubDate) and Atom `<entry>` (title/`link href`/published) with stdlib `ElementTree` —
  **no new dependency**; empty-safe on junk, skips a malformed entry.
- `web_streamlit/media.py::media_headlines` fetches + parses each `config.MEDIA_FEEDS` **per-feed** (one
  failing feed is skipped; all-failed → `{}`); `client` injectable for tests.
- **News tab:** a **"📰 Headlines — FPL analysis & football news"** section — **button-gated** ("Load
  headlines"), **`st.cache_data(ttl=1800)`**, grouped by source with each title linking out + its date;
  degrades to a "couldn't reach the feeds" note. Display-only; no server writes.
- **Feeds shipped active:** **Fantasy Football Scout** `/feed/` + **BBC Football** (both verified live —
  real titles + links). **YouTube:** the mechanism supports it, but I couldn't resolve a channel-id from the
  sandbox (YouTube's consent wall returns a JS stub), so rather than hard-code a wrong one I left a **documented
  `MEDIA_FEEDS` slot + `MEDIA_YOUTUBE_URL` template** with how-to-find-the-id instructions — adding a creator is
  one line. _(→ owner: paste a channel-id, or tell me a creator and I'll wire it.)_
- **Tests (+6):** `parse_feed` on RSS + Atom fixtures (limit + empty-safe + skips a link-less item);
  `media_headlines` skips a failing/empty feed and returns the rest (fake client); the News Headlines section +
  button render **without fetching** (no click → no live network). **745** green, ruff clean.
- **Manual smoke:** `media_headlines()` returns FFS + BBC headlines with links; junk/empty degrade to `[]`.

**US-292 — sharper "talked about" on Trending.** ✅ Done.
- `RedditRssClient.get_top_weekly()` fetches the **`top/.rss?t=week`** variant (`config.REDDIT_TOP_WEEK_URL`),
  same best-effort contract (raise `RedditError` → the caller degrades). Reuses the generic **`parse_feed`**
  (Reddit's `.rss` is Atom — verified: real titles + links).
- **Trending → Community Signals** gains a **"🔥 Top discussions this week"** list beside the buzz counter —
  **button-gated** ("Show this week's top discussions"), a cached `_cached_reddit_top()`, the top ~10 post
  titles linking out; degrades to a note if Reddit doesn't respond. Shows *what's actually being discussed*, not
  just a mention count.
- **Tests (+1, 1 extended):** `get_top_weekly` hits the top-week URL (faked HTTP); the Trending render test
  asserts the top-discussions button + caption are present **without fetching** (no live network). **746**
  green, ruff clean.
- **Manual smoke:** `get_top_weekly` → *"Are Haaland, Fernandes and Gabriel Worth Their Price?"*, *"Bruno
  Guimarães to Arsenal"*, … (real weekly-top FPL discussion).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — 2/2 stories done. Test count **739 → 746** (+7: parse RSS/Atom, per-feed degrade,
reddit-top URL, News + Trending render checks). Ruff clean; CI-parity green. **New ADR-093** (signal-source
policy + the media lens). No analytics change — display lenses; **no new dependency** and **no live network in
the suite**.

**Delivered**
- **US-291 — media-headlines lens on News.** A generic best-effort RSS/Atom aggregator (`api/feeds.py`) driven
  by `config.MEDIA_FEEDS` (Fantasy Football Scout + BBC Football live; YouTube documented), as an opt-in,
  cached, per-feed-degrading Headlines section.
- **US-292 — sharper "talked about" on Trending.** A weekly-top Reddit discussions list (titles + links)
  beside the buzz counter.

**What went well**
- **The review did the heavy lifting.** Verifying each feed *from the environment* before planning turned "12
  sources" into "4 adopt / 8 defer, here's why" — and ADR-093 records the policy so the next feed request is a
  30-second triage, not a debate.
- **One generic parser covered everything.** `parse_feed` handles RSS `<item>` **and** Atom `<entry>`, so FFS,
  BBC, YouTube **and** Reddit's `.rss` all flow through the same tested path — no per-source code, no
  `feedparser` dependency.
- **Best-effort by construction.** Every fetch is button-gated + cached + per-feed try/except, so a 403 or a
  slow feed never touches page load — and the tests prove it with fixtures + a fake client (zero live network).
- **Honest about YouTube.** Rather than hard-code a channel-id I couldn't verify (the sandbox hits YouTube's
  consent wall), I shipped the mechanism + a documented slot — the owner drops one in.

**Watch-outs / follow-ups**
- **Cloud IP blocking is real** — FFS/BBC/Reddit may 403/rate-limit from the Streamlit Cloud IP (Reddit's
  `.rss` already does intermittently); the degrade path + cache are the mitigation, but headlines may show
  "unavailable" on the deploy.
- **YouTube is wired, not populated** — needs a verified `channel_id` (owner to supply, or resolve out-of-band).
- **Deferred (ADR-093):** Reddit `.json`/HTML scraping/Transfermarkt/odds; NLP over the headlines (we show
  titles + links, not derived analysis). Odds remain a potential *Tier-3 modelling* item, not a lens.

See `Sprint115_Lessons_Learnt.md` for the detailed retro.
