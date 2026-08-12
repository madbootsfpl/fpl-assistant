# Architectural Decision Record: Split the Squads tab — Squad Lab + My Squad

**Decision ID:** ADR-105
**Date:** 2026-08-12
**Status:** Accepted
**Superseded By / Replaces:** **revises ADR-069** (the single consolidated *Squads* page) — the app has since grown
to **seven** tools on one switch, so the consolidation now *is* the clutter it once solved. Splits it into two
clearer top-level tabs. Navigation/IA only — **no** change to the analytics/engine, `decision_xp`, or any view's
behaviour (the `views/squads.py` renderers are reused as-is). Extends ADR-055 (My Squad edit).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester feedback (2026-08-12): *"the Squads tab is very busy… it's confusing why Build is there after your team is
built."* The current **Squads** page is one page with a **7-way "Tool" switch** — **`[Build] [My Squad] [AI Tips]
[Chips] [Health] [Transfer] [Captain]`** — defaulting to **Build**.

The mismatch: **Build is a *create-from-scratch* tool** (season start · wildcard · revamp), while the other six all
operate **on your existing team**. Two different jobs share one crowded switch, and the create tool is the *first,
default* thing — so a returning user with a team already asks "why Build?".

**ADR-069 originally consolidated** the old separate squad pages into this one page to cut nav clutter. That was right
then — but the tool count has since grown (AI Tips, Chips added), and a single 7-way switch is now the friction. This
is a natural evolution, not a reversal of principle.

**Owner's standing design principle (2026-08-12):** *clean, modern, easy to navigate.* And the naming steer:
**"Squad Lab"** for the builder (implies *build & experiment*, distinct from *My Squad*), with brand personality via
the **mascot on the page**, not the nav label.

#### Decision Drivers
- **Two jobs, two homes** — separate *create a team* from *manage your team*; stop them competing on one switch.
- **Clean, navigable map** — functional top-level labels; fewer options per switch.
- **Guided entry** — a new user with no squad still finds the builder easily.
- **Brand where it shines** — the MADBOOTS mascot themes the *page*, not the nav label (keep the map literal).
- **Reuse, don't rewrite** — the existing view renderers are unchanged; this is an IA move.

---

### ✅ Decision

**Split the single *Squads* page into two top-level tabs — *Squad Lab* (create) and *My Squad* (manage + tools).**

**1. Squad Lab (the builder).** The old *Build* view (`render_build`) becomes its **own top-level page**, renamed
**Squad Lab** — for creating/optimising a fresh 15 (season start · wildcard · revamp). No squad picker (it makes
one); its "**Use this squad →**" hands the built squad to the session (→ My Squad). The page header is **mascot-
themed** (the MadBoots badge/boots + "Build your squad") — brand personality on the page, a functional label in the nav.

**2. My Squad (manage + tools).** Its own top-level page holding the pitch/edit view **plus the five tools as
sub-tabs**, in **workflow order**:
**`[My Squad] [AI Tips] [Captain] [Transfer] [Chips] [Health]`** — *see/edit your team → the fast weekly answer →
who to captain → who to bring in → when to chip → the deep analysis.* Defaults to **My Squad** (the pitch). The
**squad picker + "Gameweeks ahead" horizon** live here (shared by the six sub-views); Squad Lab doesn't need them.

**3. Guided new-user path.** On My Squad with **no active squad**, show the demo + a prominent **link to Squad Lab**
("→ build your own"), so first-timers are pointed at the builder without it being the default tab.

**4. Naming — functional map, brand on the page.** The tab is **"Squad Lab"** (short; *build/experiment*; distinct
from *My Squad*). **"Draft" is rejected** — it collides with FPL Draft (a different game mode). Top-level nav labels
stay **functional** (My Squad · Squad Lab · Players · Fixtures · Ask · …); the **mascot** carries the brand on the
Squad Lab header. The **full MADBOOTS vocabulary** (MadBoots *Pick / Edge / Risk / Radar*) is a **separate** later
item (branding-E), applied *inside* the tool cards — not to nav labels.

**5. Implementation shape.** Split `pages/3_Squads.py` into two pages (**My Squad** + **Squad Lab**), re-point the
sidebar order, and reuse `views/squads.py`'s renderers unchanged. The nav becomes (Admin gated):
`Home · Players · Fixtures · My Squad · Squad Lab · Ask · News · Trending · Help · Feedback`.

**6. What this is *not*.** Not an engine/analytics change (renderers reused). Not a rename of the internal
`views/squads.py` module or its functions (kept). Not a re-org of the *other* tabs (Players/Fixtures/Ask/etc.
unchanged). Not the brand-vocabulary layer (E, separate).

---

### 🔀 Alternatives Considered

- **Keep the single 7-way Squads page.** Rejected — it's the exact clutter the tester flagged; the create/manage
  jobs stay tangled.
- **Rename *Build* in place, no split.** Rejected — a clearer name helps, but Build still sits first/default among
  the management tools; the "why is Build here?" confusion remains.
- **Brand-name the tab "MadBoots Lab".** Deferred — a lone brand-named tab among functional ones reads
  inconsistently, and brand-naming *all* tabs would hurt the map's scannability. Brand goes on the *page* (mascot) +
  inside features (E), keeping the nav literal. ("Squad Lab" is the agreed middle — a nod to *lab/experiment* without
  a pure brand label.)
- **Group the tools into fewer meta-tabs** (e.g. Plan / Analyse / Improve). Rejected — adds nesting; the tester
  asked for a flat set of clear sub-tabs, and six workflow-ordered tabs read fine.
- **"Draft" / "Team Builder" / "Optimiser" as the name.** *Draft* clashes with FPL Draft; *Team Builder* is a fine
  literal fallback; *Optimiser* is jargony. Owner chose **Squad Lab**.

---

### 🧭 Consequences

**Positive**
- **A cleaner, two-job map** — *create* (Squad Lab) and *manage* (My Squad) each have a home; no 7-way switch.
- **Reuses the renderers** — zero analytics/engine change; the behaviour of every view is identical, just relocated.
- **Brand personality** lands on the Squad Lab page (mascot) without muddying navigation.
- **Guided** for new users (the no-squad → Squad Lab pointer).

**Negative / risks (mitigations)**
- **A real refactor + a nav renumber** — splitting `3_Squads.py` shifts the page files and the sidebar order.
  *Mitigation:* a focused, gated sprint; the renderers are reused unchanged, so it's mechanical.
- **~20 tests reference the *Squads* page + the "Tool" switch + view names** (`_squads_view()`, `_PAGES` paths, the
  segmented-control lookups). *Mitigation:* update the shared test harness once (`_squads_view` → the two pages) and
  re-point the paths; the assertions on each view's content are unchanged.
- **Muscle-memory churn** for existing testers (the tab moved). *Mitigation:* a one-time thing; the new map is
  clearer; Help + Home copy updated to match.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (a gated sprint): split `pages/3_Squads.py` → a **My Squad** page (the pitch + the five tool
  sub-tabs, workflow order, the squad picker + horizon) and a **Squad Lab** page (`render_build` + a mascot-themed
  header + "Use this squad →"); the no-squad → Squad Lab pointer; re-point the sidebar order + the test harness;
  update Help/Home copy. Docs: PROJECT_STATUS, Architecture, memory.
- **Not this ADR / separate follow-ons:** the **MADBOOTS vocabulary** (branding-E — *Pick/Edge/Risk/Radar* inside the
  cards); the **per-GW xP display** (A5); the **player-actions consolidation** (A6); the **persistence + Google-auth**
  review (C-cluster). All remain in the 2026-08-12 intake (`docs/Backlog.md`).
