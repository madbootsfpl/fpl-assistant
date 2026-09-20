-- ═══ `events`: analytics go in, nothing comes out ═══
--
-- The 2026-09-19 cutover hardened `beta_users` and `beta_waitlist` and **explicitly deferred `events`**.
-- This closes it, on the terms ADR-212's `setup.sql` already describes for a fresh project.
--
-- ⭐ **Insert-only is the whole design.** A tester's browser adds a row and can never read one back; the
-- Admin view reads them with the **service-role key**, which bypasses RLS entirely.
--
-- ⚠️ **ANALYTICS.md used to justify a read policy here, and the reasoning was careful and wrong**: it argued
-- the key is safe because *"it lives in Streamlit secrets and is never sent to a browser"* — true of the
-- **key**, irrelevant to the **policy**, which applies to anyone holding that key from any source.
-- ⭐ *A permission is granted to a role, not to the place you keep the credential* (ADR-212).
--
-- ⚠️ **Nothing is lost.** Existing rows are untouched; this changes who may touch them.

revoke all on public.events from anon, authenticated;
grant insert on public.events to anon;

alter table public.events enable row level security;
drop policy if exists "anon events insert" on public.events;
drop policy if exists "anon events read"   on public.events;   -- the one ADR-212 argued against
create policy "anon events insert" on public.events for insert to anon with check (true);
