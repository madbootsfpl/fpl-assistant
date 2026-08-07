# Lessons Learned

**Sprint:** Sprint 092 — Set the bench order (persist + reorder the auto-sub priority)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let a manager set their bench sub priority on My Squad — reorder the 3 outfield subs (⬆/⬇) or one-click the
recommended (xP) order — and have it persist (session + download), driving the "Bench order (auto-subs)"
line. The GK stays keeper-only.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Giving an existing field new meaning safely** — `bench_ids` was a positional list used as a set;
  ordering it became the priority with no analytics change.
- Copy-not-mutate mutations + a Streamlit reorder UI (⬆/⬇ + rerun).

### New Skills Acquired

- A field used only as a **set** downstream can gain an **order** for display/edit without touching the
  consumers — the green suite is the proof.
- Streamlit has no drag-reorder, but **per-row ⬆/⬇ buttons** (disabled at the ends) + `st.rerun()` make a
  clean, deterministic reorder.
- A domain rule (the bench GK is keeper-only) should be encoded structurally (excluded from the reorder),
  not left as a caveat.

---

# What Went Well ✅

- **No analytics ripple** — `set_bench` preserving order changed nothing downstream (they use the set); 634
  green confirmed it.
- **Honest UI** — the line shows the *stored* order (what FPL will do), the GK is separate, and the caption
  states the auto-sub rule.
- **Reused prior work** — the "recommended" button is Sprint-091's `bench_order`; the horizon-aware xP; the
  ADR-055 edit model.
- 632 → 634 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| `set_bench` discarded the order | it rebuilt `bench_ids` in squad-position order | Preserve the given order (`list(bench_ids)`) |
| Will ordering `bench_ids` break the analytics? | they consumed it | They use it as a **set** — ordering is safe (suite green) |
| The GK shouldn't be reorderable | it's keeper-only | Exclude it from `move_bench_sub`; keep it last |
| The displayed bench was in *owned* order | built as `[p for p in owned if …]` | Build from `bench_ids` order for the priority display |
| An old test asserted squad-position order | pre-ADR-079 behaviour | Updated to assert the preserved order |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Set-consumed fields can gain order | Downstream that uses `set(x)` doesn't care about order — safe to add meaning |
| ⬆/⬇ reorder in Streamlit | Per-row buttons (ends disabled) + rerun; deterministic, no drag needed |
| Encode the rule | Keeper-only → exclude the GK from the reorder, not a caveat |
| Build from the ordered source | Display the stored order by iterating `bench_ids`, not `owned` |

---

# Development Lessons 💻

- Before repurposing a field, confirm its consumers (set vs order) so you know what's safe to change.
- Persist edits through the copy-not-mutate helpers so the session/download stay consistent.
- Keep a one-click "recommended" reset next to a manual editor — best of both.

---

# AI Collaboration Lessons 🤖

- "Set it, don't just recommend it" mapped to a small model change (order-preserving `set_bench` +
  `move_bench_sub`) + a reorder UI — the recommendation from the prior sprint became the one-click default.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-079 | **Set the bench order** (refines ADR-055/078) — `bench_ids` order = sub priority; `set_bench` preserves order; `move_bench_sub` reorders an outfield sub (GK excluded, keeper-only); My Squad shows the stored order + ⬆/⬇ + a "Use recommended (xP) order" button. Copy-not-mutate; order in the download; analytics use the set (unchanged); no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Possible: set the bench order **on Build** (start in the recommended order); annotate the pitch bench cards
  with the sub number. Backlog still open: season countdown; pronoun-aware chat; server-side persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "confirm the field's consumers before repurposing it" habit — it made this change low-risk.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → My Squad → "Reorder the bench" (⬆/⬇ + Use recommended xP order)
python -m pytest tests/test_web_squads.py -q -k bench   # set_bench / move_bench_sub unit tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Sub priority | The order your outfield bench comes on if a starter blanks |
| `move_bench_sub` | The mutation that swaps an outfield sub up/down in priority (GK excluded) |
| Recommended order | The xP ranking (`bench_order`) offered as a one-click default |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-079 | The set-the-order decision + the "field used as a set can gain order" rationale |
| `src/web_streamlit/squads.py` | `set_bench` (order-preserving) + `move_bench_sub` |
| `src/web_streamlit/views/squads.py` | The My Squad reorder UI |

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

- US-243 Bench-order model + mutations — `set_bench` preserves order; `move_bench_sub` (GK excluded) (ADR-079)
- US-244 My Squad reorder UI — the stored order + ⬆/⬇ reorder + a "Use recommended (xP) order" button

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
