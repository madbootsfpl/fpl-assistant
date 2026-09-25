# Security review — before widening the beta

**Date:** 2026-09-25
**Asked:** *"I want to review our security before this rolls out to any more testers… I don't know what I
don't know, but RLS disabled on Supabase, GitHub being public — are these a concern or not, and is there
anything else to worry about?"*

⭐ **Every claim below was checked by running something.** The commands are included so any of it can be
re-run rather than believed.

---

## The two you asked about

### 1. GitHub being public — ✅ **not a concern, and verified rather than assumed**

The whole history was scanned for credential *shapes* — not names, because a secret renamed is still a
secret — across all 13,770 objects:

| looked for | found |
|---|---|
| JWTs (Supabase anon / service_role) | **none** |
| `sb_secret_` / `sb_publishable_` keys | **none** |
| AWS keys, Google API keys, private keys | **none** |
| Postgres URI with a password | one: `postgres:postgres@localhost` — a throwaway CI container |
| sensitive filenames ever committed | only `.env.staging.example`, `key.properties.example` |

```bash
git log --all --pretty=format: --name-only --diff-filter=A | sort -u | grep -iE "\.env|keystore|\.jks|key\.properties|\.pem"
git log --all -p | grep -aoP "eyJ[\w-]{12,}\.eyJ[\w-]{20,}|sb_(secret|publishable)_[\w-]{20,}|AKIA[0-9A-Z]{16}"
```

⚠️ **One thing is public and should be known rather than discovered:** the Cloudflare **account id** is in
commit `402aff5` (`.wrangler/cache/pages.json`), swept in by `git add -A` before its guard caught it
(ADR-291). An account id is an identifier, not a credential — it appears in every Cloudflare API URL and
cannot authenticate anything. **The deploy token was never written to disk**, checked rather than assumed.

⭐ A public repo is also a *control*: `tests/test_no_signing_material_tracked.py` and
`test_no_credential_file_is_tracked` exist because the repo is public, and both have fired for real.

### 2. "RLS disabled" on Supabase — ⚠️ **the warning is real; the risk it names is not the risk you have**

Four tables show that warning: `squads`, `beta_users`, `user_prefs`, `player_watchlist`. They genuinely
do not have RLS enabled. **But every privilege is revoked from `anon` and `authenticated`:**

```sql
revoke all on public.beta_users       from anon, authenticated;
revoke all on public.squads           from anon, authenticated;
revoke all on public.user_prefs       from anon, authenticated;
revoke all on public.player_watchlist from anon, authenticated;
```

⭐ **RLS only decides which rows a role may see *after* it has table privileges.** With the grant removed
there is nothing for a policy to filter — the dashboard cannot express "no access at all", so it warns.
Access is instead through twelve `security definer` functions, which is *stronger* than policies: there
is no policy to get subtly wrong.

**So: not a concern in itself.** The concern is what those functions accept — below.

---

## 🔴 The finding: a pseudonym is doing an authentication token's job

`anon` may execute `get_squad`, `save_squad`, **`delete_squad`**, `get_prefs`, `save_prefs`,
`get_watchlist`, `save_watchlist` — each keyed on one string. That string is:

```python
def user_key(email: str) -> str:            # src/web_streamlit/auth.py
    return hashlib.sha256(clean_email(email).encode()).hexdigest()[:32]
```

⭐⭐ **It was designed so the table need not store raw emails (ADR-106) — a privacy measure — and it has
since become the access control.** `docs/SUPABASE_RLS.md` reasons — twice, and ADR-259 a third time:

> *a `sha256(email)` key is **not guessable** — those users are effectively protected*

⚠️⚠️ **That is true of a random string and false of a hash of something other people know.** Nobody has to
guess it:

```python
>>> user_key("hello@madboots.com")
'5f307f3d6117d448ddaac10ca45c1883'
```

**Anyone holding the publishable key, who knows a tester's email address, can read, overwrite or delete
that tester's saved squad, preferences and watchlist.** No brute force.

**What stops it today:** the publishable key is only in Streamlit secrets and Render's environment. It is
not in the repo, and — checked — **not in the APK**: the mobile app carries no Supabase credential at all
and reaches nothing but the API.

```bash
strings madboots-13.apk | grep -cE "supabase|sb_(secret|publishable)|eyJ[\w-]+\.eyJ"   # → 0
```

**Why it still matters:** a *publishable* key is designed to be shipped to browsers. The entire Supabase
model assumes it can be public. ⭐ *A secret whose own name says it is publishable will eventually be
published* — and the natural next step, accounts in the app (ADR-259), is exactly the change that would
put it in a client.

📌 **The right fix is Stage C** — which `SUPABASE_RLS.md` already names: *"replacing 'knowing the key'
with 'being the user'"*, i.e. real Supabase Auth and RLS on `auth.uid()`. ⭐ *The document already contains
the answer; what it got wrong was how much time it had.*

**Cheaper interim options, in order of effort:**
1. ~~**Drop `delete_squad` from `anon`.**~~ 🔴 **Withdrawn on 2026-09-25 — I checked it and it was wrong
   twice** (ADR-297).
   - **It breaks a feature.** `squads.py:500` calls it: the **Clear** button, by which a user deletes
     their own saved squad. *"Nothing in the UI needs it"* was asserted, not checked.
   - **It buys much less than it sounds like.** `save_squad` is an **upsert** —
     `on conflict (handle) do update set data = excluded.data` — so the same caller can destroy the same
     row by overwriting it with anything. ⭐ *Removing one irreversible verb while leaving another that
     reaches the same end is a fix that changes the tidiness of the attack, not its outcome.*

   ⚠️ Revoke it if you want the Clear button gone anyway; do not revoke it believing it closes the hole.
2. **Salt the key** — `sha256(SERVER_SALT + email)` with the salt held server-side. Restores "not
   guessable" without touching the schema. ⚠️ Existing rows would need migrating or would be orphaned.
3. **Accept it explicitly** while the beta is ten people who know each other, and record that as a
   decision with a date rather than as an assumption.

---

## The rest of the surface

| | finding |
|---|---|
| **The mobile API** | 🟠 **No auth, no cap.** Every route is ids-in, analysis-out and writes nothing, so there is no data to leak — the exposure is **cost and availability**. Rate limits are the only control: `/squad/build` 20/min (the LP solver, the one endpoint whose CPU a stranger sets), `/players` 60/min, `/league` 20/min, `/feedback` 5/hour. Known since ADR-283. |
| **What the API returns** | ✅ Public FPL data plus our own computations. A manager id is already public in an FPL URL. |
| **The APK** | ✅ No credentials. Signed v2+v3 with a keystore that is not in the repo and never has been. |
| **Usage telemetry** | ✅ Platform · version · a random install id · endpoint · duration. **Never** the manager id, the caller's IP, or the body (ADR-280), and the privacy sweep is a test. |
| **`events` / `beta_waitlist`** | 🟡 `anon` may **insert**. Someone with the key could pollute usage stats or the waitlist. Annoying, not dangerous; no read is granted. |
| **`/feedback`** | 🟡 Relays free text and an optional reply address to a Google Apps Script. PII in transit by design; nothing stored by us. |
| **Cold start** | ✅ Not a security issue. Noted only because it is the failure testers see most. |

---

## What I would do before widening the beta

1. **Revoke `delete_squad` from `anon`.** One line, removes the only irreversible verb.
2. ✅ **Done — Stage C is a precondition on accounts (ADR-259), not a date.** ⚠️ *A date invites
   slippage; a dependency written into the thing that would violate it does not.* ⭐ **Widening the
   mobile beta does not need it** — the app keeps everything on the device and carries no Supabase
   credential, so more testers do not change what Stage C defends. **Building accounts does.**
3. **Do not put the publishable key in the mobile app** when accounts arrive — that is the change that
   turns a theoretical finding into a live one.
4. **Correct `SUPABASE_RLS.md`.** Its "not guessable" line is the sentence that would let this be
   re-approved by a future reader in a hurry.

⚠️ **What this review is not:** no penetration testing, no dependency-vulnerability scan, no review of
Supabase's own configuration beyond what `sql/setup.sql` states, and no check of whether the deployed
database actually matches that file — ⭐ *I read what should be applied, not what is.* Verifying the live
grants needs the key and is worth ten minutes in the Supabase SQL editor.
