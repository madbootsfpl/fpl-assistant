# Sprint 154: Help revamp + Boot Battle everywhere + the Explainer (ADR-111)

**Dates:** 2026-08-13
**Status:** 🚧 Planned — US-377…379 (ADR-111)
**Capacity:** ~1–2 sessions (a small feature + a big content rewrite + a glossary)
**Carried Over:** none

> **Direction (ADR-111):** rewrite the Help page (owner's copy), reconciled against the live app; make **⚔️ Boot
> Battle** a real feature (My Squad ⚙ panel + rebrand); add the **MadBoots Explainer** glossary (one expander,
> category subheaders — Ctrl-F-able). Mostly content; the one behaviour add reuses `compare_card_html`.

---

### 🔎 Verified at planning (on the code)

- **Compare renderer exists:** `compare_card_html` / `render_player_compare` (ADR-110); the ⚙ panel already holds
  `fixtures_by_id` + `xp_by_id` for owned players → an ⚙-panel Boot Battle needs only a picker + the renderer.
- **The Players control** is `"🔍 Compare with (same position)"` (`views/players.py render_card`) → rebrand ⚔️.
- **Stale Help copy to fix:** the current `8_Help.py` caption + §7 say *"per-session, no accounts, nothing saved on
  the server"* — **wrong since auth went live** (ADR-106). Manager-ID import is built + GW1-gated (accurate).
- **Streamlit expanders can't nest** → the glossary is one expander with subheaders.

---

### 🎯 Sprint Goal

The Help page reads as the owner's rewrite, every claim true to the live app; ⚔️ Boot Battle works from a player's
card on **both** Players and My Squad; the Explainer glossary is one findable expander — suite green.

#### Success criteria
- [ ] **US-377 (Boot Battle everywhere)** — rebrand the Players compare control **⚔️ Boot Battle**; add a **"⚔️ Boot
      Battle — compare with…"** picker to the My Squad **⚙ panel** (typeable; scoped to **same-position owned**
      players; excludes the picked player) → `render_player_compare(picked, cmp, …)` in place of the single card (the
      👑/🔁 controls still act on the primary player). Reuses `fixtures_by_id`/`xp_by_id` + `compare_card_html` — no
      analytics change. Tests: the ⚙ panel renders the compare card on a Boot Battle pick; the Players control reads
      "Boot Battle".
- [ ] **US-378 (Help rewrite — 8 sections)** — apply the owner's copy: intro + trust line + **Quick start** + "Your
      squad" + a deadline note + the 8 expanders (Build · My Squad · Health · Plan/AI-Tips · Research · Ask ·
      Save/Import · Feedback). **Reconcile:** the Save/Import section → **auth-live** (account save · auto-sync ·
      Download · Upload · Manager-ID from GW1); **remove** the stale *"no accounts / nothing saved server-side"*
      line; describe Boot Battle · Radar · Edge/Risk · per-GW card as they work. **Keep the app's icons** (override
      draft conflicts). Tests: key sections render; the stale no-accounts line is gone; "auto-sync"/account wording
      present.
- [ ] **US-379 (MadBoots Explainer)** — a 9th expander: a glossary with **category subheaders** (⚽ FPL basics · 📊
      Stats · 🎯 Ratings · 🔄 Squad decisions · 🧪 Squad Lab · 🤖 AI & trust), all visible (Ctrl-F). Terms reconciled
      to the app. Test: the Explainer renders with the category headers + sample terms (xP, Boot Battle, Radar).
- [ ] **No drift** — Help is static content; the Boot Battle add is display-only (reuses the renderer); ruff + suite
      green.
- [ ] **Docs + sign-off** — a **content preview** (rendered Help) for owner approval; PROJECT_STATUS; Architecture;
      memory; mark the item shipped in Backlog. ADR-111 already written (the gate).

---

### 🧭 Design sketch

- **US-377:** `views/squads.py render_my_squad` ⚙ panel — after the card, `st.selectbox("⚔️ Boot Battle — compare
  with…", ["—", *same_pos_owned])`; on a pick, `render_player_compare(picked, cmp, a_*/b_* from fixtures_by_id +
  xp_by_id)` instead of `render_player_card`. `views/players.py render_card` — the compare selectbox label → ⚔️.
- **US-378:** rewrite `8_Help.py` — the intro/quick-start/your-squad/deadline + the 8 `st.expander` blocks (owner
  copy, reconciled, app icons).
- **US-379:** a final `st.expander("9 · MadBoots Explainer …")` with `st.subheader` per category + bolded terms.

**DoD:** tests (Boot Battle in both places; Help sections + no-stale-copy; glossary) + a content preview + docs.

**Out of scope (ADR-111):** cloud-LLM narration (P2 strategic); admin usage/logins graphs (P2).

---

### 📋 Sprint Review
*(filled at retro)*

### 🧠 Lessons
*(see `Sprint154_Lessons_Learnt.md` at retro)*
