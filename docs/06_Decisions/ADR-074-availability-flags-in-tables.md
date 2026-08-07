# Architectural Decision Record: Availability flags in the player tables

**Decision ID:** ADR-074
**Date:** 2026-08-07
**Status:** Accepted
**Superseded By / Replaces:** new **display-only** convention. Surfaces the existing availability data
(`status`/`chance`, ADR-023) as a compact flag in the web tables, next to the crowd flags (ADR-057) and the
quality rating (ADR-071/073). No analytics change. Triggered by an owner/backlog item.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The **squad** and **captain** views already warn about injured/suspended players, but the **ranking tables**
(the Players Pool, the stat boards) show no availability at all — so a user scanning them can't tell whether
a top player is actually fit without cross-checking the News tab. The backlog captured this: *"availability
flags in the ranking views — surface injury/suspension flags in `table`/`xg`/etc. the way `squad` does."*

**Verified in code (real data):** status split **a 512 · i 32 · d 18 · u 7 · s 3** → **60 flagged** of 572
*preseason* (they sharpen toward GW1). Each flagged player carries `status`, `chance`, and a `news` string.
`crowd_flags` is ownership/momentum/price/form only — **not** injuries — so availability is a separate flag.
The Pool and xG board render **raw player rows** (they have `status`); the over/under · DefCon · clean-sheets
boards render **trimmed** analytics dicts (no `status`), but each `render_*` already receives the **full
`players` list**, so the view can source the flag without any analytics change. `st.dataframe` has **no
per-cell hover** (ADR-072).

#### Decision Drivers
- **"Is this player fit?" at a glance** — where players are ranked, not only on a separate tab.
- **Reuse the existing data** — `status`/`chance` already ingested (ADR-023); no new fetch.
- **No analytics drift** — a display concern; rankings and the analytics dicts stay as they are.
- **Unambiguous** — visually distinct from the crowd flags and the rating circles.

---

### ✅ Decision

**1. A shared `availability_flag(player)` helper.** In `analytics/crowd.py` (next to `crowd_flags`, same
"display flags" home): `{"i": "🚑", "s": "🚫", "u": "⛔", "n": "⛔", "d": "❓"}.get(player["status"], "")` —
an emoji for injured / suspended / unavailable / doubtful, and **`""` for available** (`"a"`). Pure, empty-
safe, exported from the analytics package. The emojis are chosen **distinct from the rating circles**
(🟢🟡🟠🔴) so availability and quality don't blur.

**2. A compact "Fit" column in the web player tables.** The Players Pool (US-228) and all four stat boards
(US-229) gain a **Fit** column showing the flag (blank = available), placed early (right after
Player/Team/Pos). A one-line **legend** caption (`AVAILABILITY_LEGEND`) + a column tooltip explain the
emojis and point to **News** for the detail (since there's no per-cell hover). `"Fit"` is a text column, so
the number-format convention (ADR-072) leaves it as-is.

**3. Source the flag without touching analytics.** The Pool and xG board flag their raw rows directly; the
three trimmed boards build a `{(web_name, team): flag}` lookup from the **full `players` list** each render
function already receives. The analytics stat dicts (`over_under`/`defcon_reliability`/`defensive_solidity`)
are **unchanged**.

**4. Scope.** The **web** ranking/stat tables (the tester's surface). The CLI ranking views (`table`/`xg`)
are a possible follow-up, out of scope here. No server writes.

---

### 🔀 Alternatives Considered

- **Fold availability into the Trends (crowd_flags) column.** Rejected — it mixes injuries with
  ownership/momentum; a user scanning for fitness wants it separate and obvious.
- **Add `status` to the analytics stat dicts.** Rejected as unnecessary — the render functions already have
  the full `players` list, so a view-side lookup avoids changing analytics shapes (and their tests).
- **A full News/text column in every table.** Rejected — too wide; the News tab holds the detail, the table
  needs a glance-able flag. (A header tooltip + legend covers the "what does 🚑 mean?" gap.)
- **Reuse the rating circles for availability.** Rejected — 🔴 (rating) vs a red availability mark would
  blur two unrelated signals; distinct emojis keep them readable.

---

### 🧭 Consequences

**Positive**
- Availability is visible right where players are ranked; fewer surprises picking an injured player.
- Reuses ingested data; no new fetch, no analytics change, no server writes.
- One shared helper + legend → consistent across the Pool and all four boards.

**Negative / risks (mitigations)**
- **Emoji-only can be cryptic** → a legend caption + a column tooltip name each flag and point to News.
- **`(web_name, team)` join for the trimmed boards** could miss a same-name/same-team edge → acceptable for
  a display flag; the Pool/xG (raw rows) don't join at all.
- **Preseason chances shift** → the flag reflects the current snapshot (as the whole app does); it updates on
  refresh/reseed.

---

### 📊 Validation

Verified (real data): 60 flagged players with `status`/`chance`/`news`; `crowd_flags` carries no injury
signal. Acceptance: `availability_flag` returns the right emoji per status and `""` for available; the Pool
and the four stat boards show a **Fit** column (🚑 for a known-injured player, blank for a fit one) with a
legend; the analytics, `crowd_flags`, the rating, and the number-formatting are unchanged; the existing 613
tests stay green (new tests added).
