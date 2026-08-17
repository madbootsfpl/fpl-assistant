# Sprint 167: The ⭐ Watchlist (US-409, ADR-117)

**Dates:** 2026-08-18
**Status:** ✅ Complete — ADR-117 + US-409. Owner-approved shape. 1005 → 1009 tests. Before GW1 ✓.

> **Ask:** a persistent shortlist of players to keep an eye on (daily/weekly watch). **Owner shape:** ⭐ add on
> **Players**, view + act on **My Squad → Transfer**, real ⭐ toggles, **max 30** (fill as few/many as you like).

---

### 🎯 Delivered

- **`watchlist.py`** — a per-user list of player ids, held in `st.session_state` and (signed in + store configured)
  mirrored per-user in Supabase (`auth.user_key`, endpoint from `FPL_STORE_URL` — **no new secret**), restored once
  per session like the squad. **Off by default** (session-only fallback); **best-effort** (a sync hiccup never
  blocks a ⭐); **capped at `MAX = 30`** (the 31st is blocked).
- **⭐ Add on Players:** a ⭐ **toggle on the player card** (Add ⇄ ★ Watching — remove) + **row-select on the pool
  → "⭐ Add selected"**, with a **"N/30 watched"** caption. Real Streamlit widgets (the US-388 lesson).
- **View + act on My Squad → Transfer:** a **"⭐ Your watchlist"** section — each watched player's **next fixture ·
  xP · form** + **★ Remove** → bring one in via the manual transfer right below.
- **Storage:** a `player_watchlist(user_key pk, player_ids jsonb, updated_at)` table (same Supabase project); owner
  SQL in **BETA.md §7**. The app upserts it (disable RLS or insert+update policies, like the squad store).
- **Tests:** +4 (cap = 30 · the pool ⭐ control + count · starring on the card toggles · the Transfer section).

**Owner action:** run the `player_watchlist` SQL (BETA.md §7) when convenient — until then, watchlists work
in-session only.

### 🧠 Lessons

- **Reuse the persistence seam.** The watchlist is the squad-persistence pattern again (session + per-user
  Supabase + restore-once) — a whole feature with no new secret and a familiar shape.
- **Match the surface to the mental model.** Add where you browse (Players), view where you act (Transfer) — the
  owner's "it's for your squad's future" instinct put the list exactly where you'd use it.
- **Row-select is the reliable "per-row ⭐".** `st.dataframe` can't hold per-row buttons; multi-row select + an
  "Add selected" button is the honest equivalent (and the card gets a real star).
