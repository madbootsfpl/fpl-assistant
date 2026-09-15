# Architectural Decision Record: Admit up to the cap, then waitlist

**Decision ID:** ADR-193
**Date:** 2026-09-15
**Status:** ✅ **Accepted — built** (2026-09-15). **1788 → 1793 tests, ruff clean.**
⚠️ **Inert until `FPL_USER_CAP` is set** in the deployed secrets — see §🛠.
**Superseded By / Replaces:** Connects [ADR-098](./ADR-098-capped-email-registration-gate.md)'s cap to
[ADR-106](./ADR-106-google-auth-and-per-user-persistence.md)'s Google gate. [ADR-102](./ADR-102-beta-waitlist.md)'s waitlist is unchanged and
still catches everyone over the cap.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> **Owner:** *"Our onboarding process needs to change, people are getting stuck in the waitlist. We need to
> auto-allow them access up to the max number and then enter the waitlist."*

The Google-auth gate (ADR-106) had exactly two outcomes:

```
on the allow-list  → admit
otherwise          → waitlist
```

Nothing put anyone **on** the allow-list except the owner, by hand, in the Supabase dashboard. So every new
tester queued behind a manual step, and a beta that had room sat with people waiting outside it.

#### The machinery already existed

`user_store.register(email, cap)` has done this since **ADR-098**: admit under the cap, return `"full"` at it.
The registration gate (the older shared-code mode) calls it. **The Google gate never did** — the cap was read
in `access.py` for one branch and ignored in the other, and `BETA.md` even recorded *"no `FPL_USER_CAP`
needed"* for auth mode.

⭐ **This was not a missing capability. It was a missing branch** — and the older, less-used path was the one
that had it.

---

### ✅ Decision — what shipped

**1. One step between the two existing outcomes.**

```
on the allow-list           → admit
else, register under cap    → admit          ← new
else                        → waitlist       (unchanged)
```

**2. The admit path is shared, not duplicated.** Both routes call one `_admit()` closure — session flags, the
ADR-142 sign-in stamp, and US-362's per-user squad link/restore. ⭐ *Two routes to the same state is how the
second one quietly forgets a step.*

**3. Failure lands on the waitlist, never on a stack trace.** `register` raises on a malformed email, an
unconfigured store, or a store that is down; all three are caught and fall through to the waitlist a user
already understands. **The only path to `_admit()` is an explicit `"in"`.** ⭐ *The failure path of a gate is
the gate.*

**4. An allow-listed tester never consumes a registration.** The allow-list is checked first, so a full beta
cannot lock out the people it was built for.

**5. No cap set means no change.** `FPL_USER_CAP` unset → the branch is skipped and the gate stays
invite-only, byte-identical. ⭐ *A change to who can get in should require saying a number.*

#### The copy moved with the posture, because it had to

While there is room under the cap this is **open-until-full, not invite-only**, and the screens said
otherwise — *"private beta"*, *"isn't on the invite list yet"*. Both now describe the rule that actually runs.

The waitlist line mattered most. It said *"We'll be in touch as spots open"* — **a promise that needed a person
to keep it, and nobody was keeping it.** That is precisely how the queue became permanent. It now says what is
true and needs nobody: places free as testers leave, sign in again and you are let straight in if one has.

⭐ **Access copy is a claim about who can get in, and it expires the moment the rule does.**

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the cap stops being decorative; a tester who arrives while there is room is using the
  app in the time it takes to sign in; and the owner stops being a step in his own funnel.
* **Negative Impact / Trade-offs:** **this is a real change of posture.** Anyone with a Google account who
  finds the URL is admitted until the cap fills — there is no invite any more while places remain. That is the
  decision, taken deliberately rather than inherited.
* **Risks & Mitigations:**
  - **Risk:** junk sign-ups consume real places. **Mitigation:** the cap bounds it, and rows can be deleted —
    deleting one now genuinely frees a place, which it did not before.
  - **Risk:** two simultaneous sign-ups exceed the cap by one. **Mitigation:** accepted, and already documented
    in `register`'s own docstring as the count-then-insert race. A hobby beta does not need a transaction.
  - **Risk:** the store is down and everyone gets waitlisted. **Mitigation:** that is the designed degradation,
    and it is guarded by a test that raises from `register`.

---

### 🛠 Implementation & Migration
* **Components Affected:** `web_streamlit/auth.py` (the gate branch + both screens), `tests/test_auth.py`,
  `docs/BETA.md`
* **Action Items:**
  - [x] The branch, the shared `_admit()`, the failure path
  - [x] Copy on both screens rewritten to the rule that runs
  - [x] Guards: admitted under the cap · waits at the cap · a store failure waitlists rather than raising ·
        an allow-listed user never consumes a registration · **no cap set = unchanged**
  - [x] Mutation-test every guard — five mutants, all red
  - [ ] ⚠️ **OWNER: set `FPL_USER_CAP` in the deployed Streamlit secrets.** Until it is set this ADR changes
        **nothing** — the gate stays invite-only. The number you set is how many auto-admits happen before the
        waitlist starts.
  - [ ] Watch the first few sign-ups, then decide whether the number is right — it is one secret, no deploy.

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A queue with no automatic exit is a queue with no exit.**

The waitlist worked exactly as designed: it captured people and held them. What it never had was a rule for
letting anyone *out* — that was a human, and the human was busy shipping. The feature was not broken, it was
**half a mechanism**, and the missing half looked like an admin task rather than a defect.

The narrower one, which is this project's recurring shape: **the capability existed and the surface people
actually used did not call it.** Same as ADR-191, where `suggest_transfer_plan` had been correct since ADR-035
and only the week's answer was still asking the old primitive. ⭐ *"Is this function used?" answers yes. The
question that finds these is "does the path a real user takes call it?"*

---

### 🔗 References & Related Artifacts
- **The cap:** [ADR-098](./ADR-098-capped-email-registration-gate.md) · `user_store.register`
- **The gate it was missing from:** [ADR-106](./ADR-106-google-auth-and-per-user-persistence.md)
- **The waitlist, unchanged:** [ADR-102](./ADR-102-beta-waitlist.md) · *remove me* is ADR-122
- **The same shape, four days earlier:** [ADR-191](./ADR-191-spend-the-transfers-you-hold.md)
- **Found by:** the owner, watching real testers queue
