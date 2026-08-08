# Architectural Decision Record: Running a wider beta — environments, code protection, backup, monitoring

**Decision ID:** ADR-095
**Date:** 2026-08-23
**Status:** Accepted
**Superseded By / Replaces:** extends the deploy (ADR-053) and beta-enablement (ADR-087) records with the
**operational** decisions for opening the app to ~20–50 testers. Companion to ADR-094 (persistence). No product
pivot — this keeps the app a **hobby beta** (DIRECTION §1); it just runs one safely.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants to recruit **~20–50 testers** (e.g. via Reddit) and asked four operational questions:
**(1)** performance metrics to spot lag/wait times; **(2)** whether wider testing needs **dev/test/prod**;
**(3)** how to **protect the code** (currently public on GitHub — a past attempt to go private hit friction);
**(4)** a **backup** strategy. Underlying stance: *happy to stay hobby*, but tighten a few things before more
people arrive. Cost must stay ~£0.

**Verified at planning (current state):**
- **One app**, auto-redeploying off `master` (ADR-053). So **every push can break the testers' app
  mid-session** — the real risk with 50 people, more than any missing "environment."
- **No `LICENSE`** — the code is *visible* and, with no licence, legally "all rights reserved" by default, but
  nothing states the terms.
- **One git remote** (`origin` = GitHub) — a **single point of failure** for the whole history. Seed data
  (`data/seed.db`, `seed_squads.json`) is in-repo, so it rides along with any repo backup.
- **No metrics** instrumented. Streamlit Community Cloud provides an **Analytics** tab (viewer counts) + **logs**,
  but **no latency telemetry**. Free tier is **~1 GB RAM, sleeps when idle, resource-limited** — at 20–50
  concurrent testers the genuine risk is the app *struggling*, not our inability to measure lag.
- **Secrets** already live in Streamlit / env, **not** the repo (ADR-087) — so going public⇄private doesn't leak
  anything.

#### Decision Drivers
- **Don't break the testers** — a stable surface they use, insulated from mid-sprint pushes.
- **Stay hobby, ~£0** — free tiers only; no accounts, no paid infra.
- **Protect the code without hiding it** — public is fine for the Streamlit deploy; tighten the *terms*.
- **No single point of failure** — the history must survive GitHub going away / a bad force-push.
- **Cheap signal over rich telemetry** — know "is it up / slow" without building analytics.
- **Opt-in + inert-by-default** — anything added (a mirror Action, etc.) must be a no-op until the owner wires
  the secret, so CI and the public deploy are unaffected.

---

### ✅ Decision

**1. Environments — a two-app prod/staging split (not three heavyweight tiers).** Keep **`master`** as the
**working** branch → a **staging** Streamlit app (where the owner smoke-tests a build). Promote to a **stable**
branch **`main`** → the **prod** app the testers use; promotion is a **merge** `master → main`. So a push while
50 people test lands on *staging*, not their app; prod moves only on a deliberate merge. **£0** (Community Cloud
allows multiple apps). *(The repo already has a `main`/`master` split — this wires each branch to its own app and
makes "promote = merge to `main`" the rule.)* Streamlit stays **pinned** (`streamlit==1.61.1`) so both apps
render on the tested version.

**2. Code protection — stay public + a restrictive licence.** Add **PolyForm Noncommercial License 1.0.0** as
`LICENSE` (a standard *source-available, non-commercial* licence): the repo stays **visible** (so the Community
Cloud deploy is unaffected and testers/others can read it), but reuse is restricted to **non-commercial** — "look,
don't take it commercial." **£0.** *Going fully **private** is deferred* — GitHub private repos are free, but the
past friction was **Community Cloud** (its free tier limits private apps + needs re-granting repo access, i.e. a
deploy reconnection); revisit only if *hiding* the code becomes the goal (accepting that reconnection).

**3. Backup — a mirror remote + a scheduled Action (belt & braces).** Add a **second git remote** (Codeberg /
GitLab, free) and a GitHub Action (`.github/workflows/mirror.yml`) that runs `git push --mirror` **on push + on a
daily cron** to `${{ secrets.MIRROR_URL }}`. It **skips cleanly when the secret is unset** (inert until the owner
opts in — no CI change, no failing runs on forks). The in-repo seed data is covered by the mirror; a manual
`git bundle` to cloud storage is documented as the offline fallback (`docs/BACKUP.md`). **£0.**

**4. Monitoring — external uptime/latency + Cloud Analytics, not custom RUM.** Use a **free external monitor**
(UptimeRobot / Better-Uptime) pinging the live URL every ~5 min → **response-time graphs + downtime alerts** —
the cheapest, code-free signal for "is it slow / down". Read viewer counts from the Community Cloud **Analytics**
tab. **Defer** heavier instrumentation: add **server-render timing to logs** (`perf_counter` around page work)
*only if* a problem shows; **reject** third-party client-side RUM for a hobby beta (Community Cloud CSP friction +
a privacy cost for little gain). **£0.** *Honest note recorded:* the likely bottleneck at 20–50 concurrent users
is the **free-tier RAM/idle-sleep limit**, not measurement — if it bites, the answer is a paid tier or a lighter
deploy (a later decision, not now).

**5. Everything opt-in / inert by default.** The mirror Action no-ops without `MIRROR_URL`; the prod/staging
split is a branch+deploy convention (no code); the licence is inert text; monitoring is external. So the public
deploy + CI are unchanged until the owner flips each switch — the ADR-087 pattern.

---

### 🔀 Alternatives Considered

- **A full dev/test/prod (three environments).** Rejected — overkill for a hobby beta; the *actual* need is
  insulating testers from mid-sprint pushes, which a two-app prod/staging split solves at £0.
- **Keep a single app off `master`.** Rejected — it's the status-quo risk (a bad push hits every tester live).
- **Go private now.** Deferred — free on GitHub, but re-triggers the Community-Cloud reconnection friction and a
  private-app cap; and public-but-licensed already protects the *terms*. Revisit only to *hide* the code.
- **A permissive licence (MIT/Apache).** Rejected for the owner's intent — they want to *restrict* commercial
  reuse while staying hobby; PolyForm Noncommercial fits. *(An all-rights-reserved custom notice was considered;
  a recognised source-available licence is clearer and standard.)*
- **GitHub-only, no mirror** (rely on GitHub's durability + local clones). Rejected — one remote is a single
  point of failure (account loss, a bad force-push); a mirror is ~£0 insurance.
- **Custom in-app metrics / third-party RUM.** Rejected/deferred — an external uptime monitor gives the needed
  signal at zero code; RUM adds CSP friction + a privacy cost for a hobby beta.
- **A paid Streamlit / other host now.** Rejected — premature; only if the free tier demonstrably struggles under
  real tester load (the monitor will show it).

---

### 🧭 Consequences

**Positive**
- Testers use a **stable prod app**; the owner iterates on **staging** — a bad push can't break the beta.
- The code is **protected in terms** (non-commercial) while staying visible → the Community Cloud deploy is
  untouched.
- The history has **no single point of failure** (a mirror + local clones + the in-repo seed).
- "Is it up / slow" is answered by a **free monitor**; no analytics to build; the real risk (free-tier limits) is
  named and watched.
- Everything is **inert by default** — CI, forks, and the public deploy are unaffected until each switch is set.

**Negative / risks (mitigations)**
- **Promotion discipline** — someone must remember "prod moves only via a merge to `main`." *Mitigation:* the
  DEPLOY.md runbook + a short PR/merge convention; branch protection on `main` is an optional tightening.
- **A licence can't stop copying, only govern terms.** *Mitigation:* accepted — it's the honest hobby posture;
  private is the deferred lever if hiding matters.
- **A mirror needs a credential** (`MIRROR_URL` with a token/deploy key). *Mitigation:* a Streamlit/Actions
  secret, documented in BACKUP.md; the Action skips when unset so nothing breaks meanwhile.
- **Free-tier performance** may still bite under load. *Mitigation:* the monitor surfaces it; the escalation
  (paid tier / lighter deploy) is a recorded, deferred decision.

---

### 🧾 Status & follow-ups

- **Accepted.** The *cheap code* under this ADR lands in Sprint 122 stories: **US-305** (LICENSE + the mirror
  Action + `docs/BACKUP.md`) and **US-306** (feedback go-live + the DEPLOY.md prod/staging section + the uptime
  note in BETA.md).
- **Owner actions (~30 min, £0):** create the staging Streamlit app off `master` + point prod at `main`; add the
  mirror remote + the `MIRROR_URL` secret; add the uptime monitor; (feedback sink per ADR-087/BETA.md).
- **Deferred levers:** going **private** (only to hide the code); **server-render timing** in logs (only if the
  monitor shows a problem); a **paid host** (only if the free tier struggles under real tester load); **branch
  protection** on `main`.
