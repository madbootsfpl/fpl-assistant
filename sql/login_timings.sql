-- ═══ Read-only. Where do the eleven seconds actually go? ═══
--
-- ⚠️ **`data_load` says 23 ms and the owner says eleven seconds, so something outside it is the cost.**
-- `analytics.timed("data_load")` wraps the board load and nothing else — the sign-in, the allow-list check
-- and the squad restore each make their own HTTPS round trip to PostgREST and none was ever counted.
--
-- ⭐ *You optimise what you measure.* Two fixes so far have improved the instrumented part while the
-- complaint stayed the same, which is the signal that the instrument is pointed at the wrong thing.
--
-- Each leg is now timed separately, so this names the slow one rather than the total:
--   login_gate_check     is this email on the allow-list?      (one RPC)
--   login_touch          stamp last_seen                       (one RPC)
--   login_restore_squad  fetch and restore the saved squad     (one RPC, plus prefs and watchlist)
--   data_load            the board                             (cached since 2026-09-21)

select
  (meta ->> 'op')                                                   as leg,
  count(*)                                                          as samples,
  round(percentile_cont(0.50) within group (order by duration_ms))  as p50_ms,
  round(percentile_cont(0.90) within group (order by duration_ms))  as p90_ms,
  round(max(duration_ms))                                           as worst_ms
from public.events
where event = 'perf'
  and duration_ms is not null
  and ts > now() - interval '6 hours'
group by 1
order by p50_ms desc nulls last;
