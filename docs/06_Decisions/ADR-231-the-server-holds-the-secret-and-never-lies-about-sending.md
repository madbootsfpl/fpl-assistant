# ADR-231 — The server holds the secret, and never lies about sending

**Date:** 2026-09-22
**Status:** Accepted
**Closes:** ADR-228's open item

---

## Context

A beta tester on a phone is **more** likely to notice something and **less** likely to be near a laptop.
The app had no way to tell anyone.

The web form POSTs straight to `FPL_FEEDBACK_WEBHOOK`. ⚠️ **A phone cannot do that**: a secret in a mobile
binary is a secret every tester has — the same reasoning that keeps the `service_role` key out of a client
(ADR-211), where the justification *"it never leaves the machine"* was true of Streamlit and explicitly
noted as not transferring.

## Decision

**`POST /api/v1/feedback` relays it.** The server holds the webhook; the client holds nothing.

### ⚠️⚠️ It never reports a blind "sent"

`relay_result` already exists because that was a real bug: the web form said *sent* while a relay silently
refused, because the target address had never been **activated**. A form-to-email relay answers **HTTP 200**
and `{"success": false}` — so reporting the status code alone calls a refusal a success.

⭐ *A success message that cannot fail is not a success message.* Three outcomes are distinguished, and each
comes back with the relay's own words:

| outcome | what the tester sees |
|---|---|
| no sink configured | *"Not sent — no feedback sink is configured. Email us instead."* |
| relay refused | its own message, e.g. *"address not activated"* |
| unreachable | *"could not reach the feedback service"* |

⭐ **Every failure carries the email address**, so a report is never lost — a tester reporting a bug must
not hit a second one.

### Relayed verbatim

The note is trimmed and otherwise untouched. ⚠️ *A server that reformatted or interpreted a bug report
would be editing the evidence.* `source` is `madboots-mobile`, so the owner can tell a phone report from a
web one without asking.

---

## ⚠️ The gap this ships with, named rather than discovered

**There is no rate limit.** On localhost the only caller is the owner. **The day this is hosted it becomes
an open relay to his inbox**, and a limit has to arrive *with* the hosting — not after someone finds it.

⭐ Writing it here is the point: an unguarded endpoint that is currently unreachable is a problem with a
date, not a problem that does not exist.

## Verification

* **7/7 mutations killed**, including *an unconfigured sink reports success* and *the relay's verdict is
  ignored* — the two that would restore the original bug.
* Suite **2,262 passed**.

## A note on the workflow

`uvicorn` was being run without `--reload`, so it served the code as of startup. Three times today a new
endpoint 404'd against a server that predated it, and each time the first suspicion was the client. ⭐ *A
stale process is indistinguishable from a missing route from the outside* — it now runs with `--reload`.
