# ADR-353 — Published while the match was still news

**Date:** 2026-10-17
**Status:** Accepted
**Closes:** the item ADR-352 deferred ("the date window is the real discriminator")
**Extends:** ADR-347 (highlights, matched by the one thing that can verify them)

---

## Context

ADR-347 matches a video to a fixture on **both clubs and both goal counts**, and claims the failure mode
is *"a missing link, never a wrong one."* ADR-352 found the case that claim cannot cover: an **archive**
upload of an old match carries a real scoreline between two real clubs, so it parses, passes the score
check, and says *highlights*. It was excluded by its title — `classic highlights` — which worked only
because Forest brand their archive series that way.

⚠️ Two more hazards were left standing, both visible in the live feeds: **Fulham's women's results** and
**Chelsea's academy games** parse to real scorelines between real clubs, and today only the opponent's
name keeps them out.

## ⭐⭐ The discriminator a title cannot fake

A highlights package is published **while the match is still news**. An archive upload is not, whatever
it is captioned.

`parse_feed` has always returned `{title, link, published}` and `videos()` **dropped the date on the
floor** — which is why this check could not be written before. The fix is mostly deletion.

## The window is measured, not chosen

Every feed entry matching any of **30 finished fixtures** (GW4–GW6), by hours from kick-off to upload:

| | |
|---|---|
| fastest genuine package | **+4.2h** — *Coventry City 4-1 Newcastle United \| Premier League Highlights* |
| the one that had to be cleared by hand | **+9.5h** — *Arsenal 2-1 Leeds United \| Premier League highlights* |
| slowest genuine package | **+34.0h** — *Crystal Palace 3-1 Nottingham Forest \| … \| Extended Highlights* |
| not a package at all | **+53.0h** — *DUGOUT CAM 🎥* |
| published **before** kick-off | **none, ever** |

**Decision: `0 ≤ upload − kickoff ≤ 72h`.** Better than twice the slowest observed package, and the same
span as the re-check window in `fixtures_wanting_highlights` — ⭐ *the two mean the same thing, which is
how long a match is still news.*

## ⚠️⚠️ Unknown is permitted, deliberately

A feed without dates, a fixture without a kick-off, or a stamp this cannot read all **pass** the window.
⭐ *A guard that turns missing data into missing links is worse than the hazard it closes* — the module
degrades to exactly the behaviour that shipped before, rather than going silent.

📌 That is also why ADR-352's `classic highlights` guard **stays**: it is now the net for the no-date
case, which is the only case the window cannot judge. It was not retired, it was narrowed in purpose.

⭐ Both RSS (RFC-822) and Atom (ISO-8601) stamps are read, because `parse_feed` serves both and hands back
whichever the feed used. ⚠️ *A reader that assumed ISO would fail silently — as permitting everything —
the day YouTube changed.*

## Consequences

✅ **Checked against the live feeds before committing to it**: across the same 30 fixtures, the window
changes **nothing** — all 13 resolvable links are byte-identical with and without it. It closes a hazard
at no cost to what already works.

✅ An archive upload is now rejected **however it is captioned**, which the title guard never managed.

🔴 **The check was nearly wired to nothing.** `match_fixture` took the kick-off and `fill` did not pass it,
so every test written *about the window* passed while the pipeline ignored it. ⭐ *A guard reached by no
caller is tested only by tests that call it directly*, which are exactly the ones that cannot notice.
The mutation removing the argument from `fill` is now caught by an end-to-end test.

📌 Still open, and narrowed rather than closed: a women's or academy fixture whose score **and** date both
coincide with the men's match. The window makes it far rarer; only the competition would settle it, and
no club puts that in a title reliably.
