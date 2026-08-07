# Architectural Decision Record: "Talked about" — count mentions across a bigger sample

**Decision ID:** ADR-076
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** **refines ADR-059** (Community Signals / Reddit RSS buzz). No change to the
counter or to the degrade-gracefully contract — only the **size of the sample** it counts over, plus
pagination of the (now longer) board. Triggered by a tester bug report.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester on Trending → **💬 Talked about**: *"only showing 1 mention regardless of the number of mentions — can
we add all mentions?"*

**Verified in code (a live fetch):** the counter is **not** capped. `r/FantasyPL/.rss` + `community_buzz`
gave mention counts of **{1: 35, 2: 8, 3: 3, 4: 5}** across 51 players (Foden / Sánchez / Baleba each **4**);
the display already shows the true `mentions`. The real cause is the **sample size** — Reddit's default
`.rss` returns only **25 posts**, so most players are naturally mentioned once and **35 of 51 sit at "1"**,
making the board *read* as "everyone's just 1." A second fetch to confirm a larger `?limit` **429'd** (rate
limited) — which is exactly the ADR-059 degrade path working, and why the board is button-gated + cached
~30 min. Reddit RSS accepts **`?limit`** up to **100**. A 100-post sample mentions many more players, so the
board (currently *un*paginated, one expander per player — unlike the other Trending boards, which page at 30)
gets long.

#### Decision Drivers
- **Meaningful counts** — "add all mentions" = count across a *representative* sample, not just 25 posts.
- **Reuse the working counter** — `community_buzz` already sums every match across every entry; don't touch
  the maths.
- **Stay best-effort** — still cached, button-gated, degrade-on-failure (ADR-059); never touches xP.
- **Navigable** — a longer list needs the same pagination the other boards use.

---

### ✅ Decision

**1. Fetch ~100 posts (US-232).** `RedditRssClient.get_subreddit_rss(..., *, limit=config.REDDIT_RSS_LIMIT)`
appends `?limit=` to the RSS URL, with a new **`config.REDDIT_RSS_LIMIT = 100`** (Reddit's RSS max). So
`community_buzz` counts mentions across ~100 posts instead of 25. The counter is **unchanged** — it already
does `hits += len(findall(name, entry.text))` summed across all entries (a test pins that N entries → N).
The Trending caption + button help say *"across the latest ~100 r/FantasyPL posts."*

**2. Paginate the board (US-233).** The "Talked about" list uses the shared `paginate(buzz, key="buzz",
per_page=30)` (like the other Trending boards), still sorted by mentions desc — so a 100-post sample's long
list stays navigable.

**3. Degrade + scope unchanged.** A 403 / 429 / timeout / parse error still yields the "unavailable" note
(never a raise, ADR-059). It remains a **display-only buzz lens** — a test still asserts `decision_xp` is
untouched. No server writes.

---

### 🔀 Alternatives Considered

- **Leave it at 25 posts.** Rejected — that's the bug; the board reads as uniform "1 mention".
- **Paginate multiple RSS pages / crawl `after=` for >100.** Rejected — heavier, more requests → more 429s;
  100 (the RSS max) is plenty for a buzz lens.
- **Count comments/upvotes, not just post text.** Rejected — not in the RSS; a much bigger scrape. Buzz =
  post mentions (ADR-059), just over a bigger window.
- **Switch to `/new/.rss`.** Rejected — the default (hot) is the better "what's being talked about" signal;
  we just want more of it (`?limit=100`).
- **Cap to a top-N instead of paginating.** Rejected — pagination matches the other Trending boards and
  keeps the full list reachable.

---

### 🧭 Consequences

**Positive**
- Counts become meaningful and differentiated (popular players in double figures over ~100 posts).
- The board matches the other Trending boards (paginated), so the longer list is navigable.
- No change to the counter, the degrade contract, or xP.

**Negative / risks (mitigations)**
- **More requests → 429 risk** → the same cache (~30 min) + button-gate already covers it; a 429 still
  degrades cleanly. One larger request, not many.
- **The live app's Cloud IP may still be blocked** → unchanged from today; it degrades to the note.
- **Preseason the buzz is thin** (megathreads dominate) → a bigger sample helps but it truly sharpens
  in-season; the caption already frames it as best-effort.

---

### 📊 Validation

Verified (live fetch): the default feed is 25 posts and the counter already produces 1–4; the fix is the
sample size. Acceptance: the Reddit client appends `?limit=100`; `community_buzz` counts N for a player in N
entries (a fixture with repeats); the board paginates at 30 sorted by mentions desc; failure still yields the
"unavailable" note; `decision_xp` is untouched; the existing 619 tests stay green (new tests added). Manual
smoke (when Reddit isn't throttling): counts range well above 1.
