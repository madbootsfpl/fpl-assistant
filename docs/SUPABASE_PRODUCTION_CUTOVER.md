# Stage A — production cutover runbook

> # 🔴 DO NOT RUN THIS AS WRITTEN — 2026-09-19
>
> **Stage A on its own breaks ADR-122's "Remove me".** Revoking `DELETE` on `beta_waitlist` turns a tester's
> self-service deletion into `refused (HTTP 401)` — and the UI **ignores that result by design**, so nothing
> surfaces. The table simply stops honouring the promise.
>
> ⚠️ **Confirmed on staging, after Stage A was applied there**: `remove_me` returned
> `beta_waitlist: refused (HTTP 401)`. The original rehearsal checked that the waitlist *write* still worked
> and stopped there — ⭐ *a permission you remove is a promise you may have removed with it.*
>
> **The fix exists** — `forget_me` in [`sql/stage_b.sql`](../sql/stage_b.sql), which performs the one deletion
> a person is entitled to and reports a row count per table. It is built, tested against a real Postgres, and
> on `master` (`e05f2d9`).
>
> **So Stage A and Stage B now ship together.** This runbook covers Stage A alone and needs rewriting to
> cover both — including the new `FPL_ADMIN_STORE_KEY` secret, without which the Admin roster goes blank the
> moment `beta_users` is revoked.
>
> 📋 **Everything below is still accurate for Stage A itself** — the ordering rule, the measurements, the
> verification and the rollback. It is the *scope* that is wrong, not the steps.

**What this applies:** [`SUPABASE_RLS.md`](SUPABASE_RLS.md) **Stage A** — closing `beta_waitlist` to reads and
confirming `maddie_videos` is read-only. Rehearsed in full on staging on 2026-09-19; this is the same change
against the live project.

**What it does not touch:** `squads`, `beta_users`, `user_prefs`, `player_watchlist` — those need **Stage B**
(security-definer RPCs and a code change) and `events` is deferred. ⭐ *Stage A removes the read on the table
of refused addresses. It is the smallest useful piece, not the whole fix.*

**Time:** ten minutes. **Reversible:** yes, in one block — see Rollback.

---

## ⚠️ Order matters, and only in one direction

1. **The code change** (`waitlist.py`, plain INSERT) — commit `43945b7`, already on `master`.
2. **Then** the SQL.

**Code before SQL.** If the SQL lands while the deploy is still sending
`Prefer: resolution=merge-duplicates`, every waitlist write starts failing — and the write is **fail-silent**,
so nothing surfaces. The table would simply stop growing and it would look like nobody was being refused.

⭐ **The intermediate state is safe in this direction only.** New code + old policies works fine: a plain
INSERT against permissive policies behaves exactly as the upsert did, bar not refreshing `reason` on a repeat.
That is why the code can sit in production for days before the SQL follows.

---

## Step 1 — Confirm the deployed app has the new code

**Streamlit Cloud → Manage app → check the deployed commit is `43945b7` or later.** If it predates that,
Reboot from the ⋮ menu and wait for the redeploy.

⚠️ *Do not skip this on the assumption that a push auto-deploys.* Community Cloud can serve a stale or
half-synced checkout, and the symptom here would be silent.

---

## Step 2 — Record the "before", without dumping anyone's address

**SQL Editor** (you are the owner, so RLS does not apply to you — that is exactly why this belongs here and
not in a probe):

```sql
select
  (select count(*) from beta_waitlist) as waitlist_rows,
  (select max(created_at) from beta_waitlist) as newest_refusal,
  (select count(*) from beta_users)    as allow_listed;
```

**Write these down.** `waitlist_rows` is how you will know, tomorrow, that real refusals are still landing.

---

## Step 3 — Apply the SQL

**SQL Editor → New query → Run.** It will warn about destructive operations: that is the `drop policy` lines,
and there is no `DROP TABLE` in it.

```sql
-- A1 — beta_waitlist: emails go in, nothing comes out.
revoke all on public.beta_waitlist from anon, authenticated;
grant insert on public.beta_waitlist to anon;

alter table public.beta_waitlist enable row level security;

drop policy if exists "waitlist insert"        on public.beta_waitlist;
drop policy if exists "waitlist upsert-update" on public.beta_waitlist;

create policy "waitlist insert" on public.beta_waitlist
  for insert to anon with check (true);

-- A2 — maddie_videos: public read is correct; writable is not.
revoke all on public.maddie_videos from anon, authenticated;
grant select on public.maddie_videos to anon;

alter table public.maddie_videos enable row level security;

drop policy if exists "maddie_videos public read" on public.maddie_videos;
create policy "maddie_videos public read" on public.maddie_videos
  for select to anon using (true);
```

**Expect:** `Success. No rows returned.`

---

## Step 4 — Verify with the anon key

⚠️ **The SQL Editor cannot verify this.** It runs as the table owner, and owners bypass RLS — a permission
test run there passes whatever the policies say. Only the anon key sees what the app sees.

Take the **anon / publishable** key from **Project Settings → API**, and pass it inline. ⭐ Do **not** write
production credentials to a file:

```bash
SUPA_URL="https://<production-ref>.supabase.co" \
SUPA_KEY="<production anon key>" \
./scripts/supabase_probe.sh
```

**The shape you want — one of four changes:**

| probe | expected |
|---|---|
| `beta_users` | **unchanged**, still 200 with the list (Stage B's job, not this one) |
| **`beta_waitlist`** | 🔴 **HTTP 401 — permission denied** |
| `squads` | **unchanged**, still 200 |
| `maddie_videos` | **unchanged**, still 200 |

⚠️ **A change everywhere means something broke. A change nowhere means it did not land.** Neither is success.

---

## Step 5 — Prove the write still works

The lock is only half of it. The gate must still record a refusal — and that path cannot report its own
failure, so it has to be checked by hand.

```bash
curl -s -o /dev/null -w "new:    HTTP %{http_code}\n" -X POST "$SUPA_URL/rest/v1/beta_waitlist" \
  -H "apikey: $SUPA_KEY" -H "Authorization: Bearer $SUPA_KEY" -H "Content-Type: application/json" \
  -d '{"email":"cutover-check@example.invalid","reason":"not_listed"}'

curl -s -o /dev/null -w "repeat: HTTP %{http_code}\n" -X POST "$SUPA_URL/rest/v1/beta_waitlist" \
  -H "apikey: $SUPA_KEY" -H "Authorization: Bearer $SUPA_KEY" -H "Content-Type: application/json" \
  -d '{"email":"cutover-check@example.invalid","reason":"full"}'
```

**Expect `201` then `409`.** On staging this was `201 / 409 / 401` — written, duplicate refused, unreadable.

Then in the **SQL Editor**, confirm it landed and tidy up:

```sql
select email, reason from beta_waitlist where email = 'cutover-check@example.invalid';
delete from beta_waitlist where email = 'cutover-check@example.invalid';
```

⭐ The row must say **`not_listed`**, not `full`. Both halves in one column: the insert landed, and the repeat
was refused rather than merged.

---

## Step 6 — Watch it for a day

📅 **Tomorrow, re-run Step 2's query.** `waitlist_rows` should be **≥** what you wrote down, and
`newest_refusal` should move the first time someone is genuinely turned away.

⚠️ **A frozen count is the failure signal**, and the only one you will get — there is no error to wait for.
If it has not moved and you expected a refusal, roll back and tell me.

---

## Rollback

One block, restoring exactly today's behaviour. Safe to run at any point:

```sql
grant all on public.beta_waitlist to anon, authenticated;
alter table public.beta_waitlist disable row level security;

grant all on public.maddie_videos to anon, authenticated;
```

⚠️ **The code does not need rolling back.** A plain INSERT works against permissive policies — that is the
same safe intermediate state described at the top.

---

## Afterwards

**Still open, and larger:** `beta_users` is read **whole-table** on every gate check (a case-sensitivity
workaround), and `squads` can still be enumerated by anyone with the key. Both need **Stage B** — the
security-definer RPCs — which is a real code change across ~4 files. ⭐ Stage A turns *"one request takes the
table"* into *"one guess gets one row"* for the waitlist only; Stage B does it for the rest, and **Stage C**
(real identity, Phase 3) is the only thing that stops a guessed handle working at all.
