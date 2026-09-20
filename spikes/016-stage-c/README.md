# Spike 016 — Stage C: can the database know who is calling?

**Run:** 2026-09-20, against Postgres 17 in Docker, mirroring Supabase's schema layout.
**Status:** the database half is **proven**. The web sign-in half is **not**, and needs a live project.

---

## Why this is now urgent rather than tidy

`src/web_streamlit/auth.py` derives the per-user key as:

```python
hashlib.sha256(clean_email(email).encode()).hexdigest()[:32]
```

**Unsalted.** So for a signed-in user the key is not a secret — it is a restatement of their email address.
Anyone who knows the address can compute the exact key that addresses that person's squad, preferences and
watchlist. There is nothing to guess.

That is survivable today for one reason only: **the publishable key never leaves the Streamlit server.** The
mobile audit is explicit that this stops being true — *"in Flutter it is compiled into the binary and can be
extracted from the IPA in minutes"* — which is why the audit calls owner-scoped identity a **hard
prerequisite** for any mobile client, not an improvement to schedule.

⭐ **This is a sharper statement than "a guessed handle still reads a squad."** Guessing is not involved.

---

## What was proven

`target_state.sql` builds the target schema — `user_id uuid` on each user table, four policies per table, all
of the form *you may touch a row if you own it* — and `auth.uid()` reproduced exactly as Supabase defines it
(reading the verified JWT off the connection, not anything the client sends as data).

Two users, Alice and Bob, each with a real JWT:

| what Bob tried | result |
|---|---|
| read his own squad | ✅ 1 row — the app still works |
| read Alice's squad **by its exact handle** | 🔒 **0 rows** |
| overwrite Alice's squad | 🔒 no effect (data verified unchanged afterwards) |
| delete Alice's squad | 🔒 no effect |
| insert a row claiming **Alice** owns it | 🔒 `new row violates row-level security policy` |
| edit his **own** row and reassign it to Alice | 🔒 `new row violates row-level security policy` |
| a **signed-out** caller holding the publishable key | 🔒 `permission denied for table squads` |

⚠️ **Two of those refusals are silent.** An UPDATE or DELETE that RLS filters to nothing raises no error — it
reports zero rows. That is correct Postgres behaviour and it is compatible with ADR-148 (the app already
checks row counts rather than trusting a 200), but it must stay that way: *a delete that matched nothing must
not read as success.*

⭐ **Two policy details earned their place, and both are easy to get wrong:**

- **INSERT needs `with check`, not `using`.** `using` filters rows that already exist and is ignored on an
  insert — a policy written that way accepts a row claiming any owner.
- **UPDATE needs both.** `using` decides which rows you may edit; `with check` decides what they may become.
  Without the second, attack 5 above succeeds: you edit your own row and hand it to someone else.

## The migration, which is the operationally risky part

29 testers already have data keyed by the old hash. `migration.sql` adds `claim_my_legacy_rows()`, called on
sign-in:

| | |
|---|---|
| legacy owner's first sign-in | `{"squads": 1, "user_prefs": 1, "player_watchlist": 0}` — data intact |
| the same call again | `{"squads": 0, ...}` — idempotent, so calling it on every sign-in is safe |
| an impostor **who knows the email** | `{"squads": 0, ...}` and sees nothing |

⭐⭐ **The function takes no arguments.** It derives the old key from the email inside the *verified* JWT.
Accepting the old key — or the email — as a parameter would reproduce the exact hole Stage C exists to close,
with extra steps.

⭐ **It works at all only because the old key is an unsalted function of the email** — the same property that
makes today's scheme unsafe is what makes the migration computable without a mapping table built in advance.

**Verified against the real derivation:** the SQL produced `b45081123b1bb04cb138118bd82f505d` for
`tester@example.com`, identical to what `src.web_streamlit.auth.user_key` returns.

⚠️ **A portability trap, caught here rather than in production.** Supabase installs `pgcrypto` into the
`extensions` schema; a bare Postgres puts it in `public`. With `set search_path = ''` the call must be
schema-qualified, so **a function that works locally fails on Supabase and vice versa**. The spike mirrors
Supabase's layout for exactly this reason.

⚠️ **Unclaimed legacy rows are invisible to everyone** during the transition (`NULL = uuid` is `NULL`, not
true — confirmed). That is the right default, but it means `user_id` cannot become `NOT NULL` until either
every tester has signed in once or the stragglers are reconciled by the owner.

---

## What is NOT proven, and it is the thing that decides the design

**Whether Supabase Auth's sign-in flow works inside Streamlit.**

There is a specific, structural hazard. Supabase's default OAuth (implicit) flow returns the session in the
**URL fragment** (`#access_token=…`). A fragment is never transmitted to a server, and Streamlit renders
server-side — so Streamlit *cannot see it*. The mitigation is the **PKCE** flow, which returns `?code=…` as a
query parameter that `st.query_params` can read and exchange server-side.

⭐ This is a mechanism-level argument, not a measurement. **It needs a live test**, because "should work" is
how the last two incidents started.

Also open: the app talks to PostgREST with plain `requests` and no SDK (deliberately lightweight). Stage C
either adds `supabase-py` or implements PKCE in ~50 lines of `requests`.
