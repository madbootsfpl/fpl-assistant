-- ═══ Read-only. Which project am I looking at, and exactly what can `anon` do? ═══
-- Changes nothing. The first row identifies the project so there is no doubt which one this is.

select 'THIS PROJECT' as table_name,
       current_setting('request.jwt.claims', true) as anon_can,
       coalesce(current_database(), '?') || '  ·  host says: ' ||
       coalesce((select setting from pg_settings where name = 'cluster_name'), 'unknown') as verdict
union all
select '— tables below —', '', ''
union all
select t.table_name,
       coalesce(string_agg(distinct g.privilege_type, ', ' order by g.privilege_type), '(nothing)'),
       case
         when bool_or(g.privilege_type in ('INSERT','UPDATE','DELETE','TRUNCATE'))
           then '🔴 WRITABLE by the publishable key'
         when bool_or(g.privilege_type = 'SELECT') then '🟡 readable only'
         else '✅ closed to the publishable key'
       end
from information_schema.tables t
left join information_schema.role_table_grants g
       on g.table_name = t.table_name and g.table_schema = t.table_schema and g.grantee = 'anon'
where t.table_schema = 'public' and t.table_type = 'BASE TABLE'
group by t.table_name
order by 1;
