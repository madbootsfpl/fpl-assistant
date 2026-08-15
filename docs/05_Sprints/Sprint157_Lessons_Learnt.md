# Lessons Learned

**Sprint:** Sprint 157 — Ask Maddie: a Supabase-backed video hub

**Dates:** 2026-08-15

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Give the **Maddie** explainer videos a home in the app (ADR-112): a **grounded, scripted FAQ-by-video** — *not* a
live chatbot. Content lives in a **Supabase `maddie_videos` table** the owner curates from the dashboard, so videos
can be added / removed / refreshed **without a redeploy**; the app **reads** it live (cached, best-effort, with a
built-in fallback) and embeds **unlisted YouTube** clips via `st.video`. New `pages/9_Ask_Maddie.py` hub (US-382)
+ a Home teaser (US-383).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reuse the established store seam.** `maddie.py` is a near-copy of `user_store`/`waitlist`: same `_endpoint()`
  derivation from `FPL_STORE_URL`, same `FPL_STORE_KEY`, same `with_retry` + best-effort shape — so a whole new
  data source arrived with **no new secret** and no new pattern to learn.
- **Fail-soft by default.** A built-in fallback list means an unconfigured / unreachable / empty store still
  renders a sensible page — the same resilience posture as the news feeds (ADR-093), applied to a new surface.

## New Skills Acquired

- **The store's RLS posture follows its access shape.** Read-only table → RLS on + a `select using(true)` policy;
  no write path → none of the upsert/`42501` complexity the waitlist forced. Choosing "the app only reads, the
  owner writes in the dashboard" was the key design move — it made the setup a one-liner and the security trivial.
- **Requirement-driven design.** "Add/remove videos without rebuilding" is what ruled out the simpler
  code-list and selected a Supabase-backed cached read. Naming the real constraint first picked the architecture.

---

# What Went Well ✅

- Clean, small, fully-tested feature (+5 tests → 992, ruff green) with **zero new dependencies**.
- The owner's `create table` ran first time; RLS-on read policy sidestepped the earlier waitlist pain.
- The fallback let the feature ship **before** any real video exists — which mattered, because the free HeyGen
  plan turned out to block downloads (the live-video smoke is deferred to a paid plan, cleanly).

# What Was Tricky / Deferred ⚠️

- **Live-video smoke deferred** — free HeyGen can't export the rendered file, so there's no YouTube-hostable clip
  yet. Feature is code-/test-complete; the owner will smoke it after building the series + moving to a paid plan.
- **Page renumbering** touched ~11 test references — mechanical, but a reminder to `grep` the blast radius
  (`page_link`, hard-coded filenames) before a `git mv`.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
