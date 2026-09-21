-- ═══ Read-only. Today, by the hour — did the cache actually land? ═══
--
-- ⚠️ `page_timings.sql` buckets by day, which was right while the question was "did the Postgres cutover
-- cost us anything" and is too coarse now: the caching deploy landed mid-afternoon, so a single day's p50
-- averages the before and the after into a number that describes neither.
--
-- ⭐ *A bucket wider than the change you are looking for hides it.*
--
-- Expect a step: `data_load` p50 in the seconds before the deploy, and near-zero after, with the occasional
-- slow sample surviving as the **cold** load that refills the cache once every five minutes.

select
  to_char(date_trunc('hour', ts), 'YYYY-MM-DD HH24:00')            as hour,
  page,
  count(*)                                                          as samples,
  round(percentile_cont(0.50) within group (order by duration_ms))  as p50_ms,
  round(percentile_cont(0.90) within group (order by duration_ms))  as p90_ms,
  round(min(duration_ms))                                           as fastest_ms,
  round(max(duration_ms))                                           as worst_ms
from public.events
where event = 'perf'
  and (meta ->> 'op') = 'data_load'
  and duration_ms is not null
  and ts > now() - interval '36 hours'
group by 1, 2
order by 1 desc, 2;
