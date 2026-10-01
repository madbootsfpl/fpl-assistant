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
