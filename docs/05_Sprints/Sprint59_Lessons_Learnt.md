# Lessons Learned

**Sprint:** Sprint 059 — Pre-tester polish (imagery consistency + local refresh & freshness) + the feedback loop

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Two **pre-tester polish** adds so the app is consistent and self-service before it's shared, then set up a
**feedback loop**. (1) **Imagery consistency** — the Players/Fixtures photos + badges applied (augmented,
not replacing) across every squad tab. (2) A **local-only data refresh** button + a **"Data as of
\<date\>"** freshness caption on every tab, with the cloud staying read-only. Then a **tester guide** + a
**feedback triage log** (via GitHub Issues) to seed Sprint 060. This sprint also fought (and documented) a
recurring Streamlit Cloud half-synced-deploy glitch.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Keeping a multi-surface UI change DRY (one photo helper + one table renderer for five tabs).
- Protecting an architectural invariant while adding an exception (read-only web + a *narrow* local write).
- Reading deploy logs to separate "our code" from "the platform."

### New Skills Acquired

- `st.column_config.ImageColumn` to render photos/badges in a native dataframe, from one helper.
- Using an app-controlled env var (`FPL_LOCAL`, set by our runner) to distinguish local vs cloud reliably.
- Streamlit Cloud's half-synced-deploy failure mode + its fix (Manage app → ⋮ → Reboot).

---

# What Went Well ✅

- **One helper, five tabs** — `badges.photo_url*` + `tables.render_player_table` made the imagery change
  consistent and small, instead of five bespoke tables.
- **The invariant survived the first web write** — refresh is scoped to *local + the data cache only*, so
  "the cloud is read-only" stayed true; recorded honestly in ADR-056.
- **`FPL_LOCAL` was a clean signal** — our own runner sets it, so "local vs cloud" isn't a fragile guess.
- **Augment, not replace** — adding an image table above each text summary kept all the analysis (totals,
  notes, reasoning) while gaining the visuals.
- Core analytics untouched — all edge work + one config rename.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The live app kept ImportError-ing after pushes | Streamlit Cloud deployed a **half-synced** checkout (new pages, stale `src/` modules) | Reboot from Manage app's ⋮ menu (retry if needed); NOT reboot/requirements-bump alone |
| Chased two wrong causes first | Assumed env cache, then a runtime-dirtied DB | Verified: opening `seed.db` leaves it byte-identical → it's a Cloud sync glitch, not our code |
| A `SyntaxWarning` on `"\<date\>"` in a docstring | Backslash-escape in a normal string | Drop the backslashes (plain `<date>`) |
| Freshness date is approximate on the cloud | DB **mtime** = the deploy/clone date, not the snapshot date | Accept for now; a stored `refreshed_at` is the accurate future fix |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| DRY across surfaces | A shared URL helper + a shared renderer beats N near-identical tables |
| Invariants + exceptions | You can add a write path without breaking "read-only" if you scope it narrowly and record why |
| App-controlled env flags | Set your own flag in your own runner — don't guess the environment |
| Prove, don't assume, on deploy | A file hash before/after told me the DB wasn't the cause; deploy logs named the real one |
| Freshness signals | File mtime is a cheap "as of" proxy; a stored timestamp is the accurate version |

---

# Development Lessons 💻

- Factor the shared helper first, then apply it everywhere — the tabs stay consistent by construction.
- When adding a write to a read-only system, gate it explicitly and document the boundary (ADR).
- On a flaky deploy, verify our artefact is correct (git + a clean import) before touching code.
- Keep captured-vs-fixed honest: a feedback sprint *captures*; fixing is the next sprint.

---

# AI Collaboration Lessons 🤖

- The owner's "augment" call (table *and* summary) preserved the analysis while adding polish — a small
  scope decision that shaped the whole imagery change.
- "Local-only refresh + a date caption" was a crisp constraint that made the ADR-056 design obvious.
- The deploy saga was a reminder to separate *our* correctness (provable) from *platform* behaviour
  (owner-actioned) and to say so plainly rather than keep pushing speculative fixes.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-056 | A **local-only** data-refresh button (gated by `FPL_LOCAL` + a writable non-seed DB, reusing `ingest.refresh`) + a **"Data as of \<date\>"** freshness caption on every tab; the cloud stays read-only (caption only) — the first, narrowly-scoped web write path | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner:** eyeball the imagery locally; share the app + point testers at GitHub Issues; triage into
  `Feedback_Log.md`. **Sprint 060** is driven by that feedback. Candidate follow-ups already visible: a
  stored `refreshed_at` for an accurate freshness date; Path 2 (server-side squad persistence) if
  refresh-loss bites; a multi-swap positional reshape.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep sharing a shared helper across tabs; keep scoping write paths narrowly and recording the boundary.

---

# Key Commands Learned

```text
python -m src.web_streamlit          # local run — sets FPL_LOCAL=1, so the Refresh button appears
# Streamlit Cloud stale/half-synced deploy → Manage app → ⋮ → Reboot app (retry if needed)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `ImageColumn` | A Streamlit dataframe column that renders a URL as an image (photos / badges) |
| Augment (vs replace) | Add the image table *alongside* the text summary, not instead of it |
| `FPL_LOCAL` | Our runner's env flag marking a local run — enables the local-only refresh button |
| Freshness caption | "Data as of \<date\>" from the DB file mtime — how old the snapshot is |
| Half-synced deploy | Cloud updated some files but not others → stale imports; fixed by a reboot |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-056 | The local-refresh / freshness decision (the read-only boundary) |
| `src/web_streamlit/badges.py` + `tables.py` | The one source of image URLs + the shared table renderer |
| `docs/00_Project/Testing_Guide.md` | The tester onboarding + how-to-report |
| Memory: streamlit-cloud-stale-env-gotcha | The half-synced-deploy fix, so we don't re-chase it |

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

- US-179 Imagery consistency (augment) across all squad tabs
- US-180 Local refresh + a "Data as of" freshness caption (ADR-056)
- US-176 Tester guide (GitHub Issues channel)
- US-177 Feedback triage log (template; ongoing intake)
- US-178 Home feedback hint

**Stories Carried Forward:**

- Feedback intake + triage (ongoing) → seeds Sprint 060

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
