-- MadBoots — is the app still WRITING? Run this in the Supabase SQL Editor, any time.
--
-- ⭐ **Every failure mode this hardening can produce is silent.** The app catches its own store errors by
-- design — a tester must never see a stack trace because a preference did not save — so a broken write shows
-- up as *nothing happening*, not as an error. There is no alert to wait for. This query is the alert.
--
-- ⚠️ Run it as the owner (the SQL Editor), which bypasses RLS. That is correct here: the question is
-- "did the row land?", not "what can the anon key see?" — for that, use scripts/supabase_probe.sh.

select
  -- Sign-ins: ADR-193 admits a new Google account up to the cap, so this grows as people arrive.
  (select count(*) from beta_users)                     as allow_listed,
  (select max(last_seen) from beta_users)               as newest_sign_in,

  -- Refusals: someone turned away lands here (ADR-102). ⚠️ The waitlist write is FAIL-SILENT — if Stage A's
  -- insert-only policy were wrong, this would simply stop growing and look exactly like "nobody was refused".
  (select count(*) from beta_waitlist)                  as waitlist_rows,
  (select max(created_at) from beta_waitlist)           as newest_refusal,

  -- Saves: since Stage B3 these go through save_squad(). ⚠️ This is the one that caught a real failure on
  -- 2026-09-20 — a save that appeared to work had written nothing, because the deployed code was still
  -- reading the table directly. ⭐ *"It looked like it saved" and "a row appeared" are different questions.*
  (select count(*) from squads)                         as squads_saved,
  (select max(updated_at) from squads)                  as newest_save,

  -- The functions the app now depends on: 4 from Stage B1/B2 + 8 from B3.
  (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname in (
      'is_allow_listed','register_beta_user','forget_me','touch_last_seen',
      'get_squad','save_squad','squad_exists','delete_squad',
      'get_prefs','save_prefs','get_watchlist','save_watchlist'))  as functions;

-- WHAT GOOD LOOKS LIKE
--   functions      = 12. Anything less means a function is missing and something is 404ing right now.
--   newest_save    — moves whenever anyone saves a squad. On an active day, minutes or hours.
--   newest_sign_in — moves as testers arrive.
--   allow_listed   — grows as new people are admitted (baseline 2026-09-20: 29).
--   newest_refusal — moves only when someone is actually turned away, so a stale value here is usually fine.
--
-- WHAT BAD LOOKS LIKE
--   ⚠️ `newest_save` frozen for a day you know people used the app → saves are being refused silently.
--      Check scripts/supabase_probe.sh, and roll back with:
--        grant all on public.squads, public.user_prefs, public.player_watchlist to anon, authenticated;
--   ⚠️ `functions` below 12 → re-apply sql/stage_b_functions_only.sql and sql/stage_b3_functions_only.sql.
