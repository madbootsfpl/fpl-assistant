# Architectural Decision Record: A promise must cover every row we create

**Decision ID:** ADR-148
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 203, 2026-08-26). **1425 → 1429 tests, ruff clean.**
⚠️ **Corrects ADR-147's SQL**, which was missing a `delete` policy — see below. If you already ran that block,
run the one extra line.
**Superseded By / Replaces:** Extends the self-service unsubscribe (ADR-122) to cover ADR-147's `user_prefs`.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-147 added a table. ADR-122 promises *"remove me = we delete your rows"*. **`remove_me` did not know about
the new one**, so the promise quietly stopped being true the moment the feature shipped — and it was
self-inflicted, in the same session.

That is the general shape worth naming: **a new table is exactly the thing an old promise silently stops
covering.** Nothing fails. No test breaks. The guarantee just gets narrower, and only a person reading both
files at once would notice.

### 🔎 And checking it turned up a second, worse problem

`user_prefs` ships with **row-level security enabled** (ADR-147), and the SQL in that ADR created policies for
`select`, `insert` and `update` — **not `delete`**. So even after teaching `remove_me` about the table, the
delete would have been refused.

Refused *silently*. This is the third time this exact trap has come up in two days:

| | what failed | how it presented |
|---|---|---|
| ADR-142 | `beta_users` UPDATE, no policy | `200 OK`, zero rows — a day of NULLs |
| ADR-147 | anticipated on write | diagnostic shipped alongside |
| **ADR-148** | **`user_prefs` DELETE, no policy** | **`200 OK`, zero rows** |

**On a delete, that failure means telling someone their data is gone while it is still there.** Of all the
places for a silent no-op, this is the one that matters most — it is the difference between a bug and a broken
promise.

---

### ✅ Decision

**1. `remove_me` deletes `user_prefs` by `user_key`**, alongside `squads` and `player_watchlist`.

**2. It returns `{table: status}` — and the UI still ignores it.** Fail-silent is correct *at the edge*: a
crash mid-unsubscribe is worse than a retry, and nobody leaving should be shown a stack trace. But
fail-silent must not mean **unverifiable**. `Prefer: return=representation` makes PostgREST hand back the rows
it actually removed, which is the only way to tell a real delete from one that matched nothing:

```
deleted                                        the row is gone
nothing matched (no row, or no DELETE policy)  the row may still be there  ← the dangerous one
refused (HTTP 401)                             the role cannot touch the table
failed: <exception>                            never reached the store
```

**3. ADR-147's SQL is corrected** — here, in that ADR, and in the Admin panel that prints it:

```sql
create policy "prefs delete" on public.user_prefs for delete to anon using (true);
```

### ⚠️ Risks

- **`beta_users` still needs its own DELETE policy** for the email-side delete to take effect (noted in
  BETA.md, pre-existing). Now *observable* rather than assumed: `remove_me` reports `nothing matched` for it
  if the policy is absent, where before it reported nothing at all.
- **Returning a dict changes the signature.** Its two callers ignore the return, so nothing else moves.

### 🧪 Definition of Done

1. **Tests: +4, and 3 updated.** `user_prefs` is deleted by key; a delete that **matched nothing** is
   reported rather than swallowed; every table reports and a refusal is named; a network failure still never
   raises; no store returns an empty report rather than a false success. The existing fixture had to start
   returning a response object — the old one returned `None`, which is exactly why nothing could be checked.
2. **Manual smoke** — owner: run the delete policy, then Leave the beta on a throwaway account.
3. **Docs** — this ADR, ADR-147 corrected, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**Every feature that creates a row inherits every promise made about rows.** ADR-122's guarantee was written
before `user_prefs` existed and could not know about it; the obligation to check runs the other way — from the
new table back to the old promises, not forward.

Worth a standing habit rather than an ADR each time: **when a change adds a table, re-read `unsubscribe.py`.**
It is the file that encodes what we owe people, and it is the one nothing else references, so nothing else
will remind you.

And the narrower one, now proven three times in two days: **a silent best-effort operation needs a status even
when nobody displays it.** The cost of not having one is never the code — it is the day you cannot tell which
of three failures you have, or worse, the promise you kept telling people you had honoured.
