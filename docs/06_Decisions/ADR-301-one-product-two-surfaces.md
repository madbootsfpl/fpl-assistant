# ADR-301 — One product, two surfaces

**Date:** 2026-09-26
**Status:** ⏳ **Gate — measured, not decided.** The measurement has now been taken; see the end.
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


---

## The measurement (2026-09-26)

⭐ **Published, unlisted, at `madboots.com/app/web/`** — beside the APKs, linked from nothing. The landing
page and the install page are untouched.

⭐⭐⭐ **The whole app runs in a desktop browser.** Live API, real squad, the purple live-week frame, the
bench on the right — ADR-293's sideways layout triggers correctly, because a 1440×900 window is wider than
it is tall, and it is the best-looking part of the screen.

### It found a real bug in ninety seconds, which is what it was for

⚠️⚠️⚠️ **Every kit and every mugshot was a 👕.** Both image servers — `fantasy.premierleague.com` and
`resources.premierleague.com` — return **200 with no `Access-Control-Allow-Origin`**, and CanvasKit fetches
image bytes in order to draw them, so all fifteen shirts came out identical.

⭐ Fixed with `webHtmlElementStrategy: WebHtmlElementStrategy.fallback` on all three `Image.network` call
sites: when the fetch fails, Flutter hands the URL to a plain `<img>`, which a browser displays
cross-origin quite happily because it never exposes the pixels to script. **Ignored on mobile**, so it
costs the phones nothing. Rebuilt, redeployed, verified — real club shirts.

⚠️ *This is exactly the class of thing that would have been discovered by a tester, months later, and
reported as "the web version looks broken."*

### What a mouse-and-keyboard user actually hits

🔴 **It is a phone layout on a monitor**, as predicted, and the specifics are worth having:

- The four figures — Predicted · In the bank · Value · Transfers — **spread across the full 1440px** with
  gaps wide enough to lose the relationship between a label and its number.
- **Next GW · Next 3 · Price** become three pill-shaped buttons ~460px wide each.
- The **bottom nav** sits at the bottom of the window, which is a thumb pattern on a surface with no thumbs.
- The pitch itself is **fine** — better than fine: the wide shape is what ADR-293 was built for.

⭐ *None of that is a blocker and none of it is parity either.* The honest read is that the web build makes
every feature **reachable** on a desktop today, and makes roughly two screens **pleasant** there.

### What this changes about the decision

⭐⭐ **Option A is now clearly the wrong one.** Re-implementing ADR-298/299/300 in Python would be a week
of work to reach a place this build reached in an afternoon — including the season swipe, which works.

⚠️ **Option B is not free either**, and the cost is now specific rather than hand-waved: it is a
**responsive pass** over the shell — the stat row, the mode bar and the navigation — not a rewrite. The
screens inside it already behave, because they were built against `LayoutBuilder` rather than a device
class (ADR-253/293), which turns out to have bought more than it was meant to.

📌 **Still open, and unchanged by this:** Streamlit keeps the invite gate, Admin and the Help/video content,
and nothing here proposes moving them.


---

## Admin is the counter-example, and it sharpens the recommendation (2026-09-26)

**From the owner:** *"what about the Admin feature too?"* — a fair challenge to this ADR's first pass,
which waved Admin aside as *"not a user feature"*. That is a reason to **scope** it, not to skip it.

⭐⭐⭐ **Admin does not need porting, because it is already surface-agnostic.** Both front ends write to the
**same Supabase `events` table**: the web through `web_streamlit/analytics.py` (ADR-100), the app through
`service/http/usage.py` (ADR-280) — *"one place to read, whichever surface a tester used."* Admin reads that
table. It has been watching the phones since the day they shipped.

⚠️ **So nothing about ADR-301 threatens the data. It threatens the reader**, because Admin is a Streamlit
page and would go wherever Streamlit goes.

⭐⭐ **And it should not follow.** Admin is the one place where Streamlit is genuinely the better tool:

- **It is owner-only**, gated by `FPL_ADMIN_KEY`, behind the beta gate. ⚠️ *A dashboard with a password in
  a shipped mobile binary is a password in every tester's pocket* — and the anon key already ships to the
  browser, which the page itself says.
- **It is a dashboard**: tables, medians, P95s, a sign-in probe that writes one row and reports what the
  store said. ⭐ *Streamlit exists for exactly this*, and rebuilding it in Dart would be a week spent making
  something worse.
- **Its audience is one person**, who has a laptop.

## Recommendation, sharpened

⭐ **Option C, with the line drawn at "who is it for":**

| | goes where |
|---|---|
| Everything a **tester** opens | Flutter — phone, and the same build on desktop |
| Everything the **owner** opens, plus the invite gate | Streamlit, unchanged |

⚠️⚠️ **This also removes the strongest argument against retiring Streamlit as a product surface**, which
was *"but then we lose Admin."* We do not: Admin keeps reading the table both surfaces already write to,
and it keeps running on the machine it was built for. ⭐ *The question was never web-versus-app; it was
which audience each surface serves.*

📌 **What still has to move before Streamlit stops being a product surface:** `Ask` and the browsable
Headlines list (ADR-300). Help and the videos are content and can live anywhere.
