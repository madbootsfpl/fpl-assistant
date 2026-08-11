# Sprint 141: MAD BOOTS — the rebrand (visible surfaces, accent approach)

**Dates:** 2026-08-10
**Status:** 🚧 In progress — **ADR-103 Accepted**; badge art sorted (`madboots.png`, transparent, owner-approved via
the real-badge preview); name settled as **MADBOOTS** (one word — the colour split carries the word-break). Building
US-348 → US-350.
**Capacity:** ~1 session (a display-name swap · an SVG badge + a wordmark · a footer + live-doc rebrand)
**Carried Over:** none

> **Direction (owner):** rename the product from **FPL Assistant** to **MAD BOOTS** — a distinctive brand for a
> crowded space (`madboots.com` secured). Owner's two locked calls: **theme approach B** (fold the marks in as
> **accents** on the existing light/theme-aware app — *not* a dark reskin; that's deferred) and **casing** =
> **"MAD BOOTS"** for the display wordmark / **madboots** (lowercase, one word) for the domain + technical id.
> Tagline: **"Fantasy Football, Calculated."**

---

### 🔎 Verified at planning (on the code)

- **The visible name lives in ~19 `src/` spots** — every page-title/browser-tab (`… · FPL Assistant`), the Home
  header (`st.title("⚽ FPL Assistant")`), the **beta-gate** title ×2 (`_code_gate` + `_registration_gate`), the
  **player-card brand band** (`player_card.py:155`), the feedback subject, and the FastAPI `title=`. All are simple
  string/`st.markdown` swaps — **no engine touch**.
- **The favicon is `page_icon="⚽"` on all ~10 pages.** Streamlit 1.61.1's `page_icon` takes an **emoji or an image
  path** — so the **MB badge** can become the real browser-tab icon. (Verify at build time whether it wants a PNG vs.
  an SVG; rasterise a PNG fallback if so.)
- **No `assets/` dir exists yet** — I'll add `src/web_streamlit/assets/` for the badge (+ a later hero PNG).
- **The mark is a *system*, not one logo** (from the sheet): the **MB hexagon badge** = favicon / small mark; the
  **"MAD BOOTS" wordmark** = headers; the **full boots illustration** = a big hero (asset-gated — needs a clean
  transparent export; **deferred** so the sprint ships without it).
- **Keep the internal identity** — `pyproject` name `fpl-assistant`, the repo, the `fpl-assistant.streamlit.app`
  URL, and the **14 `FPL_*` secrets** stay (users never see them; renaming `FPL_*` would break every live deploy
  secret). Only the *visible* surfaces rebrand. *(The two borderline near-invisible ids — `USER_AGENT`, the CLI
  `prog=` — are a "For Tony" call below.)*
- **Don't rewrite history** — live/user-facing docs (README, PROJECT_STATUS header, Help, BETA pitch) rebrand;
  historical **ADRs + sprint logs** keep "FPL Assistant" as the record of what it was called then.

---

### 🎯 Sprint Goal

**Objective:** rebrand the product to **MAD BOOTS** across every surface a user sees — the wordmark, the tagline
**"Fantasy Football, Calculated."**, and the **MB badge** as the favicon + small mark — folded in as **accents** on
the current light/theme-aware app (approach B), with a single **`brand.py`** source of truth. No engine/xP change;
internal package + `FPL_*` secrets unchanged.

#### Success criteria
- [ ] **ADR-103 (the gate)** — record the **brand identity**: the name (**MAD BOOTS** display / **madboots**
      technical+domain), the tagline, the **mark system** (badge→small, wordmark→headers, illustration→hero), theme
      **approach B** (accents on the light app; a dark reskin is **deferred, approach A**), **keep** the internal
      `fpl-assistant` package + `FPL_*` secrets, a **not-affiliated** disclaimer, and the deferred set (approach A,
      a designer vector redraw, the `madboots.com` landing, an email/domain migration).
- [ ] **US-348 (display swap + tagline)** — swap the ~19 visible **"FPL Assistant" → "MAD BOOTS"** (page titles/
      tabs · Home header · beta gate ×2 · feedback subject · FastAPI title · card band) and place the **tagline** in
      the Home hero + the beta gate. Tests assert the new brand on the page config/titles, the gate, and the card
      band; **no stray "FPL Assistant"** left in `src/` (a guard test).
- [ ] **US-349 (badge + wordmark, one source of truth)** — a pure **`web_streamlit/brand.py`** (`NAME`, `TAGLINE`,
      the wordmark HTML, the badge asset path / inline SVG); the **MB hexagon badge** rebuilt as clean **SVG** in
      `assets/`, wired as `page_icon` on **all** pages (a crisp favicon at any size); the **"MAD BOOTS"** two-tone
      (purple/orange) wordmark rendered via CSS in the **Home header** + the **card brand band** (crisp, no image
      dependency). Tests: `brand.py` is pure/importable and returns the wordmark/tagline; every page's `page_icon`
      is the badge.
- [ ] **US-350 (disclaimer + live-doc rebrand)** — a quiet **"MAD BOOTS is not affiliated with the Premier League
      or the official Fantasy Premier League game"** footer/caption; rebrand **live** docs (README · PROJECT_STATUS
      header · Help · BETA pitch); historical ADRs/sprint logs left as the record. A test the disclaimer renders.
- [ ] **No unintended drift** — display/asset-only; the one-xP + read-only invariants hold; internal package +
      `FPL_*` secrets unchanged; existing **939** stay green; ruff clean.
- [ ] **Docs** — ADR-103 + index; the live-doc rebrand; PROJECT_STATUS; Architecture; Help; BETA; memory.

---

### 🧭 Design sketch

**`brand.py` (the single source of truth).** Constants + tiny helpers so the name/tagline/mark live in **one**
place (swap once, everywhere follows):
```python
NAME = "MAD BOOTS"; TAGLINE = "Fantasy Football, Calculated."
BADGE = "assets/madboots-badge.svg"          # the MB hexagon → page_icon
def wordmark_html(...) -> str: ...            # the two-tone "MAD BOOTS" CSS wordmark (headers)
def page_config(page: str) -> dict: ...       # {"page_title": f"{page} · {NAME}", "page_icon": BADGE, "layout": "wide"}
```
Each page's `st.set_page_config(**brand.page_config("Players"))`; Home + the card band render `brand.wordmark_html()`
+ the tagline. **The MB badge as SVG** — a hexagon, `MB` monogram, the brand palette (electric purple `#8B2FC9` /
acid green `#86D91E` / vivid orange `#FF6A00` / ink `#17131F` / white), sampled to match the sheet — scales from a
16px favicon to the card band without mush. **Approach B:** accents only — the existing light/theme-aware surfaces,
palette, and layout are unchanged; the brand shows as the favicon, the header wordmark, the tagline, and the card
band. **The illustration hero is deferred** (needs the transparent export) — Home leads with the wordmark+badge hero
until it lands.

**Deferred (backlog / owner):** approach **A** (a dark brand reskin); a **designer vector redraw** of the AI mark;
the **full boots illustration** hero (pending a clean transparent PNG); the **`madboots.com`** landing page + a
redirect to the app; an **email/domain** migration (`fpl.assistant@proton.me` → `hello@madboots.com`); renaming the
package/repo/`FPL_*` secrets (**not** planned — invisible, high-risk).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-103 | **The MADBOOTS brand identity** — name/tagline/marks/theme-B/keep-internal/disclaimer. | High | ✅ Done | gate |
| US-348 | **Display swap + tagline** — ~19 visible surfaces `FPL Assistant → MADBOOTS`. | High | ✅ Done | ~⅓ session |
| US-349 | **Badge + wordmark** — `brand.py` + the MB SVG favicon + the CSS wordmark. | High | ⬜ To do | ~⅓ session |
| US-350 | **Disclaimer + live-doc rebrand** — not-affiliated line + README/Help/BETA. | Med | ⬜ To do | ~¼ session |

---

### 🧑‍💻 Owner runbook actions (you)

1. **Sign off the Artifact preview** (published at the gate) — the rebranded Home header, beta gate, and card band
   with the MB badge + MAD BOOTS wordmark + tagline, on the light theme.
2. **Send a clean transparent PNG** of the boots illustration (and ideally the badge) when you can → unlocks the
   illustration hero (a fast follow).
3. **Later (not this sprint):** point `madboots.com` at the app (redirect or a landing page); optionally set a
   `hello@madboots.com` inbox + `FPL_FEEDBACK_EMAIL`.

---

### ✅ Definition of Done

1. **Tests** — the new brand shows on the page config/titles, the beta gate, and the card band; **no stray "FPL
   Assistant"** in `src/`; `brand.py` is pure + returns the wordmark/tagline; every page's `page_icon` is the badge;
   the disclaimer renders. Existing **939** green; ruff clean.
2. **Manual smoke** — the browser tab shows the **MB badge favicon**; Home leads with the **MAD BOOTS** wordmark +
   the tagline; the beta gate + card band are rebranded; both light/dark themes read.
3. **Docs** — ADR-103 + index; live-doc rebrand; PROJECT_STATUS; Architecture; Help; BETA; memory.

---

### 📝 Session Progress Log

- **ADR-103 (the gate)** — wrote `docs/06_Decisions/ADR-103-madboots-brand-identity.md` (Accepted) + indexed it.
  Records the identity: **MADBOOTS** (one word — the two-tone colour split carries the word-break) · tagline
  *Fantasy Football, Calculated.* · the **mark system** (badge = favicon/small, CSS wordmark = headers, illustration
  = a deferred hero) · **approach B** (accents on the light app; a dark reskin deferred) · **keep** the internal
  `fpl-assistant` package + `FPL_*` secrets (only `USER_AGENT`/CLI `prog` flip) · a **not-affiliated** disclaimer ·
  honest AI-origin/raster-PNG notes. Owner-approved via a real-badge Artifact preview. **103 ADRs.**
- **US-348 (display swap + tagline)** — new **`web_streamlit/brand.py`** as the single source of truth (`NAME =
  "MADBOOTS"`, `TAGLINE`, a pure `page_config(page)` helper) — *(brought forward from US-349's scope so the swap
  isn't ~19 hardcodes; US-349 grows it with the badge favicon + the CSS wordmark)*. Swapped every visible **"FPL
  Assistant" → "MADBOOTS"**: all ~10 pages' `st.set_page_config(**brand.page_config("…"))` (browser-tab titles), the
  Home header (`⚽ {NAME}` + the **tagline** caption), the beta gate ×2 (title + tagline), the player-card brand
  band, the feedback subject (`feedback.py` + `8_Feedback.py`), the FastAPI title + `web/templates/base.html`. The
  two borderline near-visible ids flipped to the brand: **`USER_AGENT`** (`fpl-assistant/0.1` → `madboots/0.1`) and
  the **CLI `prog`** (`fpl-assistant` → `madboots`); the package/repo + `FPL_*` secrets unchanged. **+3 tests**
  (`test_brand.py`: the constants · `page_config` titles/layout · a **guard** that no `"FPL Assistant"` remains in
  `src/` `.py`/`.html`) + updated the feedback/analytics/web/access assertions to the new name. ruff clean.
  **952 → 955.** (US-349 next: the badge favicon on every page + the two-tone CSS wordmark.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony — confirm before I gate ADR-103

1. **Home hero** — ship the **wordmark + badge** hero **now**, and add the **full boots illustration** as a fast
   follow when you send a clean transparent PNG? *(My rec: yes — don't block the rebrand on the asset.)*
2. **The two borderline internal ids** — also flip **`USER_AGENT`** (`fpl-assistant/0.1` → `madboots/0.1`, the
   courtesy string we send FPL's API) and the **CLI `prog`** (`fpl-assistant` → `madboots`, what CLI users see) to
   the brand, while **keeping** the package/repo/`FPL_*` secrets? *(My rec: yes — cheap, brand-consistent, low risk.)*
3. **Docs scope** — rebrand **live/user-facing** docs to MAD BOOTS and **leave historical ADRs + sprint logs**
   unchanged (they record what it was called then)? *(My rec: yes — don't rewrite the record.)*
4. **Tagline** — exactly **"Fantasy Football, Calculated."** (title-case, that comma + full stop)? *(As on the sheet.)*
