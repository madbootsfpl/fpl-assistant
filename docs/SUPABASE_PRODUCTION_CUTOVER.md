# Supabase hardening — production cutover (Stages A + B)

**What this applies:** [`SUPABASE_RLS.md`](SUPABASE_RLS.md) Stages **A and B** — closing `beta_waitlist` and
`beta_users` to the anon key, with the app's access replaced by four narrow functions.
Rehearsed end-to-end on staging, 2026-09-19.

**What it does not touch:** `squads`, `user_prefs`, `player_watchlist` remain readable with the anon key
(Stage B3, not built) and `events` is deferred. ⭐ *This closes the two tables holding email addresses. It is
the useful half, not the whole fix.*

**Time:** fifteen minutes. **Reversible:** yes — see Rollback.

---

## ⚠️ Read this first: the ordering rule is DIFFERENT for each stage

| stage | order | why |
|---|---|---|
| **A** (`beta_waitlist`) | **code → SQL** | The code change is a plain INSERT, which works fine against the *old* permissive policies. Deploying it early is safe; applying the SQL early would break every waitlist write, **silently**. |
| **B** (`beta_users`) | 🔴 **SQL → code** | The new code **calls functions that must already exist**. Deploying it early 404s every gate check, and — because the failures are swallowed — **every tester is told the beta is full**. |

⭐ **They are opposite, and assuming otherwise has already cost one live incident.** On 2026-09-19 the Stage B
code reached production ahead of its functions, via a push to `master` that Streamlit Cloud auto-deployed.
*"On master but not applied to production"* is not the same as *"not deployed"*.

### Where production already is (2026-09-19)

✅ **All the code is deployed**, and ✅ **the Stage B functions are applied**
([`sql/stage_b_functions_only.sql`](../sql/stage_b_functions_only.sql), the additive hotfix).
So the SQL-before-code hazard is **already behind you** — what remains is the part that *removes* access.

---

## Step 1 — Confirm the starting state

**SQL Editor** (you are the owner, so RLS does not apply to you — which is exactly why the counts belong here
and the verification does not):

```sql
select
  (select count(*) from beta_users)     as allow_listed,
  (select count(*) from beta_waitlist)  as waitlist_rows,
  (select max(created_at) from beta_waitlist) as newest_refusal,
  (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.proname in ('is_allow_listed','register_beta_user','forget_me','touch_last_seen')) as functions;
```

**`functions` must be 4.** If it is not, apply `sql/stage_b_functions_only.sql` first and stop here — the
revoke in Step 2 would lock everyone out.

**Write down `allow_listed`, `waitlist_rows` and `newest_refusal`.** They are how you will know, tomorrow,
that real sign-ins and real refusals are still landing.

---

## Step 2 — Set the Admin secret, BEFORE the revoke

**Streamlit Cloud → Manage app → Settings → Secrets**, add:

```toml
FPL_ADMIN_STORE_KEY = "<the production service_role key>"
```

⚠️⚠️ **The `service_role` key bypasses RLS completely** — everything this cutover builds is invisible to it.
It is safe here for one reason: **Streamlit renders server-side, so it never leaves the machine.** ⭐ *That
reason does not transfer* — it must never be compiled into a mobile client.

**Why before:** Step 3 revokes `anon`'s access to `beta_users`, and the Admin roster reads the whole list.
Without this secret the roster goes blank the moment you run it. It degrades to **empty**, not to an error,
so ⭐ *the symptom would read as "the roster is broken" rather than "the key is missing"*.

Save, and let the app reboot.

---

## Step 3 — Apply the hardening

**SQL Editor → New query → Run.** It will warn about destructive operations: those are the `revoke` lines.
No table is dropped.

```bash
pbcopy < sql/stage_a_and_b.sql      # puts the whole file on your clipboard
```

**Expect:** `Success. No rows returned.`

---

## Step 4 — Verify with the anon key

⚠️ **The SQL Editor cannot do this.** It runs as the table owner, and owners bypass RLS — a permission test
there passes whatever the policies say. Only the anon key sees what the app sees.

```bash
SUPA_URL="https://<production-ref>.supabase.co" \
SUPA_KEY="<production anon key>" \
./scripts/supabase_probe.sh
```

⭐ Pass them inline; do not write production credentials to a file. (The script takes explicit environment
over `.env.staging`, so this cannot accidentally probe staging.)

| probe | expected |
|---|---|
| **`beta_users`** | 🔴 **HTTP 401** |
| **`beta_waitlist`** | 🔴 **HTTP 401** |
| `squads` | **unchanged**, still 200 — Stage B3 is not built |
| `maddie_videos` | **unchanged**, still 200 |

⚠️ **A change everywhere means something broke. A change nowhere means it did not land.** Neither is success.

---

## Step 5 — Prove the app still works

The lock is half of it. Three paths must still work, and **none of them reports its own failure**.

**a. The gate admits an allow-listed tester.** Sign in to the live app with your own account. You should be
admitted as normal — not shown the waitlist message.

**b. A refusal still reaches the waitlist.** Hardest to test without a spare Google account; if you have one,
sign in with it and confirm a new row appears in `beta_waitlist` (SQL Editor — the anon key cannot read it
any more, which is the point).

**c. The Admin roster renders.** Open the Admin page. It should list your testers. Blank means Step 2's
secret did not take.

⭐ **Check "message shown" and "row written" separately.** The failure being guarded against shows the
message and writes nothing — a gate that looks perfectly healthy while recording nobody.

---

## Step 6 — Watch it for a day

📅 **Tomorrow, re-run Step 1's query.** `allow_listed` should be ≥ what you wrote down if anyone new signed
in, and `newest_refusal` should move the first time someone is genuinely turned away.

⚠️ **A frozen count is the failure signal, and the only one you will get.**

---

## Rollback

One block, restoring today's behaviour. Safe at any point:

```sql
grant all on public.beta_users    to anon, authenticated;
grant all on public.beta_waitlist to anon, authenticated;
alter table public.beta_waitlist disable row level security;
grant all on public.maddie_videos to anon, authenticated;
```

⚠️ **Do not drop the functions** — the deployed code calls them. Rolling those back means rolling back the
code too, which is the ordering hazard in reverse.

---

## Afterwards

**Still open:** `squads`, `user_prefs` and `player_watchlist` can be enumerated by anyone holding the anon
key. That is **Stage B3**, whose RPCs would be largely superseded by **Stage C** (real identity via Supabase
Auth, Phase 3) — so it is a judgement call about how far away Stage C really is, not an oversight.
