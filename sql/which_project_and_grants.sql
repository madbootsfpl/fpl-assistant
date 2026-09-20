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
       -- ⭐ **The verdict has to know what each table is FOR.** A first version called anything with INSERT
       -- "WRITABLE", which flagged `beta_waitlist` and `events` — two tables whose entire design is
       -- insert-only (emails and analytics go in, nothing comes out). ⚠️ A check that fires on its own
       -- intended state is the anti-pattern ADR-178 is about: it gets ignored, and then it is ignored on the
       -- day it is right.
       case
         when bool_or(g.privilege_type in ('UPDATE','DELETE','TRUNCATE'))
           then '🔴 WRITABLE — the key can change or destroy rows'
         when t.table_name in ('beta_waitlist', 'events')
              and bool_or(g.privilege_type = 'INSERT')
              and not bool_or(g.privilege_type = 'SELECT')
           then '✅ insert-only, as designed'
         when t.table_name in ('beta_waitlist', 'events') and bool_or(g.privilege_type = 'SELECT')
           then '🟠 insert-only table is also READABLE — the read is not needed'
         when bool_or(g.privilege_type = 'INSERT') then '🔴 unexpectedly insertable'
         when bool_or(g.privilege_type = 'SELECT') then '🟡 readable only'
         else '✅ closed to the publishable key'
       end
from information_schema.tables t
left join information_schema.role_table_grants g
       on g.table_name = t.table_name and g.table_schema = t.table_schema and g.grantee = 'anon'
where t.table_schema = 'public' and t.table_type = 'BASE TABLE'
group by t.table_name
order by 1;
