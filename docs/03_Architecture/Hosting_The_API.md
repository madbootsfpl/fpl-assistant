# Hosting the API

**What this gets you:** the app working on 4G, away from the house, for someone who is not you.
**Time:** under an hour, most of it waiting.
**Cost:** near zero at this traffic — see *What it should cost*.

---

## ⚠️ What has been executed, and what has not

⭐⭐ **This distinction is the point of the section.** The last runbook in this project was written from
knowledge and broke **four times** on first use (ADR-249) — every fault a step-to-step interaction that
reading could not have found.

✅ **Executed on this machine, and the numbers below are measurements:**

* the image builds — **234 MB**
* it runs, and reports itself **unhealthy** with a reason when no database is configured
* pointed at Postgres it serves real answers — 20 clubs, 487 players, out of the container
* cold start **0.9–1.1s** over three runs; first real request **66 ms**
* the rate limiter, under test

🔴 **Not executed — no account, and not mine to create:**

* everything from *Step 2* onward: the platform account, the deploy, the secret, the custom domain
* ⚠️ *Expect this half to have a wrinkle I have not seen.* Tell me where it goes wrong and it gets fixed
  here, the way the iPhone runbook did.

---

## Step 1 — Prove the image locally (✅ executed)

```bash
docker build -t madboots-api .
docker run --rm -p 8097:8080 madboots-api
curl -s localhost:8097/api/v1/health
```

⭐ **Expect `{"ok": false, …}`** and a reason saying `FPL_DATABASE_URL` is not set. That is correct: a
container with no database **must not** claim to be healthy.

Then with a database:

```bash
docker run --rm -p 8097:8080 \
  -e FPL_DATABASE_URL="<the session-pooler DSN>" madboots-api
curl -s localhost:8097/api/v1/health          # {"ok": true, …}
```

---

## Step 2 — Pick a platform (🔴 not executed)

Any host that runs a container and injects `$PORT`. What actually matters:

| | why |
|---|---|
| **IPv4 outbound** | ⚠️ Supabase's *direct* connection is IPv6-only on most projects. Use the **session pooler** — `…pooler.supabase.com:5432` — which is what the GitHub Actions already use (ADR-211). |
| **Scale-to-zero** | Fine here. App boot is ~1s measured; the platform adds its own overhead. |
| **HTTPS included** | ⚠️ Not optional: iOS ATS permits cleartext only on the **local** network (ADR-239), so an `http://` host would be blocked on a phone. |
| **~256 MB memory** | Peak measured is **87 MB**. Every free tier clears this. |

---

## Step 3 — Deploy (🔴 not executed)

### The one required secret

It is the same DSN the scheduled Actions already hold:

```
FPL_DATABASE_URL = postgresql://…@…pooler.supabase.com:5432/postgres
```

⚠️⚠️ **This is a database password.** It belongs in the platform's secret store, never in the image, never
in the repo, and never in a Flutter `--dart-define`. ⭐ *Same rule as the `service_role` key: the reason it
is safe server-side is that it stays there* (ADR-211).

### The rest — optional, but ⚠️ **feedback silently does nothing without them**

⚠️ **This section exists because it was missing, and the omission had a cost.** These were written up in
`docs/BETA.md` as **Streamlit secrets** and never carried across to the host, so the first thing the owner
tried on the live phone build — *Tell us something* — could not have worked. ⭐ *A variable documented for
one deployment is not documented for the next one.* `tests/test_hosting_doc.py` now fails if the API reads
a variable this table does not name.

| Variable | Without it | Set it to |
|---|---|---|
| `FPL_FEEDBACK_WEBHOOK` | ⚠️ Feedback answers **"no feedback sink is configured on the server"** — honest, and still not delivered. **Set this or in-app feedback does not reach you.** | 🔴 **neither FormSubmit nor free Web3Forms** — see below. An **Apps Script `/exec` URL** (`docs/BETA.md` §1A) |
| `FPL_FEEDBACK_KEY` | nothing, unless the relay needs an access key | ⚠️ leave unset for an Apps Script sink — it is only Web3Forms' `access_key` |
| `FPL_FEEDBACK_EMAIL` | falls back to `hello@madboots.com` | the address offered to a tester when the relay fails |
| `FPL_FEEDBACK_ORIGIN` | falls back to the Streamlit URL | ⚠️ only matters if the relay checks `Origin` |
| `FPL_STORE_URL` + `FPL_STORE_KEY` | ⭐ **no usage recording at all** — the API answers requests and counts nothing. Set them and it records load per platform (ADR-280) | the same Supabase store the web app uses; ⚠️ *no new secret, and no new table* |
| `FPL_USAGE_OFF` | nothing — recording stays on | ⭐ set to anything to stop it **without a deploy**: *a thing that records people should be possible to stop without one* |

### ⭐ What the usage rows contain, and what they never will

`platform` · `version` · a **random install id** · the endpoint · a duration. ⚠️⚠️ **Not the manager id**,
which the API receives on four endpoints and must never join to these; **not the caller's IP**, which the
rate limiter next door does read; and **not the request body**. ⭐ *The difference between "twelve Android
devices" and "Tony opened Trending" is the whole of the promise* — `tests/test_usage_recording.py` pins
both the behaviour and a source sweep that fails the day somebody adds the join.

### 🔴 FormSubmit does not work from a hosted server

⚠️⚠️ **This cost a full debugging session, and the symptom named the wrong culprit** (ADR-262). In-app
feedback returned `sent: false, "the service returned HTTP 403"` with everything configured correctly.

**FormSubmit sits behind Cloudflare, and Cloudflare refuses requests from datacenter IPs** before they ever
reach the form. The same POST — same URL, same headers, same payload — succeeds from a laptop and is
refused from Render. ⭐ *It is not the form, the address, the activation state, or the User-Agent; all four
were ruled out by probe.* FormSubmit is built for **browser** forms, and that bot protection is doing
exactly its job.

⚠️ It works on Streamlit Cloud, which is why nothing looked wrong until the API moved. ⭐ *A dependency
that works from one host is not a dependency that works.*

**Use a relay designed to be called by a server:**

⚠️⚠️ **Web3Forms is not the answer either, and it was tried.** It refuses a server-side call in its own
words — *"This method is not allowed. Use our API in client side or contact support with server IP address
(Pro plan is required)"*. ⭐ **Both free form relays are built for browsers on purpose**, and a hosted API
is exactly what their free tiers exclude. That is a category, not two coincidences.

| Option | Verdict |
|---|---|
| **Google Apps Script → Sheet** ✅ | **Use this.** Google does not bot-block server POSTs, there is no plan gate, and the script can **email you as well as log the row** (`docs/BETA.md` §1A). |
| ~~FormSubmit~~ 🔴 | Cloudflare refuses datacenter IPs before the form is reached. |
| ~~Web3Forms (free)~~ 🔴 | Server-side calls require the Pro plan. |
| A transactional email API | Resend/Postmark/SendGrid are built for servers. ⚠️ More setup — domain verification — and only worth it if the Sheet proves inadequate. |

⭐ **The app will now say which of these is happening.** A CDN block is reported as *"the relay's CDN
(Cloudflare) blocked this server… hosts on datacenter IPs are refused"*, which is a different problem from
an unactivated form — and the status code alone cannot tell them apart.

⭐ **Check it actually relays, rather than assuming.** `POST /api/v1/feedback` returns `sent: true/false`
with the relay's **own** reason — that is the whole point of ADR-231. ⚠️ **The endpoint allows 5 calls an
hour**, so a couple of test submissions will lock you out for the rest of it; that limit is a cost control,
not a security boundary.

**Verify before going further:**

```bash
curl -s https://<your-host>/api/v1/health
```

✅ `{"ok": true, "service": "madboots", "version": "0.0.1"}` — and ⚠️ **`ok: true` now means something**:
the instance has opened the database and read from it. A `false` here carries the reason.

---

## Step 4 — Measure the cold start yourself (🔴 not executed)

⭐⭐ **Do this before any tester has the URL**, because the alternative is learning it from a tester at a
deadline.

Leave it untouched for an hour, then:

```bash
time curl -s https://<your-host>/api/v1/health
```

| what you see | what it means |
|---|---|
| **under ~3s** | scale-to-zero is fine. Nothing more to do. |
| **10s or worse** | set minimum instances to 1. ⭐ One setting, same image, minutes to change. |

### ✅ Executed on Render, 2026-09-23 — and it crossed the line

| | |
|---|---|
| **cold, after idle** | **13.4 s** |
| warm `/health` | 0.10–0.18 s |
| warm `squad/analysis` | ~0.9 s |

⚠️⚠️ **13.4 seconds is the second row of that table**, and the table was written before the answer was
known. ⭐ *A threshold agreed in advance is the only kind that can overrule the person who set it* — the
earlier decision to run scale-to-zero was made on a **1-second local container boot**, and the deployed
measurement is thirteen times that.

**What 13 seconds is:** a tester opening the app for the first time that day, watching a spinner, and
concluding it is broken. It is the *first* impression, every time, for anyone who is not using it hourly.

📌 **So this is now a decision about always-on**, and the runbook's own rule says take it. See
*What it should cost* — the change is the same image and one setting, but on a free tier "minimum
instances" is not a setting you have; it means a paid instance.

📌 **A warming ping was designed and deliberately not built.** With a 1s app boot it would save a couple of
seconds, once — ⭐ *building it anyway would be building for a fear the measurement contradicts.* If Step 4
comes back slow, always-on is the simpler answer than a cron that pretends to be one.

---

## Step 5 — Point the app at it (🔴 not executed)

```bash
(cd mobile && flutter run --release \
  --dart-define=MADBOOTS_API=https://<your-host> \
  -d <device-id>)
```

⭐ No code change: the address has been runtime configuration since ADR-239.

✅ **The Settings ▸ Server field is no longer in a tester's build** (ADR-270) — it was flagged as a risk
when it was built and is now gone unless a build asks for it. ⚠️ *A tester handed an editable API address
has a way to point the app at nothing, and the only bug report that follows is "the app stopped
working".*

Add `--dart-define=MADBOOTS_DEV=true` when **you** need the field — pointing a handset at a laptop on the
LAN is the case it exists for.

⚠️ **If this ends in `Error running application on iPhone`, read the section below before changing
anything** — it has twice now meant a successful install and a refused launch.

---

## ⚠️ "Error running application on iPhone" — twice now, neither time a real error

Flutter reports a **launch** failure with the same words it uses for a build failure:

```
Xcode build done.                                           19.8s
Could not run build/ios/iphoneos/Runner.app on 00008150-…
Installing and launching...
Error running application on iPhone 17 (wireless).
```

⭐⭐ **The app is already installed at this point.** The build succeeded, the install succeeded, and only
the launch was refused — but the message reads as none of those, and ⚠️ *the tempting next move is to
re-run the command, which will fail identically every time because nothing about it is wrong.*

Ask the phone why:

```bash
xcrun devicectl device process launch --device <device-id> com.madboots.fpl
```

| what it says | what it means | what to do |
|---|---|---|
| `Locked` | the phone is locked — it cannot launch an app onto a locked screen | unlock it, open the app from the home screen |
| `…profile has not been explicitly trusted` | first install with this certificate | Settings ▸ General ▸ VPN & Device Management ▸ Trust |
| `Developer Mode` | iOS 16+ has not been switched on | see `iPhone_Free_Provisioning.md`, Step 5 |
| `expired` / will not launch at all | 🔴 the **7-day certificate** | re-run `flutter run --release` |

⭐ **In every one of those cases the app is on the phone already.** Open it from the home screen rather
than re-running the command.

---

## ⚠️ Measured on the deployed instance (Render, 2026-09-23) — ✅ executed

| | hosted, warm | local |
|---|---|---|
| `/health` | **69–78 ms** | — |
| `squad/analysis` | **787–802 ms** | 54 ms |
| `players` (97 KB) | **984–1098 ms** | 76 ms |

⭐⭐ **The network is not the problem and the code is not the problem.** `/health` does no work and returns
in ~70 ms, so the round trip is fine; the same analysis that takes 54 ms locally takes 800 ms there. The
difference is **CPU** — a shared free-tier core against an M-series Mac.

⚠️ **So the app will feel about a second per screen, not instant.** That is usable for a beta and worth
knowing before a tester says it. ⭐ *The fix, if it becomes one, is a bigger instance — not a rewrite: the
local numbers already prove the code is fast.*

📌 **Still owed: the cold-start measurement (Step 4).** Free tiers spin down; a warm instance says nothing
about one that has been idle for an hour.

---

## What it should cost

At this traffic — a handful of testers, sub-200ms calls, 87 MB — **scale-to-zero is effectively free** and
always-on is a few pounds a month.

⚠️ **I have not verified current pricing**, and would not: it changes, and the free tiers change with it.
Check today's terms before committing. ⭐ *The number that matters is not the price, it is that switching
between the two is one setting on the same image.*

---

## If something breaks

| symptom | cause | fix |
|---|---|---|
| `{"ok": false, …}` naming `FPL_DATABASE_URL` | the secret is not set, or not visible to the running process | set it and redeploy |
| `{"ok": false, …}` with a connection error | ⚠️ almost always **IPv6** — the direct Supabase host | switch to the session pooler |
| Healthy, but the phone cannot reach it | the URL is `http://` | ⚠️ iOS ATS blocks cleartext off the LAN |
| `429` with `Retry-After` | the rate limit, working | wait, or raise the limit in `limits.py` |
| Answers are stale | the **pipeline**, not the API | ⭐ the app's own banner says so (ADR-248) |
