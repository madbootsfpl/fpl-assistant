# Sprint 218: Transfer flow, and the manager id that follows you (ADR-162 · US-432)

**Dates:** 2026-08-28
**Status:** ✅ Complete — ADR-162 + US-432. 1537 → 1545 tests, ruff clean.

> **Owner:** *"do the transfer flow one"* · *"when you input your FPL team under My Squad, it should also
> import your leagues. Currently they are separate actions."* · *"both hello@ and info@madboots.com receive
> email."*

---

### 🔧 What shipped

**Transfer flow, split by what it costs.** ADR-141 deferred this with one line — *"one more call per
manager"* — and that estimate was half wrong. `entry_history` sits on every picks payload the page already
fetches, and it carries transfers made, hits taken, points left on the bench and bank. So **how much the
league moved is free**; only **which players** needs the extra call.

The free half is always drawn. The identities ask first and latch on `(league_id, gameweek)` — ADR-141's rule
that nothing costing N calls happens because someone opened a tab, plus the latching lesson from US-431 the
day before. Cached 15 minutes rather than forever: completed picks are immutable, a transfer list is not.

One net-sorted table, not two top-tens — a player with 6 in and 5 out is churning, not popular, and two lists
would have shown him twice while explaining neither.

**At GW1 it says why it is empty**, because nobody has transferred: every squad is still its opening pick.
Probed live to confirm — `/entry/{id}/transfers/` returns `[]` for everyone.

**US-432 — the manager id now follows you.** Importing your team on My Squad persists the id (ADR-147), so
Leagues no longer asks for it again, on this device or any other. Storing it *is* the fix; fetching the
leagues inside My Squad would have put that page inside this one.

**Closed:** `hello@` and `info@madboots.com` both receive email — confirmed by the owner, so the homepage
audit's open question is answered.

---

### 💡 The lesson

> **Before deferring on cost, open the response you are already getting.**

"One more call per manager" was written once, carried forward as settled, and deferred a feature whose most
useful half was sitting unread in a payload the page fetched anyway. The same ADR records the opposite error —
the league table came in **5× below** the estimate that nearly deferred it.

Cost estimates decay in one direction only: toward pessimism nobody re-checks, because being wrong that way
never breaks anything and never announces itself.

And for the second sprint running, a roadmap line bundling two things held two very different pieces of work
(ADR-161 was the first). Worth splitting such lines on sight.

### 🧪 Tests

**+8.** Movers counted separately from transfers; empty-safe including a payload with no `entry_history`; the
season-long list filtered to one gameweek; a churning player appearing once with both counts; ranking by the
size of the move in either direction; an empty gameweek yielding no rows; the page keeping the free half out
from behind the button and the paid half latched; and the manager id persisted on import.
