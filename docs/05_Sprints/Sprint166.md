# Sprint 166: Review-fixes batch (owner detailed review, 2026-08-17)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-401b (review batch), display/copy + small features, no ADR. 1005 → 1004 tests.
Shipped in 2 parts + a banner hotfix. **Radar watchlist (owner: before GW1) → Sprint 167 (spec next).**

> **Trigger:** owner's detailed post-reboot review. Also fixed the **theme regression** (`[theme] primaryColor`
> pinned light-only — reverted) and the **banner regression** (S165 token_css_vars' 2nd `<style>` block broke the
> purple card — reverted).

---

### 🎯 Delivered

**Part 1 (`d4fdccc`)**
- **MADBOOTS mark on all 6 headers** that lacked it (My Squad · Squad Lab · Ask · Help · Feedback · Admin) —
  consistent with the data pages.
- **FDR colours mirror the official FPL app** (deep-green → bright-green → **grey** → red → maroon) — calmer +
  familiar; one token (`brand.FDR_STYLE`) so Fixtures + the card pills update together. (Was the vibrant ramp.)
- **Captions rewritten:** Players (fuller stat list), My Squad (health/AI-tips/captain/transfers/chips/1–5 GW),
  Squad Lab (+ "a free hit or a total revamp").

**Part 2 (`0ca961c`)**
- **Home:** one highlighted **"get started"** box — a purple **CTA button** (links to Squad Lab via its page slug,
  same tab) with the **New-here / Maddie / Testing nudges consolidated** (were three separate callouts); the **Demo**
  bullet gets a 👀 icon.
- **News:** the shared filter (**Team · Position · Player**) + a **"My squad only"** scope.
- **Trending:** a **"My squad only"** scope on its filter.
- `filters.py`: `filter_controls` gains an optional `my_squad_ids` → a "My squad only" checkbox; `apply()` scopes.
- **Help:** §1 (Build) body bullets get icons, consistent with the other sections.

**Fixes en route:** the theme revert (`95a22be`) + the banner revert (`3e3562b`, with a regression test).

**Decisions (owner):** ① highlight the Build CTA ✓ · ② keep "Fixtures" (the "add real upcoming fixtures" idea
**parked**) · ③ Radar watchlist → **do before GW1** (Sprint 167).

### 🧠 Lessons

- **A "close-out" refactor with no user benefit isn't free.** The token retro-fit (S165) broke the banner via a
  2nd `<style>` block — reverted. Cosmetic drift-proofing wasn't worth a rendering risk (twice now: theme + banner).
- **`config.toml [theme]` pins the theme** (forces light, drops the toggle). Don't set it; keep brand colour in the
  cards, not the widget theme.
- **Consolidate callouts, one clear CTA.** Home's three separate nudges + a plain link → one purple box with a
  highlighted button reads far better as a first-run surface.
