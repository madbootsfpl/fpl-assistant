# Sprint 196: Signing in is not saving a squad (ADR-142)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-142. 1377 → 1384 tests, ruff clean. ⏳ One owner action: one line of SQL.

> **Owner, on the live Admin panel:** *"It's not a true reflection of who is logged in — tesheridan@yahoo.com
> is active, and tony.e.sheridan has also been active in the last 24 hours."*

---

### 🔍 The bug

The panel read **Registered 25 · 🟢 Active 1 · 🟡 Dormant 6 · ⚪ Never 18.**

"Active" was never measuring what its label says. The roster's only signal was the `updated_at` on a tester's
**saved squad row**:

| the label says | what it measured |
|---|---|
| 🟢 Active | saved a squad in the last 7 days |
| ⚪ Never | has never **saved a squad** |

**Saving a squad is a rare, deliberate act; using the app is not.** Most people sign in, look at their team,
read a board and leave. So the panel reported 18 of 25 testers as "never" while at least two were using it
daily.

**And it was documented.** A caption under the metrics did say *"sees signed-in + squad-persisted activity
only"*. It protected nobody, because people read metrics, not the small print beneath them.

---

### 🔧 What shipped

`user_store.touch_last_seen(email)` stamps `beta_users.last_seen` at **admit** — once per session, in the one
place the app knows a person has arrived. Not per page view: the roster only asks *which day*, so a write per
navigation would buy no signal.

**Not a de-anonymisation.** The ADR-100 event stream stays anonymous and untouched; this is the owner's own
allow-list — which already stores the email — learning when that person last arrived.

**Two signals, kept apart**: *Last used* (signed in — who is visiting) and *Last saved a squad* (pressed save
— who is actively managing a team). Status follows the sign-in; the save stays its own column, because it is
the stronger engagement signal and collapsing the two is what caused the bug.

**It degrades loudly.** The column must be added by hand, so until then reads and writes 400, status falls
back to the old save-based behaviour, and a warning names the column and gives the SQL. Showing a column of
dashes instead would read as *"nobody has been here"* — a worse lie than the one being fixed.

```sql
alter table beta_users add column if not exists last_seen timestamptz;
```

⏳ **Expect the numbers to look worse before they look right.** Nothing can be back-dated, so everyone reads
⚪ never until they next sign in.

---

### 💡 Two lessons

**1. A number that needs a caption to be true is a number that is false.** The disclaimer was accurate and
useless. Four large figures labelled Active / Dormant / Never *assert* something; a line of grey text below
does not retract it. ADR-137 found the identical shape in Squad Lab ("Balanced" meaning the strong-bench
build) and the fix was the same both times: **change the label to what the thing does, rather than explaining
the gap underneath it.** Worth noticing that this is now twice — a caption apologising for a label is a
reliable smell.

**2. ADR-120 predicted this exact symptom and mis-attributed the cause.** It recorded "all testers reading ⚪
never" as the thing to watch, and guessed a `user_key` hashing mismatch. The hash was fine; the **definition**
was wrong. Predicting a symptom is far easier than predicting its cause — and a watch-item that names one
cause can quietly stop you looking for others. The note was doing its job right up until it pointed at the
wrong thing.

### 🧪 Tests

**+7 (1377 → 1384).** Status follows the sign-in and not the save (the reported case, with the 18-of-25 figure
in the docstring so it explains itself); both signals stay on the row; the fallback when sign-in data is
absent, so the panel degrades rather than reporting everyone as never-seen; the PATCH targets the *cleaned*
email so it matches the stored row; a missing column is silent on read **and** write; nothing is called when
the store is unconfigured.
