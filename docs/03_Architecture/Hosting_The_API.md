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

One secret, and it is the same DSN the scheduled Actions already hold:

```
FPL_DATABASE_URL = postgresql://…@…pooler.supabase.com:5432/postgres
```

⚠️⚠️ **This is a database password.** It belongs in the platform's secret store, never in the image, never
in the repo, and never in a Flutter `--dart-define`. ⭐ *Same rule as the `service_role` key: the reason it
is safe server-side is that it stays there* (ADR-211).

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

⭐ No code change: the address has been runtime configuration since ADR-239, and **More ▸ Settings ▸
Server** still overrides it for you.

⚠️ **Hide that field before a build goes to testers.** It points the app wherever someone types, which was
flagged when it was built and is still true.

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
