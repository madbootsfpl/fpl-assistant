# Running a private beta — owner runbook

How to open the app to ~50 testers (e.g. via Reddit), collect feedback, and build a founding-tester list you
can honour later — **without accounts/auth**. Everything here is **opt-in**: until you set the secrets below,
the app behaves exactly as it does today (public, open, feedback → GitHub). Background: [ADR-087](06_Decisions/
ADR-087-beta-access-and-feedback.md) · [DIRECTION.md](00_Project/DIRECTION.md) §3.

---

## The switches (Streamlit secrets)

Set these in **Streamlit Community Cloud → Manage app → Settings → Secrets** (TOML). All optional; unset = off.

```toml
FPL_ACCESS_CODE      = "your-shared-beta-code"                     # gates entry; testers type it once per session
FPL_FEEDBACK_WEBHOOK = "https://formsubmit.co/ajax/you@proton.me"  # in-app feedback POSTs here (§1: a Sheet OR a relay)
FPL_FEEDBACK_ORIGIN  = "https://madboots.streamlit.app"           # the app URL FormSubmit sees (§1B) — anti-abuse
FPL_FEEDBACK_KEY     = "your-web3forms-access-key"                 # only if you use Web3Forms as the relay (§1B)
FPL_FEEDBACK_EMAIL   = "hello@madboots.com"                   # the mailto fallback address (default: this)
FPL_SIGNUP_URL       = "https://forms.gle/your-signup-form"        # the founding-tester email-capture form / waitlist
FPL_USER_CAP         = "10"                                        # cap registered testers (§4); unset = shared code only
FPL_ANALYTICS        = "1"                                         # anonymous usage/perf analytics (ADR-100); unset = off
FPL_ADMIN_KEY        = "a-long-password"                           # unlocks the 📊 Admin analytics tab for you; unset = inert
```

(Locally you can use the same names as **environment variables** instead.)

- **`FPL_ACCESS_CODE`** — when set, every page shows a 🔒 prompt until the code is entered. Rotate by editing
  the secret. It's a *shared* code (a beta gate, not per-user security) — fine here (the app is read-only,
  public FPL data).
- **`FPL_FEEDBACK_WEBHOOK`** — where the in-app **📣 Feedback** form POSTs (`{message, email, source, page,
  version, ts, _subject}`). Point it at a **Google Sheet** (§1A) *or* a **form-to-email relay** (§1B) that
  forwards to your inbox. **Unset → the form offers a pre-filled email** (`FPL_FEEDBACK_EMAIL`) — so feedback
  reaches you even with no webhook (US-307).
- **`FPL_FEEDBACK_ORIGIN`** — the app URL the relay sees as the `Origin`/`Referer`. FormSubmit (anti-abuse)
  **rejects a POST with no origin** — and this form POSTs *server-side* (Streamlit's backend, no browser origin),
  so the app always sends one. Defaults to a sensible app URL; **set it to your real Streamlit URL** if you ever
  domain-lock the form. Harmless for a Sheet/Web3Forms.
- **`FPL_FEEDBACK_KEY`** — only for the **Web3Forms** relay (§1B); it's sent as `access_key`. Leave unset for a
  Sheet or for FormSubmit.
- **`FPL_FEEDBACK_EMAIL`** — the address the in-app **"✉ Email your feedback"** / fallback links open (a
  `mailto:`). Defaults to `hello@madboots.com`; set it to change the inbox.
- **`FPL_SIGNUP_URL`** — a link shown on **Home** + **Feedback** ("✋ Join the beta"). Unset → hidden.
- **`FPL_ANALYTICS`** — turns on **anonymous usage & experience analytics** (ADR-100): what testers use, whether
  they return, and how fast/reliable it feels — written to a Supabase `events` table (reuses the store secrets, no
  new one). **Off by default**; **anonymous** (no PII, not the handle); **fail-silent** (never affects the app).
  Needs the `events` table + one flag — full runbook: **[ANALYTICS.md](ANALYTICS.md)**.
- **`FPL_ADMIN_KEY`** — unlocks the **📊 Admin** tab (a read-only dashboard: sessions · returning devices · top
  pages · success rates · median/P95 perf) for **you only**. Unset → the tab is inert; a wrong key → locked.
  Needs the anon SELECT policy on `events` (ANALYTICS.md).

> **Why a relay / mailto, not direct email?** Sending mail from the app would need SMTP credentials, and
> **Proton has no free SMTP** (it needs the paid Bridge). So feedback reaches your inbox either via a free
> **form-to-email relay** (structured, in-app submit — §1B) or the **pre-filled `mailto:`** (the tester's own
> mail client — zero setup, always on).

---

## 1. The feedback sink — pick one (both zero-cost)

The in-app form POSTs JSON to `FPL_FEEDBACK_WEBHOOK`. Point it at a **Sheet** (1A, a running log) *or* an **email
relay** (1B, straight to your inbox). **Skip this entirely** and the form still works — it offers a **pre-filled
email** to `FPL_FEEDBACK_EMAIL` (the tester's mail app → your inbox), so you can recruit before wiring anything.

### 1A. A Google Sheet (~10 min) — a running log

A Google Apps Script bound to a Sheet:

1. Create a Google **Sheet** ("FPL beta feedback") with headers: `timestamp · message · email · page · version`.
2. **Extensions → Apps Script**, paste:
   ```js
   function doPost(e) {
     const d = JSON.parse(e.postData.contents);
     SpreadsheetApp.getActiveSpreadsheet().getActiveSheet()
       .appendRow([new Date(), d.message || "", d.email || "", d.page || "", d.version || ""]);
     return ContentService.createTextOutput("ok");
   }
   ```
3. **Deploy → New deployment → Web app**, *Execute as: me*, *Who has access: Anyone*. Copy the `/exec` URL →
   that's `FPL_FEEDBACK_WEBHOOK`.
4. Test: submit the in-app form; a row should appear in the Sheet.

### 1B. An email relay (~5 min) — straight to hello@madboots.com

Free form-to-email services forward a POST to your inbox — the app's payload already carries `_subject`, the
message, the page, and the version.

**FormSubmit** (no signup) — two gotchas that will bite if you skip them:

1. **Use the `/ajax/` endpoint** — the app POSTs **JSON**, so:
   `FPL_FEEDBACK_WEBHOOK = "https://formsubmit.co/ajax/hello@madboots.com"` (or `…/ajax/<random-token>` from
   formsubmit.co to hide the address). The plain `formsubmit.co/<addr>` endpoint expects an HTML form and won't
   work here.
2. **Activate the form (one-time).** The first submit makes FormSubmit email an **"Activate Form"** link to the
   address — **open it (check spam) and click it once**. Until then it holds submissions.

The app already handles FormSubmit's **anti-abuse origin check**: FormSubmit rejects a POST with no
`Origin`/`Referer` (*"…open this page through a web server…"*), and this form runs **server-side**, so it sends
`FPL_FEEDBACK_ORIGIN` for you. If you domain-lock the form later, set `FPL_FEEDBACK_ORIGIN` to your real app URL.
**No `FPL_FEEDBACK_KEY`** for FormSubmit.

**Web3Forms** (needs a key, robust server-side) — create an access key at web3forms.com for the inbox, then set
`FPL_FEEDBACK_WEBHOOK = "https://api.web3forms.com/submit"` **and** `FPL_FEEDBACK_KEY = "<your-access-key>"` (the
app sends it as `access_key`). No origin/activation dance.

**Test it:** submit the in-app **📣 Feedback** form → the form now shows the **real** result (delivered ✓ / the
relay's message if not) — no more false "sent". An email should land in the inbox.

> **Troubleshooting — "it says sent but nothing arrives":** almost always the FormSubmit **Activate Form** email
> hasn't been clicked, or the webhook address doesn't exactly match your mailbox. Test the endpoint directly:
> ```bash
> curl -s -X POST https://formsubmit.co/ajax/<your-addr> -H "Content-Type: application/json" \
>   -H "Origin: https://madboots.streamlit.app" -d '{"message":"test","_subject":"FPL test"}'
> ```
> `"needs Activation"` → click the email; the *"web server"* message → the Origin header is missing (the app
> sends it, a bare curl needs `-H Origin: …`); an address error → fix the webhook.

*(Any service accepting a JSON POST works — Formspree, a Zapier/Make webhook, a Tally webhook, etc.)*

## 2. The signup form (email capture, ~5 min)

A **Google Form** or **Tally** form: fields = *email* (required), *how you found us*, *consent to be
contacted*. Its share link is `FPL_SIGNUP_URL`. This list is how you **honour "free for X years"** later — tag
respondents as *founding testers*; if/when you add accounts + payments (DIRECTION §1), grant those emails a
comp tier.

## 3. Pick an access code

Set `FPL_ACCESS_CODE` to something shareable (e.g. `fpl-beta-2026`). Put it in your Reddit post / signup
confirmation so testers can get in.

> **"Remember me" is automatic (ADR-099).** Once a tester passes the gate on a device, a small first-party cookie
> keeps them in across a **browser refresh/restart** — no re-typing the code/email. Nothing to configure: it ships
> in `requirements.txt` (`streamlit-cookies-controller`). Good to know:
> - **Per device** — each phone/tablet/laptop is remembered once. **Private/incognito** tabs aren't remembered.
> - **~30 days**, but **iOS Safari caps it at ~7 days** (Apple's ITP), so iPhone/iPad testers re-register weekly.
> - **It grants nothing new** — the cookie is *re-validated* on every load, so **rotating `FPL_ACCESS_CODE`** or
>   **removing a tester from `beta_users`** locks that cookie out immediately.
> - **To not be remembered:** use a private tab, or clear the site's cookies. If cookies are blocked, the app just
>   falls back to asking each session (today's behaviour).
> - **A "Log out" link** (Sprint 133) sits at the foot of the sidebar once a tester is in ("Signed in as … · Log
>   out"). Clicking it clears the cookie + the session and re-shows the gate — handy on a **shared device** or to
>   switch tester. It's per-device (there's no server session), and it only appears when a gate is active.

---

## 4. Cap the number of testers (self-registration, ~10 min) — ADR-098

To **control how many testers can use the app** (so the free tier doesn't strain) and **know who they are**, turn
on the **capped registration gate**: a visitor enters the **invite code + their email** and is admitted up to a
**cap you set**; at the cap they see a *"beta full — join the waitlist"* note. **Soft control** — the email is
self-declared (no passwords/verification), the code gates *who can* register, the cap bounds *how many*. Reuses
the cross-device-squads Supabase (§ `docs/CLOUD_SQUADS.md`) — **no new store secret**.

1. **A users table** (same Supabase project as squads) — SQL Editor, idempotent:
   ```sql
   create table if not exists beta_users (
     email       text primary key,
     created_at  timestamptz not null default now()
   );
   alter table beta_users enable row level security;
   drop policy if exists "anon users read"   on beta_users;
   drop policy if exists "anon users write"  on beta_users;
   create policy "anon users read"  on beta_users for select using (true);
   create policy "anon users write" on beta_users for insert with check (true);
   ```
   *(Or `alter table beta_users disable row level security;` — same anon-open access, one line. This is the #1
   gotcha, exactly like the squads table.)*
2. **Turn it on:** set **`FPL_USER_CAP = 10`** in Streamlit secrets (keep `FPL_ACCESS_CODE` — it's the invite).
   The gate switches from the plain code prompt to **code + email**. Unset it → back to the code-only gate.
3. **Run it:** raise the cap (`20`, `50`…) as performance holds — one edit. **See / manage testers** in Supabase
   → **Table editor → beta_users** (each row = a tester's email; **delete a row to free a seat**). At the cap,
   new visitors are pointed to `FPL_SIGNUP_URL` as the waitlist.
   > **Capitalisation & spaces don't matter** (US-381): the allow-list is matched **case-insensitively** and
   > space-trimmed, so `Colin@Live.ie` admits `colin@live.ie`. (You can still add emails lowercased for tidiness.)

> **Soft, by design.** A determined person could type a fake or a second email; that's fine for a hobby beta
> gating public FPL data — you're *counting + knowing*, not securing. Hard per-user identity (Google `st.login()`)
> is the deferred upgrade (ADR-098 / DIRECTION §1).

### 4a. Capture would-be testers (the waitlist, optional) — ADR-102

When registration is capped, someone who tries after the cap is full — **or** who mistypes the invite code — is
turned away. Turn on the **waitlist** to **record their email** so you can invite them later. Same Supabase project,
**no new secret** (it derives its endpoint from `FPL_STORE_URL`, like `beta_users`); **off until the table exists**.

1. **A waitlist table** (same project) — SQL Editor, idempotent:
   ```sql
   create table if not exists beta_waitlist (
     email       text primary key,
     reason      text,               -- 'not_listed' (Google sign-in not on the allow-list) | 'full' (over the cap) | 'bad_code' (wrong invite code)
     created_at  timestamptz not null default now()
   );
   alter table beta_waitlist disable row level security;   -- the app UPSERTS (merge-duplicates); simplest + reliable
   ```
   ⚠️ **The app writes with an UPSERT** (`Prefer: resolution=merge-duplicates`, idempotent on retries) — so a plain
   **insert-only** RLS policy is **not enough** (the upsert's conflict path needs an *update* policy too, else you get
   `42501 "new row violates row-level security policy"` — a **silent** drop, since the write is fail-silent). Two
   working options: **(a)** the one-liner above — **disable RLS** (consistent with the store: `beta_users` already has
   an open read policy, so the publishable key can already read/write); or **(b)** keep RLS on with **both** policies:
   ```sql
   alter table beta_waitlist enable row level security;
   drop policy if exists "anon waitlist write"  on beta_waitlist;
   drop policy if exists "anon waitlist update" on beta_waitlist;
   create policy "anon waitlist write"  on beta_waitlist for insert with check (true);
   create policy "anon waitlist update" on beta_waitlist for update using (true) with check (true);
   ```
   *(The app **writes** but never reads the list back — you read it in the dashboard.)*
2. **It's automatic once the table exists.** With **Google auth** (`[auth]`, ADR-106), a signed-in email **not** on
   `beta_users` lands a row with **`reason='not_listed'`** — the table existing is the only requirement (no
   `FPL_USER_CAP` needed). With the older code-gate + `FPL_USER_CAP`, an over-cap or wrong-code attempt records
   `'full'`/`'bad_code'`. Best-effort either way — a store hiccup never blocks the gate; **no table → no write** (the
   capture is silently skipped, which is why an absent table means nothing is stored).
3. **Invite from it:** Supabase → **Table editor → beta_waitlist**. `reason='full'` = wanted in but the cap was full;
   `reason='bad_code'` = mistyped the code (could be a typo or a random). Free a seat (delete a `beta_users` row or
   raise `FPL_USER_CAP`), send them the code, then **delete the waitlist row**.

> **Privacy (ADR-102).** This holds emails of people you **didn't** admit — including wrong-code attempts. It's
> minimal (email + reason + time), owner-only, and *"remove me" = delete the row*. You're opting into the wrong-code
> capture knowingly; drop the `bad_code` rows if you only want the genuine over-cap waitlist.

---

## 5. Google sign-in + cross-device squads (the robust upgrade, ~20 min) — ADR-106

The **reliable, familiar** login: testers **Sign in with Google**, and their squad **auto-syncs across devices +
survives a mobile refresh** (no more re-entering a code, no lost team). **Allow-listed by `beta_users`** — the same
table as §4 — so *invite = add the email*; anyone else lands on the waitlist. **Off until `[auth]` is set** (the §3
code / §4 registration gate stays the fallback). **Free** (`st.login`, Google OAuth, and Supabase all cost nothing).

1. **A Google OAuth client** (Google Cloud Console → *APIs & Services*):
   - **OAuth consent screen** → **External** → app name **MADBOOTS** + your email → **scopes: `openid`, `email`,
     `profile`** (nothing "sensitive"/"restricted" → **no** paid verification) → **Publish to Production** *(this
     removes the 100-test-user cap and the scary "Google hasn't verified this app" warning)*.
   - **Credentials → Create → OAuth client ID → Web application** → **Authorised redirect URI:**
     **`https://madboots.streamlit.app/oauth2callback`** → copy the **Client ID** + **Client secret**.
2. **Turn it on** — add to Streamlit **Manage app → Settings → Secrets**:
   ```toml
   [auth]
   redirect_uri = "https://madboots.streamlit.app/oauth2callback"
   cookie_secret = "a-long-random-string"                 # any long random value (signs the auth cookie)
   client_id = "…apps.googleusercontent.com"
   client_secret = "…"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```
   With `[auth]` set, the app switches to **Sign in with Google**. **Unset it → back to the code/registration gate.**
3. **Invite testers** — add their emails to **`beta_users`** (§4). A signed-in email **in** the table → admitted +
   their squad syncs; **not** in it → the **waitlist** (`reason='not_listed'`) + a "not on the list yet" screen.
4. **The squad follows them** — it's auto-saved to the same Supabase (keyed by a **hash** of the email, so the
   squads table never stores a raw address) and restored on any device / after a mobile reconnect. No handle to type.

> **Privacy (ADR-106).** With Google sign-in you now hold **emails ↔ squads** (PII). Minimal + honest: **email only**
> (no other profile data), the squad keyed by a **hash**, and *"remove me" = delete their `beta_users` + squad rows*.
> The app tells the tester this on the sign-in screen. If you ever rename the Streamlit subdomain, update the
> **redirect URI** in both Google and the secret.

---

## 6. Maddie Explains videos (optional) — ADR-112

The **🎥 Maddie Explains** page is a video hub — short explainers fronted by the mascot (Maddie). The clips live
**unlisted on YouTube**; their rows live in a **`maddie_videos`** table in the *same* Supabase project (endpoint
derived from `FPL_STORE_URL`, **no new secret**). You curate videos from the **dashboard** — add / hide / reorder /
swap — **with no redeploy**. The app only **reads** the table, so — unlike the waitlist — **RLS stays on** with a
simple public-**read** policy (no write path = none of the `42501` upsert pain).

1. **Create the table** (SQL Editor, idempotent):
   ```sql
   create table if not exists public.maddie_videos (
     id          bigint generated always as identity primary key,
     topic       text    not null,
     blurb       text,
     youtube_url text,
     sort_order  int     not null default 0,
     published   boolean not null default false,
     created_at  timestamptz not null default now()
   );

   alter table public.maddie_videos enable row level security;

   create policy "maddie_videos public read"
     on public.maddie_videos for select using (true);
   ```
2. **Add a video** — upload the clip **unlisted** to YouTube, then insert a row (or use the Table editor):
   ```sql
   insert into public.maddie_videos (topic, blurb, youtube_url, sort_order, published) values
     ('Meet Maddie — what is MADBOOTS?',
      'The 60-second intro: the analytics decide, the AI explains, you make the call.',
      'https://youtu.be/REPLACE_ME', 10, true);
   ```
   - `published=false` hides a row without deleting it; `sort_order` sets the order; a **blank `youtube_url`**
     renders a *"🎬 Coming soon"* placeholder instead of a broken player.
3. **Refresh** — edits appear within the page's **~10-minute cache**, or **instantly** via **Reboot app** (the same
   trick as the DB snapshot). Never a redeploy.

> **No table (or an unreachable store) → the hub shows a built-in "Meet Maddie — coming soon" welcome** and never
> errors (best-effort, ADR-112). So the page is safe to ship before any video exists.

---

## 7. The ⭐ Watchlist (optional) — ADR-117

Each signed-in user can ⭐ a shortlist of players (on **Players**) and view them on **My Squad → Transfer**. It
persists per user in the *same* Supabase project (endpoint derived from `FPL_STORE_URL`, **no new secret**), like
the saved squad. **Off until the table exists** (session-only fallback otherwise).

1. **Create the table** (SQL Editor, idempotent). The app **upserts** it per user (like the squads table), so —
   as with the squad store — either **disable RLS** (simplest, consistent with the store) or add insert+update
   policies:
   ```sql
   create table if not exists public.player_watchlist (
     user_key    text primary key,          -- a hash of the user's email (ADR-106), not the email itself
     player_ids  jsonb not null default '[]'::jsonb,
     updated_at  timestamptz not null default now()
   );
   alter table public.player_watchlist disable row level security;   -- the app upserts; simplest + reliable
   ```
2. **That's it** — signed-in users' watchlists now save/restore across devices; capped at **30** players.

> No table (or not signed in) → the watchlist works **in-session only** (best-effort, ADR-117) and never errors.

---

## Recruiting (Reddit etc.)

- Post in **r/FantasyPL** (and similar) with a short pitch, the **signup link**, and the **access code**.
- Set expectations: *closed beta (limited spots — register with the code + your email) · preseason data · your squad saves across devices by a handle · feedback via the 📣 tab.*
- **Watch the host:** Streamlit Community Cloud is a small free tier — if 50 testers strain it, reboot from
  *Manage app → ⋮*, or move to a sturdier host (that's also the first nudge toward the multi-user step,
  DIRECTION §1).

## ✅ Go-live checklist (do these before recruiting)

Everything below is **£0** and opt-in. Tick them off, then post the invite.

- [ ] **Feedback sink live** — a Sheet (§1A) *or* an email relay (§1B) is set as `FPL_FEEDBACK_WEBHOOK`. **For
      FormSubmit:** the `/ajax/` endpoint + click the one-time **Activate Form** email. Submit the in-app **📣
      Feedback** form → it shows **"sent ✓"** (the real result) and the row/email arrives. *(Each carries the
      **page**, **app version**, and a **timestamp**, US-306.)*
- [ ] **Signup form** — `FPL_SIGNUP_URL` set (§2); the "✋ Join the beta" button shows on Home + Feedback.
- [ ] **Access code** — decide whether to gate (§3): set `FPL_ACCESS_CODE`, or leave open. Share the code with
      testers if set.
- [ ] **Cap the numbers** *(optional, recommended)* — set `FPL_USER_CAP` (§4) + the `beta_users` table → testers
      register with the code + an email, capped; raise the cap as perf holds; see who's in via the Supabase table.
- [ ] **Waitlist** *(optional)* — create the `beta_waitlist` table (§4a) → an over-cap or wrong-code attempt records
      its email so you can invite them later. No new secret; off until the table exists.
- [ ] **Google sign-in** *(optional, the robust upgrade)* — the `[auth]` secrets + a Google OAuth client (§5) →
      testers Sign in with Google (allow-listed by `beta_users`), and their squad syncs across devices / survives a
      mobile refresh. Off until `[auth]` is set; the code gate stays the fallback.
- [ ] **Prod/staging split** — the app testers use runs off the **stable** branch (`main`); you iterate on
      **staging** (`master`) and promote by merge, so a mid-sprint push can't break the beta
      ([ADR-095](06_Decisions/ADR-095-running-a-wider-beta.md); see [DEPLOY.md](DEPLOY.md#prodstaging-adr-095)).
- [ ] **Uptime monitor** — add the live URL to a free monitor (UptimeRobot / Better-Uptime, ~5-min ping) → you'll
      get response-time trends + a downtime alert if the free tier struggles under tester load.
- [ ] **Backup** — the mirror is active (a `MIRROR_URL` secret is set; see [BACKUP.md](BACKUP.md)).

## Turning it off

Delete the secrets → the app is fully public again: the access gate opens, the signup link disappears, and
feedback falls back to the **pre-filled email** (`FPL_FEEDBACK_EMAIL`) then a GitHub issue. No redeploy needed
beyond saving secrets (reboot if Cloud serves a stale build).

---

*This is a beta-enablement runbook, not a commitment to go multi-user. See [DIRECTION.md](00_Project/
DIRECTION.md) for the hobby-vs-product decision and when to revisit it.*
