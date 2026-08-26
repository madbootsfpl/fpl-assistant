# Sprint 202: A remembered manager id (ADR-147)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-147. 1416 → 1425 tests, ruff clean. ⏳ One owner action: create `user_prefs`.

> **Owner:** *"When a league is loaded it must persist from session to session **and between devices**."*

---

### 🔍 The feature was undercutting itself

🏆 Leagues asks for a manager id, resolves every league behind it — and forgets all of it when the tab closes.

Which is a sharper miss than it first looks, because **ADR-141's own revision was about this exact friction**.
That page originally asked for a *league* id; nobody knows their league id, so it was changed to take the
number people actually have. And then it threw that number away too. The fix for "hard to supply" was
delivered without the obvious follow-through: "so don't make them supply it twice".

**"Between devices" decides the design.** A cookie survives a refresh and nothing else. Cross-device means the
per-user store — which this app already runs twice, for the squad (ADR-106) and the watchlist (ADR-117).

### 🔧 What shipped

`prefs.py`, modelled on `watchlist.py`: session_state is the truth, the cloud is a mirror, restored **once per
session** and written **only when something changed** — Streamlit reruns on every interaction, and this is a
value that moves about twice a season.

**It remembers the manager id, not just the league.** A stored league restores one league; a stored manager id
restores the *list*, so every league comes back and the picker reopens on your last choice.

Signed out, it is session-only — exactly today's behaviour, so the page still works without an account.

### 💡 The lesson: ship the diagnostic with the feature, not after the bug

ADR-142 cost a day to a silent write: `beta_users` had SELECT and INSERT policies and **no UPDATE policy**,
and PostgREST reports that as **`200 OK, zero rows`** rather than an error. Every `last_seen` stayed NULL with
nothing anywhere to say why.

This is the same shape of write against a table that does not exist yet. So the diagnostic shipped **in the
same commit as the feature**: `remember()` returns a status the page ignores, Admin ▸ 🔧 prints it, and a
non-ok result prints the exact SQL — table, RLS, and all three policies.

> **A silent best-effort write needs its explanation built at the same time as the write.** The cost of adding
> it afterwards is not the code; it is the day spent not knowing which of three failures you have.

A second, smaller call worth recording: **a new table rather than a column on `beta_users`.** The narrow grant
recommended yesterday is `grant update (last_seen)` — *one column*. Putting a preference there would mean
widening write access on the table holding **email addresses**, which is exactly what scoping it narrowly was
for. Two days of decisions agreeing with each other, which is what the ADR trail is supposed to produce.

### 🧪 Tests

**+9.** Session-only when signed out; nothing reaches the network unconfigured; a store failure leaves the
session value intact; the restore happens **once**, not per rerun; a failed restore does not wipe the session
(hence `None` ≠ `{}`); unchanged values are not re-written, compared as text so `123` and `"123"` are one id;
unknown keyword fields are dropped before they become a PostgREST 400; and **a zero-row write names row-level
security** — ADR-142's failure, pinned before it can recur.
