# ADR-262 — A dependency that works from one host is not a dependency that works

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner, on the live app — *"i am getting a HTTP 403 error, any thoughts"*
**Follows:** ADR-261 (the 500 this was hiding behind), ADR-231 (the relay's own verdict)

---

## What it turned out to be

**FormSubmit sits behind Cloudflare, and Cloudflare refuses requests from datacenter IPs.** The block
happens at the CDN, before the request reaches the form at all.

⭐ **The same POST — same URL, same headers, same payload — succeeds from a laptop and is refused from
Render.** Four plausible causes were ruled out by probe rather than argued about:

| Suspected | Ruled out by |
|---|---|
| the URL shape (`/ajax/` missing) | the owner's value was correct |
| the form not being activated | an unactivated form answers **200 `success:false`**, never 403 |
| the `python-requests` User-Agent | a browser UA from the same machine behaved **identically** |
| the `Origin` header | sent, and correct, on every request |

⚠️ **It works on Streamlit Cloud, which is why nothing looked wrong until the API moved.** ⭐ *A dependency
that works from one host is not a dependency that works* — and FormSubmit is built for **browser** forms,
so that bot protection is doing precisely its job. We were the anomaly, not it.

## What was wrong on our side

### 1. A refusal threw away the relay's own words

ADR-231's whole claim is that the relay's verdict comes back rather than a blind *"sent"*. That held for a
`200` carrying `success: false` — and **not** for a `4xx`, which was flattened to its status code with the
body discarded. ⭐ *The one response nobody could diagnose was the one that had already been diagnosed for
us.*

### 2. ⭐⭐ And the fix for that was itself wrong, in an instructive way

Reading the body surfaced a rule from ADR-261: **never echo an HTML error page**, because a proxy's markup
is boilerplate, not an explanation. Correct — and applied here it suppressed *the entire diagnosis*, since
a CDN block **is** an HTML page. The app said *"HTTP 403"* and stopped while holding a document that named
the cause.

⭐ **So HTML is classified, never shown.** A known challenge page reports *who* refused; anything else
still says nothing. ⚠️ *"Never show X" and "never look at X" are different rules, and the first does not
imply the second.*

### 3. A field spelled for one relay only

FormSubmit reads `_subject`; Web3Forms reads `subject`. Only the first was sent. ⭐ *A field a relay does
not recognise does not error — it quietly produces an untitled email*, which is the kind of defect nobody
reports because the message still arrives. Both spellings now go.

⚠️ **This one survived its first mutation test** — the field was added without a test, so nothing caught
its removal. Noted because the mutation run is what found it, not review.

## Decisions

**1. FormSubmit is not usable from a hosted server.** The runbook now says so in red, with the evidence,
and points at **Web3Forms** (an API with an access key, built to be called by a server) or a **Google Apps
Script Sheet** (Google does not bot-block server POSTs).

**2. The app names the CDN block.** *"the relay's CDN (Cloudflare) blocked this server, not the form
itself — hosts on datacenter IPs are refused"* — ⭐ because that is a completely different problem from an
unactivated form, and **the status code cannot tell them apart.**

**3. The diagnostic is defensive**, since it runs where the body is least predictable: any of three key
spellings, plain-text fallback, long bodies trimmed, an unreadable body degrading to the bare status code,
and a silent relay reading exactly as before. ⭐ *A diagnostic that can itself fail turns a reported error
into a hidden one.*

📌 **Not decided here:** which relay to adopt. That needs an account the owner holds.

⚠️ **One variable still untested, and it is the cheapest one.** The working Streamlit deployment points at
`…/ajax/fpl.assistant@proton.me`; the Render deployment was pointed at a **different mailbox**. The probes
above rule out activation as a cause of a *403* — an unactivated form answers `200` — but they were run
against a third address, so ⭐ *pointing Render at the exact value Streamlit already uses is the one test
that isolates the host from the form.* Do that before migrating relay.

## Verification

* **Diagnosed by probe, not by reasoning** — an undeliverable test address (`@example.invalid`) so no
  message could reach anyone, isolating one variable at a time.
* **16 new tests** (2,493 total); **5/5** then **3/4** mutations killed — ⚠️ the survivor was real, and closing it needed
  a new test rather than a re-run.
