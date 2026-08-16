# Lessons Learned

**Sprint:** Sprint 158 — One account-backed team (unified "Your Team" persistence)

**Dates:** 2026-08-16

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Fix a frustrating persistence bug and consolidate the squad-management UX (ADR-113). A team loaded via the manual
**☁ Save/Load** reverted on refresh (an uploaded json persisted), and **Upload · Save · Manager-ID · Save/Load**
felt like four separate tools. Root cause: two cloud stores — the **account** (`user_key`, ADR-106) vs the manual
**handle** (ADR-094) — fought over one squad. Fix: the **account is the store** when signed in (US-384, fix-first);
retire the handle UI to a no-login fallback; one inline **"Your team"** panel — import · backup · sync (US-385).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Diagnose the whole flow before editing.** The bug lived in the *interaction* of two ADRs, not in one function —
  tracing gate → `link_and_restore` → `_autosync` → `_CLOUD_LINKED` on a refresh revealed that the manual handle was
  the single divergent write. A symptom-level patch would have missed it.
- **Reuse the seam.** The panel's Manager-ID/upload/download logic moved wholesale from the sidebar into one
  function; the persistence guarantee came free because every path already routes through `set_active_squad`.

## New Skills Acquired

- **Sunset a superseded layer, don't stack on it.** Once auth made per-user persistence the real store, the
  pre-login handle store earned removal (in signed-in mode) — that single deletion fixed both the bug and the
  "four tools" confusion. New capability: recognising when the right move is *less* surface, not more.
- **Harness limits shape the UI.** `st.page_link` to a sibling page raises `KeyError: 'url_pathname'` in AppTest
  bare mode (works at runtime); a text caption is the robust choice for an in-view pointer.

---

# What Went Well ✅

- Fix-first shipped relief for the exact reported bug (US-384), fully test-covered, before the larger UX change.
- The consolidation was mostly *moving* existing, working controls into one place — low risk, +net-zero test count
  (a repurposed test), 994 green, ruff clean.
- Owner-approved the panel via an Artifact mock before deploy (the usual visual sign-off loop).

# What Was Tricky ⚠️

- `st.page_link` broke the whole My Squad page in AppTest — caught immediately by the suite, swapped to a caption.
- Two persistence systems meant the fix had to be *surgical* (auth-mode gate) to avoid disturbing the no-login
  fallback (pinned by the existing cloud tests staying green).

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
