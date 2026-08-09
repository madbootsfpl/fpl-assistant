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
FPL_FEEDBACK_ORIGIN  = "https://your-app.streamlit.app"           # the app URL FormSubmit sees (§1B) — anti-abuse
FPL_FEEDBACK_KEY     = "your-web3forms-access-key"                 # only if you use Web3Forms as the relay (§1B)
FPL_FEEDBACK_EMAIL   = "fpl.assistant@proton.me"                   # the mailto fallback address (default: this)
FPL_SIGNUP_URL       = "https://forms.gle/your-signup-form"        # the founding-tester email-capture form / waitlist
FPL_USER_CAP         = "10"                                        # cap registered testers (§4); unset = shared code only
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
  `mailto:`). Defaults to `fpl.assistant@proton.me`; set it to change the inbox.
- **`FPL_SIGNUP_URL`** — a link shown on **Home** + **Feedback** ("✋ Join the beta"). Unset → hidden.

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

### 1B. An email relay (~5 min) — straight to fpl.assistant@proton.me

Free form-to-email services forward a POST to your inbox — the app's payload already carries `_subject`, the
message, the page, and the version.

**FormSubmit** (no signup) — two gotchas that will bite if you skip them:

1. **Use the `/ajax/` endpoint** — the app POSTs **JSON**, so:
   `FPL_FEEDBACK_WEBHOOK = "https://formsubmit.co/ajax/fpl.assistant@proton.me"` (or `…/ajax/<random-token>` from
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
>   -H "Origin: https://your-app.streamlit.app" -d '{"message":"test","_subject":"FPL test"}'
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

> **Soft, by design.** A determined person could type a fake or a second email; that's fine for a hobby beta
> gating public FPL data — you're *counting + knowing*, not securing. Hard per-user identity (Google `st.login()`)
> is the deferred upgrade (ADR-098 / DIRECTION §1).

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
