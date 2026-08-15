# Sprint 157: Ask Maddie — a Supabase-backed video hub (US-382 / US-383)

**Dates:** 2026-08-15 →
**Status:** 🚧 Planned — gated by **ADR-112**. Owner action (create the table) runs in parallel with the build.
**Capacity:** ~½ session (one page · one teaser · one reader module · ~3–4 tests · no new dependency)
**Carried Over:** none

> **Goal:** give the **Maddie** explainer videos a home in the app — a **grounded, scripted FAQ-by-video**
> (ADR-112), *not* a live chatbot. Content lives in a **Supabase `maddie_videos` table** the owner manages from
> the dashboard, so videos can be **added / removed / refreshed without a redeploy**. The app **reads** it live
> (cached, best-effort, with a built-in fallback), and embeds **unlisted YouTube** clips via `st.video`.

---

### 🎯 Scope

**US-382 — the reader + the hub page.**
- **`src/web_streamlit/maddie.py`** — mirrors `user_store`/`waitlist`: `_endpoint()` derives the `maddie_videos`
  URL from `FPL_STORE_URL`'s base + reuses `FPL_STORE_KEY` (**no new secret**); `is_configured()`; a **read-only**
  `videos()` that fetches **`published=true`** rows ordered by `sort_order`, via `with_retry`. **Best-effort +
  fail-soft:** any error (or unconfigured store) → a small **built-in `_FALLBACK`** list (the current video / a
  "coming soon" welcome) so the page never breaks. Wrapped by the page in `@st.cache_data(ttl≈600)` so edits
  appear within ~10 min — or instantly on **Reboot app**.
- **`pages/…_Ask_Maddie.py`** — a "Meet Maddie" intro line (brand mark + one sentence) + one block per video:
  `topic` heading · `blurb` · `st.video(youtube_url)`. A row with **no URL** renders a subtle *"🎬 Coming soon"*
  caption instead of a broken player, so the hub reads well while the series is still being filmed.

**US-383 — the Home teaser.** A compact **"🎥 New here? Meet Maddie"** `st.page_link`/info card on `Home.py`,
sitting with the existing New-here / Testing nudges, linking to the hub. Cross-linked from the **Help** tab.

**Page placement (IA):** slot the hub into the *learn/support* cluster — **after Help**, i.e.
`… · 8 Help · 9 Ask Maddie · 10 Feedback · 11 Admin` (bump Feedback 9→10, Admin 10→11). Low-risk: **no
`st.page_link` points at those files** (only `3_My_Squad.py` is referenced). The Home teaser gives it the
prominent front-door surface without renumbering the whole nav. *(Easy to change — say if you'd rather it sat
higher.)*

---

### ✅ Definition of Done (3-part)

1. **Tests** (fake store, no live network — like the `waitlist`/`user_store` tests):
   - `videos()` returns only **published** rows, **ordered** by `sort_order`, from a faked PostgREST response.
   - On a store error / unconfigured store, `videos()` returns the **fallback** (never raises).
   - The **hub page renders** (AppTest): a configured video embeds; a URL-less row shows "Coming soon".
   - The **Home teaser** links to the hub page.
2. **Manual smoke** (owner, post-deploy): create the table + one row → the video shows; set `published=false` →
   it hides after a reboot; add a second row → it appears.
3. **Docs:** this plan + retro; ADR-112 (done); the `create table` / public-read **SQL in the runbook**;
   PROJECT_STATUS · Roadmap · Backlog (mark shipped) · Help (a pointer to Ask Maddie) · memory.

---

### 🔧 Owner action — create the table (run once in the Supabase SQL editor)

The app only **reads** this table, so — unlike the waitlist — **RLS stays ON** with a public-**read** policy
(no app write path, so no RLS-write headache). Writes happen from the dashboard/SQL editor (which bypass RLS).

```sql
-- Ask Maddie video hub (ADR-112) — one row per explainer video, dashboard-managed.
create table if not exists public.maddie_videos (
  id          bigint generated always as identity primary key,
  topic       text    not null,
  blurb       text,
  youtube_url text,
  sort_order  int     not null default 0,
  published   boolean not null default false,
  created_at  timestamptz not null default now()
);

alter table public.maddie_videos enable row level security;

create policy "maddie_videos public read"
  on public.maddie_videos
  for select
  using (true);
```

Then, once the first clip is uploaded **unlisted to YouTube**, add it (repeat per video; edit/reorder/hide any
time from the Table editor):

```sql
insert into public.maddie_videos (topic, blurb, youtube_url, sort_order, published) values
  ('Meet Maddie — what is MADBOOTS?',
   'The 60-second intro: the analytics decide, the AI explains, you make the call.',
   'https://youtu.be/REPLACE_ME', 10, true);
```

**Refresh model:** edits appear within the ~10-min cache TTL automatically, or **instantly** via **Reboot app**
(the same trick as the DB snapshot). Nothing here needs a redeploy.

---

### 📋 Sprint Review

*(filled at retro)*

### 🧠 Lessons

*(filled at retro)*
