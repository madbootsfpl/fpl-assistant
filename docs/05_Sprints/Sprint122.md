# Sprint 122: Foundations for wider testing — decisions + cheap safeguards

**Dates:** 2026-08-23 (planned)
**Status:** 📝 Planned (0/2 stories · 2 ADRs)
**Capacity:** ~¾ session (a **decisions/foundations** sprint — two ADR gates + two low-risk stories; lighter code)
**Carried Over:** none

> **Direction (owner discussion):** five strategic questions — (1) squad persistence **across devices**;
> (2) get the **feedback form** operational; (3) **Streamlit performance metrics** for wider testing; (4) do
> 20–50 testers need **dev/test/prod**; (5) **hobby vs product** — protect the code (currently public) + a
> **backup** strategy. Headline finding: **all of it is ~£0** on free tiers well past 50 users — the real cost
> is *complexity + posture*, not money — and the feedback form is **already built** (just needs config).

---

### 🔎 Verified at planning (current state)

- **Persistence today:** squads live in `st.session_state` + a downloadable `squad.json` (ADR-054); the web
  **never writes** server-side (a guardrail test enforces `.save(`-free web edges). Cross-device = download /
  upload — the pain point.
- **Feedback is already built** (`pages/8_Feedback.py`, ADR-087; runbook `docs/BETA.md`): the form POSTs
  `{message, email, source}` to `FPL_FEEDBACK_WEBHOOK` and degrades to a GitHub issue when unset. **Operational =
  config, not code** (a Google-Sheet sink + the secret). It does *not* yet capture app-version / a "which page"
  attribution (ADR-087 intended version/page).
- **Deploy today:** one app auto-redeploying off `master` (ADR-053) → *every push can break the testers' app
  mid-session.* No staging. Streamlit is pinned (`streamlit==1.61.1`).
- **Metrics today:** none instrumented. Community Cloud gives an **Analytics** tab (viewers) + **logs**; **no**
  latency telemetry. Free tier is **~1 GB RAM, sleeps when idle, resource-limited** — the real risk at 20–50
  testers is the app *struggling*, not measuring lag.
- **Code/backup today:** **no `LICENSE`** (visible, legally all-rights-reserved by default); **one git remote**
  (`origin` = GitHub) → a single point of failure. No auth/DB deps.
- **Owner decisions (this planning):** persistence = **handle-keyed free store** (Supabase, no login);
  protection = **public + a restrictive LICENSE**; set up **prod/staging split** + **mirror backup** +
  **feedback/uptime** now.

---

### 🎯 Sprint Goal

**Objective:** lay the **foundations** to open the app to ~20–50 testers safely — *record the big decisions as
ADRs* (so the next sprint builds against an agreed design) and *ship the cheap safeguards now* (a licence, a
backup, feedback go-live). No new user-facing feature; the persistence **build** is gated to Sprint 123.

#### Success Criteria
- [ ] **ADR-094 — Cross-device squad persistence (design gate, no build).** Commit to a **handle-keyed free-tier
      store** (Supabase; **no login** — a user-chosen handle is the key); supersede the relevant part of ADR-054;
      define how the **read-only guardrail evolves** (a *scoped, opt-in* save/load — still no per-account auth, no
      PII beyond the handle) and the cost (**£0**, free tier ≫ 50 users). **Build deferred to Sprint 123.**
- [ ] **ADR-095 — Running a wider beta (ops).** Record: (a) a **prod/staging** two-app split (a stable branch →
      the testers' app; the working branch → staging; promote by merge); (b) **code protection** = stay public +
      a **PolyForm Noncommercial** LICENSE; (c) **backup** = a mirror remote + a scheduled Action; (d)
      **monitoring** = an external uptime monitor + the Cloud Analytics tab. All **£0**.
- [ ] **US-305 (safeguard the code)** — add the **LICENSE** (PolyForm-NC 1.0.0) + a README line; add a
      **mirror-backup** GitHub Action (`.github/workflows/mirror.yml`, no-op until the owner adds the mirror
      remote + secret) + a **`docs/BACKUP.md`** runbook.
- [ ] **US-306 (beta go-live enablement)** — enrich the **feedback payload** (auto **app-version** + **timestamp**
      + an optional **"Which page?"** selectbox) with a test; add a **go-live checklist** to `docs/BETA.md`
      (feedback Sheet + secrets + the prod/staging deploy + the uptime monitor). Extends ADR-087.
- [ ] **No drift** — the read-only guardrail still holds (no server writes land this sprint — persistence is
      design-only); existing **775** stay green (+ the feedback-payload test); ruff clean; CI unaffected (the
      mirror Action is additive + secret-gated).
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help (n/a), Feedback_Log, Backlog, DEPLOY.md (prod/staging),
      BETA.md, BACKUP.md; ADR-index += ADR-094/095.

---

### 🧭 Design sketch

**ADR-094 (persistence).** A tiny persistence adapter (`storage`/a new `cloud_store`) behind an interface:
`save_squad(handle, squad)` / `load_squad(handle)` → a **Supabase** table `squads(handle text primary key,
json text, updated_at)` via its REST endpoint + an anon key (a Streamlit secret). **No login** — the handle *is*
the key (a hobby-beta trade-off: whoever knows a handle can overwrite it; acceptable for read-only FPL data). The
web guardrail moves from "no writes at all" to "**no writes except the scoped squad save/load**" — a named,
tested exception, off by default (unset secret → the feature hides, the app stays read-only). **This ADR is the
gate; the My-Squad "Save/Load on any device" UI is Sprint 123.**

**ADR-095 (ops).** Prod/staging: keep `master` as the working branch → a **staging** Streamlit app; promote to a
**stable** branch (`main`) → the **prod** app the testers use. Protection: public repo (Streamlit deploy
unaffected) + PolyForm-NC. Backup: `origin` (GitHub) + a **mirror** (Codeberg/GitLab) via a scheduled
`push --mirror` Action. Monitoring: an external uptime+latency monitor (UptimeRobot/Better-Uptime free) + the
Cloud Analytics tab; server-render timing to logs only *if* a problem shows.

**US-305.** `LICENSE` = PolyForm Noncommercial 1.0.0 (verbatim) + a README "License" line. `mirror.yml`: on push
+ a daily cron, `git push --mirror` to `${{ secrets.MIRROR_URL }}` — **skips cleanly when the secret is unset**
(so it's inert until the owner opts in). `docs/BACKUP.md`: the mirror setup, plus a manual `git bundle` fallback
and what the seed data covers.

**US-306.** Extend the feedback POST payload to `{message, email, source, version, page, ts}` — `version` from
`importlib.metadata.version("fpl-assistant")` (falls back to the pyproject value), `page` from a small
`st.selectbox("Which page?", [...])`, `ts` an ISO timestamp; unchanged degrade-to-GitHub behaviour. A test
asserts the enriched payload shape (with a fake/monkeypatched `requests.post`). BETA.md gains a one-page
**go-live checklist**.

**Deferred (→ Sprint 123+):** the persistence **build** (the Save/Load UI + the Supabase adapter, gated by
ADR-094); native `st.login()` (the "product" upgrade path); server-render timing instrumentation; going
**private** (revisit only if hiding the code matters — accepts the Cloud reconnection).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-094 | **Cross-device persistence** — handle-keyed free store (design gate; build = Sprint 123). | High | ✅ Done | gate |
| ADR-095 | **Running a wider beta** — prod/staging + protection + backup + monitoring. | High | ✅ Done | gate |
| US-305 | **Safeguard the code** — LICENSE (PolyForm-NC) + mirror-backup Action + BACKUP.md. | High | ✅ Done | ~¼ session |
| US-306 | **Beta go-live enablement** — enrich the feedback payload + a BETA.md go-live checklist. | High | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you — ~30 min, £0)

_(these need your account/clicks; the sprint delivers the code + the runbooks)_
1. **Feedback sink:** create the Google Sheet + Apps Script (BETA.md §1), set `FPL_FEEDBACK_WEBHOOK` in Streamlit
   secrets (+ optional `FPL_SIGNUP_URL`). Test the in-app form → a row appears.
2. **Uptime monitor:** add the live URL to UptimeRobot/Better-Uptime (5-min ping) → latency + downtime alerts.
3. **Mirror backup:** create a mirror repo (Codeberg/GitLab), add its push URL as the `MIRROR_URL` secret.
4. **Prod/staging:** create a second Streamlit app off the **staging** branch; keep the current app on the
   **stable** branch (per ADR-095 / DEPLOY.md).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the enriched feedback payload carries `version`/`page`/`ts` (a monkeypatched-`requests.post`
   test); the read-only guardrail still holds (no server writes this sprint); existing **775** stay green; ruff
   clean. The mirror Action is valid YAML + secret-gated (no CI change when the secret is unset).
2. **Manual smoke** — `python -m src.web_streamlit` → Feedback: the "Which page?" selectbox shows, submit still
   degrades gracefully with no webhook; `LICENSE` renders on the repo.
3. **Docs updated** — ADR-094/095 + the ADR-index; PROJECT_STATUS, Architecture, README, Feedback_Log, Backlog,
   DEPLOY.md, BETA.md, BACKUP.md.

---

### 📝 Session Progress Log

- **ADR-094 (cross-device persistence — design gate)** — wrote `docs/06_Decisions/ADR-094-cross-device-squad-
  persistence.md` (Accepted; **no code**). Commits to a **handle-keyed Supabase store** (no login — the handle is
  the key), a thin swappable `cloud_store` adapter (`save_squad`/`load_squad`, best-effort `requests` → Supabase
  REST, secret-gated via `FPL_STORE_URL`/`FPL_STORE_KEY`), ~£0. **Revises the read-only invariant** (ADR-054):
  from "the web never writes" → "no *local* DB/squad-file writes; the sole server write is this opt-in, tested,
  secret-gated squad save" — off by default (unset → the feature hides, app stays read-only). Records the
  hobby-beta trade-off (a handle isn't security; public FPL data, no PII) and native `st.login()` as the deferred
  "product" upgrade path (the adapter interface is chosen so a handle → an authed user id needs no re-architecting).
  **Build gated to Sprint 123** (adapter + My-Squad Save/Load UI + the guardrail-test revision + a privacy note).
  Added to the ADR index. No tests/code this story (design gate) — suite unchanged at **775**.
- **ADR-095 (running a wider beta — ops)** — wrote `docs/06_Decisions/ADR-095-running-a-wider-beta.md` (Accepted).
  Records the four operational decisions, all ~£0 + opt-in + stay-hobby: **(1)** a **prod/staging** two-app split
  (`master` → staging, `main` → prod-for-testers, promote by merge — a mid-sprint push can't break the beta);
  **(2)** code protection = stay **public** + **PolyForm Noncommercial** LICENSE (private deferred — the past
  friction was Community Cloud's private-app cap + a deploy reconnection); **(3)** backup = a **mirror remote** +
  a secret-gated `mirror.yml` Action (inert until `MIRROR_URL` set) + a `git bundle` fallback; **(4)** monitoring
  = a free external **uptime/latency** monitor + Cloud Analytics, with server-timing-to-logs + a paid host both
  deferred until the free tier demonstrably struggles (the honest real-risk note: free-tier RAM/idle-sleep at
  20–50 users, not measurement). The cheap code lands in US-305/306; the rest are owner runbook actions. Added to
  the ADR index. Design/decision record — no code; suite unchanged at **775**.
- **US-305 (safeguard the code)** — added **`LICENSE`** (PolyForm Noncommercial 1.0.0, verbatim, with a
  `Required Notice: © 2026 Tony Sheridan` header) + a **README "License"** section; a **mirror-backup** Action
  (`.github/workflows/mirror.yml`) that bare-`--mirror`-clones the repo and `push --mirror`s to
  `${{ secrets.MIRROR_URL }}` on **push + a daily cron + manual dispatch**, **secret-gated** (a `gate` step skips
  everything when `MIRROR_URL` is unset → inert on forks / until the owner opts in, no CI change); and a
  **`docs/BACKUP.md`** runbook (the mirror setup, a `git bundle` offline fallback, a restore playbook, and a note
  that the committed seed data rides along). Validated: `mirror.yml` parses as YAML (jobs `mirror`; triggers
  push/schedule/workflow_dispatch). No Python changed — ruff clean, suite stands at **775**.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
