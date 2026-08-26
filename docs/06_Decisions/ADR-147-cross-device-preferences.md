# Architectural Decision Record: A remembered manager id — per-user preferences that follow you

**Decision ID:** ADR-147
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 202, 2026-08-26). **1416 → 1425 tests, ruff clean.**
⏳ **One owner action:** create the `user_prefs` table (SQL below, complete with policies). Until then the
feature degrades to session-only — which is exactly today's behaviour — and Admin ▸ 🔧 says so.
**Superseded By / Replaces:** Reuses the per-user store pattern of ADR-106 (squads) and ADR-117 (watchlist).
Makes 🏆 Leagues (ADR-141) usable on a second visit.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on the newly-shipped Leagues page:

> When a league is loaded it must persist from session to session **and between devices**.

Leagues asks for a manager id, looks up every league behind it, and forgets all of it when the tab closes.
Re-typing an eight-digit number every visit undercuts the feature it belongs to — and **ADR-141's own revision
was about exactly this kind of friction**: nobody knows their league id, so the page was changed to take the
number people actually have. Then it threw that number away too.

**"Between devices" is the clause that decides the design.** A cookie (ADR-099's *remember me*) survives a
refresh and nothing else. Cross-device needs the per-user store — which this app already runs twice over, for
the squad (ADR-106) and the ⭐ watchlist (ADR-117), keyed by `auth.user_key(email)` off `FPL_STORE_URL`, with
**no new secret**.

---

### ✅ Decision

**1. Remember the manager id, not just the league — and the ordering is the point.** A stored *league id*
restores one league. A stored *manager id* restores the **list**, so every league you are in comes back and the
picker can open where you left off. Both are stored; the manager id is what makes it worth doing.

**2. `src/web_streamlit/prefs.py`, modelled on `watchlist.py`** — session_state is the truth, the cloud is a
mirror, restored **once per session** and written **only when a value actually changed**. Streamlit reruns on
every interaction, and a preference that moves twice a season should not cost a network call per page view.

**3. Signed out → session-only, silently.** That is precisely today's behaviour, so the page keeps working for
anyone browsing without an account. `_load` returning `None` on failure is deliberately distinct from `{}`
("nothing stored"), so a flaky network cannot look like a deliberate clearing of your preferences.

**4. A new table, and a complete grant — because ADR-142 taught this the hard way.** Yesterday an identical
write failed silently for a day: the table had SELECT and INSERT policies and **no UPDATE policy**, and
PostgREST reports that as **`200 OK, zero rows`**, not an error. So this ships with the diagnostic *first*:

```sql
create table if not exists public.user_prefs (
  user_key   text primary key,
  manager_id text,
  league_id  bigint,
  updated_at timestamptz default now()
);
alter table public.user_prefs enable row level security;

-- Postgres has no "create policy if not exists", so drop-then-create keeps the whole block re-runnable.
-- The anon key ships to the browser, so every policy is scoped to this table alone.
drop policy if exists "prefs read"   on public.user_prefs;
drop policy if exists "prefs insert" on public.user_prefs;
drop policy if exists "prefs update" on public.user_prefs;
drop policy if exists "prefs delete" on public.user_prefs;

create policy "prefs read"   on public.user_prefs for select to anon using (true);
create policy "prefs insert" on public.user_prefs for insert to anon with check (true);
create policy "prefs update" on public.user_prefs for update to anon using (true) with check (true);
create policy "prefs delete" on public.user_prefs for delete to anon using (true);
```

⚠️ **Two corrections to the first version of this SQL, both found by running it.**

1. **The `delete` policy was missing** (added by ADR-148). Without it `unsubscribe.remove_me` would have
   silently failed to delete a preference row — PostgREST answers `200 OK, zero rows` for an RLS-blocked
   delete — while telling the person their data was gone.
2. **The block was not re-runnable.** `create table if not exists` says "safe to run again"; the four
   `create policy` lines that followed it were not, so re-running to pick up the fix failed with
   `42710: policy "prefs read" already exists` and — because Postgres rolls the statement back — applied
   *nothing*. **An idempotent first line in a block that is not idempotent is worse than neither**, since it
   invites the re-run that then fails. Postgres has no `create policy if not exists`, so drop-then-create is
   the idiom; the block above is now safe to run any number of times.

`remember()` returns a **status string** the page ignores and **Admin ▸ 🔧 Are cross-device preferences
storing?** prints — running the same function the page does, because a probe down a parallel path proves only
that a second implementation works.

**Why a new table rather than a column on `beta_users`:** the narrow grant recommended in ADR-142 is
`grant update (last_seen)` — *one column*. Adding a preference there would need that grant widened, on a table
holding **email addresses**. A separate table keeps the allow-list's write surface at one harmless column,
which was the whole point of scoping it.

### ⚠️ Risks

- **Rows are keyed by a hash of the email**, never the address — the same handle `squads` uses. `user_prefs`
  holds a manager id and a league id, both already public FPL identifiers.
- **`unsubscribe.remove_me` does not yet delete `user_prefs`.** Noted as a follow-up: ADR-122 promises "remove
  me = we delete your rows", and this adds a row that promise does not currently cover.
- **Until the table exists it is invisible**, looking identical to the feature not working. Hence the
  diagnostic shipping in the same commit rather than after a bug report.

### 🧪 Definition of Done

1. **Tests: +9.** Signed-out session-only; nothing reaches the network unconfigured; a store failure leaves
   the session value intact; restore happens **once**, not per rerun; a failed restore does not wipe the
   session; unchanged values are not re-written (compared as text, so `123` and `"123"` are one id); unknown
   keyword fields are dropped; and **a zero-row write names row-level security** — ADR-142's failure, pinned
   before it can happen again.
2. **Manual smoke** — the Leagues page: manager id remembered, league picker reopening on the last choice.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, a sprint retro.
