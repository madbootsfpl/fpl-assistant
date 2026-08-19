# Architectural Decision Record: My Squad — a per-gameweek xP toggle

**Decision ID:** ADR-121
**Date:** 2026-08-19
**Status:** Accepted — owner-approved, **build now** (pre-GW1). Tester-requested; low-risk (reuses data we already
compute).
**Superseded By / Replaces:** Extends the My Squad summary (US-239/US-404) + the per-GW `by_gameweek` breakdown
already used by the player-card per-GW row (ADR-032/ADR-109). **Display-only** — no `decision_xp` change.
**Deciders / Participants:** Tony Sheridan (Owner), a beta tester, Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester (2026-08-19, pre-GW1): the "Gameweeks ahead" selector shows a **cumulative** projected xP (GW1, or GW1+GW2
at horizon 2, …). For **last-minute transfer decisions** as prices/news roll in, they want to see **each future
gameweek on its own** — e.g. select GW2 → view **GW1+GW2** (as today) *or* **GW2 alone**; same for GW3.

The per-GW data **already exists**: `decision_xp` returns `by_gameweek = {event: xP}` per player (ADR-032). So this
is a **display toggle**, not new analytics — hence low-risk and worth doing before GW1.

#### Decision Drivers
- **Real, timely need** — GW-by-GW visibility for last-minute moves (owner: "people really need this by Friday").
- **Cheap + low-risk** — reuses `by_gameweek`; display-only; no decision-logic change.
- **Don't destabilise the golden page pre-GW1** — the XI/captain *selection* stays exactly as today.

---

### ✅ Decision *(owner-approved, build now)*

**A per-GW xP toggle on My Squad**, offered when the horizon spans **>1 GW** (a no-op at horizon 1):
- **`GW1→N (cumulative)`** — today's behaviour (total over the horizon).
- **`GW N only`** — just the horizon's **last** gameweek, from `by_gameweek`.

It switches the **displayed** xP — the three metrics (**Projected XI · Captain 2× · Bench**) and the **pitch xP
chips** — via a `display_xp` map (cumulative `xp_by_id`, or `{id: by_gameweek[target_gw]}`). The captain double
applies to the **shown** gameweek. **The XI/captain *selection* stays cumulative** (`best_legal_xi(xp_by_id)`) — so
the toggle is pure visibility: *"what does my current XI project in GW N?"*, never a re-optimisation.

**What this is *not*.** Not a change to `decision_xp` or the XI/captain recommendation. Not a per-GW re-optimise
(a possible follow-up). Not (yet) applied to the ⚙ substitute panel or other tabs — My Squad first (the ask).

---

### 🔀 Alternatives Considered

- **Re-optimise the XI/captain per GW.** Deferred — more useful eventually, but a behavioural change to the golden
  page; too risky to land pre-GW1. Visibility meets the stated need now.
- **A separate per-GW table.** Rejected — the toggle reuses the existing metrics + pitch, no new surface.
- **Wait until post-GW1.** Rejected (owner) — testers need it *this week* for last-minute planning.

---

### 🧭 Consequences

**Positive** — per-GW visibility for last-minute decisions, from data already computed; near-zero risk
(display-only, XI/captain logic untouched); consistent with the card's per-GW row.
**Negative / risks (mitigations)** — a benched player may out-score a starter in a single GW (looks odd)
(*mitigation:* that's *informative* — it flags a GW-specific sub; the XI stays the cumulative-best); the ⚙ panel
still shows cumulative xP (*mitigation:* minor; a tracked follow-up); the future-GW captain double is hypothetical
(*mitigation:* a caption notes captaincy is re-picked weekly).

---

### 🧾 Status & follow-ups

- **Accepted — build now (US-422):** the toggle + `display_xp` on the 3 metrics + the pitch chips; captions
  adjusted for per-GW; a defensive AppTest; 3-part DoD.
- **Not this ADR / follow-ups:** extend the toggle to the ⚙ substitute panel + other tabs; a per-GW **re-optimise**
  option; the per-GW view on the Player DNA / other xP surfaces.
