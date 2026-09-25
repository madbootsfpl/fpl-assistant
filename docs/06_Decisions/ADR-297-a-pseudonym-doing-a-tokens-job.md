# ADR-297 — A pseudonym doing a token's job

**Date:** 2026-09-25
**Status:** Accepted — ⚠️ **one revoke recommended, Stage C still the real fix**
**From:** the owner — *"I want to review our security before this rolls out to any more testers… I don't
know what I don't know"*

---

## The two questions asked, answered

**GitHub being public: ✅ not a concern.** The whole history — 13,770 objects — was scanned for
credential *shapes* rather than names, because a secret renamed is still a secret. **No JWT, no Supabase
key, no AWS or Google key, no private key, no `.env`, no keystore, ever.** The one password-shaped match
is `postgres:postgres@localhost`, a CI service container. ⭐ The repo being public is also a *control*:
two of the guards that have fired for real exist because it is.

**"RLS disabled": ⚠️ the warning is real and the risk it names is not the risk we have.** Four tables do
lack RLS — and every privilege is revoked from `anon`, so there is nothing for a policy to filter. ⭐ *RLS
decides which rows a role may see after it has table privileges; with the grant removed it never comes
into play.* The dashboard cannot express "no access at all", so it warns. Access is through twelve
`security definer` functions, which is stronger than policies because there is no policy to get wrong.

## 🔴 What was actually wrong

`anon` may execute `get_squad`, `save_squad`, **`delete_squad`**, `get_prefs`, `save_prefs`,
`get_watchlist`, `save_watchlist` — each keyed on one string, which is:

```python
def user_key(email: str) -> str:
    return hashlib.sha256(clean_email(email).encode()).hexdigest()[:32]
```

`SUPABASE_RLS.md` reasoned, in **two places**:

> *a `sha256(email)` key is **not guessable** — those users are effectively protected*

⚠️⚠️ **True of a random string; false of a hash of something other people know.** Nobody guesses it —
they compute it, in one line, from an address that is not a secret. ⭐⭐ *It was built so the table need
not store raw emails (ADR-106) — a privacy measure — and then quietly became the access control.*

**So: whoever holds the publishable key, and knows a tester's email, can read, overwrite or delete that
tester's saved squad, preferences and watchlist.**

⭐ **What stands in the way today** — and a finding without this reads as panic: the publishable key is
in Streamlit secrets and Render's environment only. It is not in the repo, and **not in the APK**,
checked rather than assumed: the mobile app carries no Supabase credential and reaches nothing but the
API.

⚠️ **Why it still matters:** a *publishable* key is designed to be shipped to browsers — the whole
Supabase model assumes it can be public. ⭐ *A secret whose own name says it is publishable will
eventually be published*, and accounts in the app (ADR-259) is precisely the change that would put it in
a client.

## ⭐⭐ The failure mode worth naming

**The two copies corroborated each other.** ADR-281's rule was *"two copies of one rule need a test that
they agree, or one is already wrong and nobody knows."* Here both copies said the same wrong thing, so
agreement proved nothing — ⚠️ *a claim repeated is a claim that looks checked.*

And a reassuring sentence in a security document is **load-bearing**: it is what lets the next reader
stop looking. Both copies are corrected, and `tests/test_security_claims.py` now:

- asserts the key **is** a pure function of the email, so the finding is arithmetic rather than prose —
  ⭐ *if that ever stops holding, the forbidden claim becomes true again and the test is where it shows*
- forbids either document calling it unguessable
- requires the review to name `delete_squad`, Stage C, and **what it did not cover** — ⚠️⚠️ *a security
  review that lists only findings reads as a clean bill of health*

⚠️ The guard's first version fired on the Security Review's own blockquote — the sentence it exists to
refute. ⭐ *A rule that cannot tell a claim from a quotation of it forbids the correction along with the
mistake* — the fourth time this session (ADR-261, ADR-280, ADR-290).

## Recommended, in order of effort

1. ~~**Revoke `delete_squad` from `anon`.**~~ 🔴 **Withdrawn the same day, on being asked how to do
   it.** Checking produced two corrections: it **breaks the Clear button** (`squads.py:500`), and
   `save_squad` is an **upsert**, so the same caller destroys the same row by overwriting it.
   ⭐⭐ *Removing one irreversible verb while leaving another that reaches the same end changes the
   tidiness of the attack, not its outcome* — and ⚠️ *the recommendation was written from the shape of
   the grant list rather than from what calls it*, which is the same mistake as the claim it was
   recommending a fix for.
2. **Date Stage C**, or accept the email-derived key with a review date — ⭐ *an accepted risk has a
   date; an unexamined one does not.*
3. **Do not put the publishable key in the mobile app** when accounts arrive.

## ⚠️ Scope

No penetration testing, no dependency-vulnerability scan, and **`sql/setup.sql` was read rather than the
live database queried** — ⭐ *I checked what should be applied, not what is.* Confirming the live grants
needs the key and ten minutes in the SQL editor.
