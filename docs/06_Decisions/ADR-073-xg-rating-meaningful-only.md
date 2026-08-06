# Architectural Decision Record: Rate the xG board only where xGI is meaningful

**Decision ID:** ADR-073
**Date:** 2026-08-06
**Status:** Accepted
**Superseded By / Replaces:** **refines ADR-071** (the quality rating). No change to the `quality_band`
helper or the analytics — only *which rows* the xG board rates and *what pool* it rates them against.
Triggered by a tester bug report.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tester on the Players **xG** board: *"how can 0 be good and 56 be good?"* — goalkeepers show `xGI 0` /
`xGI 0.04` yet get **🟢 excellent / good**, and the one rating sits in the row next to both `xGI` (0) and
`xGC` (56), so it reads as ambiguous.

The rating (ADR-071) rates **xGI** (higher = better), "relative to the players shown". Two problems make it
wrong on this board:

**Verified in code (real data):**
- **xGI is noise for goalkeepers** — GK xGI max is **0.22**, median **0**. A keeper's "expected goal
  involvement" carries no signal, so rating it is meaningless.
- **172 / 572 players have 0 minutes** (backups) — no signal, yet they're rated.
- The pool is *every shown row including the zeros*. So when the board is filtered to **GK**, the pool is
  entirely ~0 and a keeper with `0.04` lands **top 19% of keepers → 🟢 excellent**. The *meaningful* pool
  (outfield, ≥900 mins) is **n=248, median xGI 4.12, max 28.17** — a sensible thing to rate against.
- The rating column ("Rating") is the **last** column, after `xGC`, so it visually attaches to the wrong
  number.

**Clean sheets is fine** — it's already gated (`defensive_solidity`: DEF/GK, ≥900 mins) and `xGC/90` is
meaningful for everyone it shows.

#### Decision Drivers
- **Honest** — a rating must only appear where the metric is a genuine signal for that player.
- **Useful** — keep the "is this xGI good?" cue for attackers (the tester valued the clean-sheets rating).
- **Unambiguous** — the rating must clearly be about xGI, not the xGC in the same row.
- **Minimal** — reuse the ADR-071 helper; change only inputs (rows rated, pool), not the rating maths.

---

### ✅ Decision

**1. Rate xGI only where it's meaningful.** On the xG board, a row is rated only if it is **outfield**
(`position != "GK"`) **and** has **≥900 minutes** **and** has a non-null `xGI`. The percentile is computed
over **exactly that rated pool** (not all shown rows), so an attacker's xGI is ranked against real
attackers who've played — not against a sea of zeros. Rows that don't qualify (keepers, low-minutes,
no-data) show a blank **—**, not a colour.

**2. Name and place the column so it's clearly about xGI.** Rename the column **"Rating" → "xGI rating"**
and move it **right after the `xGI` column** (order: `xG · xA · xGI · xGI rating · xGC`), away from `xGC`.
Its tooltip: *"Attacking quality (xGI) vs outfield players with ≥900 mins; keepers & low-minutes players
aren't rated."*

**3. No change to the rating maths or other boards.** `quality_band`/`rating_cell` (ADR-071) are untouched;
this is purely which rows are rated and which pool they use. **Clean sheets** (xGC/90) is already gated and
stays as-is.

---

### 🔀 Alternatives Considered

- **Remove the rating from the xG board.** Rejected — attackers lose a useful at-a-glance xGI cue; the fix
  is to scope it, not drop it.
- **Rate every player within their own position (minutes-gated).** Rejected — a keeper rated against other
  keepers on xGI is still ranking noise ("top 19% GK by xGI" means nothing); blanking GKs is the honest
  outcome.
- **Round/zero the display instead.** Rejected — the raw xGI values are fine; the bug is *rating* zeros, not
  showing them.
- **Also min-minutes-gate the whole xG *display*.** Deferred — the board intentionally shows every player's
  season totals; only the *rating* needs the gate. (Blanked rows still show their raw numbers.)

---

### 🧭 Consequences

**Positive**
- Ratings appear only where xGI is a real signal; keepers and no-minutes players are honestly left unrated.
- Attackers are ranked against attackers → the colour actually means something.
- The "xGI rating" label + its position next to xGI removes the "is this about xGC?" ambiguity.

**Negative / risks (mitigations)**
- **Blank cells for many rows** (all keepers, all 0-minute players) → intended and honest; a `—` reads as
  "not rated", and the tooltip explains who's excluded.
- **A narrow outfield filter → a small rated pool → coarse quintiles** → acceptable, same as ADR-071; the
  legend already says "vs the players shown".
- **≥900-mins bar excludes early-season rotation players** → matches the other boards' convention; revisit
  the threshold post-GW1 if it proves too strict.

---

### 📊 Validation

Verified (real data): GK xGI is ~0 (max 0.22); 172 players have 0 minutes; the outfield ≥900-min pool
(n=248, median 4.12) is the sensible rating base. Acceptance: a goalkeeper and a zero-minute player show a
blank **—** (no colour) on the xG board; an outfield ≥900-min player is rated against the outfield pool; the
column reads **"xGI rating"** and sits immediately after `xGI`; Clean sheets and `quality_band` are
unchanged; the existing 612 tests stay green (new tests added for the exclusions).
