# Sprint 156: Case-insensitive beta allow-list (bugfix, US-381)

**Dates:** 2026-08-13
**Status:** ✅ Complete — US-381 (no ADR — a bugfix). 986 → 987 tests
**Capacity:** ~¼ session
**Carried Over:** none

> **Bug (found in testing, 2026-08-13):** a tester added to `beta_users` as `Colinbermingham@live.ie` (capital C)
> was **waitlisted** when signing in as `colinbermingham@live.ie`. `user_store.is_registered` used a PostgREST
> `eq.` filter — **case-sensitive** — while `clean_email` lower-cases the incoming email, so a hand-typed uppercase
> entry never matched.

---

### 📋 Sprint Review

**Delivered — the allow-list is now matched case- and space-insensitively.**

- **US-381** — `is_registered` fetches the `beta_users` list and compares **normalised on both sides**
  (`clean_email`, which lower-cases + trims), instead of a case-sensitive `eq.` filter. So `Colin@Live.ie` (or a
  stray-space entry) still admits `colin@live.ie`. Cheap — the gate caches the admit, so `is_registered` runs **once
  per session**. +1 test (case + space insensitivity). `register()` already lower-cases on insert, so app-added
  emails were fine; only **manual** entries hit this — now tolerated.
- **BETA.md** — a note that capitalisation/spaces don't matter when adding a tester.

**Owner actions:** unblock the affected tester now by lower-casing their `beta_users` row (or reboot after this
deploys — the fix admits the uppercase entry either way), and delete their `beta_waitlist` row.

### 🧠 Lessons

- **Normalise on both sides, at the boundary.** Lower-casing only the *incoming* value isn't enough when the stored
  value is hand-entered — a case-sensitive store filter (`eq.`) then silently mismatches. Compare normalised, or
  store normalised; ideally both.
- **A "soft" store invites human variance.** Manual `beta_users` edits mean capitalisation/spaces *will* happen —
  the code has to tolerate it, not assume tidy input.
