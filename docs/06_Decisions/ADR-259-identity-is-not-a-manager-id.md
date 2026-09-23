# ADR-259 — Identity is not a manager id

**Date:** 2026-09-23
**Status:** Proposed — a gate, not a build
**Question:** *"how do people register, how would they get access, how can we save data at end of session?
Will it be same for iOS, Android & Web?"*
**Builds on:** ADR-087/106 (the web's gate), ADR-211 (Supabase), `docs/SUPABASE_RLS.md` (Stages A–C)

---

## Where we actually are

|  | Web (Streamlit) | Phone (Flutter) |
|---|---|---|
| **Register** | Google sign-in, allow-listed in `beta_users`, capped by `FPL_USER_CAP`; refusals to `beta_waitlist` | **nothing** |
| **Identity** | email → `sha256(email)[:32]` as `user_key` | **none** |
| **Saved squads** | `squads`, keyed by a handle *or* that hash | **nothing server-side** |
| **Preferences** | `user_prefs` — manager id, league | device only |
| **Survives reinstall** | yes | **no** |
| **Talks to Supabase** | yes | **no** — only to our API |

⭐⭐⭐ **The manager id is not an account, and treating it as one is the trap.** It is a *public* FPL
number: anyone can type anyone's, including the owner's. It says **which team you are looking at**, never
**who you are** — and the two do not map onto each other. One person may run several FPL teams; one team
may be watched by several people.

## ⚠️ What is actually open today

**The phone has no gate at all.** Whoever holds the app can use it. That is currently fine because
distribution *is* the gate — the owner hands it to people.

**The hosted API is unauthenticated.** Defensible while every endpoint is *ids in, analysis out* over
public FPL data, and the rate limit (ADR-256) caps the cost — ⚠️ but the code already says that reasoning
*"expires the day the answer depends on who is asking."* Accounts are that day.

🔴 **A guessed handle still reads a saved squad.** `SUPABASE_RLS.md` records it: `sha256(email)` keys are
not guessable, but the user-chosen handles from the no-login path — `ts`, `robots`, `tesheridan` — were
all visible in a pre-hardening probe. ⭐ *Only Stage C closes it, by replacing knowing the key with being
the user.*

## Decision

**One identity across iOS, Android and web, via Supabase Auth — and not yet.**

### ⭐ Why one, and why Supabase

The web already talks to Supabase; `supabase_flutter` is an official package; and RLS scoped to
`auth.uid()` is exactly the "being the user" that Stage C is. ⚠️ *Three identity systems is three places
for the same person to be a different person*, and the question that exposes it — *"I built this squad on
my laptop, where is it on my phone?"* — has an embarrassing answer today.

⚠️ **Sign in with Apple is not optional.** The App Store requires it wherever another social login is
offered. That is a review blocker, so the provider choice is Google **and** Apple, decided now rather than
discovered at submission.

### ⭐⭐ Why not yet — and the two triggers

Building accounts now means building the hardest part of the system **before knowing what people want from
it**. For a closed beta the owner hands out, distribution already controls access.

📌 **Build it when either becomes true:**

1. **Web↔phone continuity is wanted** — a tester using both asks where their squad went.
2. **Distribution goes beyond hand-delivery** — TestFlight at any scale, or an APK that can be forwarded.

### ⚠️⚠️ It is a migration, not a login screen

This is the part that needs designing, and the part that will be underestimated.

`squads` is keyed by `handle`, which is *either* a user-chosen string *or* `sha256(email)[:32]`.
`user_prefs` and `player_watchlist` are keyed by that hash. **Eight `security definer` functions** —
`get_squad`, `save_squad`, `squad_exists`, `delete_squad`, `get_prefs`, `save_prefs`, `get_watchlist`,
`save_watchlist` — all take the key as an *argument*, which is precisely what makes a guessed handle work.

⭐ Under Stage C they take **no key at all**: they read `auth.uid()`. That is the whole change, and it
means every existing row has to be claimed by a real identity or orphaned. ⚠️ *A migration that silently
orphans somebody's saved squad is worse than one that refuses to run.*

### What the phone should and should not sync

⭐ **Drafts stay on the device.** A draft is a scratchpad — ADR-225's staleness rules already treat it as
something that can rot. Syncing a scratchpad between devices creates conflicts nobody asked for.

⭐ **Squads sync.** That is the document, and it is the thing the continuity question is actually about.

📌 Open: whether *seen signals* (ADR-232) sync. ⚠️ Per-device is arguably **right** — "new since you last
looked" is a fact about a device's screen, not about a person — and that is worth deciding deliberately
rather than by whichever is easier.

## Smaller things, independent of accounts

🔴 **Hide the Settings server field before any tester build.** It points the app wherever someone types;
flagged at ADR-239 and still true.

## Consequences

⭐ **Nothing is built by this ADR.** It exists so the decision is on paper rather than in a conversation,
and so the next person to ask *"how do people register?"* finds the answer and the reasons rather than
re-deriving them.

⚠️ **Until it is built**, the honest description of the product is: *a personal tool the owner distributes
by hand, whose data lives on the device it was entered on.* That is a fine thing to be — it is just not
what "register" implies, and a tester should not be told otherwise.
