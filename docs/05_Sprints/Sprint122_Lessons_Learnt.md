# Lessons Learned

**Sprint:** Sprint 122 — Foundations for wider testing (decisions + cheap safeguards)

**Dates:** 2026-08-23

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the owner's five strategy questions (cross-device squads · feedback live · perf metrics · dev/test/prod ·
hobby-vs-product + protect/backup) into **recorded decisions** (ADRs) and **cheap safeguards** shipped now, so
the *next* sprint can open the app to ~20–50 testers against an agreed design. No user-facing feature; the
read-only guardrail held.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Gate a big change as an ADR before building** — persistence is a design record, not a rushed feature.
- **Ship the cheap safeguards, defer the risky build** — LICENSE/backup/feedback now; the first server write later.

### New Skills Acquired

- **Research the current state before advising.** The feedback form was *already built* (ADR-087); the "going
  private" pain was **Community Cloud**, not GitHub. Fifteen minutes of reading turned generic advice into
  concrete, correct answers — the same planning-on-real-data discipline, applied to strategy.
- **"~£0" is the honest headline — the cost is complexity + posture.** Every item (persistence, envs, backup,
  monitoring, protection) lands on a free tier; naming that up front reframed the whole discussion.
- **Inert-by-default is how you add infra safely.** The mirror Action *gates on a secret* and skips when unset —
  so it can live in a public repo / forks with zero CI impact until the owner opts in (the ADR-087 pattern).
- **Name the real risk, don't just build the measurable one.** At 20–50 users the bottleneck is the free tier's
  RAM/idle-sleep, not our ability to measure lag — so the answer is a free uptime monitor + a *recorded*
  escalation, not custom RUM.
- **Design the interface for the deferred upgrade.** The `cloud_store` adapter takes a *handle* now, but is shaped
  so a handle can become an authenticated `st.login()` user id later without re-architecting.

---

# What Went Well ✅

- **Planning-first** caught an already-built feature + the true private-repo blocker.
- **Two clean ADR gates** — the persistence build (Sprint 123) has an agreed design to stand on.
- **Everything opt-in / inert** — no CI, fork, or public-deploy impact until a switch is flipped.
- 775 → 776 tests; ruff + CI-parity green; the read-only guardrail untouched (no server writes landed).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Cross-device needs identity + storage | no accounts wanted | A **handle** (not a login) + a free store; accounts deferred |
| Persistence breaks "no server writes" | the guardrail is a blanket claim | ADR revises it to *one* opt-in, tested, secret-gated write |
| A mirror Action would fail on forks | no secret there | Gate on `MIRROR_URL`; skip cleanly when unset |
| "Going private" felt blocked | it's Community Cloud, not GitHub | Documented the real constraint; public + LICENSE instead |
| Measuring "lag" is hard on Cloud | no native latency telemetry | A free external uptime monitor; name the RAM limit as the real risk |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| ADR-as-gate | Record a big design; build against it next sprint |
| Inert-by-default infra | Secret-gate an Action so it's a no-op until opted in |
| Revise an invariant explicitly | "No writes" → "one named, tested write" — with a test, not a loophole |
| Interface for the upgrade | A handle-keyed adapter that a login can later slot into |
| Honest risk naming | Free-tier RAM, not measurement, is the 20–50-user bottleneck |

---

# Development Lessons 💻

- Read the code + the ADRs before recommending — half the asks were already partly built.
- Add infra opt-in and inert; never make CI or forks depend on a secret they don't have.
- When a new feature breaks an invariant, change the invariant *deliberately and testably*, not silently.

---

# AI Collaboration Lessons 🤖

- The grounded/read-only posture is a *decision*, not an accident — so relaxing it (a server write for
  persistence) is an ADR with a revised, tested guardrail, not an incidental code change.

### Notes _(for Tony)_

---

# Decisions Made 📋

_Two ADRs. **ADR-094** — cross-device persistence via a handle-keyed Supabase store (design gate; build =
Sprint 123); revises the ADR-054 read-only invariant to one opt-in, secret-gated write; native `st.login()`
deferred. **ADR-095** — running a wider beta: a prod/staging two-app split, public + PolyForm Noncommercial
LICENSE, a mirror backup, an external uptime monitor (all ~£0, opt-in). Both extend ADR-053/054/087; no
persistence code shipped this sprint._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Sprint 123 — build ADR-094:** the `cloud_store` Supabase adapter + a My-Squad "☁ Save/Load across devices"
  expander + the **guardrail-test revision** (one named write path, secret-gated) + a privacy / "clear my squad"
  note. Careful with the invariant test.
- **Owner runbook (this beta):** stand up the feedback Sheet + secret; add the uptime monitor; create the mirror
  remote + `MIRROR_URL`; create the staging app off `master` and point prod at `main`.
- **Deferred levers:** native `st.login()`; going private; server-render timing; a paid host (only if the free
  tier struggles); branch protection on `main`.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep gating big/architecture changes as ADRs *before* building; ship the cheap, reversible parts immediately.

---

# Key Commands Learned

```text
git bundle create fpl-$(date +%Y%m%d).bundle --all   # a one-file offline backup of all history
gh secret set MIRROR_URL                              # (owner) wire the mirror; the Action is inert until then
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Design gate (ADR) | An agreed design recorded before any build; the build gates on it |
| Inert-by-default | Infra that no-ops until a secret is set (safe in public repos / forks) |
| Handle-keyed store | Cross-device persistence keyed by a user-chosen handle, not a login |
| Prod/staging split | Two apps off two branches; testers on stable, you iterate on working |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-094-…` / `ADR-095-…` | The two decision gates this sprint recorded |
| `docs/BACKUP.md` | The mirror + `git bundle` backup runbook |
| `docs/BETA.md` (go-live checklist) | The owner's pre-recruit checklist |
| `.github/workflows/mirror.yml` | The secret-gated mirror Action (inert-by-default pattern) |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-094 Cross-device squad persistence — handle-keyed Supabase store (design gate; build = Sprint 123)
- ADR-095 Running a wider beta — prod/staging split, public + PolyForm-NC LICENSE, mirror backup, uptime monitor
- US-305 Safeguard the code — LICENSE (PolyForm-NC) + a secret-gated mirror Action + BACKUP.md
- US-306 Beta go-live enablement — enriched feedback payload (page/version/ts) + BETA/DEPLOY runbooks

**Stories Carried Forward:**

- The persistence **build** → Sprint 123 (gated by ADR-094).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
