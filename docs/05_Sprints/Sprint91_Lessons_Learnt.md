# Lessons Learned

**Sprint:** Sprint 091 — Bench order (the auto-sub priority)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Show which bench player subs on first — the auto-sub priority — on My Squad: outfield subs ranked by xP
(1st/2nd/3rd) with the bench GK separated (keeper-only), plus an honest explainer of the FPL rule.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Scoping to a recommendation vs a simulator** — deliver the useful insight (order by value) without
  modelling every edge (per-blank formation legality).
- The pure-helper-then-display split, with the helper reusing the shared horizon xP.

### New Skills Acquired

- The FPL **auto-sub rule**: on a 0-minute starter, the first bench player (in your order) that keeps a legal
  XI comes on; the **bench GK only ever replaces the starting keeper** — so it must be a separate slot, not
  ranked against outfielders by xP.
- A caption that *states the real rule* lets a simple recommendation be honest rather than over-claimed.

---

# What Went Well ✅

- **Honest, bounded scope** — a recommendation (outfield by xP + GK separate), with the caption naming the
  actual rule; no over-promising a simulation.
- **Correct on the key rule** — separating the bench GK keeps the ordering meaningful.
- **Compounds prior work** — the order reuses the horizon-aware xP, so it tracks the Sprint-089 selector.
- 629 → 632 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Should we simulate every possible blank? | FPL applies the first *legal* sub, which depends on which starter blanks | Recommend order-by-xP + a caption stating the rule; defer a full simulator |
| A bench GK can't be ranked with outfielders | it only replaces the keeper | Separate "GK" slot in `bench_order`, not in the xP ranking |
| Testing needs a declared bench | the demo squads have none | Inject a session squad with a valid 15 + a 4-man bench (1 GK + 3 outfield) |
| `seed.db` byte-touch after manual smokes | a SQLite file-open artifact (content unchanged) | `git checkout -- data/seed.db` before staging |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Recommendation vs simulation | Order-by-value is most of the value; simulating every blank is diminishing returns |
| Model the rule that matters | The GK-is-keeper-only rule is the one that would mislead if ignored |
| State the rule in the UI | A caption naming the FPL behaviour keeps a simple recommendation honest |
| Reuse the shared xP | The bench order tracks the horizon for free |

---

# Development Lessons 💻

- Deliver the insight first (order), leave the simulator/setter as clearly-noted follow-ups.
- When a domain rule creates a special case (keeper-only sub), encode it structurally, not as a caveat.
- Inject session state to test a path the demo data can't reach.

---

# AI Collaboration Lessons 🤖

- The backlog line ("which bench player subs on first") mapped cleanly to a small helper + a caption — a good
  example of a bounded decision-support add that ships in one short sprint.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-078 | **Bench order — the auto-sub priority** — a pure `bench_order(bench, scores)` (outfield by xP → 1st/2nd/3rd, then the bench GK → "GK", keeper-only); shown on My Squad with the FPL-rule explainer. A recommendation, not a per-blank simulator; display-only, no analytics drift | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Possible bench-order extensions: annotate the pitch bench cards with the sub number; let the user *set* the
  order (persist it); simulate specific blanks. Backlog still open: season countdown; pronoun-aware chat;
  server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "recommendation now, simulator later" instinct for domain features with combinatorial edges.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → My Squad → a "🔁 Bench order (auto-subs)" line under the pitch
python -m pytest tests/test_optimizer.py -q -k bench_order   # the bench_order unit tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Bench order | The priority your bench subs come on in if a starter blanks |
| Auto-sub | FPL bringing on the first bench player (by your order) that keeps a legal XI |
| Keeper-only sub | The bench GK, which can only replace the starting goalkeeper |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-078 | The bench-order decision + the recommendation-not-simulator rationale |
| `src/analytics/optimizer.py` (`bench_order`) | The pure helper |
| `src/web_streamlit/views/squads.py` (`render_my_squad`) | The bench-order line |

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

- US-241 `bench_order` helper — outfield bench by xP (1st/2nd/3rd) + the GK sub (ADR-078)
- US-242 My Squad bench-order line — the recommended sub priority + the auto-sub explainer

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
