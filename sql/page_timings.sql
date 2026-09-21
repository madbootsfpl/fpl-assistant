-- ═══ Read-only. What the app has been recording about its own speed ═══
--
-- ⭐⭐ **ADR-211 asked to "compare page timings against the seed", and the data already exists.**
-- `analytics.timed("data_load")` has been writing a `perf` event on My Squad and Players since US-336 — from
-- before the Postgres cutover and after it. This is a measurement taken **in the real environment**, which is
-- the one thing a local benchmark cannot be: latency from Streamlit Cloud to Supabase is not latency from a
-- laptop, and assuming otherwise is how a confident wrong answer gets made.
--
-- ⚠️ No date is hard-coded. The cutover shows up as a step in the numbers, which is more reliable than me
-- remembering when it happened.

select
  date_trunc('day', ts)::date                                        as day,
  (meta ->> 'op')                                                    as op,
  page,
  count(*)                                                           as samples,
  round(percentile_cont(0.50) within group (order by duration_ms))    as p50_ms,
  round(percentile_cont(0.90) within group (order by duration_ms))    as p90_ms,
  round(max(duration_ms))                                            as worst_ms
from public.events
where event = 'perf'
  and duration_ms is not null
  and ts > now() - interval '45 days'
group by 1, 2, 3
having count(*) >= 3          -- a percentile over two samples is not a percentile
order by 1 desc, 3, 2;
