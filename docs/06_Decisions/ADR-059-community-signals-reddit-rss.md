# Architectural Decision Record: Community Signals — Reddit RSS buzz (no auth)

**Decision ID:** ADR-059
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** The keyed-Reddit path floated in ADR-058 is replaced by a **public RSS**
approach (no OAuth/secret). A third best-effort external source, following the ClubElo pattern (ADR-010/021).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants genuine **community sentiment** — which players the FPL community is *talking about* — but
the authenticated Reddit API now requires a **Developer-access application** (a barrier the owner would
rather avoid), and Reddit's `.json` endpoints return **HTTP 403** (tested: `www`/`old.reddit`, descriptive
+ browser User-Agents — an IP/access block, not a UA issue).

**A probe found the public RSS feed works:** `https://www.reddit.com/r/FantasyPL/.rss` returned 25 recent
posts (50 KB XML) with **no auth**. Parsing the post titles and counting current-player `web_name` mentions
produced a live buzz ranking (Cunha, Mbeumo, Wirtz, Semenyo, Foden…). So a **no-auth, no-secret** community
signal is feasible.

#### Decision Drivers
- **No Developer access, no secret** — the owner's blocker; RSS is a public syndication format.
- **Degrade gracefully** — external + rate-limited; must never crash the app (ClubElo pattern).
- **Honest framing** — this is *mention frequency* (buzz), not positive/negative sentiment.
- **FPL stays the source of truth**; this is a display lens, never xP.

---

### ✅ Decision

**1. "Community Signals" = a Reddit **RSS** buzz counter (no auth).** Fetch the public
`r/FantasyPL/.rss` feed (no OAuth, no secret), parse the post titles/content, and count mentions of current
players (`web_name`, word-boundary, length ≥ 4 to cut noise) → a **"most talked about"** ranking. Named
**Community Signals** (owner's call).

**2. A self-contained, best-effort source (ClubElo pattern, ADR-021).** `src/api/reddit.py` — a
`RedditRssClient` with its own `RedditError`, a tight timeout, and one retry; `src/community.py` — a pure
`community_buzz(rss_text, players, limit)` (parse + count) + an orchestrator `community_signals(players,
limit)` that **degrades gracefully**: any 403 / 429 / timeout / parse error → **`(None, a clear message)`**,
never a raise.

**3. Cache + be a good citizen.** The fetch is **cached** (TTL ~30 min, `st.cache_data`) and **button-gated**
(the user clicks "show what's being talked about" — no fetch on every rerun), with a **descriptive
User-Agent**. Low volume; respects Reddit's rate limits (the `/hot/.rss` variant 429'd on rapid repeats).

**4. Surfaced on the Trending page.** A **"💬 Talked about"** board (Community Signals): player · team ·
**mentions** · flags, from the RSS buzz. On failure → **"community buzz unavailable right now"** (not a
crash). Display-only — `decision_xp` untouched.

**5. Cloud-IP caveat (accepted).** The RSS works from a normal IP, but Streamlit Cloud's **datacenter IP**
may be blocked (403/429). If so, the board simply **degrades to "unavailable"** on the live site — accepted,
exactly like ClubElo's intermittency. Best-effort, never required.

---

### 🔀 Alternatives Considered

- **Authenticated Reddit API (OAuth).** Rejected/deferred: needs a Developer-access application + a cloud
  secret (the owner's blocker), and the `.json` endpoints 403 without it.
- **Scraping Reddit HTML.** Rejected: fragile + higher ToS risk than reading a public RSS feed.
- **X/Twitter.** Paid/restricted — out.
- **Sentiment (positive/negative) via NLP.** Deferred — mention *frequency* is a cheap, honest first signal;
  true sentiment is a later, heavier step.

---

### 🧭 Consequences

**Positive**
- Real "community buzz" with **no Developer access, no secret** — removes the owner's blocker.
- Degrade-gracefully + cached + button-gated → robust, rate-limit-friendly, never crashes.
- FPL stays truth; display-only; `decision_xp` untouched.

**Negative / risks (mitigations)**
- **Cloud-IP may be blocked** → the board degrades to "unavailable" (accepted; best-effort like ClubElo).
- **Rate limits (429)** → cache (~30 min TTL) + button-gated + a descriptive UA.
- **Buzz ≠ sentiment** → framed honestly as "most talked about"; NLP sentiment is a later step.
- **RSS format could change** → the parser degrades to empty on a parse error, never crashes.
- **ToS** → reading a public RSS feed at low volume with a descriptive UA is the least-invasive option;
  cached to avoid hammering.

---

### 📊 Validation

Probed live: `.json` → 403 (all UAs); **`.rss` → 200** (25 posts); parsing titles + counting `web_name`
mentions yielded a live buzz list. Acceptance for the sprint: `community_buzz` counts mentions from a
sample RSS (pure, tested); `community_signals` degrades to `(None, message)` on a failing client (fake-client
test, no network); the Trending "Talked about" board is button-gated (no fetch on load) and shows the buzz
or "unavailable"; `decision_xp` unchanged; the existing 523 tests stay green.
