# Architectural Decision Record: soccerdata as a Data Source — Defer

**Decision ID:** ADR-016
**Date:** 2026-08-03
**Status:** Accepted — **Defer** (do not adopt now; revisit if a real need arises)
**Superseded By / Replaces:** N/A (evaluates the backlog "FBref xG/xA", now generalised)
**Deciders / Participants:** Tony Sheridan (Owner / Product), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tony discovered the `soccerdata` package and asked whether it's worth adopting as a data
source. Sprint 015 was a **spike** to decide with evidence, not opinion. soccerdata wraps
several scrapers (FBref, Understat, WhoScored, …); the candidate value was **npXG**
(non-penalty xG) and richer per-match / defensive stats that FPL doesn't publish.

Full evidence: `spikes/015-soccerdata/FINDINGS.md` (reproducible in a throwaway venv).

---

### 💡 Decision

**Defer.** Do not adopt `soccerdata` now. Proceed with the lighter, FPL-native model.
Record the idea in the backlog as *validated but deferred*, to revisit only if a concrete
need appears that FPL's own data cannot meet.

---

### 🧪 The evidence, against the rubric

| # | Question | Verdict | Evidence |
|---|---|---|---|
| 1 | Is matching reliable? | ✅ Yes | ~95% automatic FPL↔Understat match (formal + common-name layers, team tiebreak); residual ~3–5% ambiguous names need a small override map (like `CLUBELO_TO_FPL`); absent players degrade to `None`. No silent wrong matches. |
| 2 | Is the unique value real? | ⚠️ Real but **narrow** | npXG strips penalties FPL's xG includes (Palmer 5.7 npXG vs 10.6 xG); re-ranks ~3 of the top-10. But **for FPL, penalties score points** — you don't bench a penalty-taker for a low npXG — so the field is *nice-to-know*, not decision-driving. |
| 3 | Is the cost acceptable? | ❌ **No** | Dependency footprint **14 → 72 packages** (pandas, numpy, **selenium + seleniumbase** browser stack); web-scraping fragility (TLS anti-bot bypass); a season-alignment trap (FPL 2025/26 vs Understat 2024/25 silently mis-joined); offline-testing rework. |

**Decision drivers (Tony's, as Product Owner):**
- The data *adds some value* but is **not essential to a decision** — the FPL-native xG/xGI
  we already ship covers the actual choices. The Haaland case is decisive: you pick him
  *partly because* he takes penalties, so penalty-inclusive xG is the right FPL signal.
- The **cost is very high** — dragging in a large scraping/browser stack, with real
  potential to become **tech debt** we maintain later for a marginal field.
- The project charter prizes *"prefer simple, avoid unnecessary complexity"*.

Rubric #3 fails, and #2 is narrow — so the balance is a clear defer.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The app stays lean (14 deps: `requests` + `pulp` + test tooling); no
  scraping fragility, no browser stack, no season-alignment landmine, no offline-testing
  rework. We keep moving on FPL-native features that *are* decision-relevant.
* **Negative / Trade-offs:** We forgo npXG and Understat's richer stats (npXG, xG chain,
  key passes, shots) — a genuine but narrow analytical loss, mostly affecting
  penalty-taker nuance and deep scouting.
* **What we keep:** The spike proved the *path* is viable if we ever need it — matching
  works (~95%), Understat is fast (~3.4s), and the season-alignment gotcha is documented.
  So a future revisit starts from evidence, not zero.

---

### 🛠 Implementation & Migration
* **Components Affected:** None. `src/` and `requirements.txt` are unchanged; all spike
  code is boxed in `spikes/015-soccerdata/` (not shipped, not a dependency).
* **Action Items:**
  - [x] Evidence gathered + rubric verdicts (US-047, US-048)
  - [x] Decision recorded (US-049)
  - [ ] Backlog: add "soccerdata / npXG — validated, deferred (ADR-016)"

---

### 🔄 Review & Reconsideration
* **Revisit if:**
  - [ ] A concrete feature needs a field FPL genuinely lacks (e.g. per-match / shot-level,
    or defensive creativity stats) — *and* it's decision-driving, not just nice-to-know.
  - [ ] A **lighter** path exists — a tiny direct Understat fetch (no full soccerdata /
    selenium / pandas) — that delivers just the wanted field at a fraction of the cost.
* **What would change the call:** value moving from "nice-to-know" to "decision-driving",
  or the cost dropping sharply (a lightweight fetch).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-047, US-048, US-049 (this)
- **Evidence:** `spikes/015-soccerdata/FINDINGS.md`, `match_fpl_understat.py`, `compare_npxg.py`
- **External Docs:** [ADR-010 (ClubElo — external source pattern)](./ADR-010-clubelo-external-source.md) · [ADR-015 (FPL expected goals)](./ADR-015-expected-goals.md) · [Sprint 015](../05_Sprints/Sprint15.md)
