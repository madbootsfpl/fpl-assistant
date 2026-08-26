# Architectural Decision Record: Signing in is not saving a squad

**Decision ID:** ADR-142
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 196, 2026-08-26). **1377 → 1384 tests, ruff clean.**
⏳ **One owner action:** add the `last_seen` column (one line of SQL, below). Until then the panel degrades to
its old behaviour and *says so*.
**Superseded By / Replaces:** Corrects the tester-activity half of ADR-120. **Does not touch ADR-100** — the
anonymous event stream stays anonymous and is never joined to a name.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, reading the live Admin panel:

> It's not a true reflection of who is logged in — tesheridan@yahoo.com is active, and tony.e.sheridan has
> also been active in the last 24 hours.

The panel showed **Registered 25 · 🟢 Active 1 · 🟡 Dormant 6 · ⚪ Never 18.**

**The cause, found in the code rather than guessed at.** "Active" was never measuring what its label says. The
roster's only signal was `cloud_store.updated_at_by_handle` — **the `updated_at` on a tester's saved squad
row**. So the four metrics actually read:

| the label says | what it measured |
|---|---|
| 🟢 Active | saved a squad in the last 7 days |
| 🟡 Dormant | last **saved a squad** 7–30 days ago |
| ⚪ Never | has never **saved a squad** |

**Saving a squad is a rare, deliberate act. Using the app is not.** Most people sign in, look at their team,
read the boards and leave — they never press save. So the panel was reporting **18 of 25 testers as "never"**
while at least two were using it daily, which is precisely the failure mode ADR-120 recorded as the thing to
watch for. It just diagnosed it as a hashing mismatch; it was a definition mismatch.

**This was documented and still wrong**, which is the part worth keeping. A caption under the four metrics did
say *"sees signed-in + squad-persisted activity only"*. A disclaimer under a number does not undo the number:
four large figures labelled Active / Dormant / Never assert something, and a line of small grey text below
them does not retract it. **If the caption has to explain that the label is untrue, the label is the bug.**

---

### ✅ Decision

**1. Record when someone actually signs in.** `user_store.touch_last_seen(email)` stamps
`beta_users.last_seen` at **admit** — once per session, in the one place the app knows a person has arrived.
Not per page view: the roster only asks *which day* someone was last here, so a write per navigation would buy
no extra signal.

**This is not a de-anonymisation.** The ADR-100 event stream stays anonymous and untouched. This is the
**owner's own allow-list** — a table that already stores the email — learning when that person last arrived.
The two are never joined, and the panel says so.

**2. Two signals, kept apart, because they answer different questions.**

| column | means | who it finds |
|---|---|---|
| **Last used** | signed in | who is *visiting* |
| **Last saved a squad** | pressed save | who is actively *managing a team* |

Status is judged on the sign-in. The save time stays as its own column — it is genuinely the stronger signal
of engagement, and collapsing the two is what caused the bug in the first place.

**3. It degrades to the old behaviour, loudly.** The column has to be added by hand, so until it exists every
read and write 400s. Then: `last_seen_by_email` returns `{}`, status falls back to the save time (exactly what
the panel did before), and a **warning names the missing column and gives the SQL**. The alternative —
silently showing a column of dashes — would read as *"nobody has been here"*, a worse lie than the one being
fixed.

```sql
alter table beta_users add column if not exists last_seen timestamptz;
```

**4. Every store call is best-effort and silent.** A tester must never see an error because an admin panel
wants a nicer number.

### ⚠️ Risks

- **Signed-out browsing is still invisible**, and always will be — there is no identity to attribute it to.
  The caption says so rather than implying the panel sees everything.
- **Back-dating is impossible.** Everyone reads ⚪ never until they next sign in, so the numbers will look
  *worse* for a few days before they look right. Worth expecting rather than re-diagnosing.
- **One extra write per session.** A PATCH on a single row at admit — negligible beside the reads the same
  sign-in already does.

### 🧪 Definition of Done

1. **Tests** — status follows the sign-in and not the save; both signals stay on the row; the fallback when
   sign-in data is absent; the PATCH targets the cleaned email; a missing column is silent on both read and
   write; nothing is called when the store is unconfigured.
2. **Manual smoke** — ⏳ owner: run the SQL, sign in, confirm the panel moves.
3. **Docs** — this ADR, ADR-120 cross-referenced, PROJECT_STATUS, the Feedback_Log row, a sprint retro.

---

### 💡 The lesson

**A number that needs a caption to be true is a number that is false.** The disclaimer existed, was accurate,
and protected nobody — because people read metrics, not the small print beneath them. ADR-137 found the same
shape in Squad Lab's build modes ("Balanced" meaning the strong-bench build), and the fix was the same: change
the label to what the thing does, rather than explaining the gap underneath it.

The related one: **ADR-120 predicted this symptom and mis-attributed the cause.** It flagged "all testers
reading ⚪ never" as the thing to watch, and guessed a `user_key` hashing mismatch. The hash was fine — the
*definition* was wrong. Predicting a symptom is much easier than predicting its cause, and a watch-item that
names one cause can quietly stop you looking for others.
