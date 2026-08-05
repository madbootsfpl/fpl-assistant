# Lessons Learned

**Sprint:** Sprint 058 — Your squad, editable in the browser (name · transfers · captain · manual edit)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn the Sprint-057 **read-only** session squad into an **editable** one — name it, apply a transfer,
hand-swap any player, set the bench, and set a captain — all mutating `st.session_state` (download = save;
**no server writes**), backed by a new generic **`squad_15_issues`** legality validator. Fix a confirmed
Build bug (xP/xMins rendered 0) on the way. Scope (owner's calls): **guided + a manual picker**, a
**persisted** captain, editing **wherever the opportunity appears**, and budget as a **warning, not a block**.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reading a bug to its root by diffing the working path (the CLI attaches `xp`/`minutes_weight`; the web
  page didn't).
- Keeping a generic core: a pure validator + display-only renderer changes, policy at the edge.
- Reusing tested code rather than re-writing it (`apply_transfer` served the manual swap unchanged).

### New Skills Acquired

- Mutating Streamlit `session_state` safely across re-runs (edit a **copy**, `set_active_squad`, `st.rerun`).
- Modelling a superset schema (`captain_id`/`name`) that the CLI ignores and upload validates.
- A width-safe table marker (reserve room for ` (C)` so columns stay aligned).

---

# What Went Well ✅

- **A swap is a swap** — the manual editor reused `apply_transfer` verbatim; no second mutation path.
- **One validator, one set of helpers** — `squad_15_issues` + `rename`/`apply_transfer`/`set_bench`/
  `set_captain` meant edit logic never scattered across pages.
- **The gate paid off** — the two settled questions (edit-everywhere; warn-not-block) removed mid-build
  guesswork.
- **The mutating path found a latent bug** — adopting a demo squad (which had no `name`) crashed the
  sidebar; a read-only path had never exercised that corner.
- **Core untouched, CLI unchanged** — the analyse renderer kept its 21 tests green; all edits were at the
  edge (+ one pure core validator).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Build showed xMins/xP = 0 | The page never attached `xp`/`minutes_weight` onto the picked players | Mirror the CLI (`cmd_squad`) — attach them before `render_squad` |
| Adopting a demo squad crashed the sidebar | Demo squads (from `SquadStore`) have no `name`; `render_sidebar` read `act['name']` | `demo_squads()` injects a `name`; the sidebar reads defensively |
| Where does "budget" live in the validator? | "Warn, not block" is ambiguous if budget is in the legality list | Keep the validator **structural-only**; warn on cost at the edge |
| `(C)` broke table alignment | Appending ` (C)` overflowed the fixed name width | Reserve 4 chars — truncate the name, then add ` (C)` |
| An AppTest for Apply early-returned | The demo squad is xP-optimal → no positive-gain swaps | Raise the bank slider first → dearer upgrades → swaps appear |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Diff the working path | A web/CLI parity bug is fastest found by comparing to the path that works |
| Reuse over re-implement | The transfer mutation *was* the manual-swap mutation — one helper, one test surface |
| Soft vs hard, structurally | Making budget un-representable in the legality list makes "never blocks" impossible to get wrong |
| Superset schemas | Extra keys (`name`/`captain_id`) extend state without breaking the CLI format; validate on the way in |
| Mutating paths test corners | Editing exercises states a read-only view never reaches (the nameless-demo crash) |

---

# Development Lessons 💻

- Fix the parity bug by mirroring the reference implementation, not re-deriving it.
- Put mutation behind helpers and let pages call them — the invariant ("no inline edits") prevents drift.
- Encode "never blocks" in the *shape* of the data (not in the list of blockers), so a naive caller is safe.
- Let a new code path be a bug-finder: build it, then smoke the corners the old path never hit.

---

# AI Collaboration Lessons 🤖

- The owner's "tweak when I see the opportunity" reframed the UI: edit inline on Transfer/Captain **and** a
  My Squad hub — not one dedicated page.
- "Warn, prices drift" settled budget as a soft edge-side signal — a small call that simplified the whole
  validator.
- Recording the mid-build refinement (structural-only validator) in ADR-055 kept the decision record honest.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-055 | An **editable** session squad — mutate in `session_state` (name · apply-transfer · manual-swap · set-captain · bench; no server writes); a generic **`squad_15_issues`** validator (budget = warn, not block); `captain_id` superset + **(C)**; edit inline (Transfer/Captain) + a **My Squad** hub | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner:** redeploy (auto on push) + gather tester feedback on editing. Later: **Data Hardening** post-GW1
  (2026-08-21: per-GW history + form); a differentials/value `ask` intent; a multi-swap positional reshape;
  Path 2 server-side persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reusing tested helpers across features; keep encoding invariants in data shape, not caller discipline.

---

# Key Commands Learned

```text
python -m src.web_streamlit                       # run the multipage Streamlit app locally
grep -rn "\.save(" src/web src/web_streamlit      # the no-server-writes guardrail, by hand
python -m pytest tests/test_web_squads.py -q       # the mutation-helper + validator unit tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Mutation helper | An edge function that edits a *copy* of the squad (rename/apply_transfer/set_bench/set_captain) |
| `squad_15_issues` | The generic 15-man legality validator (positions + ≤3/club); budget stays soft at the edge |
| Superset schema | Extra keys (`name`/`captain_id`) on the CLI `SquadStore` dict — ignored by the CLI, validated on upload |
| Soft warning | A signal that never blocks (over-budget) — kept out of the legality list by design |
| Adopt (a demo) | Editing a read-only demo squad copies it into `session_state` as your active squad |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-055 | The editable-squad model (mutation, validator, captain, no server writes) |
| `src/web_streamlit/squads.py` | The edge helpers — state, picker, validator calls, mutation helpers |
| `src/analytics/optimizer.py` (`squad_15_issues`) | The generic 15-man legality check, reused by every edit |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-171 Gate — ADR-055 (editable session squad; validator; no server writes)
- US-172 Fix Build xP/xMins + name a squad
- US-173 `squad_15_issues` validator + apply a transfer
- US-174 Manual editor — the My Squad hub (swap/bench/rename/download)
- US-175 Set & persist a captain — (C) in Analyse + the download

**Stories Carried Forward:**

- Owner redeploys + gathers tester feedback on editing

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
