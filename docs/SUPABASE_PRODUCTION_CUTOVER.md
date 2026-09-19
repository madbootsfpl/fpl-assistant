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

### 🔴 Incident, 2026-09-19 — read this before Step 1

**The cutover was run against an app still serving OLD code, and sign-in crashed.** Rolled back in under a
minute; nothing lost.

**What happened:** the Stage B code was pushed to `master` hours earlier, so it was assumed deployed. It was
not — Streamlit Cloud was still serving the previous build. The revoke took `beta_users` away from `anon`,
the old `is_registered` still read that table directly, and every sign-in hit
`requests.exceptions.HTTPError`.

⭐⭐ **`git log` tells you what is on master. It does not tell you what Cloud is serving.** That distinction
was assumed twice in one evening — once producing a *false* alarm (a hotfix for a break that had not
happened, because the old code was working fine against the open table) and once producing a *real* one.

⚠️ **This runbook already said "confirm the deployed commit" and it was not enough**, because a step that can
be satisfied by glancing at a git log will be. So the check below is now **behavioural**: the app has to
demonstrate which code it is running, not be assumed to.

### The check that cannot be fudged

⭐ **Revoking SELECT is itself the test**, and it is reversible in one statement. Old code reads the table and
breaks; new code calls a function and does not.

```sql
-- 1. Take ONLY the read, from ONLY this table.
revoke select on public.beta_users from anon;
```

**Now sign in to the live app.**

| what you see | what it means | next |
|---|---|---|
| **Admitted normally** | ✅ the new code is live — it used the RPC | run the cutover |
| **A crash / `HTTPError`** | 🔴 old code still deployed | restore, then Reboot Cloud and retry |

```sql
-- 2. Restore, whichever way it went.
grant select on public.beta_users to anon;
```

⚠️ **Do this at a quiet moment**: during the window, a tester signing in on old code gets an error page. It
lasts as long as it takes you to sign in and run one statement.

**If it fails:** Streamlit Cloud can serve a stale or half-synced checkout. **Manage app → ⋮ → Reboot app**,
wait for it to come back, and run the check again. Sometimes it needs a second reboot.

### Where production already is (2026-09-19)

✅ **The Stage B functions are applied** — [`sql/stage_b_functions_only.sql`](../sql/stage_b_functions_only.sql),
confirmed by the pre-flight query returning `functions = 4`.

🔴 **The Stage B code is NOT deployed** — proven by the incident above, where the revoke crashed sign-in on
the old `is_registered`. It is on `master`; Streamlit Cloud has not picked it up.

⚠️ **So the SQL-before-code hazard is NOT behind you** — an earlier draft of this section said it was, on the
assumption that a push equals a deploy. **Run the behavioural check above and get a green before Step 1.**

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

**b. A refusal still reaches the waitlist.** ⭐ **This is the one that cannot report its own failure**, so it
is worth the five minutes.

⚠️ **A second Google account is not enough on its own.** Under the cap, ADR-193 *admits* a new address rather
than waitlisting it — so the `not_listed` path is unreachable until the beta is full. You have to close the
gap deliberately:

1. **SQL Editor:** `select count(*) from beta_users;` — note the number, call it **N**.
2. **Streamlit Cloud → Settings → Secrets:** set `FPL_USER_CAP = N`. The beta is now exactly full.
3. Sign in with a **second Google account** that is not on the allow-list.
   ✅ Expect the *"the beta is **full** right now, so you're on the waitlist"* message.
4. **SQL Editor:** `select email, reason from beta_waitlist order by created_at desc limit 3;`
   ✅ Expect that address with `reason = 'not_listed'`.
5. **Put the cap back** to whatever it was, and tidy up:
   ```sql
   delete from beta_waitlist where email = '<the second account>';
   ```

⚠️ **While the cap is lowered, a genuinely new tester signing in would be waitlisted too.** The window is
minutes and it is self-healing — ADR-193's message tells them to sign in again, and they are admitted the
moment the cap is restored — but do it at a quiet hour rather than a deadline.

⭐ **Check the message and the row separately.** The failure this exists for shows the message and writes
nothing: a gate that looks perfectly healthy while recording nobody.

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
