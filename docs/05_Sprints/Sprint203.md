# Sprint 203: A promise must cover every row we create (ADR-148)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-148. 1425 → 1429 tests, ruff clean. ⚠️ Corrects ADR-147's SQL.

---

### 🔍 A self-inflicted gap, closed in the same session

ADR-147 added `user_prefs`. ADR-122 promises *"remove me = we delete your rows"*. `remove_me` did not know
about the new table, so the promise quietly stopped being true the moment the feature shipped.

Nothing failed. No test broke. The guarantee just got narrower, and only someone reading both files at once
would have noticed. **A new table is exactly the thing an old promise silently stops covering.**

### 🔎 Checking it found something worse

`user_prefs` ships with RLS enabled, and the SQL in ADR-147 created policies for `select`, `insert` and
`update` — **not `delete`**. So even after teaching `remove_me` about the table, the delete would have been
refused. *Silently.*

Third time in two days:

| | what failed | how it presented |
|---|---|---|
| ADR-142 | `beta_users` UPDATE, no policy | `200 OK`, zero rows — a day of NULLs |
| ADR-147 | anticipated on write | diagnostic shipped alongside |
| **ADR-148** | **`user_prefs` DELETE, no policy** | **`200 OK`, zero rows** |

**On a delete that means telling someone their data is gone while it is still there.** Of all the places for a
silent no-op, this is the one that matters — it is the difference between a bug and a broken promise.

### 🔧 What shipped

`remove_me` deletes `user_prefs`, and returns `{table: status}` while the UI carries on ignoring it. Fail-silent
is right at the edge; fail-silent must not mean *unverifiable*. `Prefer: return=representation` is what
distinguishes a real delete from one that matched nothing.

ADR-147's SQL is corrected in three places — the ADR, this ADR, and the Admin panel that prints it.

---

### 💡 The lesson

> **Every feature that creates a row inherits every promise made about rows.**

ADR-122's guarantee was written before `user_prefs` existed and could not know about it. The obligation runs
the other way — from the new table back to the old promises, not forward.

Worth a habit rather than an ADR each time: **when a change adds a table, re-read `unsubscribe.py`.** It
encodes what we owe people, and nothing else references it, so nothing else will remind you.

A note on how this one was found: it came from the *retro* of the previous sprint, not from a bug report. The
line in ADR-147 read *"unsubscribe.remove_me does not yet delete user_prefs — noted as a follow-up"* — written
while the reasoning was still fresh, and acted on before anything depended on it. **The follow-ups you write
down while finishing something are worth more than the ones you rediscover later**, because at that moment you
still know why they matter.

### 🧪 Tests

**+4, 3 updated.** `user_prefs` deleted by key; a delete that matched nothing is **reported** rather than
swallowed; every table reports and a refusal is named; a network failure still never raises; no store returns
an empty report rather than a false success.

The existing fixture had to start returning a response object — it previously returned `None`, which is
precisely why none of this was checkable before.

---

### 🔁 And the corrected SQL failed too, for a third reason

The owner ran the fixed block and got:

```
ERROR: 42710: policy "prefs read" for table "user_prefs" already exists
```

**The block was not re-runnable, and its own first line promised it was.** `create table if not exists` says
*safe to run again*; the four `create policy` lines under it were not. So the re-run needed to pick up the
missing `delete` policy failed on line three — and because Postgres rolls the statement back, **applied
nothing at all**.

> **An idempotent first line in a block that is not idempotent is worse than neither.** It invites exactly the
> re-run that then fails, and it fails *after* the reader has been told the block is safe.

Postgres has no `create policy if not exists`, so drop-then-create is the idiom. The block in ADR-147 and in
the Admin panel is now safe to run any number of times.

Three attempts at one small piece of setup — a missing policy, a missing DELETE policy, and a block that could
not be re-run to fix either. Each failure was in the *instructions*, not the code, and each surfaced only when
a human tried to follow them. **Setup SQL is a user interface, and it had never been used until today.**
