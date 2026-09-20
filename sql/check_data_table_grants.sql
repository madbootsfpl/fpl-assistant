-- ═══ Read-only. What can the publishable key do to the pipeline's tables? ═══
--
-- ADR-212 hardened the seven tables holding user data. The FPL **data** tables were never in its scope —
-- and they are created by the pipeline with a plain `CREATE TABLE`, so they inherit whatever the project's
-- default privileges are. On a stock Supabase project that default is:
--
--     alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
--
-- ⭐ Reproduced locally and confirmed: every table the pipeline creates comes out with DELETE, INSERT,
-- TRUNCATE and UPDATE granted to `anon`. This query says whether that is true HERE.
--
-- ⚠️ It changes nothing. Run it and read the answer.

select
  table_name,
  string_agg(distinct privilege_type, ', ' order by privilege_type) as anon_can,
  case
    when bool_or(privilege_type in ('INSERT','UPDATE','DELETE','TRUNCATE'))
      then '🔴 WRITABLE by the publishable key'
    when bool_or(privilege_type = 'SELECT') then '🟡 readable only'
    else '✅ closed'
  end as verdict
from information_schema.role_table_grants
where grantee = 'anon'
  and table_schema = 'public'
group by table_name
order by 3, 1;
