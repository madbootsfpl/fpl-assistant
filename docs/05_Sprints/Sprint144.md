# Sprint 144: Brand polish — tester feedback

**Dates:** 2026-08-11
**Status:** ✅ Complete — US-355 (no new ADR; extends ADR-103/084). 958 → 959 tests
**Capacity:** ~¼ session (three small fixes)
**Carried Over:** none

> **Direction (tester → owner):** three quick brand fixes on the rebrand: (a) the My Squad picker copy; (b) the
> player-card wordmark shows a **space** ("MAD BOOTS"); (c) the **captain card** has no MADBOOTS branding. Owner's
> steer on a 4th (branding the *hover* cards): **skip it** — too much (the compact popover was slimmed in S140,
> there are ~15 on the pitch, and the pitch already sits under MADBOOTS chrome).

---

### 🔎 Verified at planning (on the code)

- **#2 is a bug from US-349.** The card band's brand mark is one `inline-flex` with **`gap:6px`** and **three**
  children (badge · `MAD` span · `BOOTS` span), so the gap also falls **between MAD and BOOTS** → the space the
  tester sees. Fix: wrap MAD+BOOTS in **one** span so the badge↔word gap can't land inside the word.
- **#3 the captain card** (`captain_card.py`) is its own ADR-084-family card but never got the US-349 brand band
  (only `player_card.py` did). It's **theme-aware** (neutral grey bg) — the mark must read on light *and* dark.
- **#1** the picker label is `👤 View a player's card` (`views/squads.py`) — it's *your* squad → `View your player's
  card`.

---

### 🎯 Sprint Goal

Fix the three tester-flagged brand nits, and **DRY the mark** — extract a shared `brand.mark_html()` (badge +
two-tone wordmark, MAD+BOOTS as one flex child) used by both the player-card band and the captain card. Display-only.

#### Success criteria
- [ ] **US-355** — (#1) picker copy → **"View your player's card"**; (#2) a shared **`brand.mark_html()`** (fixes the
      MAD/BOOTS gap) used in the player-card band; (#3) the same mark added to the **captain card** (readable on both
      themes). No new ADR; display-only; existing **958** green; ruff clean.
- [ ] **Docs** — Help/PROJECT_STATUS/Architecture as needed; memory.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-355 | **Brand polish** — picker copy · fix the wordmark gap (shared `mark_html`) · captain-card branding. | Med | ✅ Done | ~¼ session |

---

### ✅ Definition of Done

1. **Tests** — `brand.mark_html()` is one lockup (a single `inline-flex`, so MAD/BOOTS aren't separate flex
   children) with the badge + two-tone wordmark; the player-card band + the captain card both render it; the picker
   reads "View your player's card". **958** green; ruff clean.
2. **Manual smoke** — the card band reads **MADBOOTS** (no gap); the captain card shows the mark on both themes; the
   picker copy.
3. **Docs** — PROJECT_STATUS/Architecture; memory.

---

### 📝 Session Progress Log

- **US-355 (brand polish, 3 fixes)** — (#1) the My Squad picker → **"👤 View your player's card"** (it's your
  squad). (#2) **fixed the MAD/BOOTS gap** by extracting a shared **`brand.mark_html(badge_px, font_px, purple)`** —
  the badge + wordmark as **one** `inline-flex` with **MAD+BOOTS wrapped in a single span**, so the `gap:6px`
  (badge↔word) can't fall *inside* the word (the US-349 band had three flex children → a gap between MAD and BOOTS).
  The player-card band now calls `mark_html` (`PURPLE_LT` on its dark ground). (#3) the **captain card**
  (`captain_card.py`) gains the same mark as a `cc-brand` footer (a top-bordered strip, theme-aware) — it joins the
  player-card brand family. Owner's 4th item (branding the *hover* popovers) **skipped** by steer — too much (slimmed
  compact card · ~15 on the pitch · already under MADBOOTS chrome). **+1 test** (`mark_html` is one lockup / no
  word-gap) + a captain-card mark assertion + updated the picker-label test refs. Display-only. ruff clean.
  **958 → 959.**

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Complete — three tester-flagged brand nits fixed in one story. Display-only; no engine/xP change.

- **#1** picker copy → "View your player's card". **#2** the MAD/BOOTS **gap bug** (a US-349 regression: the band's
  brand mark was one `inline-flex` with three children, so `gap:6px` fell between MAD and BOOTS) — fixed by a shared
  **`brand.mark_html()`** (badge + wordmark as one lockup, MAD+BOOTS in a single span). **#3** the **captain card**
  gains the same mark. **#4** (branding the hover popovers) skipped by owner steer.
- **Bonus:** the mark is now **DRY** — one helper feeds both the player-card band and the captain card.
- **Tests:** 958 → **959** (+1). ruff clean; CI-parity green.
- **Lesson:** a `gap` on a flex container hits **every** child boundary — wrap the parts that must stay together in
  one child. And a new shared helper (`mark_html`) is the moment to fix a duplicated bug once, not twice.
- **Owner smoke:** the band reads MADBOOTS (no gap); the Captain card shows the mark on both themes; the picker copy.
- **Lessons:** `docs/05_Sprints/Sprint144_Lessons_Learnt.md`.
