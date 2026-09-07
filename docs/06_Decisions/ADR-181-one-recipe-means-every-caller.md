# Architectural Decision Record: One recipe means every caller

**Decision ID:** ADR-181
**Date:** 2026-09-07
**Status:** ✅ **Accepted — built** (Sprint 242, 2026-09-07). **1731 → 1733 tests, ruff clean.**
**Superseded By / Replaces:** Repairs a gap left by [ADR-173](./ADR-173-minutes-you-have-actually-played.md);
enforces [ADR-041](./ADR-041-one-xp-metric-and-squad-build-intent.md)'s *one xP recipe* at the **call site**.
**No `decision_xp` change** — the recipe was already right; one surface was not using it.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner-reported, from the deployed app:

> *"Bug: different recommendations from My Squad 'what should I do this week' and captaincy."*

Two surfaces on **the same page**, for **the same squad**, in **the same gameweek**, naming different
captains at different projections. Reproduced immediately on the live data:

```
Captain tab      B.Fernandes 4.8 · Virgil 4.5 · João Pedro 4.3 · Rice 4.3 · Truffert 4.3
This week        João Pedro  6.3 · B.Fernandes 5.4 · Mbeumo 5.1 · Virgil 4.6 · Gibbs-White 4.5
```

Not a rounding difference: **a different captain**, and the same player (B.Fernandes) priced 4.8 against 5.4.

#### The cause — one argument, one call site

```python
# src/web_streamlit/views/squads.py, render_captain
minutes_weight = minutes_weight_from_history(history)          # ← no gw_history
```

**ADR-173** made the minutes weight prefer the minutes a player has *actually played this season* over last
season's share — the fix that closed the Kinsky bug and stopped Calafiori being sold. It reads that from the
per-gameweek history, passed as a second argument.

Every other caller passes it — `ask` twice, the CLI's `captain` command, `decision_xp` itself. **The Captain
tab never did**, and its own caller never handed it the data to pass. So one surface was still running the
pre-ADR-173 model while every other surface ran the current one.

#### Why it was invisible for four days

The signature makes the argument optional, so omitting it is not an error, not a warning, and not a crash.
**It silently prices a different player.** ADR-173 shipped on 2026-09-02 and moved 186 players; this surface
kept the old numbers and nothing said so.

#### Decision Drivers

- **Driver 1 — ADR-041 is a claim about surfaces, not about a function.** *"One xP recipe"* is worth nothing
  if a caller can opt half-way out of it by leaving an argument off.
- **Driver 2 — this is a shape this project has paid for before.** The reported-departure signal needed
  teaching to **six** surfaces one at a time (ADR-151→156), every one found by the owner using the product.
  A new fact reaching some call sites and not others is the recurring failure, not a one-off.
- **Driver 3 — the next omission must fail in the suite, not in his hands.**

---

### 🎯 Decision & Justification

**1. `render_captain` takes and forwards `gw_history`**, and its caller passes the value the page already
holds. One line each; the two surfaces now agree exactly:

```
This week   : João Pedro 6.3
Captain tab : João Pedro 6.3          AGREE
```

**2. A cross-surface guard**, comparing the two rather than pinning either. Pinning a name would fail every
time the data moves and would still say nothing about *agreement*, which is the requirement.

**3. A sweep guard** treating the second argument as **mandatory at every call site**. Any
`minutes_weight_from_history(x)` with a single argument fails the suite, naming the file. That is the
Driver-2 lesson made mechanical: the next surface to forget it is caught by CI, not by the owner.

---

### 🔬 Found while building — the first guard was testing itself

The cross-surface guard, as first written, **recomputed** the Captain tab's picks with the correct arguments
and compared them to the week's answer. Mutation-testing killed it: with the bug restored, it **passed**.

> **A test that rebuilds the thing under test is testing the test.** It never touched `render_captain`, so
> the code that was getting it wrong was not in the path at all.

Rewritten to drive the real page through `AppTest` and read the **rendered captain card**, it now fails on
both layers of the mutation — the view dropping the argument, and the page not passing it.

This is the fifth guard in six sprints that passed while protecting nothing, and it is a new member of the
family: not a hedge, not a source scan, not a skip — **a faithful re-implementation of the correct
behaviour, standing in for the code that was wrong.**

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the page stops contradicting itself; ADR-173's correction finally reaches the last
  surface that needed it; the failure mode is now mechanical rather than observational.
* **Negative Impact / Trade-offs:** the sweep guard is a text scan over `src/`, so it reasons about how a
  call is *written* rather than what it *does*. A caller that passed `None` explicitly would satisfy it.
  Accepted as strictly better than nothing, and stated here rather than implied.
* **Risks & Mitigations:**
  - **Risk:** another optional argument develops the same split. **Mitigation:** the pattern is named here;
    the sweep is a template.
  - **Risk:** a legitimate call site genuinely wants history-only. **Mitigation:** none exists today, and one
    would have to argue for itself in this ADR's terms rather than appear by omission.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`views/squads.py`, `pages/1_My_Squad.py`), Tests, Docs
* **Action Items:**
  - [x] `render_captain` accepts and forwards `gw_history`; the page passes it
  - [x] Guard: the Captain tab's **rendered card** names the same captain, at the same xP, as the week's answer
  - [x] Guard: no call site drops the in-season history
  - [x] Mutation-test both, at both layers (the view, and the page that feeds it)
  - [x] Sweep every other `minutes_weight_from_history` call — `ask` ×2, CLI, `decision_xp` all correct
  - [ ] Owner reboot → confirm the two surfaces agree in the app

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
**Not applicable** — no surface renamed, moved or retired. A number changes on one tab, toward the number
every other surface was already showing.

---

### 💡 The lesson

> **"One recipe" is a claim about every call site, not about the function.**

`decision_xp` has been correct since ADR-173. The bug lived in an argument list. A shared primitive with an
optional refinement gives every caller a silent opt-out, and the caller that takes it does not look broken —
it looks like an older, plausible answer, which is far harder to spot than a crash.

The mechanical form, which is what the sweep guard encodes: **when a correction lands in a shared helper
behind an optional argument, the argument stops being optional.**

---

### 🔗 References & Related Artifacts
- **Repairs:** [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the in-season minutes share
- **Enforces:** [ADR-041](./ADR-041-one-xp-metric-and-squad-build-intent.md) — one xP recipe
- **Same shape as:** ADR-151→156 — one fact, six surfaces, each found by the owner
- **Found by:** the owner, comparing two answers on one page — the fifth analytics fault this week found by
  using the product rather than by a test
