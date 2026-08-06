# Lessons Learned

**Sprint:** Sprint 061 — Finish Phase 6 Tier-1: crowd flags on Captain/Transfer (+ template-risk); trends intent deferred

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Finish **Phase 6 Tier-1**: extend the `crowd_flags` lens to **Captain + Transfer**, add a **template-risk**
captaincy framing, and add a grounded **"trends"** `ask`/`chat` intent — all still a **lens, not xP**
(ADR-057). In practice: shipped the flags (useful now) and **deferred the trends intent to nearer GW1**,
since its momentum data is 0 in preseason.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing a pure helper (`crowd_flags`) across more surfaces with a one-line join per page.
- Judging *when* a feature is worth building vs deferring — matching the build to when its data is live.
- Framing a signal honestly (a template-risk *lens*, not a full EO model).

### New Skills Acquired

- Joining crowd flags onto view rows that don't carry the fields (captain picks / swap summaries) by
  looking them up by id from the full player rows the page already holds.

---

# What Went Well ✅

- **The pure helper paid off again** — Captain + Transfer each needed a single `crowd_flags(...)` join, no
  new logic; the lens is now on every player surface.
- **Deferring US-185 was the right call** — its value is momentum (0 preseason), so building it now would
  ship an empty feature for two weeks. Shipping the useful-now flags and parking the GW1-gated piece kept
  the sprint honest.
- **Phase 6 Tier-1 reached a clean state** — "done bar the GW1-dependent intent," clearly recorded.
- xP stayed untouched (the Sprint-060 invariance test still guards it); display-only throughout.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Captain/Transfer rows lack the crowd fields | The pick/swap **summary** dicts carry only display fields | Join `crowd_flags` by id from the full player rows the page already loads |
| The trends intent would be empty preseason | Its questions are about momentum (0 until GW1) | Defer to a GW1-timed sprint; ship the flags now |
| A `Sprint61.md` table row was missing its Status cell | Authoring slip in the plan | Fixed when marking US-185 deferred |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse over rebuild | A pure row→flags helper composes onto any surface that can produce a player id |
| Build when the data's live | A momentum feature is worth deferring to when its inputs exist (GW1) |
| Honest framing | Call a proxy a lens (template-risk), not the full model (captaincy-% EO) — it manages expectations |
| Join by id | Views with thin summary rows can still show rich signals by looking up the full row |

---

# Development Lessons 💻

- Extend a settled helper rather than duplicating logic per surface.
- Match the build to the data calendar — don't ship a feature that can't be exercised yet.
- Keep display signals off the prediction path; let the invariance test prove it.

---

# AI Collaboration Lessons 🤖

- The owner's split call — "ship US-184 now, defer US-185 to GW1" — matched effort to when value lands.
- Surfacing the preseason-emptiness up front (at planning) made that split an easy, informed decision.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — this sprint executes ADR-057 (Phase 6 Tier-1). US-185's intent design will be settled (or
promoted to ADR-058) when it's built nearer GW1._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 sprint (~2026-08-21):** build **US-185** (the trends `ask`/`chat` intent) on live data; **calibrate**
  `TRENDING_NET` / `FORM_MIN`; confirm the momentum flags/questions populate across the app; pair with
  **Data Hardening** (per-GW history + form). Meanwhile: triage any **tester feedback** (Sprint 059 loop).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep matching build timing to data availability; keep reusing pure helpers across surfaces.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -q    # the Captain/Transfer flag AppTests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Template-risk (captaincy) | An ownership-based lens: a template captain is safe; a differential captain is a rank swing |
| Join by id | Attaching rich signals to thin view rows by looking up the full row by player id |
| GW1-gated | A feature whose data (momentum) only exists once the season starts (2026-08-21) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/crowd.py` | The pure `crowd_flags` helper reused across every player surface |
| Roadmap → Phase 6 | Tier-1 status (lens + template-risk ✅; trends intent 🕓 → GW1) |
| ADR-057 | The lens-not-xP model this sprint executes |

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

- US-184 Crowd flags on Captain + Transfer + a template-risk captaincy caption

**Stories Deferred:**

- US-185 The "trends" `ask`/`chat` intent → nearer GW1 (momentum data is 0 preseason)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
