# Architectural Decision Record: Admin — tester activity + load/concurrency views

**Decision ID:** ADR-120
**Date:** 2026-08-18
**Status:** ✅ **Accepted — built** (Sprint 186, 2026-08-24). Spec'd 2026-08-18 and gated then; built
post-GW1 as planned. ✅ **Owner smoke DONE and good (2026-08-25)** — `FPL_ADMIN_KEY` set, the anon SELECT
policy on `events` in place, and both panels read correctly against real data. This also closes the same step
ADR-100 had outstanding. Answers two owner questions: *"which testers are
actually testing?"* and *"am I hitting performance/capacity limits, and can I add more testers?"*
**Superseded By / Replaces:** Extends the anonymous analytics (ADR-100, Sprints 136–137) + the per-user account
store (ADR-106) + the `beta_users` allow-list (ADR-098). **Adds no new table, no new secret, no analytics-payload
change** (the anonymity invariant is untouched) and no `decision_xp` change — it's owner-only **reads**.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner wants to (a) know **which beta testers are actually using it** — to gauge whether feedback will be
enough — and (b) understand whether **more testers** risks **degrading/crashing** the platform (Streamlit
Community Cloud + Supabase free tier).

Key constraint (verified): **the analytics are anonymous by design** (random session id + a random `fpl_anon`
returning-device id — *no emails/user_keys/IPs*, ADR-100). So the Admin page today can say *"12 returning devices
this week"* but **cannot name a tester**. The privacy-respecting way to answer *"who?"* is a separate owner-only
join of data we already hold — **not** by de-anonymising analytics.

Reframe on capacity: **registered ≠ concurrent.** Total registered testers is cheap (Supabase rows; bounded only
by `FPL_USER_CAP`); the real limit is **concurrent** active users on one small Community-Cloud container running a
`decision_xp` compute per interaction. The failure mode is **sluggishness / cold starts**, not a crash — most
likely at a **deadline spike**.

#### Decision Drivers
- **Answer "who's testing" without breaking anonymity** — join the allow-list × the account store, owner-only.
- **Make capacity observable** — surface a live concurrency proxy + latency so the owner sees the edge coming.
- **Cheap + safe** — reads only; reuse the `events` table + the account store + `beta_users`; no new writes/secrets.
- **Don't distract before GW1** — build post-GW1; manual methods bridge Friday (see below).

---

### ✅ Decision *(owner-approved: gate now, build post-GW1)*

**1. A "Tester activity" roster (who's actually testing).** On the gated **Admin** page (`FPL_ADMIN_KEY`), a
table joining the **`beta_users`** allow-list (the emails the owner owns) to the **account store**: for each
allow-listed email, hash it to its **`user_key`** (`auth.user_key`, sha256) and look up that account's
**`updated_at`** → columns: **email · last active · status** (🟢 active this week · 🟡 dormant · ⚪ never signed
in). This is **owner-only** (the owner already owns the allow-list) and keeps analytics anonymous — the roster is a
*separate* join, not an analytics field.
- **Honest caveat (surface it):** this measures **signed-in + squad-persisted** activity (the account store records
  squad save/sync). A tester who only *browses* signed-out won't appear here — so pair the roster with the
  **anonymous totals** already shown (sessions / returning devices) for the full picture: *named* engaged users +
  *anonymous* overall usage (incl. browse-only).

**2. A "Load & concurrency" health panel (am I hitting limits).** From the existing `events` table:
- **Active now (proxy):** distinct sessions with an event in the **last ~10 min** — a live concurrency read.
- **Peak concurrent:** the max of that over the period (the number to watch at a deadline).
- **Latency:** the **P95** of the `analysis` (decision_xp) + `data_load` perf timers, prominent — the contention
  signal (P95 climbing = the container is stretched).
- A simple **🟢/🟡/🔴 health read** from thresholds (e.g. P95 under/over a budget · peak concurrent under/over a
  soft cap), so "are we near the edge?" is answerable at a glance.

**What this is *not*.** Not a change to the analytics payload (stays anonymous). Not a new table/secret. Not a
`decision_xp` change. Not real-time infra monitoring (that's Streamlit Cloud's "Manage app" + logs — see the
bridge below).

---

### 🔀 Alternatives Considered

- **Put emails/user_keys into analytics events.** Rejected — breaks the anonymity invariant (ADR-100). The roster
  join gets the same answer without it.
- **A third-party APM / uptime tool.** Overkill for a hobby beta; the events table + Cloud logs suffice.
- **Build before GW1.** Rejected — a deploy right before the deadline is the wrong risk; the manual bridge covers
  Friday. *(The owner may pull the concurrency panel forward if they want a polished gauge for the GW1 spike — a
  conscious call, not the default.)*

---

### 🧭 Consequences

**Positive** — answers both owner questions from data already held; keeps analytics anonymous; makes the
"registered vs concurrent" distinction visible so the owner can **add testers confidently and watch the real
limit**; near-free (reads, no new infra).
**Negative / risks (mitigations)** — the roster only sees signed-in/persisted activity (*mitigation:* pair with
anonymous totals + label it); "active in last 10 min" is a proxy, not a true concurrent-connection count
(*mitigation:* it's directional — trend + P95 together are the signal); thresholds for the health read are
heuristic (*mitigation:* calibrate against real GW1 load, like the weight-calibration ethos).

---

### 🧾 Status & follow-ups

- **✅ Built (Sprint 186).** The roster (`web_streamlit/roster.py`, pure) + the load panel
  (`analytics.load_summary`, pure), both rendered on the gated Admin page. Two small readers were needed and
  added: `user_store.all_emails()` and `cloud_store.updated_at_by_handle()` — the latter **batched**, because a
  beta in the tens would otherwise mean tens of round-trips per Admin render. 13 tests. 1265 → **1278**.
- **The `updated_at` check the ADR asked for: it was already there.** The account store is
  `squads(handle, data, updated_at)` and stamps every save, so "when did this tester last persist?" needed no
  new column and no new write.
- **The anonymity boundary is now structural, not a comment.** The roster lives in its own module rather than in
  `analytics.py`, so the anonymous-events code has no idea emails exist. That was the ADR's central constraint
  and it is worth being able to see it in the file layout.
- **Four states, not three.** The spec listed active / dormant / never; the build adds **lapsed** (over 30
  days). A tester who signed in and drifted away is a different problem from one who never arrived, and
  collapsing them hides which of the two you have.
- ✅ **Owner smoke DONE (2026-08-25) — all good.** `FPL_ADMIN_KEY` set, anon SELECT policy on `events` applied,
  both panels read against real data. Until this point everything here was verified pure-function and
  page-renders only; the numbers had never been seen, and now they have. **This also closes ADR-100's
  long-outstanding verification** — the analytics path is confirmed end-to-end in production, not just at the
  write end. The thing to keep half an eye on: if *every* tester ever reads ⚪ never, that is the `user_key`
  hash failing to match the account-store handles rather than a quiet beta.
- **Bridge until then (manual, no build) — how to watch concurrency at the GW1 deadline:** see the runbook note in
  `GW1_RUNBOOK.md` / the owner brief — Streamlit Cloud **Manage app → Logs** (+ watch for "over resources"
  reboots) · the Admin page's **P95 latency** + session counts · tester reports of slowness.
- **Not this ADR:** raising `FPL_USER_CAP` (an owner config change, do anytime) and any paid-host upgrade (a
  separate call if concurrency actually bites).

**Retention signal — the roster supersedes the anonymous metric (added 2026-08-18).** The Admin's anonymous
**"Returning"** count (devices seen on 2+ days, via the `fpl_anon` cookie) is showing **0 with Sessions==Devices**,
i.e. the cookie isn't persisting across visits in prod (a browser cookie-jar issue, same class as Sprint 132/134;
verify with a real browser — logged in `Feedback_Log.md`). **Don't rely on it for retention.** The **tester-activity
roster in this ADR** (signed-in `user_key` + `updated_at`) is the **trustworthy** "who's returning / who's actually
testing" signal — server-side, named, cookie-independent. The anonymous panel stays useful for *usage volume +
error rate* only.
