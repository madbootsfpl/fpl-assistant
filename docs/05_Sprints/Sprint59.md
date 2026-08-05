# Sprint 059: Tester feedback loop (share the live app · capture · triage — no feature build)

**Dates:** 2026-08-05
**Status:** 📝 Planned
**Capacity:** ~1 session of scaffolding (a tester guide + a feedback log) + owner-run calendar time (share + collect)
**Carried Over:** None (Sprint 058 shipped the editable squad; the app is live + rebooted healthy)

> **Direction (owner):** *"gather feedback first"* — but first, **two pre-tester polish adds** so the app is
> consistent and self-service before it's shared: (1) **imagery consistency** — the Players/Fixtures
> photos+badges applied (augmented) across all squad tabs; (2) a **local-only data refresh** button + a
> **"Data as of \<date\>"** freshness caption (the cloud stays read-only). Then put it in front of testers
> with a guide + a triage log that **seeds Sprint 060's backlog**.

---

### 🔎 Verified at planning

- **The app is live + healthy** (rebooted after the Sprint-058 stale-env fix; My Squad / Transfer / Captain
  all load). Ready to share.
- **A zero-infra feedback channel exists:** the repo is **public on GitHub**, so **GitHub Issues** is a
  natural, no-account, no-server way for testers to report — nothing to build or host. *(Confirm the channel
  at "start US-176" — email or a shared doc are alternatives.)*
- **We already know the top likely friction** (from the Sprint-058 retro, to pre-empt in the guide): a
  session squad is **lost on a browser refresh until downloaded**; the manual swap is **same-position only**.

---

### 🎯 Sprint Goal

**Objective:** get the live editable app in front of testers with a **short "what to try" guide** and a
**feedback log** to capture + triage what comes back — turning tester reactions into a prioritised **Sprint
060 backlog**. No feature code.

#### Success Criteria
- [ ] **Feedback channel chosen** (proposed: GitHub Issues on the public repo) — where testers report
- [ ] **Tester guide** — a short `docs/00_Project/Testing_Guide.md`: what the app does, a **try-this**
      checklist (build → name → edit/swap → set captain → download → re-upload), the **known limits**
      (refresh-loss; same-position swaps), and **how to report**
- [ ] **Feedback log** — `docs/00_Project/Feedback_Log.md`: a simple triage table (date · tester · area ·
      what happened · severity · → backlog?) to collect + categorise, feeding Sprint 060
- [ ] *(Optional, needs owner OK — it's a 1-line UI text edit, not a feature)* a Home hint: "Testing this?
      Tell us what breaks → \<channel\>"
- [ ] **No feature code** — analytics / the editor / the engine are untouched this sprint
- [ ] Docs: PROJECT_STATUS updated (sprint + the feedback loop); Backlog seeded from any feedback received

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-179 | **Imagery consistency (augment)** — pull the photo-URL helper into the shared image module; add photo + team-badge columns to **Build · Analyse · Transfer · Captain · My Squad** (an image table *alongside* the existing summary text, not replacing it) | High | ✅ Done | 1 session |
| US-180 | **Refresh + freshness** (**ADR-056**) — a **local-only** "🔄 Refresh data" button (writable, non-seed DB) + a **"Data as of \<date\>"** caption on every tab (disabled/caption-only on the read-only cloud). The first web write path — gated | High | ✅ Done | 0.5 session |
| US-176 | **Tester guide + channel** — channel = **GitHub Issues** (public repo); `docs/00_Project/Testing_Guide.md` (what it does · a try-this checklist · known limits · how to report) | High | ✅ Done | 0.5 session |
| US-177 | **Feedback log + triage** — `docs/00_Project/Feedback_Log.md` (a triage table); as feedback arrives, log + categorise it and seed the **Sprint 060** backlog | High | ✅ Done (template; ongoing intake) | ongoing |
| US-178 | **Home feedback hint** — a single line on Home linking the channel (owner-approved) | Low | ✅ Done | 0.1 session |

#### Technical Tasks & Maintenance
- [x] `docs/00_Project/Testing_Guide.md` + `Feedback_Log.md` — _US-176/177_
- [x] PROJECT_STATUS: the feedback loop + Sprint 059 — _US-177_
- [ ] (Owner) share the app link with testers + point them at the channel

---

### ✅ Definition of Done (this sprint)

Not the usual 3-part code DoD (no feature ships). Instead:
1. **The guide + log exist and read clearly** — a tester can open the app, follow the checklist, and report.
2. **The app is shared** (owner) and the channel is live.
3. **Feedback is captured + triaged** in the log, with the top items promoted to the **Sprint 060** backlog.
4. **Docs updated** — PROJECT_STATUS reflects the feedback loop.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A tester guide + a feedback/triage log (docs) | Any feature / analytics / editor / engine change |
| Choosing + pointing at a feedback channel | A server-side feedback form / accounts (no infra) |
| Seeding the Sprint 060 backlog from feedback | Acting on feedback (that *is* Sprint 060) |
| *(Optional)* a 1-line Home hint | New pages / interactivity |

**External Dependencies:** the **owner** shares the app + recruits testers; feedback arrives on the owner's
calendar, so US-177 completes over days, not in one session.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| No feedback arrives (few/slow testers) | Med | A crisp try-this checklist lowers the effort to report; owner nudges a few testers directly |
| "Squad lost on refresh" dominates as noise | Low | Pre-empt it in the guide's *known limits* so it's expected, not reported as a bug |
| Feedback is vague / unactionable | Med | The log's triage columns (area · severity) force it into shape before it hits the backlog |
| Scope creep into fixing things now | Low | This sprint only *captures*; fixes are Sprint 060 (keeps the loop honest) |

---

### 📝 Session Progress Log

- **US-179 ✅** — **Imagery consistency (augment).** Promoted the player-photo helper into the shared
  `badges.py` (`photo_url` + `photo_url_by_id`) — one source of image URLs for every tab — and deduped it
  out of the Players page. New `src/web_streamlit/tables.py` `render_player_table(rows)` (one place for the
  photo/badge/out/in `ImageColumn` config). Added an image table (photos + team badges) to **Build**
  (the 15, XI-then-bench), **Analyse** (the squad, **(C)** marked), **Captain** (ranked candidates),
  **Transfer** (out→in swaps, both players' photos), and **My Squad** (added columns to its existing table)
  — each **above** the existing text summary (the totals / notes / reasoning stay). Tests (+3 → **484**):
  `photo_url`/`photo_url_by_id`; the squad tabs show photo+badge columns; Transfer shows out/in photo
  columns (after bank→swaps). Smoke: all six data tabs render image tables headlessly; `ruff` clean.
- **US-180 ✅** — **Refresh + freshness (ADR-056).** A shared `src/web_streamlit/status.py`
  `render_data_status()` (sidebar), called on **every** page: a **"📅 Data as of \<date\>"** caption (the
  DB file's mtime — last refresh locally, deploy snapshot on the cloud) always, plus — **only locally** — a
  **"🔄 Refresh data"** button that reuses the CLI's `ingest.refresh` (spinner + `FplApiError` → error →
  `st.rerun`). Local is gated by **`FPL_LOCAL=1`**, set by the `python -m src.web_streamlit` runner **and**
  requiring a writable non-seed DB (`config.SEED_DB_PATH` named for the check) — so the **cloud shows the
  caption only, no write path** (the first web write is deliberately narrow; the no-`SquadStore.save`
  guardrail still holds). Tests (+3 → **487**): the caption renders in both modes on every tab; the button
  is present only when `FPL_LOCAL` + a live DB; `is_local()` needs both. Smoke: cloud → caption only; local
  → the refresh button appears; `ruff` clean.
- **US-176 ✅** — **Tester guide.** Channel chosen: **GitHub Issues** (public repo, zero infra).
  `docs/00_Project/Testing_Guide.md` — what the app is + the live URL; a ≈5-min **try-this** checklist
  (Players → Fixtures → Build/name/download/use → My Squad edit → Captain → Transfer/Apply → Analyse →
  Ask); **known limits** (refresh-loss until download; same-position swaps; data snapshot / local-only
  refresh; Ask without the LLM on cloud); and **how to report** (issue link + what to include).
- **US-177 ✅ (template)** — **Feedback log.** `docs/00_Project/Feedback_Log.md` — a triage table
  (date · tester · tab · what · severity · → backlog?) + how it feeds **Sprint 060** + pre-seeded themes to
  watch (refresh-loss, cross-position swaps, freshness clarity). Intake is **ongoing** (owner shares →
  reports land → triaged here).

---

### 🏁 Sprint Review & Retrospective

_(to be completed at sprint close)_
