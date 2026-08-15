# Sprint 157: Ask Maddie — a Supabase-backed video hub (US-382 / US-383)

**Dates:** 2026-08-15
**Status:** ✅ Complete — US-382 + US-383 (ADR-112). 991 → 992 tests. *(Live-video smoke deferred — see below.)*
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

**Delivered — a grounded, dashboard-managed video hub, code- and test-complete.**

- **US-382 — the reader + hub page.** `src/web_streamlit/maddie.py` mirrors `user_store`/`waitlist`: the
  `maddie_videos` endpoint is derived from `FPL_STORE_URL`'s base, reusing `FPL_STORE_KEY` (**no new secret**),
  via `with_retry`. `videos()` is **read-only + fail-soft** — it fetches `published=true` rows ordered by
  `sort_order`, cleans them (trimmed; a blank URL → `None`), and falls back to a built-in **"Meet Maddie —
  coming soon"** welcome when the store is unconfigured / unreachable / has no published rows, so the hub is
  **never blank and never raises**. `pages/9_Ask_Maddie.py` renders 🎥 title + the MADBOOTS mark + one
  `st.video` block per clip (a URL-less row degrades to **"🎬 Coming soon"**); cached ~10 min.
- **US-383 — the Home teaser.** A 🎥 *"Meet Maddie"* `st.page_link` by the existing "New here?" nudge + a
  sidebar-list bullet under Help.
- **IA renumber** — the hub slots into the learn cluster: `8 Help · 9 Ask Maddie · 10 Feedback · 11 Admin`
  (`git mv` on Feedback/Admin; nothing `page_link`ed them; ~11 test references updated + 2 stale doc refs fixed).
- **Tests:** +5 → **992**, ruff clean. `videos()` published-ordered-cleaned · fallback-when-unconfigured ·
  fallback-on-error (never raises) · the page embeds a clip & degrades a URL-less row · Home links to the hub.
- **Owner setup:** the `create table maddie_videos` + public-**read** policy ran clean (RLS stays on — the app
  only reads, so none of the waitlist's RLS-upsert pain). SQL also captured in **BETA.md §6**.

**⏳ Live-video smoke deferred (owner):** the current HeyGen plan is **free**, which **can't download** the
rendered video — so there's no shareable/YouTube-hostable file yet. The owner will **build the series first**,
then move to a **paid plan**, download the clips, upload them **unlisted to YouTube**, add rows to
`maddie_videos` (`published=true`), and verify the hub shows them. Until then the page shows the built-in
"coming soon" fallback — **expected, not a bug**. The code path is fully covered by tests with a faked store.

### 🧠 Lessons

- **Match the store pattern to the access shape.** The waitlist needed RLS *disabled* only because the app
  **upserts** it; a **read-only** table (the app never writes — the owner curates in the dashboard) keeps RLS
  **on** with a simple `select using(true)` policy. Deciding "who writes" up front removed a whole class of the
  `42501` pain we hit before.
- **Config-in-a-table beats config-in-code when the owner must self-serve.** A `VIDEOS = [...]` list would have
  been simpler to build but chained every content edit to a redeploy. One Supabase table + a cached read turned
  "refresh the videos" into a dashboard task — the requirement ("no rebuild") drove the design, not the other way.
- **A fail-soft fallback makes an external dependency safe to ship early.** Because `videos()` degrades to a
  built-in welcome, the feature ships and renders sensibly **before** a single real video exists — decoupling the
  build from the owner's content pipeline (and, as it turned out, from a paid-plan blocker).
- **Renumbering pages is cheap *if* nothing links by filename.** One `grep` confirmed only `3_My_Squad.py` was
  `page_link`ed; the rest was mechanical `git mv` + find/replace in tests. Verify the blast radius, then it's safe.
