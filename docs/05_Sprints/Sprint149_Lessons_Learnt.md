# Lessons Learned

**Sprint:** Sprint 149 — The My Squad player-actions panel

**Dates:** 2026-08-12

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Consolidate the scattered My Squad pitch-view controls into **one inline "⚙ Player actions" panel** (ADR-108): a
single owned-player selection → the **full card** + **👑 Make captain** + **🔁 Substitute**, together. Absorb the
card picker + the Substitute expander; bring captain-setting onto the pitch. Work on desktop + phone/tablet; close the
desktop-only-hover mobile gap. **Reuse** `substitute()` / `set_captain()` / the card renderer — no engine change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Consolidation, not new features.** The whole sprint reused existing pure helpers (`substitute`, `set_captain`,
  `render_player_card`) — the work was *re-layout + wiring one selection to all three*, not new analytics. The value
  is UX, the risk is low, because the engine is untouched.
- **Ship a golden-page refactor in two safe steps.** US-365 added the panel (selector → card + captain) while leaving
  the old Substitute expander working (pre-filled off the new selector); US-366 folded substitute in and retired the
  old machinery. Each commit left the app coherent and the suite green — no big-bang rewrite of the most important page.

### New Skills Acquired

- **A selection *is* the pre-fill.** The old flow needed an edge-triggered `_sub_prefill_for` marker to seed the
  Substitute "Bring off" from the card pick — a whole mechanism to sync two independent pickers. Once one selection
  drives everything, that mechanism **deletes itself**: the selected player is simply one side of the swap. Unifying
  the input removed state, it didn't add it.
- **The mobile fix fell out of the consolidation.** We set out to tidy scattered controls; because the panel is native
  `selectbox`+`button` (not a CSS `:hover`), phone/tablet users get the full card for the first time. The cleanest
  version was also the more capable one.

---

# What Went Well ✅

- **Reused every helper** — zero analytics/`decision_xp` change; `substitute()` still gates legal swaps.
- **Green throughout** (972→973) — the two-step split kept each commit shippable; +1 Make-captain test.
- **Deleted machinery** — the `_sub_prefill_for` seed + the two-selectbox `sub_off`/`sub_on` dance are gone; less state.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The golden page is the riskiest to refactor | Many tests exercise `render_my_squad` | Two-step (US-365 add panel; US-366 fold + retire); full suite each step |
| Two directions of substitute | The selected player can be a starter *or* a bench player | Branch on `pid in bench_ids`: starter → pick the bring-on; bench → pick the starter to drop |
| Old Substitute tests asserted retired keys | `sub_off`/`sub_on`/`do_sub` gone | Rewrote both to the panel's `pa_pick`/`pa_sub`/`pa_do_sub`, one per direction |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Unifying inputs | One selection driving N actions removes the sync state N independent pickers needed |
| Static-pitch wall | The pitch stays one `st.markdown` block (no callback); the *panel* is the interaction, the pitch the display |
| Native widgets = mobile | `selectbox`/`button` tap on touch; the only desktop-only thing was the CSS hover — the panel replaces it |

---

# Development Lessons 💻

- Refactor the golden page in shippable steps, not one commit — each step green, each reviewable.
- When you unify a selection, hunt the now-dead sync state (`_sub_prefill_for`) and delete it — don't leave it orphaned.
- After retiring widget keys, `grep tests/` for them — the two Substitute tests keyed off `sub_off`/`sub_on`/`do_sub`.

---

# AI Collaboration Lessons 🤖

- Display/UX only: the read-only invariant + every sanctioned server write are unchanged. The custom **JS
  tap-the-pitch** component was **deliberately deferred** (ADR-108) — the panel is its ~90%-reused foundation, so the
  future component only swaps the *input* (dropdown → tap), not the panel. Feedback-driven, post-GW1.

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-108 — the My Squad player-actions panel.** One inline panel consolidating card · make-captain · substitute,
driven by one selection; Transfer stays separate; the Captain sub-tab keeps its recommendation. Reuses the helpers.
Defers "My Squad v2: tap-the-pitch" (custom JS component) to its own spike + ADR, post-GW1, feedback-driven.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner smoke (once deployed):** on a phone — pick a player → full card; **Make captain** sets the (C); a starter →
  bring a bench player on; a bench pick → bring them on for a starter. Confirm it's tappable end-to-end.
- **Watch the feedback** — if "I want to *tap* the shirt" stays the top ask, that's the green light for the deferred
  **tap-the-pitch** component (its own spike + ADR, post-GW1).
- **Still on the 2026-08-12 intake (`docs/Backlog.md`):** per-GW xP on the pitch (A5 — now ripe); player-card 2-up
  **compare** (UX H — pairs with this panel: "open card → compare with…"); the Squad Lab lab-icon shipped (Branding G).
- **GW1 (2026-08-21, ~9 days):** the dormant-weight calibration remains the data-gated thread (ADR-101).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Two-step a risky refactor: add-the-new-alongside-the-old, then retire — each commit shippable.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -q -k "panel or substitut or captain"   # the golden-page panel
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Player-actions panel | The unified ⚙ panel: one selection → full card + Make captain + Substitute (ADR-108) |
| `pa_pick` / `pa_sub` / `pa_do_sub` | The panel's selector / bring-on-or-off picker / Substitute button keys |
| Tap-the-pitch (deferred) | A future custom JS component so a shirt-tap opens this same panel (post-GW1) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-108-player-actions-panel.md` | The decision + the JS-component deferral (spike + ADR, post-GW1) |
| `src/web_streamlit/views/squads.py` (`render_my_squad`) | The panel — one selection driving card + captain + substitute |

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
