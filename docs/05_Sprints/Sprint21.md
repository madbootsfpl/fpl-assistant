# Sprint 021: Validate a Legal Bench (squad polish)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a small correctness closer — no new data)
**Carried Over:** None (Sprint 020 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Sprint 013 (ADR-014) *displays* the bench-implied XI shape but doesn't *police* it — a
declared bench can leave an illegal starting XI. A probe confirmed the fix is clean and
data-supported (no new data):

- **Legal** bench (1 GK, 1 DEF, 1 MID, 1 FWD) → starters **4-4-2** → no issues.
- **Illegal** bench (1 GK, 3 FWD) → starters **5-5-0** → "0 FWD (need 1-3)".
- **Illegal** bench (1 GK, 3 DEF) → starters **2-5-3** → "2 DEF (need 3-5)".
- **Incomplete** (only 2 benched) → 13 starters → *not* validated (no complete XI yet — the
  existing "bench 4 for a full XI" message stands).

The check **reuses `XI_FLEX`** (the legal-formation ranges from Sprint 013: GK 1, DEF 3–5,
MID 2–5, FWD 1–3) — so it's one small pure function, gated to fire only when a *complete*
4-man bench is declared. **No new dependency.**

This sprint is Tony's Sprint 020 pick — closing an open backlog item (ADR-014 follow-on) to
help *complete the phase*.

---

### 🧭 Architecturally, what's new — display the shape, now *check* it too

`--bench` in `--full` shows the implied starting shape (Sprint 013). But a shape can be
*displayable yet illegal*: bench all three forwards and the "5-5-0" prints while being an
illegal XI (0 FWD). This sprint adds the missing **validation**:

```
starters = the 15 minus the declared bench
if exactly 11 starters (a complete 4-man bench):
    each position count must sit inside XI_FLEX (GK 1, DEF 3–5, MID 2–5, FWD 1–3)
    else → warn, listing what's wrong (e.g. "0 FWD (need 1-3)")
```

**Warn, don't block.** The bench is the manager's advisory choice; we *inform* ("this bench
doesn't leave a legal XI: …") and still show the squad — we don't error out. It reuses the
Sprint-013 legal-XI definition, so the rules live in one place.

---

### 🎯 Sprint Goal

**Objective:** When a full 4-man bench is declared, validate that the 11 starters form a
legal XI (per the `XI_FLEX` ranges) and warn clearly if not — closing the ADR-014 gap so the
squad feature is airtight.

#### Success Criteria
- [x] Approach agreed (**ADR-022**) before code
- [x] A pure `legal_xi_issues(starters)` reuses `XI_FLEX`; returns the reasons (empty = legal)
- [x] `render_squad` warns when a **complete** (11-starter) bench leaves an illegal XI
- [x] A legal complete bench still shows the "Starters (11) — {shape} is your XI" note
- [x] Fewer than 4 benched is unaffected (the existing "bench 4 for a full XI" message)
- [x] The warning lists the specific problem(s) (e.g. "0 FWD (need 1-3)")
- [x] It **warns, not blocks** — the squad still prints
- [x] Existing views/objectives unchanged
- [x] Tests cover legal / illegal (each position) / incomplete cases (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-062 | Agree the approach (**ADR-022**): validate only a complete (11-starter) bench, check each position against `XI_FLEX`, **warn not block**, the message format — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-063 | Implement `legal_xi_issues(starters)` (reuse `XI_FLEX`) + the `render_squad` warning. Tests (legal / illegal per position / incomplete) + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-022 recorded + added to the ADR index — _US-062_
- [ ] Update Architecture doc (changelog: bench legality validated) — _US-062_
- [ ] Update `README.md` / Handbook Ch 22 with the bench-legality warning — _US-063_
- [ ] Update the Backlog (mark "validate a legal bench" done) — _US-063_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for twenty sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Validate a complete (4-man) bench's XI legality | Blocking / erroring on an illegal bench (we warn) |
| Reuse `XI_FLEX` for the legal ranges | Auto-fixing the bench for the user |
| A clear, specific warning message | Bench *order* (which sub first) — stays on the backlog |
| Warn-not-block; the squad still prints | Validating an incomplete (< 4) bench |

**External Dependencies:**
- [ ] Existing players data + the stored squad logic; **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Warning fires on an incomplete bench (13 starters) | Med | Gate the check on `len(starters) == 11`; a test covers the incomplete case |
| Duplicating the legal-XI rules | Low | Reuse `XI_FLEX` (one definition, shared with Sprint 013's formations) |
| A blocking error frustrates the user | Low | **Warn, not block** — the squad still prints, the manager decides |
| Message unclear | Low | List the exact problem per position (count + legal range) |

---

### 🗝️ Gating decision (US-062 → ADR-022)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **When.** Validate only when a **complete** bench is declared (exactly 11 starters). Fewer
   benched → no complete XI → the existing "bench 4 for a full XI" message (unchanged).
2. **The check.** Each starter position count must sit inside `XI_FLEX` (GK 1, DEF 3–5, MID
   2–5, FWD 1–3). Any outside → an issue. Reuses the Sprint-013 legal-XI definition.
3. **Warn, not block.** Show the squad, then a clear warning listing the problems. The bench
   is advisory; we inform, not error.
4. **Message.** e.g. "Note: this bench doesn't leave a legal XI — 0 FWD (need 1-3)".

**Worked example to verify at the gate:** on real data — bench 1 GK + 3 FWD → 5-5-0 →
"0 FWD (need 1-3)"; bench 1 GK + 3 DEF → 2-5-3 → "2 DEF (need 3-5)"; a legal 1/1/1/1 bench →
4-4-2, no warning; an incomplete 2-man bench → 13 starters, no legality warning. Confirms the
gate + the message before any code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-062: ADR-022 — validate a legal bench)
* **Completed:** Recorded **ADR-022**: validate only a *complete* 4-man bench (11 starters);
  each starter position must sit inside `XI_FLEX` (GK 1, DEF 3–5, MID 2–5, FWD 1–3, reused from
  ADR-014); **warn, not block** (Tony confirmed) — show the squad + a specific message, don't
  refuse. `legal_xi_issues(starters)` returns the reasons. **Pressure-tested on real data:**
  1/1/1/1 → 4-4-2 legal; 1 GK+3 FWD → 5-5-0 → "0 FWD (need 1-3)"; 1 GK+3 DEF → 2-5-3 → "2 DEF
  (need 3-5)"; incomplete 2-man bench → 13 starters, not validated. Added to the ADR index;
  Architecture §12 changelog. US-062 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-022 (new) + index, Architecture changelog, Sprint21 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Reuses `XI_FLEX` — one legal-XI definition.)
* **Next Steps:** US-063 — implement `legal_xi_issues` + the `render_squad` warning.

#### Session 2 — 2026-08-03 (US-063: legal_xi_issues + the render warning)
* **Completed:** Added `optimizer.legal_xi_issues(starters)` — pure, reuses `XI_FLEX`
  (GK's `(1,1)` reads "need 1", not "need 1-1"); returns specific reasons, empty if legal.
  `render_squad`'s full 4-man-bench branch calls it: issues → a warning; none → the existing
  "is your XI". **Warn, not block** — the squad still prints. **+5 tests → 202 total, all
  green** (legal_xi_issues: legal / 0 FWD / 2 DEF / 2 GK; render: legal → "is your XI",
  illegal → warned + squad still shown; the 13-starter incomplete case unchanged; rewrote the
  one 11-all-MID test to a legal shape). US-063 **complete** — Sprint 021 done.
* **Manual smoke test:** ✅ `squad --full --bench <3 FWD + GK>` → "Note: this bench doesn't
  leave a legal XI — 0 FWD (need 1-3)." (squad still printed); a legal 1/1/1/1 bench → "is your
  XI"; `--help` unchanged.
* **Docs touched:** Handbook Ch22 (bench-validation section), Backlog (item done), Sprint21
  board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 021 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-062 (ADR-022) and US-063. A declared 4-man bench is now
  **validated**: if the 11 starters aren't a legal XI, the tool warns (with the specific
  problem) but still prints the squad. Tests grew 197 → **202**. **No new data or
  dependency** — reuses `XI_FLEX`. A backlog item closed.
* **Carried Forward:** None. Backlog: bench order; an auto-suggested legal bench; the other
  open items (combined defensive value, saved squad, small polish).
* **Key Artifacts / Decisions:** ADR-022 (validate-a-complete-bench, warn-not-block, reuse
  `XI_FLEX`); `legal_xi_issues`; the `render_squad` warning; Handbook Ch22 section.

#### Retrospective
* **What Went Well?**
  - **A tidy correctness closer.** The ADR-014 gap (shape shown but not policed) is closed —
    the squad feature is airtight, and a backlog item is ticked toward completing the phase.
  - **One rule, reused.** `legal_xi_issues` uses the *same* `XI_FLEX` ranges as flexible
    formations — so bench-legality and formations can never disagree. No second definition.
  - **Warn-not-block was the right product call.** The tool proposes; it doesn't submit — so
    it informs and leaves the manager in control.
  - Verified at planning, mechanical to build; DoD held (21st sprint).
* **What Could Be Improved?**
  - The check only covers a *complete* bench — a partial bench isn't "illegal", just
    incomplete (handled by the existing message). Fine, but worth being explicit about.
  - `render_squad` is growing several caveat branches (objective / full / bench / legality);
    still readable, but a candidate for a small tidy if it grows further.
* **Lessons Learned?**
  - Displaying a value isn't validating it — a shape can print yet be illegal.
  - Reuse the definition, not just the idea: sharing `XI_FLEX` keeps two features consistent.
  - Choose warn vs block by what the tool *is* — a proposer, not a submitter.
* **Action Items for Next Sprint (022):**
  - [ ] Consider: combined defensive value, a saved squad, small polish, or bench order —
    keep closing the phase. Check first.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 022):** another backlog closer — combined defensive value, a
saved squad, or a small polish bundle — toward completing the phase.

**Completion Date:** 2026-08-03
**Final Notes:** A small, tidy correctness closer — an illegal declared bench is now warned,
reusing the one legal-XI definition. Sprint outcome: **Successful** — 2/2 stories, zero
roll-over, DoD held, a backlog item closed.
