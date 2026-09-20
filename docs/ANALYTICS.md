# Beta usage & experience analytics — owner setup (~5 min, £0)

See **what testers use, whether they return, and whether the app feels fast/reliable** — anonymously, in your own
Supabase, with **no third-party analytics** and **no way to affect the app**. Background:
[ADR-100](06_Decisions/ADR-100-beta-usage-analytics.md).

> **Reuses the Supabase project** that already powers cross-device squads (ADR-094) + the registration gate
> (ADR-098) — a third `events` table on the same `FPL_STORE_URL`/`FPL_STORE_KEY`. **No new secret.**

**Off by default:** until you set **`FPL_ANALYTICS`** *and* the store is configured, the app writes **zero** events
(no thread, no network). And when it *is* on, every event is **fire-and-forget** and **fail-silent** — a Supabase
outage, a slow network, or a bad row can **never** slow or break a tester's session (a lost event is fine; a broken
FPL experience is not).

---

## 1. Create the `events` table (Supabase)

Run [`sql/setup.sql`](../sql/setup.sql) in the **SQL Editor** — it creates `events` along with everything
else, in its hardened form, and is safe to re-run.

| column | what it holds |
|---|---|
| `ts` | set by the database, not the client |
| `session_id` | a random per-session id — **anonymous** |
| `anon_id` | a random returning-device id (the `fpl_anon` cookie) — **anonymous** |
| `version` | app version (`config.APP_VERSION`) |
| `event` | `session_started` · `page_viewed` · `analysis_run` · `squad_saved` · … · `error` · `perf` |
| `page`, `duration_ms`, `ok` | context; `duration_ms` is for `perf` events |
| `meta` | small structured context only, e.g. `{"view":"Health","n":15}` |

**Insert-only for the app.** Testers' browsers add events and can never read them back.

🔴 **This page used to add a read policy too**, so the in-app Admin view could use the publishable key. That
justification was wrong in a way worth naming: it argued the key is safe because *"it lives in Streamlit
secrets and is never sent to a browser"* — true of the **key**, but the policy it created applies to
**anyone holding that key**, wherever they got it. ⭐ *A permission is granted to a role, not to the place you
happen to keep the credential.*

**The Admin view now reads with the service-role key** (`FPL_ADMIN_STORE_KEY`) instead, which bypasses RLS
entirely. ⚠️ That is safe **only** because Streamlit renders server-side — it must never be compiled into a
mobile client.

## 2. Turn it on (Streamlit secrets)

The store secrets are already set (for squads). Add the one flag:
```toml
FPL_ANALYTICS = "1"                # "1"/"true"/"yes"/"on" turns analytics on; unset (or anything else) = fully off
FPL_ADMIN_KEY = "a-long-password"  # unlocks the in-app Admin tab for you only; unset → the tab is inert
```
Reboot the app. Unset `FPL_ANALYTICS` any time → analytics is completely off again. Unset `FPL_ADMIN_KEY` → the
**Admin** tab shows a "not configured" note (testers can't read the numbers).

## 3. What's collected (and what isn't)

**Anonymous + minimal.** Two random ids (a per-session id + a returning-device id) and small event rows —
**no names, emails, IPs, or the squad handle; no full squad data; no click/mouse/screen tracking; no third-party
service.** `meta` holds only small structured context. The returning id lives in an anonymous first-party cookie
(`fpl_anon`) — clear cookies / a private tab and it's a fresh, still-anonymous id.

**Events:** `session_started`, `page_viewed`, `error`, `perf` (from this sprint) — plus `squad_created`,
`analysis_run`, `player_viewed`, `squad_saved`, `squad_loaded`, `feedback_opened`, `feedback_submitted` as
instrumentation grows (Sprint 137).

## 4. Inspect it — the Admin tab (US-337)

Open the **📊 Admin** tab (bottom of the sidebar) → enter your **`FPL_ADMIN_KEY`** → a read-only dashboard:
**Events · Sessions · Devices · Returning** metrics, **most-viewed pages**, **event counts**, a **success rate**,
and **median / P95** duration per timed op (`data_load` · `analysis` · `squad_save` · `squad_load`). It reads the
last ~2000 events (via the anon key + the SELECT policy above) and aggregates **in the app** — best-effort, so a
store hiccup shows a note, never a crash. Unset the key → the tab is inert; a wrong key → locked.

## 4b. Inspect it (raw SQL)

Or run these directly in the Supabase SQL editor:
```sql
-- Unique returning devices, and sessions, in the last 7 days
select count(distinct anon_id) as devices, count(distinct session_id) as sessions
from events where ts > now() - interval '7 days';

-- Most-used pages / features
select event, page, count(*) from events group by 1, 2 order by 3 desc;

-- Returning users (a device seen on 2+ distinct days)
select count(*) from (
  select anon_id from events where anon_id is not null
  group by anon_id having count(distinct date(ts)) >= 2
) t;

-- Success vs failure by operation
select event, ok, count(*) from events group by 1, 2 order by 1, 2;

-- Performance: median + P95 duration per timed op (perf events)
select meta->>'op' as op,
       percentile_cont(0.5)  within group (order by duration_ms) as p50_ms,
       percentile_cont(0.95) within group (order by duration_ms) as p95_ms,
       count(*)
from events where event = 'perf' group by 1 order by p95_ms desc nulls last;
```

---

## How it fails safe

Every event is built on the main thread (so anonymous ids are read safely) then **POSTed fire-and-forget on a
daemon thread** with a tight timeout, the whole post wrapped so **no error can reach the app**. When analytics is
off it's a hard no-op (no thread, no request). A guardrail test pins both: **no secrets → zero writes** (the suite
is byte-identical), and **a raising store never breaks a page**.

## Turn it off

Delete `FPL_ANALYTICS` (or set it to anything non-truthy) → analytics is fully off; existing rows stay in Supabase
until you delete them / the table.

## Later (deferred)

Sprint 137 added the feature events (`squad_*`, `analysis_run`, `feedback_submitted`), `error`, perf timers, and
the gated Admin view. Still deferred until there's meaningful beta data: a full **BI dashboard**, event
**batching** (if volume grows), and **cohort/funnel** analysis. (`player_viewed` was intentionally skipped as
low-value/chatty.)
