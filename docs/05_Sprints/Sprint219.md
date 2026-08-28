# Sprint 219: The stuck player card, and a Home page that can't rot again (US-444 · US-433)

**Dates:** 2026-08-28
**Status:** ✅ Complete. 1545 → 1549 tests, ruff clean.

> **Owner (UX review, 17 items):** *"Clicking on a player shows the condensed player profile, however you
> cannot release it unless you leave the page and return."* · *"Home page needs updating to reflect latest
> changes."*

The two items from the batch that needed no design decision. The other fifteen are logged as US-434…US-449 and
cluster into IA, one squad lens, component standardisation, and one product question about Ask.

---

### 🔧 What shipped

**US-444 — a tap now undoes itself.** Tapping a shirt selected a player and there was no way back: the picker
beside it *could* clear the selection (its first option is `—`) but nobody opens a dropdown to undo a tap.
`_write_selection` makes a second tap on the same thing clear it. The caption says so, because an affordance
nobody can discover isn't one.

Surfaces without a "nothing selected" option — the Team DNA scan's picker — pass `none_label=None` and keep
re-selecting, rather than being handed a state their dropdown cannot display.

**US-433 — Home fixed, and guarded.** It still listed **Fixtures** and **News** after ADR-134 and ADR-149
renamed them, and never mentioned 🏆 Leagues, which had been live for days. Fixing the words would leave the
next rename to somebody's memory, so the list is now **derived from `pages/` by a test**.

---

### 🐛 Two things found while doing it

**A test was holding the stale name in place.** `test_home_hero_box_consolidates_cta_and_nudges` asserted
`"📅 **Fixtures**" in blob` — so *correcting* Home broke the suite. A test pinning outdated copy is worse than
no test: it turns silent rot into an active obstacle.

**And my first guard couldn't fail.** It searched the whole file for each page name, so deleting the Leagues
bullet still passed — the word survives in the docstring and in another sentence. Caught by deliberately
breaking it, then narrowed to match the tour's bullets only, and re-broken to confirm it now fails.

**A third test had a shelf life.** `test_squads_gameweeks_selector_drives_the_horizon` asserted a literal
`GW2` column, which stopped being true **during this session** — GW2's deadline passed, and ADR-123 cuts
upcoming fixtures at the deadline, so the horizon rolled to GW3. It expired on the calendar rather than on a
code change. Now derives the gameweek numbers from the same data the page reads.

---

### 💡 The lesson

> **A test that pins copy can be the reason the copy is wrong.**

Three tests in one sprint were assertions about how things *were* rather than what the feature *promises*: one
pinned a renamed page, one couldn't fail at all, one expired on a date. All three passed happily while the
thing they guarded drifted.

The distinction worth keeping: assert the **contract** (every page appears in the tour; the horizon narrows to
the selected number of gameweeks), never the **instance** (the third bullet says "Fixtures"; the column says
"GW2"). The first survives the app changing around it, which is the only reason to have it.

### 🧪 Tests

**+4, and three repaired.** Tapping the selected shirt clears it; tapping a different one moves the selection;
a surface with no `—` option never writes one; and the Home tour lists every page in `pages/` (Admin excluded
— owner-only, and advertising it would be a UX bug). Repaired: the hero-box test that pinned *Fixtures*, the
horizon test that pinned *GW2*, and the guard that couldn't fail.
