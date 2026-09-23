# ADR-254 — Help goes out, feedback stays in

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"is it better/more convenient to route the feedback through madboots.com or
straight from the device? I have no preference."*
**Builds on:** ADR-231 (the relay), ADR-238 (feedback as a destination)

---

## Context

The owner's earlier note suggested *"Tell us something — should maybe link straight back to Madboots.com
and get help, faqs, tell us something, report a bug from there"*, and observed the competitor does exactly
that.

⭐⭐⭐ **They look like one item and they are two jobs.**

## Decision

**Feedback stays in the app. Help goes out.**

**Reporting happens the instant you notice something**, and ⚠️ *every step between noticing and reporting
loses reports.* A tap that opens Safari, loads a page and shows an empty form is several steps — and worse,
**it throws away context the app already has**: the in-app form sends the screen and the build without the
tester typing a word. On a web form they would have to remember and describe both, which is exactly what
people skip, and then the report is half as useful.

⭐ ADR-238 already noticed this about the competitor: *their* help sends you to a desktop, and that loses
the report, not just the convenience.

**Help is the opposite.** It is content — long, searchable, better on a big screen, and the real argument:
**updatable without an App Store release.** Fixing a wrong answer should not need a build.

⚠️ **And it already exists**, which decided the timing. `pages/7_Help.py` has been there since ADR-068 with
both the written walkthrough and Maddie's videos (ADR-166 folded them together). The owner pointed this out
— I had assumed from `~/madboots-site/index.html` being a single landing page that a help section would
have to be built. ⭐ *The site is the front door, not the building.*

So: a **Help & videos** row in More, opening `madboots.streamlit.app/Help`.

⚠️ **The row says where it goes.** Tapping a list item and landing in Safari is a surprise unless it was
announced — *the surprise is the cost, not the browser.* And the link **reports a failure** rather than
doing nothing: a row that silently does not open is worse than one that is not there, because the reader
taps twice, concludes the app is broken, and is right.

## ⚠️⚠️ A link into another app's routing is a promise nothing else keeps

Streamlit derives its URLs from filenames: `pages/7_Help.py` is served at `/Help`. Rename or renumber that
file and the phone's link **404s silently, in a browser, for a tester who concludes the app is broken**.

⭐ *A cross-repo link needs a test on the side that can see both* — so `tests/test_help_link.py` reads the
URL out of `main.dart`, strips it the way Streamlit does, and fails when no page answers to it. It also
checks the page still offers **both** reading and watching, because the row promises both.

## Consequences

📌 **Still owed on the in-app path, and both land with hosting:** a **rate limit** (a form anyone can post
to needs one before it is public) and the relay secret staying server-side, which it already does.

## Verification

* **4 tests**: the linked slug matching a real page; the URL being deployed rather than `localhost` — ⚠️
  *the exact class of bug that kept the whole app on one Mac* (ADR-239); the page still being the Help page
  with both halves; and the row announcing that it leaves the app.
* **3/3 mutations killed**: the link pointing at a page that does not exist; pointing at a dev server; and
  the row dropping the words that say it opens the web.
