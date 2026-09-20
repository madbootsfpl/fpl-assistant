-- ═══ The pipeline's tables: readable by everyone, writable by nobody ═══
--
-- ⭐⭐ **ADR-212 closed the tables that existed. This closes the door they keep arriving through.**
-- The seven web tables were hardened by hand. The FPL **data** tables are created by the pipeline with a
-- plain `CREATE TABLE`, so they inherit the project's default privileges — and on a stock Supabase project
-- that default is `grant all on tables to anon`. Reproduced locally: every table the pipeline creates comes
-- out with **DELETE, INSERT, TRUNCATE and UPDATE** granted to the publishable key.
--
-- ⚠️ **The data is public — this is not a confidentiality problem.** Anyone can pull the same numbers from
-- the FPL API. What it allows is **vandalism**: one `truncate players` with a key that ships in a mobile
-- binary takes the app down for every tester. That is an availability risk and it is worth closing.
--
-- **Safe to run while the pipeline is live.** The pipeline connects as the database owner, not as `anon`,
-- so nothing here touches it. Verified by running a real pipeline tick after applying this file.

-- ── 1. The part that actually matters: future tables arrive CLOSED ────────────────────────────────────────
-- ⭐ Without this, the next table anyone adds repeats the whole problem, and nothing says so. Failing closed
-- is the right direction: a new table the mobile client cannot read is a visible bug, where a new table the
-- world can delete is an invisible one.
alter default privileges in schema public revoke all on tables from anon, authenticated;

-- ── 2. The pipeline's tables: SELECT only ────────────────────────────────────────────────────────────────
-- Board-wide public football data. Mobile reads these directly (audit §4.1), so they must stay readable —
-- and there is no caller anywhere that writes them with the publishable key.
do $$
declare t text;
begin
  foreach t in array array[
    'players', 'teams', 'fixtures', 'player_history', 'player_history_past',
    'headline_events', 'player_availability', 'player_transfer_flow', 'data_status',
    'xp_board', 'team_dna_board'
  ] loop
    if to_regclass('public.' || t) is not null then
      execute format('revoke all on public.%I from anon, authenticated', t);
      execute format('grant select on public.%I to anon, authenticated', t);
    end if;
  end loop;
end $$;
