# Architectural Decision Record: The MADBOOTS brand identity

**Decision ID:** ADR-103
**Date:** 2026-08-11
**Status:** Accepted
**Superseded By / Replaces:** Establishes the product's **brand identity** and renames its **user-facing** surfaces
from **"FPL Assistant"** → **"MADBOOTS"**. Display/asset-only — **no change** to the analytics/decision core, the
one-xP metric (ADR-041), or the read-only web guardrail (ADR-053/054). Extends the web edge (ADR-050/084).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The working name **"FPL Assistant"** is descriptive and undifferentiated — the FPL-tools space is crowded with
"FPL / Fantasy / Assistant / Hub" names. The owner has chosen a distinctive brand, **MADBOOTS**, and secured
**`madboots.com`** + **`@madbootsfpl`** across socials + GitHub. Tagline: **"Fantasy Football, Calculated."** — it
names what the product *is* (the maths: `decision_xp`, the optimiser, grounded answers) and counterbalances the
brand's playful chaos.

**The mark journey (verified on real artefacts, not assumed):**
- An AI-generated (Gemini) sheet produced a rich **grinning-boots mascot** + an **MB hexagon badge**. The detailed
  mascot **does not survive shrinking** to an icon (traced favicons lost the teeth / muddied the colours) — a
  detailed illustration and a small icon are **two different jobs**.
- After several trace attempts (Inkscape greyscale/colour, background-merge problems), the owner produced a **clean,
  crisp, transparent PNG badge** (`madboots.png`, background removed) that reads on **both** light and dark and holds
  to **~32px**. A faithful **Artifact preview** with this real badge in the Home header / beta gate / card band was
  **owner-approved** before any wiring.

**Verified at planning (on the code):**
- The visible name lives in **~19 `src/` spots** (page titles/tabs, Home header, beta gate ×2, the player-card brand
  band, the feedback subject, the FastAPI title) — all simple string / `st.markdown` swaps, **no engine touch**.
- The favicon is `page_icon="⚽"` on all ~10 pages; Streamlit 1.61.1's `page_icon` takes an **image path**, so the
  badge can be the real tab icon.
- The **14 `FPL_*` secrets** and the `fpl-assistant` package/repo are **invisible plumbing** — renaming `FPL_*`
  would break every live Streamlit/Supabase deploy secret for zero user benefit.

#### Decision Drivers
- **Stand out** in a crowded space with an ownable, non-descriptive brand.
- **Ship visible value, avoid invisible risk** — rebrand what users see; leave internal names + secrets alone.
- **A mark that renders** — a simple badge for small/favicon; the rich illustration reserved for big surfaces.
- **Accents, not a reskin** — fold the brand into the *current* light/theme-aware app; don't destabilise the UI.
- **Honest sourcing + legal hygiene** — an AI-origin mark (redraw is a later upgrade), and a not-affiliated
  disclaimer now that the product carries a *name*.

---

### ✅ Decision

**Adopt MADBOOTS as the product brand and rebrand every user-facing surface, folding the mark in as accents on the
current light/theme-aware app — while keeping the internal package, repo, and `FPL_*` secrets unchanged.**

**1. Name & casing.** **"MADBOOTS"** — **one word** — is the display name/wordmark; **madboots** (lowercase) is the
domain/handle/technical identifier. The wordmark is **two-tone** (MAD purple · BOOTS orange), so the **colour split
carries the word-break** — no literal space is needed, and one word matches the one-word `madboots.com` /
`@madbootsfpl`. Tagline: **"Fantasy Football, Calculated."** (title-case, that comma + full stop). A single
**`web_streamlit/brand.py`** holds these as the one source of truth (`NAME = "MADBOOTS"`, `TAGLINE`, the wordmark
HTML, a `page_config()` helper).

**2. The mark system (three marks, different jobs).**
- **The badge** (`madboots.png`, transparent) = the **favicon** (`page_icon` on every page) + the **small mark** in
  the Home header and the player-card brand band. Copied into `src/web_streamlit/assets/` (padded to a square for a
  clean favicon).
- **The "MADBOOTS" wordmark** = headers, rendered as **CSS text** — **one word, two-tone** (MAD purple · BOOTS
  orange, the colour split doing the word-break) — no image dependency, crisp at any size. A designer/exported
  wordmark can replace it later.
- **The boots illustration** = a **big hero only** (landing / splash) — **deferred**, a separate transparent asset.

**3. Theme — approach B (accents, not a reskin).** The brand shows as the favicon, the header, the tagline, and the
card band on the **existing light / theme-aware** surfaces; palette, layout, and components are unchanged. A full
**dark brand reskin (approach A) is deferred** — a deliberate later choice, not this sprint.

**4. Keep the internal identity.** The `fpl-assistant` package name, the GitHub repo, the `*.streamlit.app` URL, and
the **14 `FPL_*` secrets** are **unchanged** — invisible to users, high-risk to rename (renaming `FPL_*` breaks every
deploy secret). Only *visible* surfaces rebrand. The two **borderline near-visible** identifiers — `USER_AGENT`
(`fpl-assistant/0.1` → `madboots/0.1`, the courtesy string sent to FPL's API) and the **CLI `prog`**
(`fpl-assistant` → `madboots`, shown to CLI users) — **flip** to the brand (cheap, consistent, trivially reverted).

**5. Not-affiliated disclaimer.** A quiet footer/caption — *"MADBOOTS is not affiliated with the Premier League or
the official Fantasy Premier League game."* — standard hygiene now that the product carries a name (the descriptive
old name dodged this).

**6. Asset provenance & format — recorded honestly.** The badge is an **AI-generated** mark (Gemini), traced/
background-removed to a **transparent PNG** (raster, not vector). This is **fine for the favicon/header/band sizes**
(~330px, crisp to ~32px). A **true-vector SVG** (re-export with transparent background) and a **designer redraw** of
the AI mark are **deferred niceties**, not blockers.

**7. What this is *not*.** Not a dark reskin (deferred, approach A). Not a repo/secret rename (kept). Not the
illustration hero (deferred). Not the brand-infra changeover — the **repo transfer to `madbootsfpl`** + the
**`madboots.com` domain** (rename the subdomain + 301-forward) are a **separate backlog item** to do together,
knowingly, because of the Streamlit reconnection risk (see `docs/Backlog.md` "Branding").

---

### 🔀 Alternatives Considered

- **Keep "FPL Assistant".** Rejected — descriptive and undifferentiated in a crowded space; the owner wants an
  ownable brand behind the secured domain.
- **Rename the package / repo / `FPL_*` secrets too.** Rejected — invisible to users, and renaming `FPL_*` breaks
  every live deploy secret. Only visible surfaces rebrand; the infra move is a separate, deliberate backlog step.
- **A full dark brand reskin now (approach A).** Rejected for this sprint — bigger, riskier change to a working UI;
  the marks-as-accents (B) lands the brand with near-zero UI risk. A dark theme stays a later option.
- **Block on a true-vector SVG / a designer redraw first.** Rejected — the transparent PNG badge is approved and
  renders well at the sizes used; SVG/redraw are follow-ups, not gates.
- **Use the detailed boots illustration as the icon.** Rejected — it turns to mush small; a simple badge is the
  small mark, the illustration a big-surface hero.

---

### 🧭 Consequences

**Positive**
- A **distinctive, ownable identity** across the app, delivered as **low-risk accents** on the current UI — one
  `brand.py` source of truth, one badge asset, a CSS wordmark.
- **No engine/xP/secret change** — display/asset-only; the one-xP + read-only invariants hold; existing deploys +
  secrets keep working (nothing renamed that a deploy depends on).
- **Owner-approved visually** before wiring (the real-badge Artifact preview), reducing rework.

**Negative / risks (mitigations)**
- **An AI-origin, raster (PNG) mark.** *Mitigation:* documented; fine at the sizes used; a vector re-export +
  designer redraw are recorded follow-ups.
- **A named product on official FPL data** invites a brand/affiliation question. *Mitigation:* the not-affiliated
  disclaimer; the name avoids "FPL/Premier League" in the wordmark itself.
- **Two identities during transition** (visible MADBOOTS · internal fpl-assistant). *Mitigation:* deliberate and
  documented; the infra changeover (repo/domain) is a separate, planned step, not silent drift.

---

### 🧾 Status & follow-ups

- **Accepted.** Built this sprint (Sprint 141): **US-348** (swap the ~19 visible "FPL Assistant" → "MADBOOTS" +
  the tagline; flip `USER_AGENT`/CLI `prog`), **US-349** (`brand.py` + the badge favicon on every page + the CSS
  wordmark), **US-350** (the not-affiliated disclaimer + rebrand the *live* docs; historical ADRs/sprint logs keep
  "FPL Assistant" as the record). Docs: PROJECT_STATUS, Architecture, Help, memory.
- **Owner actions (separate, bundled — `docs/Backlog.md` "Branding"):** transfer the repo to `madbootsfpl` (reconnect
  Streamlit) + rename the subdomain to `madboots.streamlit.app` + 301-forward `madboots.com` — done together,
  knowingly (the live beta can briefly blink offline).
- **Deferred:** the boots **illustration** hero (a transparent export); a **true-vector SVG** badge + a **designer
  redraw**; a **dark brand reskin** (approach A); a **`madboots.com` landing page**; an **email/domain** migration
  (`fpl.assistant@proton.me` → `hello@madboots.com`).
