# Sprint 160: UX Sprint A — brand & copy consistency polish (owner batch, 2026-08-17)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-389–393, display/copy only, **no ADR**. Owner confirmed: keep Radar under Fixtures +
signpost · bundle the audit-honesty fixes. 998 → 1001 tests.
**Capacity:** ~½–1 session

> **Owner batch (2026-08-17), verbatim triage.** Sidebar: *leave as is.* Home: purple callouts · all bullets
> icon-led · de-jargon "squad.json" · **rename "Ask Maddie" → "Maddie Explains"**. Fixtures: colours more vibrant
> (yellow looks brown); Radar — move under Players? Help: consistent (tasteful) icons on the dropdowns.

---

### 🎯 Scope

**US-389 — Home polish.**
- The two callouts ("🧭 New here?", "🧪 Testing this?") render on Streamlit's default **blue** `st.info` — reskin to
  **brand purple** (a small self-contained HTML callout, brand tint) so they read as MADBOOTS, not generic.
- **"Explore the sidebar" bullets — all icon-led.** Today only Squad Lab (🧪) and Ask Maddie (🎥) carry an icon;
  give every bullet its icon (Players 👟 · Fixtures 📅 · My Squad 🧩 · Ask 💬 · News 📰 · Trending 📈 · Help 🧭 …)
  matching the app's established set — consistent, not gratuitous.
- **De-jargon `squad.json`** in Home copy → "a backup file" / "a backup" (keep the literal filename only where it's a
  real file action).

**US-390 — Rename "Ask Maddie" → "Maddie Explains"** (owner decision — keeps the mascot, drops the "Ask" that
implied a chatbot; resolves the audit's naming finding). Rename `pages/9_Ask_Maddie.py` → `9_Maddie_Explains.py`
(so the **sidebar label** updates), page title **"🎥 Maddie Explains"**, the Home teaser + bullet, the Help mention,
and docs (Video_Scripts, PROJECT_STATUS, memory) + the tests that name the page.

**US-391 — Fixtures colours + legibility.** Make the FDR difficulty ramp **more vibrant** (the amber currently reads
brownish, and white-on-amber fails contrast — audit) and **put the FDR number in each cell** so difficulty isn't
colour-only (colour-blind-safe; audit HIGH). One change fixes the owner's "vibrancy" note and the accessibility gap.

**US-392 — Help expander icon consistency.** Give every Help section title a **consistent, tasteful icon** (some have
one, some don't) — adds a little interest without crowding; skip an icon where it'd add no value.

**Answered / owner call (not built this sprint):** *Radar selection* = 6 easiest-run teams × top-3 by xP (≤18).
*Move Radar under Players?* — recommend keep the lens under Fixtures (it's fixtures-derived) + add a Players
signpost; gate separately if the owner wants the full move.

**Optional add-ons (cheap audit-honesty items, only if owner wants them bundled):** gate the dead "☁ Save/Load is in
the sidebar" caption on `not auth.is_configured()`; refresh the stale Feedback page-picker (`_PAGES`); replace the
"run `python app.py refresh`" empty-state copy for web users.

---

### ✅ Definition of Done
1. **Tests:** Home callouts render (purple HTML present) + bullets carry icons; the page renumber/rename holds
   (page list, emoji map, Home-teaser link → Maddie Explains); Fixtures cells show the FDR digit; Help titles carry
   icons. Update the ~handful of tests that name `9_Ask_Maddie` / "Ask Maddie".
2. **Manual smoke** (owner): Home callouts are purple + every bullet has its icon; the tab reads "Maddie Explains";
   Fixtures colours pop + show the number; Help sections are consistently icon-led.
3. **Docs:** this plan + retro; PROJECT_STATUS; Feedback_Log (this batch); memory; the Maddie rename swept through
   Video_Scripts + Help.

### 📋 Sprint Review

**Delivered — the owner's smoke-test batch + the cheap audit-honesty fixes, all display/copy.**
- **US-389 Home:** brand-purple callouts (self-contained HTML, was default-blue `st.info`); every "Explore the
  sidebar" bullet icon-led; "squad.json" → "a backup".
- **US-390 "Ask Maddie" → "🎥 Maddie Explains":** `git mv 9_Ask_Maddie.py → 9_Maddie_Explains.py` (so the sidebar
  label follows), title/config/boot, Home teaser, BETA §6, `maddie.py` docstring, tests. Historical ADR-112/
  Sprint-157 keep the old name (record).
- **US-391 Fixtures:** vibrant FDR ramp (brownish `#b7791f` → gold `#f9a825`) with a per-band **text colour** that
  clears contrast, and the **difficulty digit in every cell** (colour-blind-safe). A **Radar signpost on Players**
  (kept the lens under Fixtures per the owner).
- **US-392 Help:** a consistent leading icon on all nine dropdown sections (+ "MadBoots" → "MADBOOTS" casing).
- **US-393 bundled honesty fixes:** removed the dead "☁ Save/Load in the sidebar" caption (also dropped the now-
  unused `cloud_store` import); synced the stale Feedback page-picker to the live nav; replaced "run `python app.py
  refresh`" empty-states with "it's refreshing; check back shortly".
- **+3 tests** (Home callouts+icons · Feedback picker · Fixtures digit legend) + the rename swept through the
  page-list/emoji/title/teaser tests. **1001 total.**

**Owner smoke (post-deploy):** Home callouts purple + every bullet iconed; the tab reads "Maddie Explains";
Fixtures colours pop and show the number; Help sections consistently icon-led; the Feedback "which page?" list is
current.

### 🧠 Lessons

- **A UX audit pays for itself fastest on the cheap "honesty" items.** The dead caption, stale picker and terminal-
  command empty-states were tiny but each quietly broke the "shows its working" promise — bundling them with the
  owner's visual batch cost almost nothing.
- **Rename via the filename when the sidebar is filename-derived.** Streamlit's auto-nav labels come from the page
  filename, so "Ask Maddie → Maddie Explains" *had* to `git mv` the file; a title-only change would have left the
  sidebar stale. Keep historical ADR/sprint names as-is — rename the live surface, not the record.
- **Contrast is a colour *pair*, not a colour.** Making the FDR ramp "more vibrant" only worked because each band
  also got a text colour (dark ink on the gold/light-greens, white on the dark/red) — vibrancy alone would have
  kept failing AA. This is the pattern the Sprint-B semantic token should encode.
- **De-jargon at the surface, keep precision underneath.** "squad.json" → "a backup" for users on Home, while the
  literal filename stays where it's a real file action — plain words out front, accuracy in the detail.
