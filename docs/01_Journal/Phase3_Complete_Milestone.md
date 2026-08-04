# Milestone — Phase 3 Complete (Decision Support)

**Date:** 2026-08-04 · **Sprints:** 027–030 · **Decisions:** ADR-029 / 030 / 031 / 032

---

## The milestone

**Phase 3 — Decision Support — is substantially complete.** The app no longer just *ranks* data; it
**recommends and explains** — the point where an analytics tool becomes an *assistant*. Three
cross-linked commands, each grounded in the same foundation:

- **`captain --squad`** (Sprint 027, ADR-029) — the best captain picks for the next gameweek, by xP,
  with opponent / venue / penalty duty. GKs excluded (captaincy is a ceiling bet); doubtful flagged.
- **`transfer --squad`** (Sprint 028, ADR-030) — the best single *legal* transfers by xP gain: same
  position, ≤3/club, affordable (sale + `--bank`). GKs included; bench flagged.
- **`analyse --squad`** (Sprint 029, ADR-031) — a squad's health over N gameweeks: projected XI xP
  (with a per-gameweek breakdown, Sprint 030 / ADR-032), weak links, injuries, club concentration —
  indicators, not a made-up grade.

They form a **workflow**: `analyse` surfaces a weak link → `transfer` fixes it → `captain` picks the
armband. Tests grew 227 → **279**; ADRs 28 → 32; **no new dependency, no new data source** across the
whole phase.

## Why it went so smoothly — the dividend of clean layers

Every Phase-3 feature was **mostly wiring**. Because the earlier phases kept strict one-way data flow
— pure analytics that *return data*, views that *format* it, a solver, saved squads, a shared
renderer — each new recommendation was a small composition of existing, tested pieces, plus
decision-appropriate *policy* at the edge (exclude GKs for captaincy but include them for transfers;
flag doubtful; flag bench). The architecture chosen back in ADR-002/003 paid off a phase later.

## Honest boundaries (recorded, not hidden)

- **xP is a mean, not a ceiling** — so a high-upside differential won't always top a list (GK
  exclusion is the one place we hard-code around it; a ceiling view is on the Backlog).
- **No expected minutes (xMins) yet** — recommendations assume the player starts; bench players are
  *flagged*, not modelled. xMins waits on the season starting.
- **A saved squad, not a live manager ID** — auth (`/my-team/`) is deferred; the analyser reads a
  saved squad.

## What's next

The season-gated work (per-GW history + in-season form + xMins) waits for GW1 (2026-08-21). In the
meantime, Phase 4 (an LLM/chat layer) is being **spiked** — a grounded `ask` where local Ollama
*narrates* a decision the analytics made, never computing or inventing numbers. The Phase-3
structured outputs are exactly what makes that grounding possible.

## Notes for future me

- The gate + 3-part DoD held for the whole phase; each feature was pressure-tested on a real squad
  before code, which is what surfaced the two probe-driven calls (GK exclusion, the transfer
  freed-slot case).
- Composability is not luck — it's the earned interest on keeping layers pure and separate.
