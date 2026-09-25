# ADR-300 — Chatter and News under Signals

**Date:** 2026-09-25
**Status:** ⏳ **Gate — asked, not agreed.** Nothing in this ADR ships code, and one half of it is a
recommendation to **not build**.
**From:** the owner — *"Signals: can we add in the Headlines — FPL analysis & football news as well as the
Community chatter, maybe stick under one or two new sub tabs under Signals called Chatter and/or News. Can
we have images rather than just links. Thoughts?"*

---

## Chatter already exists, and the phone cannot reach it

⭐⭐⭐ **`src/community.py` has been in this repo since Sprint 067 (ADR-059).** It fetches `r/FantasyPL`'s
public RSS, counts whole-word player mentions against the squad index, and returns a ranked *most talked
about* list. It degrades on 403 / 429 / timeout / parse error to `(None, message)` and never raises.

⚠️ **It is wired to Streamlit and to nothing else.** There is no route in `src/service/`, so the Flutter
app has never been able to ask for it. ⭐ *The expensive half of "Chatter" was paid for a year ago and has
been invisible to every tester since the app shipped.*

**Cost to surface it:** one endpoint, one model, one sub-tab. No new dependency, no new source, no new
failure mode — the degradation path is already written and already tested.

⭐ It also fits what Signals **is**. The tab's existing promise is *"what changed that you should know
about"*, and *"forty people are arguing about Mbeumo today"* is that, in the one currency Signals already
trades in: attention. ⚠️ Worth keeping the existing framing on it — **mention frequency, not sentiment** —
because *a count of names is not an opinion about players, and a screen that blurs the two is inventing
analysis it did not do.*

## News is a different kind of thing, and I would not build it

🔴 **This is the half I would push back on**, and the reason is not effort.

⚠️⚠️⚠️ **It changes what the product is.** Everything in this app answers *"what should I do about my
squad?"* from numbers it computed and can explain — the landing page says **"Analytics decide. Logic
explains."** A headline feed answers *"what is happening in football?"*, which is a question a hundred
apps already answer better, and it is the first surface here that would carry text nobody could hold this
app accountable for. ⭐ *A tool people open to decide something is a different product from one they open
to browse, and the second is much harder to stop becoming.*

**Three concrete costs, on top of the philosophical one:**

1. ⚠️ **Someone else's words and pictures.** Republishing headlines with thumbnails means hot-linking
   images from publishers who have not agreed to it, at whatever scale this grows to. Fine at nine
   testers; ⭐ *a decision that is fine at nine and not at nine hundred is a decision worth making at
   nine.*
2. ⚠️ **A feed is a liability the pipeline does not have.** Every other source here is FPL or Reddit, both
   with a known shape and a written degradation path. A news feed is an editorial firehose — 🔴 *the first
   time it carries something distasteful next to a manager's squad, the app published it.*
3. ⚠️ **It never says it was wrong.** Signals exists because *"the server says what exists; only the device
   knows what is new"* (ADR-232/256). Headlines do not expire, cannot be marked seen in any meaningful
   way, and would sit at the top of the tab going stale.

⭐ **What I would do instead, if the want behind this is real:** the actual need is probably *"tell me
when something happened to a player I own"* — which is what Signals already does from **price, minutes,
status and ownership**, and could do better from **team news** without importing a newspaper. ⚠️ *The
feature to build is the one the request is reaching for, not the one it names.*

## Images

⚠️ **Worth separating from the tabs.** A Reddit entry carries no reliable thumbnail; a club-badge or
player-mugshot beside each row is **already in hand** (`shirt_url`, the mugshots the player sheet uses)
and costs nothing new. ⭐ *An image that identifies the subject is worth more than one that decorates the
page*, and it is the one this app can supply without asking anyone's permission.

## Recommendation

| | |
|---|---|
| **Chatter** | ✅ Build. One endpoint away, fits the tab, degrades already. |
| **News** | 🔴 Do not build — see above. Happy to be overruled, but this one is a fork in what the product is. |
| **Images** | ✅ Build with Chatter, from **our own** badges and mugshots. |

📌 **If the answer is "build News anyway"**, the version I would argue for is *narrow*: team-news and
injury headlines **only**, filtered to clubs in your squad, with the source named on every row — ⚠️ *which
is a Signals feature wearing a News label, and that is rather the point.*
