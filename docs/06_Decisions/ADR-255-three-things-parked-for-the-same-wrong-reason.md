# ADR-255 — Three things parked for the same wrong reason

**Date:** 2026-09-23
**Status:** Accepted
**Covers:** player photos · the signals pitch badge · the *"Add filter"* dropdown
**Builds on:** ADR-084 (the kit, not the mugshot), ADR-232 (the device remembers), ADR-238 (filters)

---

## Context

Three items had sat on the owed list, and two of them for the same reason: *"that would need another round
trip."* Neither did.

## 1. Player photos — ADR-084 was right, and narrowly

`photo_url` lived in `web_streamlit/badges.py`, which imports Streamlit, so the API could not reach it. It
moved to `kits.py` beside `shirt_url`, **verbatim**, and the web re-exports. ⚠️ *The shirt template lost
its `-66` in a move like this one and every kit on the pitch broke* — there is a test asserting the web's
name is the **same object**.

⭐ Keyed by **`code`, never `id`**: code is stable across seasons and the id restarts every August
(ADR-201), so a photo built from an id would point at whoever inherited the number — *and it would look
entirely fine.*

⚠️⚠️ **On the named cards, and still not on the pitch.** ADR-084 chose the kit there on purpose: FPL's
photo CDN lags a transfer by weeks while the kit graphic updates instantly, so a just-transferred player
would sit on the pitch wearing his old club's face. ⭐ *On a card his name is beside him and the staleness
is a curiosity; on the pitch it is the app being visibly wrong about your team.* There is a test that the
pitch payload carries no photo.

⭐ A missing photo degrades to **initials**, not a broken-image glyph. *A placeholder that looks deliberate
reads as "no photo"; one that looks broken reads as "this app is broken".*

## 2. The signals badge — the round trip was imagined

ADR-228 wanted a badge and parked it on the assumption it cost a fetch. **Measured: a squad sweep is
~50ms**, so `my-team` carries it.

⭐⭐⭐ **It sends the keys, not the signals.** The badge is a count, and a count does not need the things it
counted — sending them would put a full sweep's worth of player summaries on the screen that has to be
fastest.

⭐⭐ **And the server never says what is *new*.** It cannot: it has no idea when you last looked. It says
what **exists**; the device compares against its own memory. That is ADR-232's split reused rather than a
second mechanism invented — and there is a test asserting the service has **no** `unseen` or `new_count`
field, because such a field would be a guess.

⚠️ The keys must be **the same keys** the Signals screen marks as seen. Two generators for one identity is
a badge that lies forever and never errors; a test compares both.

⭐ The badge clears on the way back from Signals. *A badge that survives the thing it pointed at is a badge
nobody trusts twice.*

## 3. "Add filter" — disclosure, not a tax

The row now shows the filters **in play**, plus a `+ Filter` button. ⚠️ Position and price stay visible:
they were already there and already used, and *hiding a filter people reach for is not disclosure, it is a
tax.*

⭐ Tapping a filter chip **removes** it — a separate ✕ would be a second control for one idea, and at this
size a target nobody hits. The button disappears when everything is on: *a button that can only disappoint
should disappear.* Clubs come from the board, so a promoted side appears without a release.

## Verification

* **7 tests**, including the code-versus-id distinction asserted by showing the two produce **different**
  URLs for the fixture player, and the absence of any server-side claim about what a reader has seen.
* **6/6 mutations killed**: the photo keyed by id; a missing code producing a URL anyway; a mugshot
  reaching the pitch payload; the badge's keys built differently from the screen's; the service claiming
  to know what is unseen; and the web redefining `photo_url` rather than re-exporting it.
