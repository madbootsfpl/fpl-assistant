# Architectural Decision Record: The ⭐ Watchlist — a per-user player shortlist

**Decision ID:** ADR-117
**Date:** 2026-08-18
**Status:** Accepted — owner-approved. Build = Sprint 167 (before GW1).
**Superseded By / Replaces:** New feature. Reuses the per-user persistence seam (ADR-106: `auth.user_key` +
Supabase) and the shared filter/card patterns. Complements the Radar (ADR-107) — Radar *suggests* who to watch;
the Watchlist is the ones you *chose* to keep watching.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester ask (2026-08-17): a way to **shortlist players and keep an eye on them** across sessions — a daily/weekly
watch — without re-deriving it each time. Currently the Radar is auto-generated (6 easiest-run teams × top-3) and
nothing is *kept*. Owner wants it **before GW1**.

#### Decision Drivers
- **Add where you browse; view where you act.** You discover targets on **Players**; you act on them (transfer one
  in) on **My Squad → Transfer**.
- **Persists across sessions/devices** — reuse the per-user store behind the squad (ADR-106), off-by-default.
- **A shortlist, not a second squad** — a hard cap; fill as few or as many as you like.
- **Reliable ⭐** — real toggles, not painted-on affordances (the US-388 lesson).

---

### ✅ Decision  *(owner-approved: add on Players · view on My Squad → Transfer · ⭐ · max 30)*

**1. A per-user watchlist of player ids** (`web_streamlit/watchlist.py`) — held in `st.session_state` and, when
signed in + the store is configured, mirrored per-user in Supabase keyed by `auth.user_key` (best-effort, restored
once per session, like the squad). **Off by default** — no store/login → session-only. **Cap `MAX = 30`** (a
*maximum*, not a target; the 31st is blocked with a gentle "watchlist full").

**2. ⭐ Add on Players.** A ⭐ on the **player card** (Players ▸ Card → *⭐ Add to watchlist* / *★ Remove*) and a
**multi-row select on the pool** → *⭐ Add selected*, with a "⭐ N/30 watched" caption. Real Streamlit widgets.

**3. View + act on My Squad → Transfer.** A **⭐ Watchlist** section on the Transfer sub-tab listing each watched
player with **next fixtures · FDR · xP · form**, a **★ Remove**, and (reuse) the manual transfer to bring one in —
so the watchlist is your bring-in candidate list right where you'd act.

**4. Storage** — a `player_watchlist(user_key text primary key, player_ids jsonb, updated_at)` table in the same
Supabase project (endpoint derived from `FPL_STORE_URL`, **no new secret**); the app upserts it (like the squad).
Owner SQL in BETA.md.

**What this is *not*.** Not a change to `decision_xp`/the Radar algorithm. Not a new tab (owner: too many already).
Not on Fixtures (owner steer → Players/My Squad). Not required to be filled.

---

### 🔀 Alternatives Considered

- **A dedicated ⭐ Watchlist tab.** Rejected (owner) — too many tabs already.
- **On Fixtures/Radar.** Rejected (owner) — a watchlist serves your *squad's* future, so it belongs with team
  management; and you star while browsing *Players*.
- **⭐ per-row buttons in the pool.** Deferred — `st.dataframe` can't hold per-row buttons cleanly; row-select +
  an "⭐ Add selected" button is the reliable equivalent (the card gets a direct ⭐).
- **Session-only (no persistence).** Rejected — the whole point is to *keep* it across sessions/devices.

---

### 🧭 Consequences

**Positive** — a persistent shortlist that follows you; a clean browse→star→transfer flow; My Squad stays lean
(the list lives on Transfer, where you act).
**Negative / risks (mitigations)** — depends on the store when signed in (*mitigation:* best-effort +
session fallback, never blocks a ⭐); one more table (*mitigation:* one-time SQL, same shape as the squad);
another server write (*mitigation:* off-by-default, secret-gated, fail-silent — the invariant holds).

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**Sprint 167**): `watchlist.py` (session + per-user sync, cap 30); ⭐ on the Players card +
  pool-select add; the ⭐ Watchlist section on My Squad → Transfer; the `player_watchlist` table SQL (BETA.md).
- **Not this ADR / follow-ups:** ⭐-per-row in the pool; a watchlist-vs-owned "already own it" hint; price-change
  alerts on watched players.
