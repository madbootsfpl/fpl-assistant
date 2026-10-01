-- ═══ Read-only. What testers actually USE — by feature, by surface ═══
--
-- ⭐⭐ **Written because the question "which parts of MadBoots create value?" turned out to be already
-- recorded.** Both apps have been writing to `public.events` all along: Streamlit writes
-- `event='page_viewed'` with a page name, the API writes `event='api'` with an endpoint path and a
-- platform. One table, two vocabularies.
--
-- ⚠️⚠️ **This exists because the admin panel cannot answer it.** `admin.summarise()` builds its page
-- breakdown from `event = 'page_viewed'` only (`src/service/http/admin.py:287`), and the phone writes
-- `event = 'api'`. ⭐ *Every Flutter feature-usage row is in the table and in no view* — so the panel has
-- been showing Streamlit pages and nothing else, which reads as "the phone is not being used".
--
-- Run these in the Supabase SQL editor, in order. Nothing here writes.
--
-- 🔴🔴 **READ THIS BEFORE COMPARING THE TWO SURFACES.**
--
-- `anon_id` means something different on each side, and treating it as one thing will produce a
-- confident wrong answer about which app people prefer:
--
--   * **API rows** — a random install id, minted once per app install and kept. Stable.
--   * **Streamlit rows** — the `fpl_anon` returning-device cookie, which the Feedback Log records as
--     **over-minting in production** (a sample read Sessions 40 = Devices 40, Returning 0 — exact
--     equality means every visit minted a fresh id).
--
-- ⭐ So a distinct-`anon_id` count **overstates Streamlit's reach and not Flutter's**. Compare *events*
-- between surfaces, and compare *people* only within one. ⚠️ Neither id is a person in any case — one tester
-- with a phone and a laptop is two ids, and nine testers can look like fifteen.


-- ── 1. Coverage: is there enough data to decide anything? ─────────────────────────────────────────────
-- ⭐ First question, because every number below is worthless if the history is a week long. Run this
-- before reading anything else.

select
  case when event = 'api' then 'phone/web app (Flutter)' else 'web app (Streamlit)' end as surface,
  min(ts)::date                                     as first_seen,
  max(ts)::date                                     as last_seen,
  count(*)                                          as events,
  count(distinct date_trunc('day', ts))             as active_days
from public.events
where event in ('api', 'page_viewed')
  and page not in ('/api/v1/health', '/health')   -- ⚠️ a probe would say "plenty of data" (ADR-306)
group by 1
order by 1;


-- ── 2. What gets used — the main answer ───────────────────────────────────────────────────────────────
-- ⭐⭐ Ordered by **reach** (how many installs touched it), not by hits. One person hammering a page is
-- not a feature nine people want, and a raw count cannot tell those apart.

select
  case when event = 'api' then 'Flutter' else 'Streamlit' end       as surface,
  page                                                              as feature,
  count(distinct anon_id)                                           as installs,
  count(*)                                                          as uses,
  round(count(*)::numeric / nullif(count(distinct anon_id), 0), 1)  as uses_per_install,
  round(100.0 * count(*) filter (where ok is false) / count(*), 1)  as pct_failed,
  max(ts)::date                                                     as last_used
from public.events
where event in ('api', 'page_viewed')
  and page is not null
  and page not in ('/api/v1/health', '/health')   -- a liveness probe is not usage (ADR-306)
  and ts > now() - interval '90 days'
group by 1, 2
order by 1, installs desc, uses desc;


-- ── 3. Which platform people are actually on ──────────────────────────────────────────────────────────
-- ⚠️ Counts EVENTS, not people — see the warning at the top. This is the comparison that is safe to make
-- across surfaces.

select
  coalesce(meta ->> 'platform', 'streamlit')  as platform,
  count(*)                                    as events,
  count(distinct anon_id)                     as ids,          -- ⚠️ not people — see the header
  min(ts)::date                               as first_seen,
  max(ts)::date                               as last_seen
from public.events
where event in ('api', 'page_viewed')
  and page not in ('/api/v1/health', '/health')
  and ts > now() - interval '90 days'
group by 1
order by events desc;


-- ── 4. Do they come back? ─────────────────────────────────────────────────────────────────────────────
-- ⭐ The question behind "would anyone pay": not whether they tried it, but whether they returned.
-- 🔴 **Flutter rows only.** The Streamlit id over-mints (header), so a return rate computed over it would
-- read as near-zero no matter how loyal the user is — ⚠️ *that is a broken counter, not a finding.*

select
  days_active,
  count(*)  as installs
from (
  select anon_id, count(distinct date_trunc('day', ts)) as days_active
  from public.events
  where event = 'api'
    and anon_id is not null
    and page not in ('/api/v1/health', '/health')
    and ts > now() - interval '90 days'
  group by anon_id
) per_install
group by 1
order by 1;


-- ── 5. What a session looks like — which features travel together ─────────────────────────────────────
-- ⭐ A feature nobody opens alone may still be load-bearing. This shows what an install uses in a day,
-- so a "low-traffic" screen that always accompanies a decision is not mistaken for a dead one.

select
  date_trunc('day', ts)::date                  as day,
  anon_id,
  count(distinct page)                         as distinct_features,
  string_agg(distinct page, ' · ' order by page) as features_used
from public.events
where event = 'api'
  and anon_id is not null
  and page not in ('/api/v1/health', '/health')
  and ts > now() - interval '30 days'
group by 1, 2
having count(distinct page) > 1
order by 1 desc, distinct_features desc
limit 100;


-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════
--  FOLLOW-UPS (2026-10-01) — written after the first run of this file against live data
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════
--
-- The first run found three endpoints returning real HTTP errors to testers: `squad/replacements` 19.0%,
-- `squad/signals` 14.7%, `squad/my-team` 5.2% — roughly 41 failed calls in front of nine people in eight
-- days, against 0.0% on every Streamlit page.
--
-- ⚠️⚠️ **THE ROWS YOU ARE READING TODAY CANNOT SAY *WHICH* ERROR, AND NEWER ONES CAN.**
--
-- `usage.record()` stored `ok` as a bare boolean — `ok=response.status_code < 400` — and threw the code
-- away, two lines below a log string that *formats the same code*. ⭐⭐ *The one field that would make a
-- 19% failure rate diagnosable was already in the function and discarded.* A 422 (impossible input), a
-- 429 (rate limited), a 502 (Reddit refused us) and a 500 (our bug) all read identically, and those four
-- need four different responses — one of which is "nothing, that is an upstream having a bad day".
--
-- ✅ **Fixed 2026-10-01 (ADR-343):** `meta ->> 'status'` now carries the HTTP code.
--
-- 🔴 **So there is a date in this data.** Rows written before that deploy have **no** `status` key — not
-- null, absent. ⚠️ *A query that filters on `status` silently drops every row from before the fix*, which
-- would make a long-standing failure look like it started the day the column did. Query 6 therefore still
-- keys on `ok` and reports `status` beside it, and query 8 says plainly how much of the window it covers.


-- ── 6. The failures: when, which build, and is it already fixed? ──────────────────────────────────────
-- ⭐ **Read the `version` column first.** If a page's failures stop at a build boundary, the bug shipped
-- fixed and these numbers are history being averaged into the present. If they run across every build,
-- it is live and nine people are still hitting it.

select
  page,
  version,
  date_trunc('day', ts)::date                                       as day,
  count(*)                                                          as calls,
  count(*) filter (where ok is false)                               as failed,
  round(100.0 * count(*) filter (where ok is false) / count(*), 1)  as pct_failed,
  count(distinct anon_id) filter (where ok is false)                as installs_hit,
  -- ⭐ Absent for rows older than ADR-343. A blank here means "before the fix", never "no error".
  string_agg(distinct meta ->> 'status', ', ') filter (where ok is false) as codes
from public.events
where event = 'api'
  and page not in ('/api/v1/health', '/health')
  and ts > now() - interval '90 days'
group by 1, 2, 3
having count(*) filter (where ok is false) > 0
order by page, version, day;


-- ── 6b. Is it everyone, or one tester with one odd squad? ─────────────────────────────────────────────
-- ⚠️ A failure rate averaged over installs hides the difference between *a broken endpoint* and *one
-- manager id that breaks it* — ⭐ and those need completely different fixes.

select
  page,
  count(distinct anon_id)                                              as installs_calling,
  count(distinct anon_id) filter (where ok is false)                   as installs_failing,
  count(*)                                                             as calls,
  count(*) filter (where ok is false)                                  as failed,
  round(100.0 * count(*) filter (where ok is false) / count(*), 1)     as pct_failed
from public.events
where event = 'api'
  and page not in ('/api/v1/health', '/health')
  and ts > now() - interval '90 days'
group by 1
having count(*) filter (where ok is false) > 0
order by pct_failed desc;


-- ── 7. Streamlit before and after the phone app (2026-09-24) ──────────────────────────────────────────
-- ⭐⭐ The decisive question for *"does Streamlit stay?"*. The totals in query 2 are cumulative since
-- 2026-08-09 and cannot answer it: a page with 827 uses and a `last_used` of 2026-09-23 is not a page in
-- use, it is a page that was.
--
-- ⚠️⚠️ **Per-day rates, not totals.** The two periods are different lengths, and comparing their sums
-- would say Streamlit collapsed no matter what happened. 🔴 And `installs` is NOT people on this side —
-- the `fpl_anon` cookie over-mints (see the header), so read the events column and treat the id column as
-- a shape, never a headcount.

with periods as (
  select
    page,
    case when ts < timestamptz '2026-09-24' then 'before the app' else 'after the app' end as period,
    count(*)                                        as events,
    count(distinct date_trunc('day', ts))           as active_days,
    count(distinct anon_id)                         as ids,
    max(ts)::date                                   as last_used
  from public.events
  where event = 'page_viewed'
    and page is not null
    and ts > now() - interval '120 days'
  group by 1, 2
)
select
  page,
  period,
  events,
  active_days,
  round(events::numeric / nullif(active_days, 0), 1)  as events_per_active_day,
  ids,
  last_used
from periods
order by page, period desc;


-- ── 8. Which error, now that the rows can say ─────────────────────────────────────────────────────────
-- ⭐ The query that was impossible before ADR-343 — and the one that decides what to do about a failing
-- endpoint, because the answer is different for every code:
--
--   4xx | **422** the caller sent something the server cannot accept — our bug or a stale client
--       | **429** the rate limit did its job — not a fault, unless honest use is hitting it
--   5xx | **500** ours, and the only one that is unambiguously a defect
--       | **502/503/504** an upstream refused or timed out (Reddit blocks datacentre IPs at times)
--
-- ⚠️⚠️ **Read `covered_pct` before reading anything else.** It is the share of failures in the window that
-- carry a code at all. Low means most of this window predates the fix, and the breakdown describes the
-- recent tail rather than the problem.

select
  page,
  coalesce(meta ->> 'status', '(before ADR-343)')                    as status,
  count(*)                                                           as failures,
  count(distinct anon_id)                                            as installs_hit,
  min(ts)::date                                                      as first_seen,
  max(ts)::date                                                      as last_seen,
  round(100.0 * count(*) filter (where meta ? 'status')
        / nullif(sum(count(*)) over (partition by page), 0), 1)      as covered_pct
from public.events
where event = 'api'
  and ok is false
  and page not in ('/api/v1/health', '/health')
  and ts > now() - interval '90 days'
group by 1, 2
order by page, failures desc;
