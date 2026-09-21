-- ═══ Read-only. The last 25 perf samples, individually, with their timestamps. ═══
--
-- ⚠️ **A percentile over a window that spans a deploy describes neither side of it.** `data_load` p90 has
-- read ~10,800 ms across three consecutive readings with a *worst* of 10,863 each time — the same sample,
-- surviving in a six-hour window while the p50 fell from 3,026 ms to 20 ms around it.
--
-- ⭐ *When a summary stops moving while the thing it summarises does, stop summarising and look at the rows.*

select
  to_char(ts, 'HH24:MI:SS')      as at,
  (meta ->> 'op')                as leg,
  page,
  duration_ms
from public.events
where event = 'perf'
  and duration_ms is not null
order by ts desc
limit 25;
