# Lessons Learned

**Sprint:** Sprint 117 — A `history <player>` view (past seasons now, per-GW at GW1)

**Dates:** 2026-08-18

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Pick up the open half of ADR-027/060: a **`history <player>`** view — a player's season-by-season record (real
now) + a this-season per-GW trend (from GW1) — on the CLI and via a grounded `ask`/`chat` intent. A read-view
over data we already ingest; the analytics/xP untouched, every number verified (✓).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Check the data before planning** — the DB confirmed real past-season rows, so the feature isn't dormant.
- **Reuse the grounded-ask pattern** — a new intent = a resolver + an assembler + facts + cues.

### New Skills Acquired

- **"Wired-dormant" can still ship value now.** The per-GW half is empty preseason, but past seasons are real —
  so the view is useful today and *also* lights up at GW1. Not every GW1-gated feature has to wait.
- **Facts are the verification hook.** Putting the last season's points/minutes/xGI into `facts` means the LLM
  narration is checked against them (✓) — a lookup answer can't hallucinate a number.
- **Place a new intent by specificity.** `history` sits after `worth` so *"is X worth it"* still wins, and its
  cues (*last season · how did · past seasons*) don't collide with the squad commands — a routing test pins it.
- **A read-view is trivially a lens.** It reads stored rows and formats them; the `decision_xp` invariant isn't
  even in question, and the read-only web guardrail holds by construction.

---

# What Went Well ✅

- **Real data now** — `history Haaland` shows four seasons immediately.
- **Small, reused surface** — the CLI command + the ask intent both call one pure assembler + renderer.
- **Grounded end-to-end** — the answer narrates + verifies, or degrades to the facts block.
- 751 → 762 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Overwrote an existing test file | `Write` to `tests/test_history.py` (ingestion tests already there) | Caught via the dropped suite count → restored from git → new tests in `test_history_view.py` |
| Keep `history` from stealing `worth` | both are single-player questions | Place `history` after `worth`; distinctive cues; a routing test |
| A history answer could hallucinate | free narration | Put the numbers in `facts` → the verifier checks them (✓) |
| Price units looked wrong | a mis-divide in a debug probe | The stored cost is already £m (the ingestion test confirms) — deferred cleanly |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Verify data first | It decides "dormant" vs "useful now" |
| Grounding hook | Facts carry the numbers the narration is checked against |
| Intent placement | Order by specificity; pin with a routing test |
| Read-view lenses | No xP contact → the invariant is automatic |

---

# Development Lessons 💻

- **Before `Write`-ing a new test module, check for an existing file of that name** — prefer a distinct name or
  an `Edit`; a suite-count drop is the tell.
- Reuse the resolver + assembler + facts pattern for any new single-entity `ask` intent.
- Put every user-facing number into `facts` so the answer verifies.

---

# AI Collaboration Lessons 🤖

- A lookup intent stays honest the same way a recommendation does: the data is the truth, the facts anchor the
  narration, and the verifier catches any drift.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-295/296 extend **ADR-027/060** (history ingest) + **ADR-037** (grounded ask). New:
`analytics/history.py::player_history`; `ui/history.py::render_player_history`; the CLI `history <player>`
positional; a `history` `ask`/`chat` intent (`_decide_history`)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **A per-season price / price-change column** in the history view (the cost units are verified now).
- **A web History tab** / rolling-form sparkline as a visual pass.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the per-GW history fills → the trend goes live; Data Hardening + xP calibration;
  the price/form/ownership signals sharpen.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Guard against clobbering: check `ls tests/` (or an `Edit`) before creating a same-named test module.

---

# Key Commands Learned

```text
python app.py history Haaland          # a player's season-by-season record
python app.py ask "Haaland's history"  # the same, narrated + verified (✓)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| History view | A player's past-season record + this-season per-GW trend |
| Pts/90 | Points per 90 minutes — a minutes-fair rate |
| Read-view lens | A view over stored data that never touches `decision_xp` |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/history.py` | The pure history assembler |
| `src/ui/history.py` | The season table + per-GW trend renderer |
| `src/ask.py` (`_decide_history`) | The grounded history intent |

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

- US-295 A `history <player>` view (analytics + CLI) — past seasons now, per-GW at GW1 (ADR-027/060)
- US-296 A grounded `history` ask/chat intent — "how did X do?" → the view, verified (ADR-037)

**Stories Carried Forward:**

- None. (Price column + a web History tab are follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
