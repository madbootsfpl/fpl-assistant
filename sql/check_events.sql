-- ═══ Read-only, one row. Exactly what can the publishable key do to `events`? ═══
-- `events` should accept INSERT and nothing else: anonymous analytics go in, and you read them with the
-- service-role key. Anything more is left over from the cutover, where events was explicitly deferred.

select
  coalesce(string_agg(distinct privilege_type, ', ' order by privilege_type), '(nothing)') as anon_can,
  case
    when bool_or(privilege_type in ('UPDATE','DELETE','TRUNCATE'))
      then '🔴 the key can CHANGE or DESTROY analytics rows — fix this'
    when bool_or(privilege_type = 'SELECT')
      then '🟠 readable — not needed since the Admin view uses the service key'
    when bool_or(privilege_type = 'INSERT') then '✅ insert-only, as designed'
    else '⚠️ cannot insert at all — analytics would be silently dropped'
  end as verdict
from information_schema.role_table_grants
where grantee = 'anon' and table_schema = 'public' and table_name = 'events';
