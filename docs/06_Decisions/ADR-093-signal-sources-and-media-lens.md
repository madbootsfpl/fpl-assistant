# Architectural Decision Record: External signal-source policy + a media-headlines lens

**Decision ID:** ADR-093
**Date:** 2026-08-16
**Status:** Accepted
**Superseded By / Replaces:** extends the **news lens** (ADR-058) and **Community Signals** (ADR-059); follows
the crowd-lens invariant (ADR-057 — signals never feed `decision_xp`). Also a **policy** record: which external
signal sources we adopt vs defer, so future feed requests triage fast.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner asked to review a list of ~12 external feed groups (official APIs, Reddit, Fantasy Football Scout,
BBC, Premier League, Premier Injuries, Sky, club sites, Transfermarkt, betting/odds, YouTube) and add the ones
that add value to the **News** / **Trending** sections.

**Verified from the dev environment:** Fantasy Football Scout `/feed/` (12 items), BBC Football RSS (70) and
Reddit `r/FantasyPL/top/.rss?t=week` (25, real FPL titles) all return **public RSS/Atom** with no auth; YouTube
`feeds/videos.xml?channel_id=…` is public Atom. The FFS **FPL-tag** feed returned malformed XML (use the main
`/feed/`). The other sources are **HTML pages** (Premier League, Sky, club sites, Premier Injuries),
**anti-scrape** (Transfermarkt), or **auth-walled** (Reddit `.json` needs OAuth; Betfair needs a key).

The app is a **read-only, multi-user Streamlit deploy** whose IP can be 403'd/rate-limited (Reddit's `.rss`
already does, intermittently), with a strong bias toward **lightweight, degrade-gracefully** and **signals as a
lens, never xP** (ADR-057).

#### Decision Drivers
- **FPL-relevant value** for News/Trending, without over-building.
- **Public + no-auth + no-scrape** — RSS/Atom feeds only; no HTML scraping, no keys, no ToS risk.
- **Cloud-safe** — any feed may fail, so fetches must be best-effort (cached, button-gated, degrade).
- **A lens, never xP** — headlines/buzz inform the human; they must not touch `decision_xp`.
- **Cheap to maintain** — adding/removing a feed should be a one-line config change; no new dependency.

---

### ✅ Decision

**Adopt the public, no-auth, FPL-relevant RSS/Atom feeds via one generic best-effort mechanism; defer
everything requiring scraping, auth, or odds.**

**A media-headlines lens.** `api/feeds.py::MediaFeedsClient` (the `RedditRssClient` shape — our UA, tight
timeout, retry-once, raise on failure) + a pure `parse_feed(xml, limit)` that extracts `title` · `link` ·
`published` from **both** RSS `<item>` and Atom `<entry>` (stdlib `ElementTree` — **no new dependency**). A
`config.MEDIA_FEEDS` list (name + url) drives it — **Fantasy Football Scout** · **BBC Football** · a **YouTube**
FPL creator to start. `web_streamlit/media.py::media_headlines` fetches + parses each **per-feed** (one bad feed
is skipped), and the **News** tab shows an opt-in **Headlines** section — **button-gated**, **`st.cache_data`**
(~30 min), grouped by source, each a link back to the source. Total failure → a graceful "couldn't reach the
feeds" note.

**Trending weekly-top.** `RedditRssClient` gains a `top/.rss?t=week` variant → a "top discussions this week"
list beside the existing buzz counter (US-292).

**Policy — the verdicts (for future requests):**
- **Adopt (public RSS, FPL-relevant):** Fantasy Football Scout `/feed/`, BBC Football RSS, Reddit
  `top/.rss?t=week`, YouTube creator RSS.
- **Defer:** Reddit `.json` (OAuth); Premier League / Sky / club-site / Premier-Injuries pages (HTML scraping —
  and FPL's own `status`/`news` is our grounded injury source); Transfermarkt (anti-scrape ToS); **betting/odds**
  (auth **and** it's a *modelling input* that would cross the lens→xP line — a possible gated **Tier-3** effort,
  not a lens); NLP/sentiment over the headlines (we show titles + links, not derived analysis).

Every adopted feed is **display-only** (never xP) and **best-effort** (cached, gated, degrade).

---

### 🔀 Alternatives Considered

- **Scrape the HTML sources** (Premier League, Sky, clubs, Premier Injuries). Rejected — fragile, high
  maintenance, ToS risk; FPL's own news/status already grounds injuries.
- **Reddit `.json` / Betfair API** for richer data. Rejected for now — OAuth/keys + rate limits on a read-only
  cloud; the public `.rss` covers buzz.
- **Fold odds into xP.** Rejected — crosses the lens→xP line (ADR-057); a separate, gated modelling effort if
  ever pursued.
- **A dependency (`feedparser`).** Rejected — stdlib `ElementTree` handles RSS + Atom; keep deps lean.
- **Fetch on page load.** Rejected — button-gated + cached, so a slow/blocked feed never delays the page.

---

### 🧭 Consequences

**Positive**
- FPL-relevant headlines (analysis + football news) on News, and sharper "talked about" on Trending, from
  public feeds — no auth, no scraping, no new dependency.
- Adding a feed is a one-line `MEDIA_FEEDS` change; a documented policy triages future requests.
- Best-effort + gated + cached → no impact on load time or reliability; a lens, so `decision_xp` is untouched.

**Negative / risks (mitigations)**
- **Cloud IP blocking / feed outages** → per-feed try/except (skip the failed one), total-failure note, cache,
  button gate; tests use fixtures (no live network).
- **Content/ToS** → we show **titles + links + dates** (standard RSS syndication) and link back to the source;
  no full-text reproduction, no derived analysis.
- **YouTube channel curation** → channel-ids finalised by fetching to verify; unverified → a documented config
  slot for the owner, not a hard-coded guess.
- **Feed-format drift** → the parser tolerates missing fields + junk (empty-safe); a bad feed degrades, never
  crashes.

---

### 📊 Validation

Fetched FFS `/feed/`, BBC football RSS and Reddit `top/.rss?t=week` successfully before deciding. Acceptance:
`parse_feed` extracts title/link/date from an RSS `<item>` **and** an Atom `<entry>` fixture (empty-safe);
`media_headlines` returns the good feeds when one fails (a fake client); the News Headlines + Trending
weekly-top render (AppTest, faked client — no live network) and degrade to a note on total failure;
`decision_xp` is unchanged; existing **739** tests stay green; ruff clean.
