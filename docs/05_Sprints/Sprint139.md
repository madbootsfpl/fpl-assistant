# Sprint 139: A rich player card on the Players tab

**Dates:** 2026-08-09
**Status:** ✅ Complete (US-342/343/344 · no new ADR — extends ADR-084 · retro pending)
**Capacity:** ~¾–1 session (a self-contained HTML card + two wirings; display-only)
**Carried Over:** none

> **Direction (owner):** the FFH "Player Profile" card is a great visual — build our own, in **two places**: (1) a
> **"Card" view** on the Players tab, and (2) **hover / pick a player on the My Squad pitch** → their card. Uses the
> rich data we already have. Owner-approved the preview. **Ship with our data** (Understat's Key Passes /
> Shots-in-Box = backlog; Big Chances is Opta-paywalled, dropped).

---

### 🔎 Verified at planning (on real data + the preview)

- **It's our existing card pattern.** `pitch.py` + `captain_card.py` already render **self-contained HTML/CSS**
  blocks (ADR-084) — theme-neutral, every value `html.escape`d, no JS, `st.markdown(unsafe_allow_html=True)`. A
  player card is a third of the same family; **no new ADR, no dependency, no analytics change**.
- **Our data fills it richly — and adapts per position** (verified on real rows): **FWD** Haaland → Points 239 ·
  Goals 27 · xG 25.5 · xGI 28.17 · ICT 302; **MID** B.Fernandes → Goals 9 · Assists 24 · xGI 23 · DefCon/90 8.43 ·
  ⚽🎯 set-pieces; **DEF** Gabriel → xGC 22.0 · **DefCon/90 9.07** · CBI 239 · Tackles 38; **GK** Raya → xGC 27.6 ·
  Recoveries 304 · CBI 37. So the grid **swaps stat sets by position** rather than showing a striker's stats for a
  keeper.
- **Our differentiators beat FFH's card:** we surface **Projected xP** (`decision_xp`), **Value** (pts/£m),
  **Ownership tier** (💎/⭐/🟦/👑), **DefCon/90**, and **set-piece duty** (⚽🚩🎯) — none of which FFH shows.
- **The header pieces already exist:** `badges.photo_url_by_id` (photo, else club shirt) + `badge_url_by_short_name`
  (the live CDN images the app already renders); `get_upcoming_fixtures(team)` + the stored FDR for the fixture
  pills; the crowd/price/availability flags. Trimmed to **3 fixtures** (owner: keep the pills on one line).
- **The Opta stats are out of scope** — Shots-in-Box / Key Passes need an Understat/FBref fetch (ADR-016 deferred);
  Big Chances is Opta-only (paid). Backlogged, not faked.
- **Pitch hover is de-risked; pitch *click* has a hard Streamlit limit.** `pitch.py` already uses CSS `:hover`
  (`.kit:hover{…}`) in its `st.markdown` blob — so a **hover popover** (a compact card) is a pure-CSS extension, no
  JS, headless-testable. But a **static markdown block can't call back to Python**, so a literal "click the kit →
  Streamlit renders a card" isn't possible without a bespoke component (fragile). The robust, all-device path is a
  **player picker** (selectbox) by the pitch → the full card — which also covers **touch** (no hover on mobile).

---

### 🎯 Sprint Goal

**Objective:** a **rich, position-adaptive player card** — photo · badge · Team·Pos·£price · big name · **3-GW FDR
fixture pills** · a **Projected-xP** hero + ownership/set-piece flags · a two-column stat grid — in **two places**:
a **Card view** on Players, and a **hover popover + picker** on the My Squad pitch. Display-only, self-contained
HTML (ADR-084), fed by data we already hold.

#### Success criteria
- [x] **US-342 (the card renderer)** — `web_streamlit/player_card.py::render_player_card(player, *, team_name,
      photo_url, badge_url, fixtures, projected_xp=None)` → one self-contained HTML block (the pitch/captain
      pattern): a header (photo · badge · **Team · Position · £price** · name) + **FDR pills** (next 3, opp + H/A,
      colour by difficulty) + flags (💎/⭐/🟦/👑 tier · ⚽🚩🎯 set-pieces · 🚑/❓ availability · a **Proj. xP** chip
      when given) + a **position-adaptive** 2-col stat grid via a pure `_stat_rows(player)` (FWD/MID → goals·xGI·
      ICT·assists; DEF → xGC·DefCon/90·CBI·tackles; GK → xGC·recoveries·CBI; all + PPG·Value·Ownership·Minutes).
      Every value `html.escape`d; empty-safe; no JS. Unit/AppTest-covered (the right stats per position; escaping).
- [x] **US-343 (wire into Players)** — a **"Card"** option on the Players `st.segmented_control` → a **player
      selectbox** (scoped by the existing filter) → the card. The view loads the player's team **fixtures** (next 3
      + FDR) + computes **`decision_xp`** for the pool (our Projected xP, wrapped in `analytics.timed`) + reuses
      `photo_url`/`badge_url`. Degrades cleanly (no fixtures → no pills; xP unavailable → no chip). AppTest-covered.
- [x] **US-344 (the My Squad pitch)** — reuse the renderer for a **compact** card on the pitch: a pure-CSS
      **hover popover** per kit (extends the existing `.kit:hover`; absolute-positioned, parent overflow allowed) +
      a **player picker** (selectbox: "👤 View a player's card") above/below the pitch → the **full** card (the
      all-device / touch path). Same self-contained HTML, `html.escape`d, no JS. Degrades (no photo → shirt; no
      xP → no chip). AppTest-covered (the popover HTML per kit; the picker renders a card).
- [ ] **No unintended drift** — display-only; `decision_xp`/analytics unchanged; the server-write posture untouched;
      existing **916** stay green; ruff clean.
- [ ] **Docs** — Help (the new Card view); PROJECT_STATUS; Architecture; Backlog (Understat Key-Passes/Shots-in-Box
      as a deferred idea); a faithful **Artifact preview** already approved.

---

### 🧭 Design sketch

**No new ADR — extends ADR-084** (self-contained HTML cards). The card is a renderer + a Players-tab view; the
engine and the read-only posture are untouched.

**US-342 — `player_card.py`.** Mirrors `captain_card.py`: a module-level HTML/CSS template + a pure builder.
```
def render_player_card(player, *, team_name, photo_url, badge_url, fixtures, projected_xp=None) -> None:
    st.markdown(_card_html(...), unsafe_allow_html=True)     # one self-contained block, html.escape'd, no JS
def _stat_rows(player) -> list[tuple[str, str]]:            # position-adaptive; pure + unit-tested
def _fdr_pill(opp, home, difficulty) -> str                # colour by FDR (green/amber/red), escaped
```
Reuses `crowd.ownership_tier`/`set_piece_flags`/`availability_flag`. The FDR palette matches the Fixtures ticker.

**US-343 — the Players "Card" view.** In `views/players.py` (or the page), a segmented-control option renders a
selectbox (using the shared filter's scoped names) → loads `get_upcoming_fixtures(team)[:3]` + `decision_xp` (pool,
timed) → `render_player_card`. Projected xP is our edge; if the compute is skipped/empty the chip just hides.

**US-344 — the My Squad pitch (two affordances).** (a) **Hover popover** — `render_pitch` embeds a **compact**
`render_player_card(..., compact=True)` per kit inside a `.kit .popover{position:absolute;…}` shown on `.kit:hover`
(a pure-CSS extension of the existing hover-lift; the pitch/kit containers get `overflow:visible` so it isn't
clipped). Desktop only (hover). (b) **Picker** — a `st.selectbox` ("👤 View a player's card") over the squad's 15 →
the **full** card below the pitch; this is the **touch/all-device** path (and the honest answer to "click", since a
static markdown block can't call Streamlit). Both reuse the one renderer; the compact card is a header + ~6 key
stats + fixtures + flags (the full 12–16-stat grid stays the Players-tab view). A quick spike confirms the popover
survives Streamlit's sanitizer + isn't clipped before committing the exact markup.

**Deferred (backlog):** an Understat/FBref fetch for **Key Passes + Shots-in-Box** (ADR-016 revisit — a separate
sprint + a data-source decision); **Big Chances / Big Chances Created** (Opta paid — not planned); a card on other
tabs (Trending / My Squad) if it proves popular.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-342 | **The card renderer** — `player_card.py` (self-contained HTML, position-adaptive stats). | High | ✅ Done | ~⅓ session |
| US-343 | **Wire into the Players tab** — a "Card" view (selectbox → card) + fixtures + Projected xP. | High | ✅ Done | ~⅓ session |
| US-344 | **The My Squad pitch** — a hover popover (compact card) + a player picker → the full card. | Med | ✅ Done | ~⅓ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `_stat_rows` returns the right per-position set (a GK has no goals/xG; a DEF has xGC + DefCon/90;
   a FWD has goals + xGI); the card HTML contains the name/price/stats and is fully `html.escape`d (an injection
   test); empty-safe (missing fixtures/xP → no pills/chip, no crash). The Players **Card** view renders on
   selecting a player (AppTest reads the HTML blob, like the pitch tests). Existing **916** green; ruff clean.
2. **Manual smoke** — Players → Card → pick Haaland / Gabriel / Raya → the card shows the right position stats,
   3 fixture pills, the flags + Projected xP; real photo/badge render (CDN, in the live app). **My Squad** → hover a
   kit → the compact popover; the picker → the full card. No clipping; reads on both themes.
3. **Docs updated** — Help; PROJECT_STATUS; Architecture; Backlog (the Understat idea).

---

### 📝 Session Progress Log

- **US-342 (the card renderer)** — added `web_streamlit/player_card.py`: `player_card_html(player, *, team_name,
  photo_url, badge_url, fixtures, projected_xp, compact)` (pure, empty-safe) + `render_player_card` — **one
  self-contained HTML/CSS block** (the pitch/captain pattern, ADR-084), a **fixed dark surface** that reads on both
  themes, **no JS**, every value `html.escape`d. A pure, position-adaptive **`_stat_rows(player)`** (FWD/MID lead on
  goals/xGI/ICT · DEF on Expected-GC/DefCon-90/CBI/tackles · GK on Expected-GC/recoveries; skips missing → no blank
  rows) + **FDR fixture pills** + flags (ownership tier · set-piece · availability · a **Projected-xP** chip) + a
  **`compact`** variant (no band, ~5 stats) for the pitch popover. **+9 tests** (per-position sets · an
  injection/escaping test · fixtures + FDR colours + xP/flag chips · compact trims · empty-safe). Refreshed the
  **Artifact preview** to the *real* renderer output for FWD/DEF/GK (position-adaptive, real data + Projected xP) —
  matches the approved mock. Display-only; no engine change. ruff clean. **916 → 925.** (US-343 wires the Players
  "Card" view; US-344 the pitch hover popover + picker.)
- **US-343 (the Players "Card" view)** — added a **"Card"** option to the Players `st.segmented_control` (2nd, after
  Pool) → `views.render_card(rows, sel, teams, photos, badges)`: a **player selectbox** scoped by the shared filter
  → `render_player_card` with the team's **next-3 fixtures** (a new `_card_fixtures` helper: opp · H/A · FDR) +
  the real **photo/badge** (`photos`/`badges`) + our **Projected xP** from a lazy, `analytics.timed`-wrapped
  `decision_xp` compute (per selection). Empty-safe (no filter matches → a note; no xP → the chip hides).
  **+1 AppTest** (Card view → the picker + the `pl-card` HTML + brand band render, no exception). *(Fixed a
  mis-placed insertion that split `render_history` — functions now live at the module end.)* Display-only; no
  engine change. ruff clean. **925 → 926.** (US-344 = the My Squad pitch hover popover + picker.)
- **US-344 (the My Squad pitch)** — refactored `player_card.py` to split **`CARD_CSS`** (public) + **`card_body`**
  (CSS-less) so the pitch includes the stylesheet **once** and drops a compact card per kit. `pitch.py`: each kit
  gains a pure-CSS **hover popover** (`.kit:hover .kit-pop` — an absolute-positioned compact card; `.kit`
  `position:relative`, popover `z-index:40`; no clipping since the pitch containers are `overflow:visible`) using
  `card_body(..., compact=True)` with the pitch's own `xp_by_id` as Projected xP. `render_my_squad` gains a **"👤
  View a player's card"** picker → the **full** card (fixtures from `upcoming`, our xP) — the all-device/touch path
  (a static pitch can't call back to Python). Threaded `teams` → friendly team names. **+2 tests** (the pitch
  embeds `kit-pop` popovers with the CSS once; the picker renders the full card); updated the pre-existing
  set-piece test (the hover card now repeats the flags → `>= expected`). Display-only; no engine change. ruff
  clean. **926 → 928.** **Sprint 139 complete — the card lives in both places.**

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony

- **Where it lives — confirmed: both** the Players "Card" view **and** the My Squad pitch (hover popover + a picker
  for touch/click). Just confirming you're OK that **literal "click a kit → card" isn't possible** on a static
  pitch — so the **hover** (desktop) is the pure-CSS win and the **picker** is the reliable tap/click path. (A
  bespoke clickable-pitch component is possible later but fragile — not this sprint.)
- **Projected xP as the hero** — lead with our `decision_xp` number (the FFH-beating differentiator)? *(My rec: yes.)*
- **Which stats lead the grid** per position — happy with the verified sets above, or reorder?
