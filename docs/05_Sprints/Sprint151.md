# Sprint 151: Compare two players on the card (ADR-110)

**Dates:** 2026-08-12
**Status:** ✅ Complete — US-369 + US-370 (ADR-110). 976 → 981 tests
**Capacity:** ~1 session (a compare renderer + the Players-view wiring; no new xP math)
**Carried Over:** none

> **Direction (ADR-110):** a **same-position, winner-highlighted** two-player comparison on the Players Card view.
> Pick A, then a **🔍 "Compare with"** typeable picker (same-position only) → a merged **A · stat · B** grid with the
> **better value tinted**. Reuses the card's stat catalog + `decision_xp` (xP for all players is already computed) —
> **display-only**.

---

### 🔎 Verified at planning (on the code)

- **The pattern exists:** `render_history` (`views/players.py`) already has a **"Compare with (optional)"** second
  selectbox — mirror it. Streamlit selectboxes **filter as you type** → a 🔍-labelled one *is* the search.
- **xP is free:** `render_card` (`views/players.py:305`) computes `decision_xp` over **all** rows → `xp` keyed by id
  covers any compare target. The target's `fixtures` = one more `_card_fixtures(store, b_team)` read.
- **Same-position aligns:** `_stat_rows`' `order` (in `player_card.py`) is position-keyed + drops `None` → aligned
  rows only for same position. So scope the picker to same position; align by **stat key**.
- **No per-stat winner analytics** (`ask`'s compare gives only an overall xP winner + text) → compute the per-stat
  winner from the card's existing values.

---

### 🎯 Sprint Goal

On the Players Card view: pick A → 🔍 pick a same-position B → a merged comparison with the better value tinted per
stat, from reused data, with the suite green.

#### Success criteria
- [ ] **US-369 (the compare renderer)** — expose `(key, label, raw, formatted)` from the card's per-stat catalog
      (keep `_stat_rows`' external `(label, formatted)` shape). A pure **`compare_rows(a, b)`** → `[(label,
      a_formatted, b_formatted, winner)]` aligning by key, `winner ∈ {"a","b",None}` via a **direction map**
      (higher-better default; `xgc` lower-better; `own` neutral; ties/missing → None). A **`compare_card_html(a, b,
      *, …)`** (two headers with photo·team·pos·£·name·**projected xP** [xP winner tinted]·fixtures + the aligned
      winner-tinted grid), `CARD_CSS` extended, + `render_player_compare(...)`. Deterministic tests: same-position
      alignment; the right winner per direction (incl. `xgc` lower, `own` neutral); a missing stat → `—`, no tint.
- [ ] **US-370 (wire the Players Card view)** — a **🔍 "Compare with (same position)"** selectbox after the player
      picker (options = same-position players, A excluded, `"—"` default); on a pick → `render_player_compare(a, b)`
      in place of the single card (unchanged when `"—"`). Both xP from the existing `xp` dict; B's fixtures via
      `_card_fixtures`. A **preview** for sign-off. Test: picking a compare target renders the compare markup.
- [ ] **No drift** — display-only; no `decision_xp`/analytics change; the single-card path unchanged; ruff + suite green.
- [ ] **Docs** — Help (the compare option); PROJECT_STATUS; Architecture; memory. ADR-110 already written (the gate).

---

### 🧭 Design sketch

```
Players ▸ Card:   Player [ Haaland · MCI ]     🔍 Compare with [ Isak · NEW ]

     Haaland  MCI·FWD  £15.5m            Isak  NEW·FWD  £10.5m
     ◆ 5.7 xP   BOU(H) CRY(A) COV(H)     ◆ 4.9 xP   ...
   ───────────────────────────────────────────────────────────
      ●27      Goals               21
      ●28.2    xG Involvement      19.4
      ●6.8     Points / game       5.9
       74.4    Ownership          31.0        ← neutral (no tint)
      ...      (● = better; xGC lower-is-better)
```

- `player_card.py`: `_stat_catalog(player)` → `{key: (label, raw, formatted)}`; `_stat_rows` reuses it. `compare_rows`
  + `_BETTER` direction map + `compare_card_html` (+ compare CSS in `CARD_CSS`). `render_player_compare` wrapper.
- `views/players.py` `render_card`: the 🔍 same-position picker → `render_player_compare(a, b, …)` vs the single card.

**DoD:** deterministic renderer tests (winner directions, alignment, missing/tie) + an AppTest (compare markup on the
Card view) + a manual smoke / **preview** + docs.

**Out of scope (ADR-110):** cross-position compare; the ⚙ panel "compare with…" (My Squad) — a follow-on.

---

### 📋 Sprint Review

**Delivered — same-position compare on the Players Card view; display-only, 981 tests, ruff clean.**

- **US-369 (the compare renderer)** — refactored the card's stat catalog to `_stat_catalog(player)` → `(key, label,
  raw, formatted)` (`_stat_rows` keeps its `(label, formatted)` shape — existing card tests unmoved). `compare_rows(a,
  b)` aligns by key with a per-stat winner via `_BETTER` (higher-better default; `xgc` lower-better; `own` neutral;
  ties/missing → `—`, no winner). `compare_card_html` / `render_player_compare` — two headers (photo·team·pos·£·name·
  projected-xP-tinted-if-winning·FDR fixtures) + the winner-tinted grid. Dict-safe (accepts `sqlite3.Row`).
- **US-370 (wire the Card view)** — a **🔍 "Compare with (same position)"** picker (searchable — type to filter),
  scoped to same-position players across the whole pool; on a pick → `render_player_compare` in place of the single
  card (`—` → the unchanged single card). Both xP from the existing `xp` dict; the target's fixtures from one extra
  `_card_fixtures` read.

**Reused, unchanged:** the card's stat values + `decision_xp` — **no analytics change**; the single-card path is
byte-identical on "—". **DoD:** ✅ tests (deterministic `compare_rows` winners incl. lower-is-better xGC + neutral
ownership + missing→`—`; the compare card structure; an AppTest on the Card view) · ✅ a manual smoke (real
`sqlite3.Row` players — Haaland vs Thiago winners correct) + an **Artifact preview** (owner sign-off) · ✅ docs (Help;
PROJECT_STATUS; Architecture; memory). **Follow-on:** the ⚙ panel "compare with…" (My Squad, owned 15).

### 🧠 Lessons
*(see `Sprint151_Lessons_Learnt.md`)*
