# Running a private beta — owner runbook

How to open the app to ~50 testers (e.g. via Reddit), collect feedback, and build a founding-tester list you
can honour later — **without accounts/auth**. Everything here is **opt-in**: until you set the secrets below,
the app behaves exactly as it does today (public, open, feedback → GitHub). Background: [ADR-087](06_Decisions/
ADR-087-beta-access-and-feedback.md) · [DIRECTION.md](00_Project/DIRECTION.md) §3.

---

## The switches (Streamlit secrets)

Set these in **Streamlit Community Cloud → Manage app → Settings → Secrets** (TOML). All optional; unset = off.

```toml
FPL_ACCESS_CODE      = "your-shared-beta-code"                 # gates entry; testers type it once per session
FPL_FEEDBACK_WEBHOOK = "https://formsubmit.co/ajax/<token>"    # in-app feedback POSTs here (§1: a Sheet OR a relay)
FPL_FEEDBACK_KEY     = "your-web3forms-access-key"             # only if you use Web3Forms as the relay (§1B)
FPL_FEEDBACK_EMAIL   = "fpl.assistant@proton.me"               # the mailto fallback address (default: this)
FPL_SIGNUP_URL       = "https://forms.gle/your-signup-form"    # the founding-tester email-capture form
```

(Locally you can use the same names as **environment variables** instead.)

- **`FPL_ACCESS_CODE`** — when set, every page shows a 🔒 prompt until the code is entered. Rotate by editing
  the secret. It's a *shared* code (a beta gate, not per-user security) — fine here (the app is read-only,
  public FPL data).
- **`FPL_FEEDBACK_WEBHOOK`** — where the in-app **📣 Feedback** form POSTs (`{message, email, source, page,
  version, ts, _subject}`). Point it at a **Google Sheet** (§1A) *or* a **form-to-email relay** (§1B) that
  forwards to your inbox. **Unset → the form offers a pre-filled email** (`FPL_FEEDBACK_EMAIL`) — so feedback
  reaches you even with no webhook (US-307).
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

- **FormSubmit** (no signup): use `FPL_FEEDBACK_WEBHOOK = "https://formsubmit.co/ajax/<random-token>"` (get the
  token from formsubmit.co by tying it to fpl.assistant@proton.me — the token hides your address in the repo).
  **First submit sends a one-time confirmation email — click it once**, then feedback flows to the inbox.
- **Web3Forms** (needs a key): create an access key at web3forms.com for fpl.assistant@proton.me, then set
  `FPL_FEEDBACK_WEBHOOK = "https://api.web3forms.com/submit"` **and** `FPL_FEEDBACK_KEY = "<your-access-key>"`
  (the app sends it as `access_key`).

Test: submit the in-app form → an email lands in fpl.assistant@proton.me.

*(Any service accepting a JSON POST works — Formspree, a Zapier/Make webhook, a Tally webhook, etc.)*

## 2. The signup form (email capture, ~5 min)

A **Google Form** or **Tally** form: fields = *email* (required), *how you found us*, *consent to be
contacted*. Its share link is `FPL_SIGNUP_URL`. This list is how you **honour "free for X years"** later — tag
respondents as *founding testers*; if/when you add accounts + payments (DIRECTION §1), grant those emails a
comp tier.

## 3. Pick an access code

Set `FPL_ACCESS_CODE` to something shareable (e.g. `fpl-beta-2026`). Put it in your Reddit post / signup
confirmation so testers can get in.

---

## Recruiting (Reddit etc.)

- Post in **r/FantasyPL** (and similar) with a short pitch, the **signup link**, and the **access code**.
- Set expectations: *closed beta · preseason data · no accounts yet · your squad is a downloadable file · feedback via the 📣 tab.*
- **Watch the host:** Streamlit Community Cloud is a small free tier — if 50 testers strain it, reboot from
  *Manage app → ⋮*, or move to a sturdier host (that's also the first nudge toward the multi-user step,
  DIRECTION §1).

## ✅ Go-live checklist (do these before recruiting)

Everything below is **£0** and opt-in. Tick them off, then post the invite.

- [ ] **Feedback sink live** — the Google Sheet + Apps Script (§1) is deployed, and `FPL_FEEDBACK_WEBHOOK` is set
      in Streamlit secrets. Submit the in-app **📣 Feedback** form → a row appears in the Sheet. *(US-306: each
      row now also carries the **page**, the **app version**, and a **timestamp**, so a report is easy to place.)*
- [ ] **Signup form** — `FPL_SIGNUP_URL` set (§2); the "✋ Join the beta" button shows on Home + Feedback.
- [ ] **Access code** — decide whether to gate (§3): set `FPL_ACCESS_CODE`, or leave open. Share the code with
      testers if set.
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
