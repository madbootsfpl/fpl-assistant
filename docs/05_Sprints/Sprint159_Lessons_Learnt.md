# Lessons Learned

**Sprint:** Sprint 159 — "Your team" visibility polish

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Close the visibility gap the Sprint-158 persistence fix exposed. Cross-device sync now works (a tester's iPhone
transfer showed on a refreshed Mac), but they couldn't *see* their team or where Save/backup lived. A prominent,
brand-boxed **"Your team"** status card at the top of My Squad (US-386) makes the team stand out and signposts
backup; two quick wins (US-387) fix the upload copy and name the download after the team.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Self-contained HTML card (ADR-084 pattern).** The banner is one `st.markdown(unsafe_allow_html=True)` string
  with its own scoped `<style>` and the shared `brand.mark_html()` — display-only, no widget plumbing.
- **State detection from the session.** "Is this *your* team vs the demo?" = the shown squad is the session's
  active squad (identity, with a player-ids fallback); "synced" = `auth.is_configured()`. Two booleans drive the
  card and the panel's expand-by-default.

## New Skills Acquired

- **A correct model still needs a legible surface.** The persistence architecture was right after Sprint 158; the
  remaining problem was purely *seeing* it. The fix was a visual card, not more logic — a reminder to treat
  "obvious" as its own deliverable.

---

# What Went Well ✅

- Owner-approved the card via an Artifact mock first, so the build matched the intent on the first pass (one tweak:
  the MADBOOTS mark in the demo state).
- Small, display-only, fully covered (+4 tests → 998, ruff clean); the panel got *tidier* (its status line moved to
  the card), not busier.

# What Was Tricky ⚠️

- Renaming the expander + the upload label broke their exact-string tests — expected; updated in step.
- Keeping the visual chips honest: they're signposts to the panel just below (which auto-expands when it isn't your
  team), not clickable buttons — the panel is the interactive part.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
