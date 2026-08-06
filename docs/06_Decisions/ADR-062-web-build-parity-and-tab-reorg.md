# Architectural Decision Record: Web build parity + squad-tab reorg

**Decision ID:** ADR-062
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** none — extends the Streamlit edge (ADR-052) and the session-squad model
(ADR-054/055) to full CLI `squad` parity. No engine change (reuses the optimiser of ADR-008/043/044/045 and
`decision_xp` of ADR-041). Triggered by tester feedback (Feedback_Log, 2026-08-06).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The CLI `squad` command builds with a rich option set — budget · include · exclude · bench · formation ·
objective · no-xmins · cheap · premium · differential · weekly | bench-boost · include-unavailable · save.
The web **Build** page exposes only **budget / cheap / premium / differential**. Testers want to build with
*any/all* of these in the web, save into the session so **My Squad** picks it up to tweak, then download —
and want the squad tabs named + grouped sensibly.

**Verified on real data (2026-08-06):** `select_squad` already accepts every option; a probe built an
xp+include+exclude+≥2-differentials+weekly squad (`Optimal`) and an xgi XI in a pinned 3-4-3 — so this is a
**UI/edge sprint with no engine change**.

#### Decision Drivers
- **Reliable > fragile** — ~10 structured options belong in **form widgets**, not natural language.
- **One engine** — the web must call the *same* `select_squad` / `decision_xp` as the CLI (no drift).
- **The save flow is a 15** — My Squad tweaks a full 15; the build that saves must be a 15.
- **No server writes** — Download / "Use this squad" only (ADR-054/055).

---

### ✅ Decision

**1. Full option parity as widgets on "Build Squad" (US-200).** The Build page gains form controls for the
missing options — **include · exclude · declared bench** (multiselects over player names), **objective**
(xp *(default)* / points / value / xgi), **no-xmins**, **build mode** (Balanced / Weekly / Bench Boost),
**include-unavailable** — alongside the existing budget / name / cheap / premium / differential. They feed
the *same* engine, mirroring the CLI verbatim: `full=True` (a 15), `available_players(keep_ids=include∪bench)`
unless include-unavailable, `bench_weight=WEEKLY_BENCH_WEIGHT` for Weekly, `archetype_bands` +
`min_differentials`, and the score from **`decision_xp`** (xp, xMins-aware, honours no-xmins) or
**`objective_scores`** (points/value/xgi). Simple conflicts (include∩exclude, bench>4, weekly+declared-bench)
surface as a soft `st.warning`, mirroring the CLI's `validate_*`. **The saveable build stays a full 15** —
Download (`SquadStore` shape) + **Use this squad →** unchanged.

**2. Formation is an XI-only display preview (US-200).** `--formation` shapes a *starting XI (11)*, but a
saveable squad is a *15* (its bench sets the shape). So a **"Preview best XI shape"** control (DEF/MID/FWD
selectors, size 11) is **display-only** — it does **not** produce a saveable squad. This keeps the save flow
unambiguous (always a 15) while still answering "what's the best 3-4-3?".

**3. My Squad stays the tweaker + a rebuild link (US-201).** No duplicate optimiser UI. My Squad keeps its
edit/pitch controls and gains a **"🔧 Rebuild in Build Squad →"** `st.page_link` back to the builder.

**4. Tab rename + logical reorder (US-201).** Streamlit derives the sidebar label + order from the page
filename. Rename **"Squads" → "Squad Health"** and **"Build" → "Build Squad"**, and renumber so the trio is
grouped: **Build Squad · My Squad · Squad Health**. Update the AppTest page-path references + Home copy.

**5. Ask-build → session-squad bridge (US-202, optional).** `_decide_build_squad` already computes a squad;
surface its `player_ids`/`bench_ids`/`name` on the decision (and `AskResult`) so the web Ask page can offer
**"Use this squad →"** (→ the session squad → My Squad) for the NL-supported options. CLI output unchanged;
defer if the contract change outweighs the value (US-200 covers the core need).

---

### 🔀 Alternatives Considered

- **All options via NL on the Ask tab.** Rejected — parsing include/exclude/formation/objective from prose
  is fragile and un-grounded; widgets are reliable and self-describing. (Ask keeps the NL-friendly subset.)
- **A full optimiser panel on My Squad too.** Rejected (owner's call) — duplicates the Build UI in two
  tabs; My Squad stays the tweaker and links to the builder.
- **Formation on the saveable build.** Rejected — an 11 isn't a 15; mixing them muddies the save flow.
  Formation is a display-only preview.
- **Importing the CLI's `validate_*` into the web edge.** Rejected — a thin inline check avoids an
  edge→cli coupling; the rules are trivial.

---

### 🧭 Consequences

**Positive**
- Full CLI build power in the web, via reliable widgets, calling the *same* engine (no drift).
- The build → save → My Squad → tweak → download flow works end-to-end for a full 15.
- The squad tabs read + group logically (Build Squad · My Squad · Squad Health).

**Negative / risks (mitigations)**
- **Renaming page files** touches AppTest refs + Home copy + the rebuild link → update them together; a
  test run catches a missed ref.
- **Formation only previews** (no save) → clearly labelled, so it doesn't surprise.
- **The Ask bridge changes the ask contract** → keep it additive (a new optional field) and optional;
  defer if heavy.
- **More controls = more UI** → group them, keep xp/Balanced as defaults so the page opens sensible.

---

### 📊 Validation

Probed live: `select_squad` builds with objective + include + exclude + differentials + weekly (Optimal) and
an XI in a pinned formation. Acceptance: Build Squad drives each option to the *same* engine and still
produces a saveable 15 (Download / Use this squad); the formation preview is display-only; My Squad links to
the builder; the tabs are renamed + grouped and the AppTest refs resolve; the web writes nothing
server-side (the `.save(` guardrail holds); the existing 556 tests stay green.
