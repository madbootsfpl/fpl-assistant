# Lessons Learned

**Sprint:** Sprint 143 — Clearer transfers (My Squad + accept the AI plan)

**Dates:** 2026-08-11

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

From tester feedback: make transfers easy from **both** My Squad and the Transfer page, **flag overspend**, and let
the Transfer page **accept AI-suggested transfers**. Grounding revealed most of this already existed — so the sprint
became *clarify + close three small gaps*, not build-from-zero: rename the My Squad transfer (distinct from the new
Substitute), a **live** overspend flag, an **include-injured** option, and — the one real feature — **applying the
coordinated AI plan** (not just a single swap).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Ground the feedback in the code before planning.** Reading `render_my_squad` / `render_transfer` first showed
  ~⅔ of the ask already shipped — so we didn't rebuild it, we clarified it. Saved a sprint's worth of duplication.
- **The N-of-a-thing mirrors the one-of-a-thing.** `apply_transfer_plan` is `apply_transfer` over a dict of
  `out→in` pairs with a single legality check — same shape, same guarantees.

### New Skills Acquired

- **"Already built" feedback usually means a *naming* problem.** The tester asking for "transfers on My Squad" when
  they were already there was the tell — and we'd made it worse ourselves by adding **🔁 Substitute** right above a
  control still called **"Swap a player"** (synonyms). The fix was a rename + a one-line distinction, not a feature.
- **Flag state *live*, not only on submit.** The overspend check existed but only fired *after* applying. Computing
  the projected 15-cost on each rerun (the selectbox change already reruns) surfaces *"£X over"* **before** the
  click — the same data, shown at the moment of decision.
- **Apply a coordinated set atomically.** `apply_transfer_plan` maps *all* `out→in` first, then validates the whole
  15 **once** — so the plan is accepted or rejected as a unit, never left half-applied.

---

# What Went Well ✅

- **Right-sized by grounding** — the plan honestly said "most of this exists", so scope was clarify + one feature.
- **Small, faithful, low-risk** — reused `apply_transfer` / `suggest_transfer_plan`; session-state only, no engine
  or server change.
- **Fixed a confusion we'd introduced** — Substitute (lineup) vs Transfer (a new player) now read as distinct.
- 945 → 952 tests (+7); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "Add transfers to My Squad" — but they existed | the control was named "Swap a player" (clashing with 🔁 Substitute) | Rename → "Transfer" + a Substitute-vs-Transfer caption |
| Overspend only known after applying | the check lived in `apply_transfer` (post-apply) | Compute the projected cost each rerun → a live flag before apply |
| The AI *plan* couldn't be accepted | only the single-swap branch had an Apply button | `apply_transfer_plan` + an "Apply this plan →" on the `count>1` branch |
| Two existing tests keyed on old labels | renamed "Replace"/"With" → "Transfer out"/"Bring in" | Updated the two label assertions |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Read before planning | Grounding feedback in the code turns "build X" into "clarify X" more often than you'd think |
| Naming | Two near-synonym controls (Substitute/Swap) side by side read as one — rename to disambiguate |
| Live feedback | Show a derived flag (overspend) at the moment of choice, not only on submit |
| Atomic multi-op | Map all `out→in`, validate the whole result once — accept/reject as a unit |

---

# Development Lessons 💻

- Before building on feedback, read the exact code path — "make it easier" is often "name it clearly."
- Compute decision-relevant flags on every rerun so they show *before* the commit, not after.
- Build the N-case as the 1-case over a set + one whole-result check; reuse the same legality guard.

---

# AI Collaboration Lessons 🤖

- Both stories are **session-state only** — `apply_transfer` / `apply_transfer_plan` mutate a copy of the squad and
  the caller sets it active; no server write, no xP/engine change. The read-only + one-xP invariants hold. The
  Transfer page's AI plan comes from `suggest_transfer_plan` (the analytics decide); "Apply" just commits it.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — extends **ADR-055** (My Squad edit) + **ADR-046** (Transfer). New `apply_transfer_plan(squad, plan,
players)` in `web_streamlit/squads.py`. My Squad's "Swap a player" → **"Transfer"** (owner's steer: plain *Transfer*)
with a Substitute-vs-Transfer caption, a live overspend flag, and an opt-in include-injured toggle (US-353). The
Transfer page gains **"Apply this plan →"** for the coordinated multi-transfer suggestion (US-354)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (browser smoke):** My Squad → **Transfer** reads distinctly from **🔁 Substitute**; a pricey buy flags the
  overspend **live**; **Include injured/suspended** surfaces flagged players. Transfer page → a 2–3 transfer plan
  **applies** with "Apply this plan →".
- **Deferred (backlog):** points-hit (−4) modelling of a plan (GW1+, live); a My Squad "apply the best suggested
  transfer" shortcut; wildcard/free-hit-aware planning.
- **Branding** stays parked pending art (resume at `start ADR-103`); **GW1 (2026-08-21)** calibration flip remains
  the data-gated owner thread.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep opening a feedback item by reading the exact code path first — it reframes "build" as "clarify" surprisingly
  often.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_squads.py -k "apply_transfer_plan" tests/test_web_streamlit.py -k "transfer" -q
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Transfer (vs. Substitute) | Bring in a **new** player (sell one of your 15); Substitute is a lineup change |
| Live overspend flag | The projected 15-cost / bank shown *as you pick*, before you apply |
| `apply_transfer_plan` | Accept a coordinated N-transfer plan atomically (one legality check) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/squads.py` (`apply_transfer` · `apply_transfer_plan`) | The 1- and N-transfer appliers |
| `src/web_streamlit/views/squads.py` (`render_my_squad` · `render_transfer`) | The Transfer control + the plan-apply |

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

- US-353 My Squad transfer — renamed "Transfer" (+ Substitute distinction), a live overspend flag, include-injured
- US-354 Accept the coordinated AI transfer plan (`apply_transfer_plan` + "Apply this plan →")

**Stories Carried Forward:**

- None. (Points-hit modelling / a My Squad apply-best-swap shortcut / chip-aware planning are backlog ideas.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
