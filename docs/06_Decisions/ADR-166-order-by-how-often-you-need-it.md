# Architectural Decision Record: Order the app by how often you need it

**Decision ID:** ADR-166
**Date:** 2026-08-29
**Status:** ✅ **Accepted — designed with the owner in conversation, built** (Sprints 225-226, 2026-08-29).
**1569 tests, ruff clean. Sidebar 12 → 9 pages.**
**Superseded By / Replaces:** Partly reverses **ADR-105** (the My Squad / Squad Lab split) and moves ADR-141's
Leagues page. Delivers US-434 · 436 · 437 · 440 · 445 · 448 from the 2026-08-28 UX review.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Seven items of the review were one question: **what belongs on the sidebar, and what belongs inside a page?**
The sidebar was 12 pages, ordered by *the order things were built* — so **Squad Lab sat first**, above Players
and My Squad, despite being used a handful of times a season.

The owner asked to *"reduce to 10 if possible"*. **That target was the trap**, and naming it was the most
useful part of the conversation: doing every move the review proposed gives sidebar 12 → 9 ✅, My Squad
6 → 9 sub-tabs, and Players 10 → 11 — **against a ceiling written in the code itself**:

> ⚠️ TEN IS THE CEILING… The next view this page gains needs a **merge** first, not another label.

The number improves by pushing the crowding down a level. That is ADR-135 exactly: hit the target, worsen the
thing. So the ordering principle came from the owner's own words on a different item — *"you will only use
the lab a few times a season"* — and the count was allowed to fall out of it rather than drive it.

---

### ✅ Decision — order by frequency, and let the number follow

**Squad Lab → My Squad ▸ Lab.** A builder for season start, wildcards and free hits had the top sidebar slot.
It keeps its own **5-GW horizon** via a per-mode widget key: folding two pages together must not fold their
horizons together.

**Leagues → My Squad ▸ Leagues.** The owner: *"Leagues is tightly associated with your squad."* It is — every
number there measures *your* picks against other people's.

**Maddie Explains → Help ▸ Watch.** Both answer *"how does this app work?"*; text-versus-video is a
preference, not a topic.

**Chips → AI Tips**, and **Health → DNA**, leading with the fingerprint rather than a 15-row table.
**FDR finally has a heading** (US-440) — the page said *"Team DNA & FDR"* and only ever announced the first half.

**Chips now look to the chip deadline, not the tab's horizon.** This is the substantive half of US-434. A chip
expires at the end of each half-season (`fpl_rules.chip_deadline` → GW19/GW38), so *"which week should I play
this?"* only means anything across the weeks that remain. The tab defaulted to **one gameweek** — which asked
whether *this* week is good and could never answer *which* week is. Today that is **17 gameweeks instead of 1**.

**Not done: Trending → Players** (US-438), held at the owner's request pending a separate idea — and blocked
anyway by the ten-view ceiling.

### 🐛 Four things measurement caught, two of them my own proposals

1. **AI Tips as the default tab was wrong.** It is the *answer*, so leading with it was the obvious call —
   `ask.answer` takes **4.4 s**, so every visit would have paid it before the page showed anything. The pitch
   is default again; the answer is one tap away, the same distance as before.
2. **Merging chips in eagerly cost another 6.6 s** — an **11-second landing** on the default tab. They are
   behind a button now, per ADR-141: nothing expensive happens because someone opened a tab. **The first sign
   was the test suite going from 60 s to 600 s**, which was very nearly dismissed as test churn.
3. **The Tool switch had no `key`.** Streamlit identifies an unkeyed widget positionally, so a tab that adds
   widgets — Leagues adds a dozen — can shift its identity and silently reset the selection. A real product
   bug, exposed by the move rather than caused by it.
4. **`from src.api.client import FplClient` behaves differently in a view module.** A *page* is re-imported
   every run, so the name re-binds and a test can swap it; a *view module* is imported **once** and keeps
   whatever was installed the first time — in practice the first test's fake, for the whole session. Now
   reached as `_client.FplClient()`, resolved per call.

**The nine `st.stop()` calls became `return`s**, which was the whole risk of moving Leagues: `st.stop()` halts
the *entire script*, so as a page it meant "stop drawing Leagues" and inside a tab it would have meant "stop
drawing My Squad" — every guard clause silently truncating its host.

### 🧪 Definition of Done

1. **1569 tests green**, ruff clean. No new behaviour tests were needed for the moves themselves; ~20 existing
   tests were rewritten to address widgets **by label rather than by index**, which is the assumption that
   broke as pages grew.
2. **Manual smoke** — every tab renders; sidebar is 9 pages.
3. **Docs** — this ADR, the feedback log, Home's tour, the Feedback page-picker, PROJECT_STATUS, a retro.

---

### 💡 The lesson

**A count is a symptom; frequency is the cause.** *"Reduce to 10"* could have been satisfied in an afternoon
by moving three things and making two other pages worse. Ordering by how often each page is genuinely needed
produced **nine** — and every move had a reason a user would recognise, which a count never gives you.

The second lesson is narrower and cost the most time here: **moving code between a page and a module changes
its semantics, not just its location.** `st.stop()`, unkeyed widgets and `from x import y` all behave
differently in a re-imported script than in an imported-once module. None of that is visible in a diff.
