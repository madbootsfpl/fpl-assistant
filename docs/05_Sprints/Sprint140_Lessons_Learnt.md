# Lessons Learned

**Sprint:** Sprint 140 — Tester-feedback polish + a beta waitlist

**Dates:** 2026-08-10

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Clear the tester-feedback annoyances from the 2026-08-10 intake (price filter · card label · Trending order · Help
copy · the card-hover fit) **and** add a **beta waitlist** — when a registration attempt fails (the cap is **full**
or the invite code is **wrong**), record the email so the owner can invite them later. Owner's steer: *"inc #6 and
use only waitlist #5"* → **one** table capturing **both** cases.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reuse the store pattern for a 4th time** — `waitlist.py` mirrors `cloud_store`/`user_store`/`analytics`:
  derive the table endpoint from `FPL_STORE_URL`'s base, reuse `FPL_STORE_KEY`, **no new secret**.
- **Best-effort, never-blocks writes** — the same shape as the analytics write: try/except-all, off by default,
  a lost row is acceptable but a broken gate is not.

### New Skills Acquired

- **A shared test fake must model the real table boundary.** `_fake_user_store` recorded **any** POST as a
  registration insert. The moment the gate gained a *second* server write (the waitlist, to a different table), the
  fake conflated them and a neighbour test failed. The honest fix was to make the fake **URL-aware** (only a
  `/beta_users` POST records a user) — the fake now reflects the real two-table world, not a one-write assumption.
- **A new write on an existing branch can pollute a pre-existing test.** Adding `waitlist.add(email, "bad_code")`
  to the wrong-code branch routed a POST through the shared `requests` fake and corrupted the admits-test's `rows`.
  A new side effect on a shared path needs the pre-existing tests re-checked, not just new tests added.
- **Capture the email on *both* failure branches, one table, two reasons.** The cap-full and wrong-code cases are
  genuinely one need ("someone wanted in, didn't get in — save the email"); a single `beta_waitlist(email, reason)`
  with `reason ∈ {full, bad_code}` beats two mechanisms. The owner reads `reason` to decide who to invite.

---

# What Went Well ✅

- **Four tester fixes were tiny and real** — verified on the code/real data at planning (Haaland £15.5m was the
  proof for the price cap), each a one-liner, tested where it bites.
- **The card-hover fit** — compact trimmed to 4 stats + a 250px kit-pop + `.pl-card.compact` overrides; the full
  card unchanged.
- **The waitlist reused everything** — endpoint derivation + `clean_email` + the best-effort wrapper; off by
  default, idempotent on the email PK, a real ADR (ADR-102) for the privacy surface.
- 932 → 939 tests (+7); ruff + CI green; display/store-only, no engine change.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A pre-existing gate test broke | the wrong-code branch now POSTs to the waitlist through the shared `requests` fake | Made `_fake_user_store`'s POST fake **URL-aware** (only `/beta_users` records a user) |
| Two tables, one fake | the fake assumed every POST was a registration | Reflect the real boundary — the waitlist writes to a different endpoint |
| Where to record failed-registration emails | a real privacy decision (holds the *non-admitted*, incl. wrong-code) | A short **ADR-102** + an honest posture (owner-only, "remove me = delete the row") |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Test fakes | A shared fake must model the real table boundary, or a new write conflates with an old one |
| Blast radius | A new side effect on a shared branch needs the *existing* tests re-verified, not just new ones |
| Store reuse | A 4th best-effort store slots onto the derive-endpoint/reuse-key pattern — no new secret |
| Privacy surface | Capturing the *non-admitted* (incl. wrong-code) deserves its own ADR + a stated posture |

---

# Development Lessons 💻

- Verify a "quick fix" on real data at planning — the price cap was only obviously right once Haaland's £15.5m
  showed it excluded him.
- When you add a server write to an existing branch, run the *whole* suite — the break was in a test I didn't touch.
- Model the real world in the fake: two tables → two endpoints → a URL-aware fake.

---

# AI Collaboration Lessons 🤖

- The waitlist is the **4th** opt-in, secret-gated server write (after squad-save · registration · analytics). It
  keeps the read-only invariant honest by **naming** its exception: off by default, best-effort, never blocks the
  gate, no new secret. The polish stories are display/config-only — no engine or xP change.

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-102 — the beta waitlist.** On a failed registration (cap **full** or a **wrong invite code**) capture the
email into one `beta_waitlist(email PK, reason ∈ {full, bad_code}, created_at)` table in the existing Supabase
(endpoint derived, **no new secret**), via `waitlist.add(email, reason)` wired into `_registration_gate`'s two
failure branches. Best-effort + never blocks; off by default; privacy posture recorded. US-345/346 = polish, no ADR
(extends ADR-084 for the card fit).

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (enable the waitlist):** create the `beta_waitlist` table (BETA.md §4a) → with `FPL_USER_CAP` set, an
  over-cap or wrong-code attempt lands a row → invite from Supabase → delete the row. Off until the table exists.
- **Owner (browser check):** Players price filter shows Haaland · the card band reads "Last season" · the pitch
  hover card fits (bench kits) · Trending shows 🔥 Top discussions first · Help step 7 mentions ☁ Save/Load.
- **GW1 (2026-08-21):** the big body — `history --backfill` + verify the gated features; ~GW4–6 `calibrate` the
  weights (tooling shipped Sprint 138, `docs/GW1_RUNBOOK.md`).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- After adding a server write to a shared branch, always run the full suite — neighbour tests can break silently.

---

# Key Commands Learned

```text
python -m pytest tests/test_waitlist.py tests/test_web_streamlit.py -q   # the store + the gate wiring
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Beta waitlist | A `beta_waitlist` table capturing failed-registration emails (cap-full / wrong-code) |
| `reason` | `full` (over the cap) or `bad_code` (wrong invite code) — how the owner triages who to invite |
| URL-aware fake | A test fake that branches on the endpoint, so two real tables aren't conflated |
| Best-effort write | A server write wrapped try/except-all — a lost row is fine, a broken gate is not |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/waitlist.py` | The store (`add`/`_endpoint`/`is_configured`) |
| `src/web_streamlit/access.py` (`_registration_gate`) | The two-branch wiring |
| `docs/06_Decisions/ADR-102-beta-waitlist.md` · `docs/BETA.md` §4a | The decision + the owner runbook |

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

- US-345 The polish bundle (price filter cap · card band "Last season" · Trending order · Help ☁ Save/Load)
- US-346 The card hover-popover fit (compact = 4 stats + a 250px kit-pop, no truncation)
- ADR-102 The beta waitlist gate (the failed-registration capture + its privacy posture)
- US-347 `waitlist.py` + the `_registration_gate` wiring (best-effort, off by default, no new secret)

**Stories Carried Forward:**

- None. (Unique per-user invite codes · email verification · an in-app waitlist/roster admin view are backlog ideas.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
