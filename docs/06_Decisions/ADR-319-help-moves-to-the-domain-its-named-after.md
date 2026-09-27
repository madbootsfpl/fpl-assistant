# ADR-319 — Help moves to the domain it is named after

**Date:** 2026-09-27
**Status:** ✅ **Built.**
**From:** the owner — *"We need to put all our help on MADBOOTS.com, driving users to the streamlit.app is
not the best user experience. Can you create and port the streamlit.app help pages to the MadBoots.com/help
page. Can you keep the videos data driven so I can easily add/replace videos."*

---

## The decision

**`madboots.com/help` is a static page in this repo, generated from the same sources the app answers from,
with the videos fetched at read time from the table the owner already curates.**

Three links in the phone app now point at it. Nothing in `mobile/lib/` says "streamlit" any more.

## Why it was wrong before

⚠️⚠️ **The phone app sent a phone user to a desktop web app to read about the phone app.** Tapping
**More ▸ Help & videos** opened `madboots.streamlit.app/Help` — a page that describes *Streamlit's* screens
(My Squad, FDR, Players), behind a beta access gate, on a host the product is not named after. ⭐ *Every
one of those is a small tax on the one reader who has already admitted they are stuck.*

## What the page is

`scripts/generate_help_page.py` → `site/help.html`, published by `release_web.sh` alongside the landing page.

- **Getting started** — five numbered steps, written for **the Flutter app**, not ported verbatim. ⭐ The
  old text was a faithful description of a different product; porting it would have moved the problem
  rather than fixed it. The numbering is real: you cannot read your week before your team is in.
- **Maddie explains** — see below.
- **FPL rules, in plain English** — all 21 topics, generated from `src.fpl_rules.RULES`, ⭐⭐ *the same
  module Ask answers from, so the page and the assistant cannot tell a reader two different things.*
- **FAQ** — five questions, including where to report something.

## The videos stay rows, not markup

⭐⭐ **The owner adds a clip by editing a row, never by cutting a release.** `site/help.js` reads
`maddie_videos` — `select=topic,blurb,youtube_url,sort_order&published=eq.true&order=sort_order`, the same
query `src/web_streamlit/maddie.py` has always used. Add, replace, reorder or unpublish from the Supabase
dashboard and the page changes on the next load.

⚠️ Baking the list into the generated page would have been simpler to write and would have turned *"add a
clip"* into *"run a deploy"* — ⭐ *the version that is easier to build is the one that quietly becomes the
reason nobody adds another video.* `test_the_clips_are_rows_not_markup` pins this.

Three rendering paths, because the data has three shapes: a parseable YouTube URL becomes an embed, an
unparseable one becomes a **link** (*a clip that will not play should still be reachable*), and an empty
one says **Coming soon** rather than drawing an empty player.

## The key is published, not committed

⚠️⚠️ The publishable key reaches the page from `release_web.sh`'s environment. `site/help-config.js` is
committed **empty**.

The key is safe to publish — `maddie_videos` is `SELECT`-only for `anon`, the same reasoning ADR-216
records for the key compiled into the app binary. ⭐ But *"safe to publish" and "safe to commit" are
different questions, and only one of them has an audit trail.* Without the environment the page renders in
full and the video section says it is not configured — the same fail-soft promise as the Streamlit hub,
which never raised *so the hub always rendered*.

## What did not move

`src/web_streamlit/pages/7_Help.py` **stays.** It is not a duplicate: it explains Streamlit's own screens
to the people looking at them. It gains one line pointing phone users at `madboots.com/help`. The halves
that overlap — the 21 rules — are generated from `fpl_rules` on both surfaces, so they cannot drift.

## The bug this found

⚠️ **`getElementById('videos')` matched the `<h2 id="videos">` anchor, not the list.** Duplicate id: the
heading was the jump-link target and the container wanted the same name. Every clip rendered *inside the
heading* and inherited its italic display face. ⭐ *Invalid HTML does not fail; it picks one for you* — and
it picked the one that made the page look deliberate. Caught by rendering the page and looking at it, which
no assertion in this repo would have done. The list is `#video-list`; the heading keeps the shareable
`#videos`.

## Definition of done

- **Tests** — `tests/test_help_link.py`, rewritten. The old version checked that a matching
  `pages/*.py` existed, because Streamlit derives URLs from filenames; that risk is gone and a new one
  replaces it — ⭐ *the page is generated and nothing makes anyone run the generator*, so the guard
  regenerates and compares, exactly as `test_site_palette.py` does. Six mutants killed: a swallowed
  fetch error, an ignored `sort_order`, a committed key, an unpublished stylesheet, a baked-in clip, a
  one-character typo in the URL.
- **Smoke test** — rendered at 390 px in headless Chrome with a stubbed store, all three video paths
  checked by eye.
- **Docs** — this ADR, the index, the journal.
