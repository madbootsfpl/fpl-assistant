# FPL Assistant — Direction & Options

A record of the **strategic** questions (2026-08-07) and the options explored, so the direction is captured
and shareable on GitHub. This is deliberately honest about effort and trade-offs; nothing here is committed —
it's a map for deciding *when* and *whether* to leave the current simple design.

**Today's design (why it matters here):** the app is intentionally **backend-free** — no accounts, no
server-side writes, your squad lives in your session or a downloaded `squad.json`, data is a committed
`seed.db`, hosted free on Streamlit Community Cloud, with an optional local LLM. Everything below is measured
against *leaving* that simplicity.

**The headline recommendation:** stay **community / hobby** through a wider beta (below), use it to **validate
demand**, and only then decide on multi-user / paid. Capture tester **emails** now so any future "free for X
years" promise can be honoured.

---

## 1. Multi-user · registration · paid — how big a step?

Going multi-user is a **real architectural pivot**, because it adds exactly the three things the current design
avoids on purpose:

| Piece | What it needs | Effort |
|---|---|---|
| **Accounts / auth** | email or Google sign-in (Supabase Auth · Clerk · Firebase) | Medium |
| **Per-user storage** | a real database (Postgres) for each user's squads/settings — the biggest shift | Medium–High |
| **Hosting** | Community Cloud isn't built for auth / many users → Render · Fly · a VPS | Medium |
| **Payments** | Stripe subscriptions, features gated by tier | Medium |
| **Ops & legal** | scheduled data refresh, backups, secrets, GDPR, support | Ongoing |

**Pragmatic stack if/when we do it:** **Supabase** (Postgres + Auth + storage, generous free tier) +
**Stripe** + a proper host. It's well-trodden (weeks, not months), but it turns a hobby app into a *product
with ongoing ops and cost*.

**Verdict:** don't build the *hard* pivot (accounts/auth/payments) until demand is proven. The no-backend design
stays a feature, not a gap.

> **Decision (2026-09-01, ADR-098) — a *soft* step taken, the *hard* pivot still deferred.** To control tester
> numbers before recruiting (protect the free tier) and know who's in, we added a **capped email-registration
> gate**: a visitor enters the **shared invite code + their email** and is admitted up to a **variable
> `FPL_USER_CAP`** (raise it 10 → 20 → 50 as performance holds); at the cap → a waitlist note. Backed by a small
> `beta_users` table in the **existing Supabase** (reuses the cross-device-squads store, no new secret). It's
> **soft** — the email is self-declared (no passwords/OAuth/verification), so it's *counting + knowing*, not
> security; the code is the real anti-abuse lever. This **softens** "no accounts" without the pivot above:
> **no auth, no per-user product storage, no payments, same host**. The cap limits *registered* users (a load
> proxy); a paid host is the escalation (ADR-095). **Off by default** (unset the cap → the old code/open gate).
> The **hard** version — real per-user identity via native **`st.login()`** (Google) — remains the deferred
> upgrade if the beta becomes a product.

---

## 2. iOS / Android apps — what's involved?

**Key dependency:** native apps talk to an **API**, not to a Streamlit app — so this presupposes the backend
from §1. Options, cheapest first:

- **Responsive web + PWA ("add to home screen")** — ~90% of the value for ~5% of the effort. Streamlit isn't
  a *great* PWA (heavy, not mobile-first) but it works; the pitch redesign already improved mobile.
- **WebView wrapper** (Capacitor) → store-publishable, but Apple often rejects "just a website" wrappers.
- **Native / cross-platform rebuild** (Flutter · React Native) over a real API — a whole second frontend.
  High effort; needs the backend first. *(The frozen FastAPI edge, ADR-050, is the seed of that API.)*

**Verdict:** no native apps yet. Make the web app mobile-friendly + installable (PWA); native comes **after** a
real API and proven demand.

---

## 3. Wider testing — 50 strangers (e.g. via Reddit)

You can do this **without building auth**. The goal is: some access control, low-friction feedback, and the
ability to honour a future "free for X years" promise.

> ✅ **Built (Sprint 102, ADR-087):** the beta *infrastructure* is in place and **opt-in** — a shared
> access-code gate (`FPL_ACCESS_CODE`), an in-app **📣 Feedback** tab (→ `FPL_FEEDBACK_WEBHOOK`, degrades to
> GitHub), and a **"Join the beta"** email-capture link (`FPL_SIGNUP_URL`). **Off by default**; flip it on by
> setting the three secrets and recruit — runbook: **[../BETA.md](../BETA.md)**. What remains is the owner's
> (create the forms/webhook, set the secrets, post on Reddit).

- **Access** — keep the URL open, optionally behind a shared **access code** (a Streamlit password/secret
  gate). No accounts needed.
- **Recruit + capture** — a **Google / Tally signup form** that collects **emails** and tags people as
  *founding testers*. Capturing emails now is what lets you comp them later, even before accounts exist.
- **Feedback** — an **in-app feedback form → a Google Sheet / webhook** (GitHub Issues is too much friction
  for non-devs). Keep the existing Issues link for the technical few.
- **Recruit on** r/FantasyPL and similar — set expectations (beta · data may reset · no accounts yet).
- **Watch the host** — Community Cloud is a small free tier; 50 concurrent testers may strain it. If load
  grows, move to a sturdier host (this is also the first nudge toward §1).

**"Free for X years" only needs an email list now** — grant those addresses a comp tier if/when auth +
payments arrive. Don't build accounts just for the beta.

**Suggested first step:** a small sprint — an access-code gate + an in-app feedback form → a Google Sheet +
the external signup form. (Planned on request; not yet built.)

---

## 4. Decision framework — hobby vs product

**Stay hobby/community (default) while:** usage is you + a handful of testers; the joy is the build/learning;
you don't want ops, cost, or support obligations.

**Consider the product pivot when *several* are true:**
- The beta shows **repeat, sustained use** by strangers (not just curiosity clicks).
- People ask to **save their team** / come back to it (the no-persistence limit starts to bite).
- There's **willingness to pay** signal (people ask for premium features, or the data/LLM costs start mattering).
- You're happy to take on **ongoing ops** (uptime, backups, support, GDPR, payments).

If those hold, the **lowest-regret path** is: Supabase (auth + DB) → server-side squads → a paid tier via
Stripe → *then* PWA/native — reusing the existing analytics engine unchanged (the core already imports nothing
from the web edge, so a new frontend/API sits cleanly on top).

---

*Companion docs: [PRODUCT.md](PRODUCT.md) (what exists + gating), [../Backlog.md](../Backlog.md),
[../04_Roadmap/Roadmap.md](../04_Roadmap/Roadmap.md). This file records direction; it commits to nothing.*
