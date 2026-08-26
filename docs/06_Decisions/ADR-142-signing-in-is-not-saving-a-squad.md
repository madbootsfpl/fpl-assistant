# Architectural Decision Record: Signing in is not saving a squad

**Decision ID:** ADR-142
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 196, 2026-08-26). **1377 → 1384 tests, ruff clean.**
✅ **Owner action DONE and verified (2026-08-26)** — column added, column-restricted UPDATE policy applied,
`touch_last_seen` returns `ok` against the live store. Sign-in times now record.
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

---

### 🔁 Revision — the column existed, and every value was still NULL

**Owner, having run the SQL:** *"ran the SQL, checking admin now, it's not updating as I have logged in and
out and back in again."* The Supabase screenshot showed `last_seen` present on all 28 rows and **NULL on every
one**.

**Two faults, and only one of them is the likely cause.**

**1. `eq.` is case-sensitive — a trap this codebase already documents.** `touch_last_seen` filtered with
`email=eq.<cleaned>`, but the allow-list is hand-maintained and holds **both** `markcondron88@gmail.com` and
`Markcondron88@gmail.com`. For the capitalised row that filter matches **no row at all** and PostgREST cheerfully
reports success — it updated zero rows, which is not an error.

The infuriating part: `is_registered`, forty lines above the code I wrote, carries this in its docstring —
*"A PostgREST `eq.` filter is case-sensitive, so we fetch the list and compare normalised."* **The warning was
already written, by this project, in the file being edited.** Now fixed the same way: read the stored spelling,
patch *that*.

**2. A missing UPDATE policy — since confirmed by the diagnostic (below).** At the time of writing this was a
suspicion that could not be checked from here. `beta_users` needs SELECT and INSERT policies for the gate to work at all (they demonstrably do),
and a table can easily have those and **no UPDATE policy**. PostgREST then refuses the PATCH with a 401/403 —
which the first version swallowed, by design.

### 🔎 The design flaw underneath both: silent was undiagnosable

Every store call here is best-effort and silent, and that is *right* for a tester: nobody should see an error
because an admin panel wants a nicer number. But it left the owner looking at a column of NULLs with no way to
distinguish **never attempted** from **matched nothing** from **refused by a policy** — three different
problems with three different fixes and one identical symptom.

So `touch_last_seen` now **returns a status string** and the Admin page runs it on demand and prints it. Two
things about that:

- **The caller at admit still ignores the return**, so a tester's experience is unchanged.
- **The diagnostic runs the same function the sign-in does.** A probe down a parallel path would prove nothing
  about the real one — it would only prove that a second implementation works.

**The rule: best-effort is a promise to the user, not a licence to be unexplainable to the operator.** Swallow
the error at the edge; keep the reason.

### ⚠️ Correction — the first policy suggested here was too permissive

An earlier draft of this ADR suggested:

```sql
create policy "beta_users update last_seen" on beta_users for update using (true) with check (true);
```

**Do not run that.** A policy alone is *row*-level: it would let the `anon` role update **any column** of any
row — including `email`. The Supabase anon key ships to the browser, so anyone who lifted it could rewrite an
allow-listed address to their own and **admit themselves to the beta**. That is a privilege escalation, not a
cosmetic over-grant.

Column restriction in Postgres comes from a `GRANT`, not from the policy. And it is safe to restrict here
because **the app never updates any other column of this table**: the only writes are `INSERT` (register),
`DELETE` (unsubscribe) and this one `last_seen` stamp.

**Owner action, in order:**

```sql
-- 1. the column (already done)
alter table public.beta_users add column if not exists last_seen timestamptz;
```

Then open **Admin ▸ 🔧 Why isn't `last_seen` filling in?**, stamp yourself, and read the result.
**Only if it reports 401/403** is anything else needed — and then:

```sql
-- 2. Supabase often grants UPDATE broadly by default; take it back first
revoke update on public.beta_users from anon;

-- 3. hand back exactly one column
grant update (last_seen) on public.beta_users to anon;

-- 4. and a row policy to permit the update at all
create policy "anon stamps last_seen" on public.beta_users
  for update to anon using (true) with check (true);
```

With step 3 in place, `using (true)` is no longer dangerous: the role can reach every row but only one
harmless column. `REVOKE` first, because a pre-existing broad grant would otherwise make the narrow one
pointless.

**The lesson, and it is a general one:** *"it didn't work, add a permission"* is how over-broad access gets
written, and the widest thing that makes the error go away is almost never the right thing. Ask what the code
actually writes — here, one column, provably — and grant that.

---

### 🔬 Confirmed by the diagnostic — and it did not fail the way this ADR predicted

The owner ran **Admin ▸ 🔧** and got:

```
touch_last_seen(tony.e.sheridan@gmail.com) → wrote nothing — no row matched
```

**Not a 401/403.** This ADR said twice that a missing UPDATE policy shows up as a hard refusal. It does not.
The two failures are genuinely different, and the distinction is the useful thing to come out of this:

| cause | what PostgREST returns |
|---|---|
| the role lacks the table privilege (a missing `GRANT`) | **401 / 403** — rejected outright |
| **RLS enabled with no UPDATE policy** | **HTTP 200, zero rows** — no error anywhere |

Postgres does not raise when RLS excludes rows from an `UPDATE`; it simply narrows the statement to nothing.
So the *quieter* of the two failures is the one that was actually happening — which is the same theme as the
rest of this ADR, one layer further down.

**And the reading is unambiguous**, because of the order the function does things: the `GET` immediately above
had just found that exact row. **A filter that matches for SELECT and not for UPDATE can only be RLS.** The
first version of the message guessed *"is the column present?"*, which was wrong and would have sent the
operator hunting the wrong thing — the column was visibly there in the screenshot. The message now names RLS,
and the Admin panel prints the exact SQL beneath it.

**So the policy IS needed here** — the narrow, column-restricted version in the correction above, not the
blanket one. Every store call in this module is best-effort and silent, and this is the third layer at which
that turned out to hide something: the write failed politely, then reported a 200, and Postgres declined to
mention that it had updated nothing.

**✅ Verified end to end (2026-08-26).** Owner ran the narrow SQL; the Admin diagnostic went from
*"the row exists but the update reached no rows"* to **`ok`**, against the real store, through the same
function the sign-in calls.

⏳ **The numbers will lag for a few days and that is expected, not a third bug.** Nothing can be back-dated, so
every tester reads ⚪ never until they next sign in. Judge the panel at the end of the week, not tonight.

### 📌 What this one cost, and what it bought

Three attempts to fix one wrong number: the definition (measuring squad-saves), the filter (`eq.` is
case-sensitive — documented forty lines above the code I wrote), and the store (RLS silently updating nothing).
**Every layer failed quietly, and none of them failed the way the layer above had predicted.**

The durable output is not the fix. It is that `touch_last_seen` now returns a reason, and the Admin panel runs
**the real function** and prints it — so the next time this class of thing breaks, the first question is
answered in one click instead of three round-trips through a live deployment.
