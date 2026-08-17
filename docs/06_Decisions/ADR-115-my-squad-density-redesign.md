# Architectural Decision Record: My Squad density redesign (progressive disclosure)

**Decision ID:** ADR-115
**Date:** 2026-08-17
**Status:** Accepted — owner-approved via a before/after wireframe. Build = Sprint 163 (Sprint D of the UX audit).
**Superseded By / Replaces:** Reshapes the **My Squad edit sub-tab** (`render_my_squad`, ADR-105/108). Keeps every
feature — reorganises the layout. Removes the in-page Transfer (duplicated ADR-055/046, which live in the Transfer
sub-tab). Display/IA only — no analytics/engine change.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The UX audit (`docs/00_Project/UX_Style_Audit.md`) flagged **My Squad** as the app's densest page — the "golden"
page, but a wall. `render_my_squad` stacks **14 blocks**: banner → ⚙ Your-team panel → legal line → a **5-across
metric row** → captain caption → flagged caption → price caption → pitch → ⚙ Player-actions → bench-order caption →
Reorder expander → "Edit" → Rename → **Transfer expander (open)** → Set-whole-bench. Concretely:
- a **5-metric row** cramps to slivers on a phone; **4 stacked grey captions** form an undifferentiated wall;
- **three overlapping bench/lineup controls** (Substitute · Reorder · Set-whole-bench);
- an in-page **Transfer expander that fully duplicates the 🔄 Transfer sub-tab** (a real redundancy).

Nothing signals *the* primary action, and the pitch (the hero) sits below a stack of status.

#### Decision Drivers
- **Progressive disclosure** — lead with the pitch + a compact status; keep the primary action visible; collapse
  the rest.
- **Kill redundancy** — one place to transfer (the tab), not two.
- **No feature loss** — everything still reachable; just grouped.
- **Mobile-first** — fewer across-columns; one status strip, not five metrics.
- **Streamlit constraint** — expanders can't nest, so grouped sections are **flat** inside one expander.

---

### ✅ Decision  *(owner-approved: 3 ✓, and 1-2-4 ✓)*

**1. Compact the status.** The **5-across metric row → a 3-number strip** (`st.columns(3)`: Projected XI · Captain ·
Bench). The **4 stacked captions → one availability + price line** ("✓ N available · M doubtful · 💷 price note");
the legal/cost becomes the strip's leading pill. The captain "×2 is a one-week thing" / benched-captain note stays
**conditional** (only when it applies).

**2. Lead with the pitch; one visible primary.** Order: banner → Your-team panel → **status strip** → **pitch** →
**⚙ Players & lineup** (the selection-driven card · ⚔️ Boot Battle · 👑 captain · 🔁 substitute) with the **bench
order + Reorder folded in** (a lineup action). This is the single visible primary block.

**3. Remove the duplicate Transfer.** The in-page **Transfer expander is deleted**; in its place a one-line pointer
to the **🔄 Transfer tab** (which already holds the full, identical transfer UI — ADR-055/046). One place to
transfer.

**4. Fold the rest into one "⚙ Manage".** **Rename** + **Set the whole bench** move into a single collapsed **⚙
Manage** expander as **flat** subsections (no nested expanders). The **⚙ Your team** panel (import/backup, US-386)
stays top-level under the banner (it owns an expander, so it can't nest inside ⚙ Manage — and the banner signposts
it).

**What this is *not*.** Not a change to the pitch renderer, the player card, `decision_xp`, `substitute`,
`apply_transfer`, or the other sub-tabs (AI Tips · Captain · Transfer · Chips · Health). Same features, ~half the
vertical stack.

---

### 🔀 Alternatives Considered

- **Keep a slimmed in-page Transfer.** Rejected (owner ✓ on removal) — the Transfer tab is one click away; two
  transfer UIs is the redundancy the audit flagged.
- **Tabs within the edit view** (Lineup / Manage as sub-sub-tabs). Rejected — the page already has a segmented
  sub-nav; another tab layer adds nav depth. Expanders (progressive disclosure) are lighter.
- **Keep the 5 metrics, just wrap.** Rejected — Unavailable/Doubtful are already restated in the availability line;
  three numbers + one line reads far cleaner on mobile.

---

### 🧭 Consequences

**Positive**
- The pitch leads; **one obvious primary action**; ~half the vertical height; far better on a phone.
- **No duplicate Transfer** — a single, unambiguous place to make one.
- Every feature intact, just progressively disclosed.

**Negative / risks (mitigations)**
- **Behaviour change:** transfers now only on the Transfer tab. *Mitigation:* a clear pointer where the expander
  was; the tab is adjacent in the sub-nav.
- **A big diff in one function** (~350 lines) risks regressions. *Mitigation:* pure reorganisation — reuse every
  existing helper (`render_pitch`/`render_player_card`/`substitute`/`set_captain`/`move_bench_sub`/`set_bench`/
  `rename`); the ~20 My-Squad tests pin behaviour (update the ones that assert the old in-page Transfer / metric
  labels). Owner-approved wireframe first.
- **Expander nesting:** ⚙ Manage holds **flat** Rename + Set-bench (Streamlit can't nest expanders). *Pinned.*

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**Sprint 163**): **US-404** the compact status (3-metric strip + one availability/price
  line); **US-405** remove the in-page Transfer → the tab pointer; **US-406** the progressive-disclosure
  restructure (pitch-led · ⚙ Players & lineup primary with bench-reorder folded · ⚙ Manage = Rename + Set-bench).
- **Not this ADR:** the header-sort-vs-pagination honesty item; the incremental token retro-fit (Sprint B); any
  change to the Transfer/Captain/Health sub-tabs.
