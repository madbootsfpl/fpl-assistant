# Supabase access hardening — draft for review

**Date:** 2026-09-18 · **Status:** 📋 **Draft, nothing applied.** Phase 1.5 of the mobile plan.
**Source:** the Phase 1 audit, [`03_Architecture/Mobile_Platform_Audit.md`](03_Architecture/Mobile_Platform_Audit.md) §2.3
**Supersedes the SQL in:** [`CLOUD_SQUADS.md`](CLOUD_SQUADS.md) §1 and [`BETA.md`](BETA.md) §4 — **once applied**.

> **Naming, because three documents use the word "stage".** The work in *this* file is **Phase 1.5**, and its
> parts are **Stage A / B / C** — letters, never numbers. **Stage 2a–2f** is something else entirely: the
> autonomous data pipeline in [ADR-211](06_Decisions/ADR-211-the-pipeline-runs-without-you.md), which belongs
> to Phase 2. ⚠️ An earlier draft of this file numbered its sections *as well as* lettering its stages, so
> "Stage A" sat under a heading reading "2." — ⭐ *two numbering systems on one heading is one too many.*

> Run nothing from this file until the staging is agreed. **Stage A is safe today. Stage B needs a code
> change and will break the live app if applied without one.** That distinction is the whole document.

---

## The actual control surface — and why the current docs mislead

The existing setup SQL reaches for `alter table … disable row level security` as the "simplest alternative."
⚠️ **That is not a weaker lock, it is no lock.** And even with RLS *enabled*, `create policy … using (true)`
is equivalent to open.

⭐ **RLS is only half of it. Postgres checks table privileges first, and PostgREST acts as the `anon` role.**
A policy is never consulted for a verb the role was never granted. So the real lever is `revoke`, and the
current tables rely on the default grants that Supabase hands `anon` on table creation.

Both halves appear below, in that order.

---

## What the app actually does — measured, not assumed

Every policy below is derived from this table. It was built by reading the PostgREST calls in
`src/web_streamlit/`, not from the docs.

| table | app **reads** | filtered by key? | app **writes** | holds |
|---|---|---|---|---|
| `squads` | `select data` · `select handle,updated_at` | ✅ **yes** (`handle=eq.` / `in.`) | upsert, delete | user squads |
| `beta_users` | `select email` ×3, `select email,last_seen` | 🔴 **NO — whole table** | insert, patch, delete | **raw emails** |
| `beta_waitlist` | **never read** | — | upsert only | **raw emails** |
| `user_prefs` | `select *` | ✅ yes (`user_key=eq.`) | upsert | manager/league id |
| `player_watchlist` | `select player_ids` | ✅ yes (`user_key=eq.`) | upsert, delete | watchlist |
| `maddie_videos` | `select` 4 cols | no (public content) | none | marketing links |
| `events` | `select *` (Admin page only) | no | insert | anonymous analytics |

### 🔴 The finding that shapes the staging

**`beta_users` is read unfiltered on every gate check.** `user_store.is_registered()` pulls the **entire
email list** and matches in Python. Its own docstring says why:

> *"A PostgREST `eq.` filter is case-**sensitive**… `eq.<cleaned>` silently matches **no row** for the
> capitalised one."*

So the whole-table read is a **workaround for case-sensitivity**, not a design choice. ⚠️ **Revoking `select`
on `beta_users` therefore locks every tester out of the app.** It cannot be in Stage A.

⭐ And the fix is pleasing: moving the lookup into SQL (`lower(email) = lower($1)`) fixes the exposure **and
deletes the workaround** — the security fix and the bug fix are the same change.

---

## Stage A — small and safe, but A1 needs one line of code

Two real wins, both on tables holding **personal data**.

### A1. `beta_waitlist` — never read by the app, currently wide open 🔴

It holds the email of everyone who tried to sign in and was refused. RLS is **disabled** on it today, so the
anon key can read the lot — and **delete it**.

#### ⚠️ Corrected 2026-09-19 — this needs a one-line code change, and the first draft was wrong

The original A1 claimed *"safe to apply today, no code change"*. **It is not**, and the staging rehearsal is
what found it. Measured across four variants on Postgres 17:

| grants / policies | anon can read? | the app's upsert |
|---|---|---|
| `insert, update` + insert/update policies | ❌ denied ✅ | ❌ **permission denied** |
| …plus `select` privilege, no select policy | ❌ 0 rows ✅ | ❌ **RLS violation** |
| …plus a `select` policy `using (false)` | ❌ 0 rows ✅ | ❌ **RLS violation** |
| …plus a `select` policy `using (true)` | 🔴 **everything** | ✅ works |

⭐⭐ **`ON CONFLICT` — `DO UPDATE` *and* `DO NOTHING` — requires a permissive SELECT policy, because it has to
read the conflicting row.** So the read exposure and the app's write are **coupled**: there is no combination
of grants and policies that keeps one and removes the other.

⚠️ **Had this gone to production as drafted, the waitlist would have silently stopped recording people.** The
write is fail-silent (`except Exception: return`), so nobody would have seen an error — the table would just
have stopped growing, and it would have looked like nobody was being refused.

#### The fix: make it a plain INSERT

`waitlist.py` sends `Prefer: resolution=merge-duplicates`, which is what makes it an upsert. Remove that
header and it becomes a plain INSERT, which needs **only** the INSERT privilege.

Verified against the live staging project:

| request | status |
|---|---|
| duplicate email, **no** `Prefer` header | **409** — and `requests.post` does not raise on an HTTP error, so the app never even sees it |
| duplicate email, with `merge-duplicates` | 200 |

**What it costs:** a repeat refusal no longer updates `reason` (`not_listed` → `full`). The row still exists
and the person is still on the waitlist; only the *most recent* reason is lost. ⭐ *The upsert's whole job was
to avoid an error the app already ignores.*

```sql
-- A1 — beta_waitlist: emails go in, nothing comes out.
-- ⚠️ Apply the one-line change in waitlist.py FIRST (drop the Prefer header), or repeat sign-ins will 409
--    and — because the write is fail-silent — stop being recorded without saying so.
revoke all on public.beta_waitlist from anon, authenticated;
grant insert on public.beta_waitlist to anon;

alter table public.beta_waitlist enable row level security;

drop policy if exists "waitlist insert"        on public.beta_waitlist;
drop policy if exists "waitlist upsert-update" on public.beta_waitlist;   -- from the superseded draft

create policy "waitlist insert" on public.beta_waitlist
  for insert to anon with check (true);
```

**Verified as anon after applying:** `select` → *permission denied*; `delete` → *permission denied*;
`insert` of a new email → succeeds; `insert` of a duplicate → unique violation, swallowed.

#### ✅ Verified on staging — 2026-09-19

**The probe, before and after** (`scripts/supabase_probe.sh`, anon key):

| probe | before | after | |
|---|---|---|---|
| `beta_users` | 3 emails, 200 | 3 emails, 200 | unchanged ✅ |
| **`beta_waitlist`** | **2 emails + reasons, 200** | **HTTP 401, permission denied** | **the win** ✅ |
| `squads` | handles listed, 200 | handles listed, 200 | unchanged ✅ |
| `maddie_videos` | `[]`, 200 | `[]`, 200 | unchanged ✅ |

⭐ **One probe changed and three did not**, which is the shape that matters: a change everywhere would have
meant the app broke, and a change nowhere would have meant the fix never landed.

**The write, end to end:** `201` for a new address · `409` for a repeat · `401` reading it back. Write-only,
as designed — the app can record a refusal and then cannot read it, or anyone else's, back.

⚠️ **And the fail-silent path was tested by hand, through the real gate**, because it is the one that cannot
report its own failure. With the registration gate on (`./scripts/run_app_staging.sh --gate`), both
no-auth paths that call `waitlist.add()`:

| path | message shown | row written |
|---|---|---|
| wrong invite code → `bad_code` | ✅ *"That invite code isn't right"* | ✅ |
| at the cap → `full` | ✅ *"The beta is full right now (3 testers)"* | ✅ |

⭐ **"Message shown" and "row written" are two separate observations on purpose.** The failure this guards
against shows the message and writes nothing — a gate that looks perfectly healthy while recording nobody,
discovered weeks later by an empty waitlist. Checking only the message would have passed.

*(The third path, `not_listed` via Google sign-in, is the same `waitlist.add()` call and the same table; only
its trigger differs. It needs OIDC credentials with a `localhost` redirect to exercise locally.)*

### A2. `maddie_videos` — read-only, confirm no write path

Public marketing content, no personal data. Public read is correct; it should not be writable.

```sql
revoke all on public.maddie_videos from anon, authenticated;
grant select on public.maddie_videos to anon;

alter table public.maddie_videos enable row level security;
drop policy if exists "maddie_videos public read" on public.maddie_videos;
create policy "maddie_videos public read" on public.maddie_videos
  for select to anon using (true);
```

### A3. `events` — insert-only ⚠️ *one decision needed*

Analytics rows are anonymous by design (ADR-100: random `session_id` / `anon_id`, no PII), so the exposure is
low. But the **Admin page reads them with the same anon key** (`analytics.recent_events`), so locking this
costs you that panel unless it gets a privileged key.

```sql
revoke all on public.events from anon, authenticated;
grant insert on public.events to anon;

alter table public.events enable row level security;
drop policy if exists "events insert" on public.events;
create policy "events insert" on public.events
  for insert to anon with check (true);
```

**Choose one:**
- **(a)** apply it, and read usage in the Supabase dashboard (Admin's usage panel goes dark), or
- **(b)** apply it *and* give Admin a separate `FPL_ADMIN_KEY` (service role) — a small code change, and the
  right shape long-term, or
- **(c)** defer to Stage B. 💡 **My recommendation: (c)** — the data is anonymous, so this is tidiness, and
  spending a code change here before the tables holding real emails is the wrong order.

---

### ✅ Stage B verified on staging — 2026-09-19

| check | before | after |
|---|---|---|
| `beta_users` direct read | 200, **3 addresses** | **HTTP 401** |
| `beta_waitlist` direct read | 200, 2 addresses | **HTTP 401** |
| `is_allow_listed` — wrong case, stray spaces | *(fetched the whole list)* | `true` |
| `is_allow_listed` — not listed | — | `false` |
| `touch_last_seen` | read-the-list-then-PATCH | `true` / `false` |
| **"Remove me" on the waitlist** | 🔴 **`refused (HTTP 401)`** | ✅ **`deleted`** |
| registration | — | `in` · `in` (idempotent) · `full` (at cap) |
| `squads`, `maddie_videos` | 200 | 200 — **unchanged** |

⭐ **Both email tables are now closed** and the gate still works — it asks a question instead of downloading
the answer. And ADR-122's promise is back, an hour after Stage A quietly removed it.

**The Admin roster, with `FPL_ADMIN_STORE_KEY` set:** `all_emails()` → 3 addresses; `last_seen_by_email()` →
1 stamp, the one written by the `touch_last_seen` RPC minutes earlier. ⭐ *That single stamp proves the whole
chain — the anon RPC wrote it and the service key read it back.*

⚠️ **With the key unset it returns `[]`, not a crash and not a fallback.** A silent fall back to the anon key
would 401 anyway, but it would read as *"the roster is broken"* rather than *"the key is missing"* — and the
second is the one you can act on.

---

## 🔴 What Stage A **cannot** fix, and why

`squads`, `beta_users`, `user_prefs` and `player_watchlist` **cannot be secured by policy alone**, because
there is no identity to scope a policy to. `using (auth.uid() = owner)` requires Supabase Auth to have issued
that `uid`; the current key is a `sha256(email)` minted by Streamlit's OIDC session, which means nothing to
Postgres.

⚠️ And RLS cannot express *"only if you asked by exact key"*. A policy is evaluated per row, so an unfiltered
`select` with a permissive policy returns **every** row. **Enumeration is not a policy problem.**

⭐ **The Postgres answer is to stop exposing the tables at all and expose narrow functions instead** — a
`security definer` function that takes the key as an argument and can only ever return that one row. This
works **today, without auth**, and it is Stage B.

---

## Stage B — narrow functions, then revoke the tables

Needs a matching change in `src/web_streamlit/` (PostgREST table calls → `rpc/` calls). Roughly half a day.
Two representative functions; the rest follow the identical pattern.

### ✅ B1–B4 — built 2026-09-19, SQL in [`sql/stage_b.sql`](../sql/stage_b.sql)

⭐ **One definition, loaded by both this runbook and the tests.** `tests/test_stage_b_sql.py` runs that exact
file against a real Postgres, because the behaviour left Python and a mock would only test itself.

| function | who calls it | replaces |
|---|---|---|
| `is_allow_listed(email) → bool` | every gate check | **reading the whole allow-list** to match case-insensitively in Python |
| `register_beta_user(email, cap) → text` | the registration gate | check + count + insert, three round trips |
| `touch_last_seen(email) → bool` | every admit | read-the-list-then-PATCH, two round trips |
| `forget_me(email, user_key) → jsonb` | a tester leaving | five separate DELETEs |

**Then** `revoke all on public.beta_users from anon, authenticated`.

#### ⚠️⚠️ Two things this stage found the hard way

**1. "One function" is not the same as "atomic."** `register_beta_user` was written to close the race the old
code conceded in its own docstring. The first version moved check-count-insert into a function and **the cap
still broke** — four concurrent calls against a cap of 5 admitted **6**, because `select count(*)` takes no
lock. It now takes `share row exclusive` first, and the same test admits exactly 5. ⭐ *Measured, twice,
rather than reasoned about.*

**2. 🔴 Stage A had already broken "Remove me", and nothing said so.** Revoking DELETE on `beta_waitlist`
turned ADR-122's promise into `refused (HTTP 401)` — and because the UI ignores that result by design, it
surfaced nowhere. Found only by running `remove_me` against staging **after** the hardening; the original
rehearsal checked that the waitlist *write* still worked and stopped there.

⭐ **A permission you remove is a promise you may have removed with it.** The fix is not to hand DELETE back —
it is `forget_me`, which performs the one deletion a person is entitled to and **reports a row count per
table**, which is strictly better than the old DELETE's inability to tell *"no such row"* from *"no policy"*.

#### The owner's reads need a different credential, not a function

`all_emails()`, `last_seen_by_email()` and `recent_events()` are owner-only **by intent** and were anon **by
credential** — the Admin page is gated by a password, so the page was protected and the data path was not.
No narrow function helps here: *"every address"* **is** the question.

They now use **`FPL_ADMIN_STORE_KEY`**, a service-role key. ⚠️ It bypasses RLS completely, and is safe here
for one specific reason — **Streamlit renders server-side, so it never leaves the machine**. ⭐ *That reason
does not transfer*: it must never be compiled into a mobile client. Unset, the roster degrades to empty
rather than falling back to the anon key, because a silent fallback would look like it worked right up until
the revoke.

### B4. Then, and only then, close the tables

```sql
-- After every call site is on rpc/ and verified against a staging project.
revoke all on public.squads, public.beta_users, public.user_prefs, public.player_watchlist
  from anon, authenticated;
```

---

## ⚠️ What this does and does not achieve

**Stage B stops:** enumeration (dumping every squad or every tester email), mass deletion, and arbitrary
overwrites of rows you have not identified. That is the difference between *"one request takes the whole
table"* and *"one guess gets one row."*

**Stage B does not stop:** someone who **knows a key** reading that row. That is unchanged from ADR-094's
original design, and it splits in two:

- a `sha256(email)` key is **not guessable** — those users are effectively protected
- a **user-chosen handle** from the no-login path (`"TS"`, `"RoboTS"`) **is** guessable, and always was

⭐ **Only Stage C fixes the second case**, by replacing "knowing the key" with "being the user".

---

## ✅ LIVE ON PRODUCTION — 2026-09-20

Stages A and B applied to the production project (`msdjmztujzonzgjjfbky`) and verified with the anon key:

| probe | before | after |
|---|---|---|
| `beta_users` — the allow-list | 200, all 29 addresses | **401 · `42501` permission denied** |
| `beta_waitlist` — refused sign-ins | 200, addresses + reasons | **401 · `42501` permission denied** |
| `squads` | 200 | 200 — unchanged (B3 not built) |
| `maddie_videos` | 200 | 200 — unchanged, correctly public |

⚠️ **`42501` is the detail that makes this a result rather than a guess.** It is Postgres's *insufficient
privilege* code. A **rejected key** also returns 401 — with `{"message":"Invalid API key"}` — and four of
those reads as total success at a glance. It happened on the first attempt here, and the canary is
`maddie_videos`: it is supposed to stay **200**, so four 401s means the key, not the lock.
⭐ *A check that cannot distinguish two outcomes is not a check* — the probe now refuses to report a rejected
key as a result at all.

Sign-in admits normally; the Admin roster renders via `FPL_ADMIN_STORE_KEY`.
**Neither table holding an email address can be read with the anon key any more.**

### What it cost to get here, recorded because the lessons are the value

* ⭐ **"No code change" was wrong.** `ON CONFLICT` — `DO UPDATE` *and* `DO NOTHING` — needs a permissive
  SELECT policy, so the upsert and the locked read are mutually exclusive. A1 needed a one-line code change.
* ⭐ **"One function" is not "atomic".** `register_beta_user` moved check-count-insert into a function and the
  cap still broke: four concurrent calls against a cap of 5 admitted **6**. It needs an explicit table lock.
* ⭐ **A permission you remove is a promise you may have removed with it.** Stage A silently broke ADR-122's
  "Remove me"; found only by running it *after* the hardening.
* ⭐⭐ **`git log` tells you what is on master, not what Cloud is serving.** Assumed twice in one evening —
  once raising a false alarm, once causing a real outage. The deploy check is behavioural now.
* ⭐⭐ **And this section was first committed while the verification had not run.** The probe command used
  `read -p`, which is bash; the owner's shell is zsh, so it errored and the check never executed — and the
  expected result was recorded as though it were the measured one. ⚠️ *The same failure as the two above, in
  the document whose whole purpose is recording what was actually checked.* The numbers here are now from a
  real run; the instruction that failed silently in one shell has been moved inside the script, where it
  works in both.

📋 **Follow-up, not urgent:** `beta_users` holds **29 rows for 26 distinct addresses** — about three differ
only by capitalisation or whitespace (the ADR-120 problem). Harmless for admission now that matching is
`lower(trim())` in SQL, but `register_beta_user` counts **rows**, so those duplicates consume cap places.

---

## Stage C — real identity (Phase 3, with the mobile API)

Supabase Auth issues a `uid`; every user-data table gains an `owner uuid references auth.users`; policies
become the real thing:

```sql
create policy "own squad only" on public.squads
  for all to authenticated
  using (owner = (select auth.uid())) with check (owner = (select auth.uid()));
```

⚠️ **This is a risked migration of a live system** and is deliberately *not* drafted here: the existing
`sha256(email)` keys must be mapped to new `auth.uid()`s without stranding anyone's saved squad, and the
Streamlit `st.login()` path has to keep working throughout. It needs its own ADR, a mapping table and a
dual-run period — which is why the audit puts it in Phase 3 rather than now.

---

## Recommended order

> 🔴 **Superseded in one respect (2026-09-19): Stage A can no longer ship alone.** Revoking `DELETE` on
> `beta_waitlist` breaks ADR-122's "Remove me", silently, and the fix (`forget_me`) lives in Stage B. The
> order below still reflects *risk*; it no longer reflects *shippable units*.


| | action | risk | code change | do it |
|---|---|---|---|---|
| **1** | **A1 — `beta_waitlist`** | none (never read) | ⚠️ **1 line** — drop the `Prefer` header in `waitlist.py`; see A1 | ✅ **today** |
| **2** | **A2 — `maddie_videos`** | none | none | ✅ today |
| **3** | Rotate `FPL_STORE_KEY` | low | 1 secret | ✅ after A1/A2 |
| **4** | **B1/B2 — `beta_users` via RPC** | low, testable | ~1 file | 🔜 next sprint |
| **5** | B3 — squads/prefs/watchlist via RPC | med | ~4 files | 🔜 with 4 |
| **6** | A3 — `events` | low | Admin key | ⏸ with 5 |
| **7** | **C — Supabase Auth + owner RLS** | 🔴 **high** | large | ⏸ **Phase 3, own ADR** |

⭐ **Steps 1–3 are an evening and remove the raw-email exposure entirely.** Everything after that is the
mobile programme, and can move at its own pace.

### Before applying anything

1. **Test on a branch/staging Supabase project**, not production. Supabase free tier allows a second project.
2. **Take a backup** — `pg_dump`, or the dashboard's backup, before the first `revoke`.
3. ⚠️ **Verify the live app after each step**: sign in, save a squad, load it on another device, and check
   a refused email still lands on the waitlist. The waitlist write is **fail-silent**, so it will not tell
   you it has broken — ⭐ *the one path that cannot report its own failure is the one to test by hand.*
