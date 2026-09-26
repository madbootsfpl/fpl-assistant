# ADR-301 — One product, two surfaces

**Date:** 2026-09-26
**Status:** ⏳ **Gate — measured, not decided.** Nothing here ships code.
**From:** the owner — *"where possible, the desktop should reflect the apps & vice versa; we did state that
in the architecture redesign when we decided to support Android & iPhone."*

---

## The principle is on record, and it is narrower than memory has it

`Mobile_Platform_Audit.md` states the target as **"Streamlit web/desktop + a Flutter mobile client"**, and
ADR-219 named the mechanism: *one contract, two transports* — `src/service/` as plain functions, FastAPI
wrapping them for Flutter, Streamlit importing them in-process.

⚠️ **What was agreed was a shared *contract*, not a shared *feature set*.** That distinction is why the
drift happened without anybody breaking a rule.

## What the drift actually is — measured, not felt

⭐ **Feature parity is better than it feels.** Of eighteen user-facing things, **both surfaces carry
sixteen**: the pitch, This week, Signals, Players, Trending, FDR, Team DNA, Player DNA, Chips, Squad Lab,
mini-leagues, Boot Battle, Help, Feedback.

⚠️ **The genuine gaps are three, and all three are this week's work:**

| gap | where | ADR |
|---|---|---|
| Swipe through the season | app only | ADR-298 |
| The week-aware player card | app only | ADR-299 |
| Chatter | app only *(and the web had it first)* | ADR-300 |

🔴 **The one that should worry us is Chatter, and it drifted the other way.** It shipped on the **web** in
Sprint 068, sat on Trending until 26 Aug, and was dropped by ADR-150's reorganisation. For a month it was
called by **no caller on any surface** — dead code passing its own unit tests. ⭐⭐ *A feature does not have
to be deleted to be lost*, and nothing in this repo could tell us it had gone.

## The real cost is underneath the features

⚠️⚠️⚠️ **The two surfaces do not share the contract they were supposed to share.** Of 23 service functions:

- the **app** reaches **19** of them, over HTTP;
- **Streamlit** calls **4**, and otherwise goes straight to `src.analytics.*`, `src.ask` and `src.ui.*`.

⭐ *That is why every feature costs twice.* A new screen is not "Dart plus Python" — it is Dart against the
service contract, plus Python against a different, older internal API, with two renderers, two idioms and
two sets of tests. ⚠️ *Parity maintained by discipline is parity that survives exactly as long as the
discipline does*, and ADR-298/299 are what it looks like when a busy week arrives.

## The option the architecture already permits

⭐⭐⭐ **Flutter builds for web today.** Verified on 2026-09-26, not assumed:

- `flutter build web --release` — **succeeds**, unchanged.
- `main.dart.js` — **2.8 MB, 0.8 MB gzipped**.
- The API already sends `allow_origins=["*"]`, so a browser can call it now.
- `scripts/release_android.sh` already deploys a folder to Cloudflare Pages.

So *"the desktop reflects the app"* has a second reading: **let the desktop be the app.** Parity stops
being a discipline and becomes a property of there being one codebase.

## Three ways to honour the principle

| | what it means | cost |
|---|---|---|
| **A — port by hand** | Build ADR-298/299/300 again in Python | Every future feature twice, forever. ⚠️ *And it is the option that just failed.* |
| **B — Flutter web becomes the desktop** | One codebase, parity by construction | 🔴 Streamlit still owns the **invite gate**, **Admin** and the **Help/video** content. Flutter web is poor for SEO and first-load, and the landing page is where new testers arrive. |
| **C — split by what each is good at** | Product surfaces from Flutter web; Streamlit keeps Help, Admin and the gate | ⭐ Smallest honest step, and it does not throw away either investment. |

## Recommendation

⭐ **C, and the first move is a measurement, not a migration**: publish the Flutter web build to a path
(`madboots.com/app/web/`), open it on a desktop, and see what a mouse-and-keyboard user actually hits — the
pitch is built for thumbs, and ⚠️ *a phone layout on a 27-inch monitor is not parity, it is a phone layout
on a monitor.*

🔴 **What I would not do is Option A.** Re-implementing the season swipe in Streamlit is a week of work to
reach a place the Flutter build already reaches for the cost of a deploy step.

📌 **And whatever is decided, one small thing is worth doing regardless:** a test that fails when a service
function has **no caller on any surface**. Chatter was invisible for a month and every suite was green.
⭐ *The parity problem that actually bit us was not a feature missing from one surface — it was a feature
missing from both, with nothing able to say so.*
