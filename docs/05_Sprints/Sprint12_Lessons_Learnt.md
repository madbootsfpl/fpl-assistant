# Lessons Learned

**Sprint:** Sprint 012 — A Declared Bench (`--bench`)

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let the manager **declare a bench** — `squad --full --bench <1–4 players>` — so the full
squad renders as a clear starters + bench view (bench marked `**`, sorted to the end),
with a starters' points subtotal that finally means "weekly".

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing the forcing mechanism (`pick == 1`) instead of adding new machinery.
- Annotating a result (a `bench` tag) and letting display do the rest.
- Extracting a pure helper (`validate_bench`) so validation is testable without a DB.

### New Skills Acquired

- Turning a retro reflection directly into a sprint plan.
- Making honesty an *output* (a starters' subtotal), not just a caveat.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- The feature came from Tony's own Sprint 011 reflection and landed as sketched.
- Visibility and honesty turned out to be one fix — the subtotal answers ADR-012's caveat.
- The reuse pattern held a third straight sprint — tag + marker + sort key + subtotal.
- The gate proved the mechanism on real data; the 3-part DoD held (12th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Bench must sort to the end without disturbing the XI order | Shared sort function | `bench` as the primary key — constant-False with no bench, so order is unchanged |
| Cap / conflict logic lived in a DB-bound handler | Hard to unit-test | Pure `validate_bench(bench, include, exclude)` → messages |
| The subtotal is a true XI only at a full 4-man bench | Fewer than 4 benched | Label by count; soften the caveat only when 11 starters |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse | Benching *is* forcing-in; the new work is annotation + display |
| Sort keys | A constant-valued key leaves an existing order untouched |
| Honesty as output | Show the starters' subtotal rather than caveating the squad total |
| Pure helpers | `validate_bench` keeps a handler's logic testable without a database |

---

# Development Lessons 💻

- Add the concept as a *tag* on the result, then let the renderer interpret it.
- A marker legend that only shows markers actually used keeps output clean.
- Reach for the same seam again (`--include` → `--bench`) before inventing a new one.

---

# AI Collaboration Lessons 🤖

- Tony's retro reflection was specific enough to plan against almost verbatim.
- The gate's worked example (run live) proved the tag/sort/subtotal before any code.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-013 | A declared bench (`squad --bench`): force-in + `bench` tag + `**`/sort-to-end; implies `--full`; cap 4; conflicts errored; starters' subtotal labelled by count | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Flexible formations, bench *order* (who subs first), a saved/persistent squad, or FBref
  xG/xA once feasible.
- Watch the growing `squad` surface (`--full`, `--bench`, `--include`, `--exclude`,
  `--objective`) — a future tidy-up may help.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep turning retro reflections into the next plan; keep the gate + 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --bench Dubravka Diop        # declare a bench (** , shown last)
python app.py squad --full --bench A B C:TEAM D   # a full 4-man bench → Starters (11) = your XI
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Declared bench | A bench the manager names (vs one the solver would pick) |
| Result tag | A flag added to a result row (`bench`) for the display to read |
| Starters' subtotal | Points of the non-bench players — the honest weekly number |
| Pure helper | A function with no I/O — same inputs, same outputs, easy to test |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-013 | Records the declared-bench design + the starters'-subtotal rule |
| Handbook Ch 22 | Optimisation, now with the declared-bench section |

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

- US-040 Declared-bench design + ADR-013
- US-041 The `squad --bench` command

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
