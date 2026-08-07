# Running a private beta — owner runbook

How to open the app to ~50 testers (e.g. via Reddit), collect feedback, and build a founding-tester list you
can honour later — **without accounts/auth**. Everything here is **opt-in**: until you set the secrets below,
the app behaves exactly as it does today (public, open, feedback → GitHub). Background: [ADR-087](06_Decisions/
ADR-087-beta-access-and-feedback.md) · [DIRECTION.md](00_Project/DIRECTION.md) §3.

---

## The three switches (Streamlit secrets)

Set these in **Streamlit Community Cloud → Manage app → Settings → Secrets** (TOML). All optional; unset = off.

```toml
FPL_ACCESS_CODE     = "your-shared-beta-code"                 # gates entry; testers type it once per session
FPL_FEEDBACK_WEBHOOK = "https://script.google.com/.../exec"    # in-app feedback POSTs here (see below)
FPL_SIGNUP_URL      = "https://forms.gle/your-signup-form"     # the founding-tester email-capture form
```

(Locally you can use the same names as **environment variables** instead.)

- **`FPL_ACCESS_CODE`** — when set, every page shows a 🔒 prompt until the code is entered. Rotate by editing
  the secret. It's a *shared* code (a beta gate, not per-user security) — fine here (the app is read-only,
  public FPL data).
- **`FPL_FEEDBACK_WEBHOOK`** — where the in-app **📣 Feedback** form POSTs (`{message, email, source}`). Unset →
  the form politely points testers to a GitHub issue instead.
- **`FPL_SIGNUP_URL`** — a link shown on **Home** + **Feedback** ("✋ Join the beta"). Unset → hidden.

---

## 1. The feedback sink (a Google Sheet, ~10 min)

Simplest zero-cost webhook — a Google Apps Script bound to a Sheet:

1. Create a Google **Sheet** ("FPL beta feedback") with headers: `timestamp · message · email · source`.
2. **Extensions → Apps Script**, paste:
   ```js
   function doPost(e) {
     const d = JSON.parse(e.postData.contents);
     SpreadsheetApp.getActiveSpreadsheet().getActiveSheet()
       .appendRow([new Date(), d.message || "", d.email || "", d.source || ""]);
     return ContentService.createTextOutput("ok");
   }
   ```
3. **Deploy → New deployment → Web app**, *Execute as: me*, *Who has access: Anyone*. Copy the `/exec` URL →
   that's `FPL_FEEDBACK_WEBHOOK`.
4. Test: submit the in-app form; a row should appear in the Sheet.

*(Any service that accepts a JSON POST works — Formspree, a Zapier/Make webhook, a Tally webhook, etc.)*

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

## Turning it off

Delete the three secrets → the app is fully public again, feedback falls back to GitHub, the signup link
disappears. No redeploy needed beyond saving secrets (reboot if Cloud serves a stale build).

---

*This is a beta-enablement runbook, not a commitment to go multi-user. See [DIRECTION.md](00_Project/
DIRECTION.md) for the hobby-vs-product decision and when to revisit it.*
