# ADR-305 — The owner's view, without the owner's key

**Date:** 2026-09-26
**Status:** ✅ **Built.**
**From:** the owner — *"index.html needs to be updated so selecting desktop version drives you to the web
app and not streamlit. Can we add in the Admin, bury it in Settings so I can look at the stats … on my
desktop only."*

---

## The landing page

⭐ Three links repointed from `madboots.streamlit.app` to `/app/web/`. It is the **same app** in a browser
now — same screens, same numbers — where the old link led to a product that had drifted three features
behind. ⚠️ *A button labelled "use on desktop" that opens something else teaches people the two are
unrelated.*

📌 The Settings copy went with it. That paragraph has now gone false **twice**: it once named the ticker,
Team DNA and Trending as web-only (all three already shipped), and then said *"the web app stays the
exploration layer"*, which stopped being true the day the desktop became this app. ⭐ *Positioning copy
outlives the positioning it describes* — so the new version claims the smallest true thing: where the
videos are.

## Admin: the design is forced, and worth saying why

🔴 **The obvious implementation would publish a service-role key.** Reading the `events` table needs
`FPL_ADMIN_STORE_KEY`, which bypasses RLS completely and which `web_streamlit/analytics.py` marks
*"server-side only"*. ⚠️⚠️⚠️ **The web build is public JavaScript** — anyone can open
`madboots.com/app/web/` and read the bundle. *A key shipped to this client is a key published*, and that
is true of the mobile binary too, only less obviously.

⭐⭐ **So the client holds no credential at all.** The owner types a password; it travels per request; the
server compares it against `FPL_ADMIN_KEY` and does the reading itself. `POST /api/v1/admin/usage`.

**The door, and each part of it:**

| | |
|---|---|
| unconfigured | **404** — ⭐ *an endpoint that exists but cannot work is one somebody will spend an afternoon debugging*, and it tells a stranger nothing about this deployment |
| half configured | **404** — a password with nothing to read is not a working page |
| wrong key | **401**, and nothing else in it — ⭐ *the only thing a failed attempt should teach is that it failed* |
| the comparison | `hmac.compare_digest` — ⚠️ a plain `==` leaks the common prefix to anyone timing it |
| rate limit | **10/min** — ⭐ *the difference between a secret and a secret you can guess at leisure* |
| the answer | `Cache-Control: no-store` — one person's private view of the whole beta, on a CDN-fronted domain |

⚠️⚠️ **Aggregates, never rows.** `usage.py` refused to store a manager id on the owner's own instruction —
*"I am not interested in personal information"* — and ⭐ *a promise kept by the writer and broken by the
reader is not a promise.* The response carries counts, a median, a P95 and a slowest; the word is
**installs**, not users, because an install id is tied to nothing.

⚠️ **An unreadable store degrades rather than 500s**, and reports the exception **class** rather than its
message: a Supabase error echoes the URL, and the URL carries the project ref. ⭐ *An error string is a
place secrets go to be logged.*

## Where it sits

⭐ Last in Settings, behind a disclosure, and only above **600pt** — the same threshold the pitch uses for
a tablet. ⚠️⚠️ **Hiding it is tidiness, not security**, and saying which of the two a control is doing
matters: *the day someone mistakes the second for the first is the day a secret goes into a binary.* The
panel is not built until it is opened, so arriving in Settings fetches nothing.

📌 **Not built: the Admin page's "Ask — under evaluation".** That section existed to judge whether
narration was worth a hosted model; Ask is a first-class feature on every surface now (ADR-302), so the
question is answerable from the product rather than from a debug panel.

## What the owner has to do

⚠️ **`FPL_ADMIN_STORE_KEY` must be set on Render** for this to return anything. Until then the endpoint is
a 404 and the panel says so — ⭐ *which is the honest state, not a broken one.*

## Tests

15 service, 11 widget — mutation-tested **9/9** and **8/8**, after the gaps they found. ⚠️ The one worth
naming: `key_matches` returning `True` for an **unset** key survived every test, because `is_enabled()`
404s first and nothing reached the comparison. ⭐ *A security guard that is only correct because a
different guard runs first becomes wrong the day somebody reorders them* — and that one fails **open**.
It is now tested at the function.

---

## The silence reached the wrong person (2026-09-26)

⚠️⚠️⚠️ **The owner typed the right PIN and the screen said "Not found".**

The endpoint is deliberately silent about whether a key is **wrong** or **absent** — that is the point of
the 404, and it is correct. But the client printed the raw detail, so the one word that reached the person
who *has* the key was the one word that helps him least. ⭐ *A refusal designed to teach a stranger nothing
had ended up teaching the owner nothing either.*

⭐⭐ **Fixed on the client, not the server.** One message covers both, so a stranger still learns nothing —
the text is identical for 401 and 404, and a test pins that. What changed is that it names the two things
to check: *"That key was not accepted — or this server has no admin key set. They are separate secrets:
the API reads its own environment, not the web app's."*

⚠️ And a **500 says something else entirely**, because *not every failure is the key* and a server that is
simply down must not send the owner hunting for a secret.

📌 **The underlying cause was configuration, not code**: Streamlit reads `st.secrets`, Render reads its own
environment, and the PIN had only ever been given to the first. `"usage":"ok"` on `/health` already proved
Render had `FPL_STORE_URL` and `FPL_STORE_KEY` — so the two to add are **`FPL_ADMIN_KEY`** and
**`FPL_ADMIN_STORE_KEY`**.
