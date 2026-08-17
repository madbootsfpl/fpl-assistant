# Sprint 165: Token retro-fit close-out — brand colours single-sourced (US-408)

**Dates:** 2026-08-17
**Status:** ✅ Complete — extends ADR-114/116, display-only (no user-visible change). 1004 → 1005 tests. **The last
UX-audit carry-over — the audit is now fully closed.**

> **The item:** route the remaining hard-coded brand hexes through `brand.py` (drift-proofing). **Verified first:**
> the actual brand-palette drift was **~6 spots, not the audit's "~50"** — the rest are intentional
> component/object colours (dark card surface · pitch turf · countdown slate · context-specific greys) that ADR-114
> already declares fixed. So the honest close-out is small.

---

### 🎯 Delivered (US-408)

- **`brand.token_css_vars()`** — the palette as CSS custom properties (`:root{--mb-purple/--mb-orange/--mb-teal/
  --mb-good/warn/bad …}`), built from the `brand.py` constants and **prepended to each card's CSS block** so the
  vars are always defined where a card renders.
- **Re-pointed the genuinely-shared brand hexes at the tokens:** the **player-card accent teal** (4×
  `#5eead4` → `var(--mb-teal)`) and the **team-banner accent bar** (`#8B2FC9,#FF6A00` → `var(--mb-purple/-orange)`).
  Change a brand colour in `brand.py` now, and these follow.
- **Left intentionally component-specific:** the dark card gradient, the pitch green, the countdown slate,
  dark-mode greys — object colours per ADR-114, *not* drift.
- **Deliberately deferred:** a shared `card_css()` recipe adopted across all 5 cards — high regression risk, zero
  user-visible change; not worth it (especially pre-GW1). Documented in ADR-114.
- **Tests:** +1 (the cards reference `var(--mb-*)`; the hex appears only in the `:root` definition). **1005 total.**

**No user-visible change** — same colours, now single-sourced.

### 🧠 Lessons

- **Verify the size of a cleanup before committing to it.** The audit said "~50 hexes"; the real brand-palette drift
  was 6. Measuring first turned an open-ended refactor into a small, safe change — and avoided a risky full-card
  rewrite right before GW1.
- **Distinguish drift from intent.** A hard-coded hex isn't automatically wrong — the object surfaces are
  deliberately fixed. Tokenise the *shared* colours; leave the component ones (and say so).
