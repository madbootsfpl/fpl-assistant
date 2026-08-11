# Lessons Learned

**Sprint:** Sprint 142 — An intuitive substitution on My Squad

**Dates:** 2026-08-11

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make a substitution on My Squad a **two-dropdown, one-click** action — bring a starter **off** (to the bench) and a
bench player **on** (into the XI), offering **only legal swaps** — and have the pitch **card picker pre-fill "Bring
off"**, so selecting a player flows straight into the sub. From tester feedback: the old "Set the bench (pick 4)"
multiselect didn't match how anyone thinks about a sub.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Design around the Streamlit "static markdown can't call back" wall** — the same constraint we hit in Sprint 139.
  A button *on* the hover card is impossible; the answer is real widgets near the pitch + the picker as the bridge.
- **Reuse the existing mutation + legality helpers** — a substitution is just `set_bench` + `legal_xi_issues`; the
  new `substitute()` helper composes them, so the rules stay in one place (ADR-014/022/079).

### New Skills Acquired

- **Let legality *filter the choices*, not just validate on submit.** Instead of letting someone pick an illegal
  swap and then erroring, the "Bring on" list is pre-filtered to bench players whose swap returns **no** issues — so
  a GK is only offered for a GK, and outfield swaps only when they keep a legal formation. The UI can't offer a wrong
  answer. (The apply path still re-checks, belt-and-braces.)
- **Seed a widget from another, but edge-trigger it.** The picker pre-fills "Bring off" by writing
  `st.session_state["sub_off"]` *before* the selectbox is created — but only when the **picked id changes** (a
  `_sub_prefill_for` marker). Unconditional reseeding every run would trap the field on the picked player; edge-
  triggering seeds once per pick and leaves it user-editable after.
- **A widget value set via `session_state` must be a current option.** Safe here because a *starter* is always in
  the XI (so its label is always in the "Bring off" options) — a benched pick deliberately doesn't seed (it's a
  bring-*on*), it just hints.

---

# What Went Well ✅

- **Small, faithful, low-risk** — session-state only, no engine/server change; reused `set_bench` + `legal_xi_issues`.
- **Honest about the constraint up front** — named the "button on the card is impossible" wall (S139) and offered the
  three real shapes; the owner chose "both" (picker feeds the control).
- **Legality-as-filter** — only legal swaps are ever offered, so the control can't produce an illegal XI.
- 939 → 945 tests (+6); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A button on the hover card | static `st.markdown` HTML can't call back to Python (S139) | Real widgets near the pitch + the picker as the bridge |
| Offering only legal subs | a naive control could pick an illegal swap | Pre-filter "Bring on" to swaps `legal_xi_issues` clears |
| The picker pre-fill trapping the field | reseeding every run would pin "Bring off" to the pick | Edge-trigger on a `_sub_prefill_for` id marker |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Streamlit interactivity | Static HTML can't call back → substitution is widgets + a picker bridge, not a card button |
| Validation vs. filtering | Filter the *choices* by legality so the UI can't offer a wrong swap (still re-check on apply) |
| Cross-widget seeding | Set `session_state[key]` before the widget, but edge-trigger it so it stays user-editable |
| Reuse | A substitution = `set_bench` + `legal_xi_issues`; compose, don't re-implement the rules |

---

# Development Lessons 💻

- When a platform can't do the literal interaction, pick the affordance it *can* do well (a keyed control + a picker).
- Make illegal states unrepresentable in the UI (filter the options), not just rejected after the fact.
- Edge-trigger any "seed one widget from another" so you don't fight the user's own edits.

---

# AI Collaboration Lessons 🤖

- The substitution is a **lineup change**, not a transfer — it moves the XI/bench split of the same 15, mutating
  `st.session_state` exactly like the existing bench controls. No server write, no xP/engine change; the one-xP +
  read-only invariants hold.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — extends **ADR-055** (My Squad edit) + the S139 picker. New `substitute(squad, off_id, on_id, by_id)`
in `web_streamlit/squads.py` (returns `(new_squad, issues)` via `set_bench` + `legal_xi_issues`). A "🔁 Substitute"
control on My Squad (US-351) with the card picker pre-filling "Bring off" (US-352). The "Set the bench (pick 4)"
multiselect is kept below as the bulk path._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (browser smoke):** My Squad → pick a starter on the card picker → "Bring off" pre-fills → pick a bench
  player → Substitute → the pitch + bench update; an illegal swap (the only GK) isn't offered; a benched pick hints.
- **Deferred (backlog):** a truly clickable pitch (needs a bespoke component — rejected as over-engineered);
  drag-and-drop; auto-suggest the best legal sub by xP.
- **Branding** stays parked pending art (resume at `start ADR-103`); **GW1 (2026-08-21)** calibration flip remains
  the data-gated owner thread.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep offering the "here's the platform constraint + the shapes that fit it" framing before building an interaction.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_squads.py -k substitute tests/test_web_streamlit.py -k "substitute or prefills" -q
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Substitution (vs. transfer) | A lineup change — swap a starter with a bench player; the 15 are unchanged |
| Legality-as-filter | Only offer bench players whose swap keeps a legal XI (GK↔GK; a legal formation) |
| Edge-triggered seed | Pre-fill a widget only when the source selection *changes*, so it stays user-editable |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/squads.py` (`substitute`) | The helper — bench math + legality in one place |
| `src/web_streamlit/views/squads.py` (`render_my_squad`) | The 🔁 Substitute control + the picker pre-fill |

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

- US-351 The 🔁 Substitute control (`substitute()` helper + bring off ↔ bring on, legal swaps only)
- US-352 The card picker pre-fills "Bring off" (a benched pick hints)

**Stories Carried Forward:**

- None. (A clickable pitch / drag-and-drop / auto-suggest-the-best-sub are backlog ideas.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
