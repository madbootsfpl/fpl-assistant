# MADBOOTS — App-wide UX / Style Audit

**Date:** 2026-08-17 · **Method:** four parallel read-only reviewers (squad surfaces · browse/data
surfaces · onboarding/support · brand/style-system), each auditing against the same lenses — interaction
honesty · hierarchy/density · brand consistency · mobile · copy/terminology · accessibility — then synthesised
here. **This is an audit, not a plan.** Each action goes through the normal gate (verify on real data before
building); a few findings are marked *(verify)* where the reviewer may have over- or under-stated.

**The through-line to protect:** *the analytics decide, the AI explains, you make the call.* The costliest
findings are the ones that quietly undercut that promise — controls that **look like they work but don't**.

---

## The six themes (most impactful first)

### 1. Interaction honesty — "looks like it works, but doesn't"  ⚠️ trust risk
This is the same class as the card chips we just fixed (US-388), found elsewhere:
- **[HIGH] Column-header sort silently lies.** `paginate()` slices the list *before* `st.dataframe`, so clicking
  a native column header only re-sorts the **visible page**, not the full result set (Players pool, all stat
  boards, Trending, Set-pieces). → Sort the full ranked list server-side for the active key, or drop native
  header-sort and keep the explicit "Sort by" selectbox as the single source of truth. *(effort: M)*
- **[HIGH] Fixture difficulty is colour-only.** The Fixtures ticker encodes FDR by cell colour with **no digit**
  in the cell → fails colour-blind users; also low-contrast amber. → Put the FDR number in each cell. *(effort: S)*
- **[MED] A dead pointer.** When signed in, `render_cloud_sync` is hidden, yet My Squad still prints "☁ Save/Load
  is now in the sidebar" — pointing at a control that isn't there. → Gate that caption on `not auth.is_configured()`.
  *(effort: S)*
- **[MED] Registration-full dead end.** At the cap, if no `FPL_SIGNUP_URL` is set the user gets a warning and **no
  next action**. → Always offer a mailto/email fallback. *(effort: S)*
- **[LOW/RESOLVED] The Your-team card chips** — fixed in US-388; a repo-wide scan now finds **zero** clickable-
  looking HTML inside `st.markdown`. Keep the guardrail: anything that looks clickable must be a real widget.

### 2. Naming, IA & onboarding clarity
- **[HIGH] "Ask Maddie" reads as a chatbot but is a video list** — and sits near the *real* "Ask" chat, so a
  newcomer hunts for an input that isn't there. → **Keep Maddie**, drop the "Ask" verb: e.g. **"Watch with
  Maddie" / "Video Guides"**; reserve "Ask" for the chat surface. *(effort: S)* — owner call (it's your brand).
- **[HIGH] Home has no single primary action.** The value path (build a squad) is buried in a bullet list; the
  only nudge appears just when the deadline is close. → A persistent primary **"Build your first squad → Squad
  Lab"** above the fold. *(effort: S)*
- **[HIGH] The Feedback page-picker is stale.** `10_Feedback.py` `_PAGES` still lists the pre-ADR-105 "Squads"
  and omits My Squad, Squad Lab, Ask Maddie. → Sync it to the live nav. *(effort: S)*
- **[MED] Sidebar labels don't match the copy.** Docs/captions say "🧪 Squad Lab / 🧩 My Squad"; Streamlit's
  auto-sidebar shows plain filename labels with no icons. → Set explicit page labels/icons, or stop prefixing
  emoji in copy. *(effort: M)*
- **[MED] The mantra is worded ~4 ways** across Home/Help/Ask/Ask-Maddie, separate from `brand.TAGLINE`. → One
  canonical line sourced from `brand.py`. *(effort: S)*
- **[MED] Ask polish** — the default prompt shows the raw token `my-team` (→ "my squad"); answers render in a
  monospace **code block** (→ markdown), which contradicts "plain-English chat". *(effort: S–M)*

### 3. Density & redundancy (My Squad especially)
- **[HIGH] My Squad is a wall of widgets** — banner + backup + import + legal line + 5 metrics + 4 stacked
  captions + pitch + player-actions (selectbox→Boot Battle→card→captain→substitute) + bench caption + reorder +
  Edit/Rename + Transfer expander + Set-bench. Nothing signals *the* primary action. → Group into 2–3 collapsed
  sections (Lineup / Transfers / Manage); lead with the pitch + this-week status; progressive disclosure. *(L)*
- **[HIGH/MED] Overlapping lineup/transfer controls** — Substitute vs "Set the whole bench" vs "Reorder bench" vs
  an in-page **Transfer expander that duplicates the Transfer tab**. → Collapse to one "Change lineup" affordance;
  drop the in-page Transfer expander. *(effort: M)*
- **[MED] Mobile cramping** — a 5-across metric row and the 15-column Players pool + 8-tab sub-nav overflow to
  slivers on a phone. → Fewer columns / wrap; group niche stat boards under one "Stats" entry. *(effort: M)*
- **[MED] Caption walls** — 5+ consecutive grey `st.caption` lines bury the availability signal. → One status
  strip (icons + counts). *(effort: M)*

### 4. Brand & style-system drift  🎨 the foundation
- **[HIGH] Colour is not sourced from the brand.** ~**50 distinct hex values** across `web_streamlit/`, only **4**
  defined in `brand.py`; the hero `PURPLE`/`ORANGE` appear ~2× each outside brand.py. *(effort: L to route
  through tokens)*
- **[HIGH] No semantic good/warn/bad token** — the same concept is reinvented per component (~12 greens, 4 ambers,
  5 reds) and *also* as emoji (🟢🟡🟠🔴) in `ratings.py`. → Define `GOOD/WARN/BAD` (+ tint/fg) once and map FDR,
  captain bands, countdown urgency and rating quintiles onto them. *(effort: M)*
- **[MED] No Streamlit theme** → primary buttons are off-brand **red** (`#FF4B4B`); only 1 of 22 `st.button`s sets
  `type=`. → Set `primaryColor = #8B2FC9` in `.streamlit/config.toml`; adopt "one primary action per view". *(S)*
- **[MED] 5 bespoke card styles** — radii 14/16/18px, three theming strategies (fixed-dark / theme-neutral /
  fixed-light), one-off shadows; they don't read as one family. → One "card recipe" with a light/dark variant.
  *(effort: M)*
- **[MED] Thin brand presence** — most page headers use a bare emoji title; only Home + Ask Maddie carry the
  MADBOOTS mark. → A small `brand.mark_html` lockup on each page header. *(effort: S)*
- **[MED] No type/spacing/radius scale** — one-off font sizes and paddings everywhere. → A small scale in
  `brand.py`. *(effort: M)*

### 5. Accessibility (thread through the above)
- **[MED] State chips fail WCAG AA contrast** — white text on FDR green `#22a559` (~2.6:1) and amber `#c98a1a`
  (~2.7:1); tiny low-contrast countdown labels. → Darken the mid-tints (falls out of the semantic-token work). *(S)*
- **[LOW] Missing alt/text equivalents** — `st.image` brand badges have no alt; emoji-only table cells (Fit/Set/
  Trends) carry meaning only in a separate legend. *(effort: S–M)*

### 6. Consistency nits & copy (lower, but each nicks the polish)
- **[MED] "run `python app.py refresh`"** is shown to *web* users in every empty state — a terminal command they
  can't run. → A user-facing "data refreshing / check back" message. *(effort: S)*
- **[MED] Availability vocab differs** — News uses text ("Out/Injured") + a Chance column; every other surface
  uses emoji Fit flags (⛔🚑❓). → One availability vocabulary. *(effort: S)*
- **[MED] xP absent from the main Players pool** though it's the product's headline metric (and the star of
  Fixtures' Radar). → Surface xP in the pool. *(effort: M)*
- **[LOW]** Set-piece `FORMATS` keys are stale (never match headers); horizon default differs My Squad(1) vs Squad
  Lab(5) silently; "sign in" vs "log in" verb mismatch; stat boards bypass `formats.py`/`column_config`. *(S each)*

---

## The foundation: a lightweight design-token set (proposed for `brand.py`)

Codifying these first makes most of Themes 4–5 mechanical and stops future drift:
- **Brand:** `PURPLE #8B2FC9 · PURPLE_LT #B45CF0 · ORANGE #FF6A00 · INK` — *actually consumed* everywhere.
- **Semantic triad (AA-safe):** `GOOD #1e8047 · WARN #b7791f · BAD #c62828`, each with a `_TINT` (chip bg) and
  `_FG` (text on tint). Retire the ~12/4/5 ad-hoc greens/ambers/reds; map FDR, captain bands, countdown urgency
  and rating quintiles onto these. `ACCENT_TEAL #5eead4` stays the single "projected/winner" highlight.
- **Neutrals:** a 5-step grey ramp (text/muted/line/surface/surface-2) replacing per-card rgba mixes.
- **Scales:** spacing `4/8/12/16/20/24`; radius `SM 10 · MD 14 · LG 18 · PILL 999`.
- **Card recipe:** one function (border/radius/surface/shadow/padding) with a `dark`("objects": player card,
  pitch, countdown) vs `theme-aware`("chrome": captain card, team banner) flag — cards *call* it, not hand-roll.
- **Buttons:** `primaryColor = PURPLE` in config.toml; one primary action per view (`type="primary"`).

---

## Recommended action sequence (each behind the usual gate)

1. **Sprint A — ✅ DONE (Sprint 160):** the owner's smoke-test batch (Home purple callouts + icon bullets +
   de-jargon; "Ask Maddie" → "Maddie Explains"; vibrant Fixtures colours + FDR digit; Help icons) **plus** the
   bundled audit-honesty fixes (dead Save/Load caption, "run refresh" copy, stale Feedback picker). **Still open
   from this theme:** header-sort-vs-pagination (M) and the registration dead-end fallback (S) — carry to a later
   pass.
2. **Sprint B — ✅ DONE (Sprint 161, ADR-114):** tokens in `brand.py` (semantic pairs, FDR scale, neutrals,
   scales, `MANTRA`); the purple `primaryColor`; the AA-contrast chips fixed; the mark on the 4 data-page headers;
   the mantra unified. **Deferred (incremental retro-fit):** the remaining ~50 hexes + all 5 cards → tokens; a
   shared `card_css()`. *(This was the backbone the rest aligns to.)*
3. **Sprint C — ✅ DONE (Sprint 162):** Home primary CTA; Ask → fenced markdown + "my squad"; News availability
   vocab (Fit). *(rename → "Maddie Explains" + empty-state copy done S160.)* **Dropped per owner:** *sidebar icon
   labels* ("leave the sidebar as is").
4. **Sprint D — My Squad density / progressive disclosure** *(largest; needs its own design pass + mock):*
   consolidate the lineup/transfer/captain controls, the metric row and the caption walls.

Threaded throughout: accessibility (contrast, alt) rides on Sprint B's tokens; mobile checks each sprint.
