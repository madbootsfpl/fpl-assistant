# Sprint 152: Wave-3 polish — Boot Battle band + static GW1–3 (ADR-109/110)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-371 + US-372. 981 → 982 tests
**Capacity:** ~½ session (two small display tweaks on shipped features)
**Carried Over:** none

> **Direction:** two pieces of wave-3 tester feedback on just-shipped features (no new ADR — extends ADR-110 and
> ADR-109). **US-371:** give the compare card a MADBOOTS brand band like the single card, titled **"Boot Battle"**.
> **US-372:** the per-GW hover card should show a **static GW1–3** regardless of the "Gameweeks ahead" selector
> (a horizon of 1 was leaving GW2/GW3 at 0.0 after the Total column was dropped).

---

### 🎯 Sprint Goal

The compare card reads **🥾 Boot Battle · Last season**; the per-GW card row always shows GW1–3's real scores
independent of the page horizon — with the suite green.

#### Success criteria
- [x] **US-371 (Boot Battle band)** — add the shared `brand.mark_html()` band to `compare_card_html` (badge +
      two-tone wordmark), titled **"Boot Battle"** + **"Last season"**, between the two headers and the grid; drop the
      grid's now-redundant border-top. Test: the compare card contains "Boot Battle" + "Last season".
- [x] **US-372 (static GW1–3)** — in `render_my_squad`, source the card's per-GW xP from a **fixed 3-GW** view
      (reuse `ranked` when `horizon ≥ 3`; else one extra `decision_xp(horizon=3)`), so the per-GW row is decoupled
      from the "Gameweeks ahead" selector. Test: the selected player's panel-card per-GW cells are identical at
      horizon 1 and horizon 5.
- [x] **No drift** — display-only; no `decision_xp`/analytics change; ruff + suite green (981 → 982).
- [x] **Docs** — PROJECT_STATUS; Architecture; memory. Preview refreshed (Boot Battle band) for owner sign-off.

---

### 📋 Sprint Review

**Delivered — both wave-3 tweaks; display-only, 982 tests, ruff clean.**

- **US-371** — `compare_card_html` gains the brand band (mirrors the single card, ADR-110/355), titled **Boot
  Battle** · Last season; the compare grid's border-top dropped (the band separates). Owner-signed-off on the refreshed
  Artifact preview.
- **US-372** — the per-GW card row (ADR-109) is now **horizon-independent**: it always shows GW1–3's real xP (the
  common `horizon ≥ 3` case reuses the existing compute; `horizon < 3` does one extra `decision_xp(horizon=3)` just
  for the card). Fixes the GW2/GW3 = 0.0 at horizon 1 that the dropped-Total left behind. Both the hover popover and
  the ⚙ panel card benefit (both feed off `fixtures_by_id`).

**Reused, unchanged:** `decision_xp` / the card renderer — no analytics change. DoD: tests + a refreshed preview + docs.

### 🧠 Lessons
*(see `Sprint152_Lessons_Learnt.md`)*
