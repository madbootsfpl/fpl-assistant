# Sprint 226: Leagues joins the squad — sidebar 12 → 9 (ADR-166)

**Dates:** 2026-08-29
**Status:** ✅ Complete — ADR-166. 1569 tests, ruff clean.

> **Owner:** *"Leagues is tightly associated with your squad, so let's do that along with your other
> suggestions and let's see where we land."*

---

### 🔧 Where we landed

```
Home · Players · Team DNA & FDR · My Squad · Ask · Signals · Trending · Help · Feedback   (+ Admin)
My Squad ▸  My Squad · AI Tips · Transfer · Captain · DNA · Leagues · Lab
```

**Nine pages, from twelve** — and not one of them by pushing crowding into Players, which the code's own
comment forbids (*"TEN IS THE CEILING… the next view needs a merge first, not another label"*).

---

### 🐛 Moving a page into a module changes its semantics

This was the real work, and none of it is visible in a diff.

**`st.stop()` halts the entire script.** Nine of them guarded the Leagues page; as a page that meant "stop
drawing Leagues", but inside a tab it would have meant "stop drawing My Squad" — every guard clause silently
truncating its host. They are guard clauses, so `return` is exact.

**An unkeyed widget is identified positionally.** The Tool switch had no `key`, so a tab that adds widgets —
Leagues adds a dozen — could shift its identity and reset the selection. A real product bug, exposed rather
than caused.

**`from src.api.client import FplClient` binds once in a module.** A page is re-imported every run, so the
name re-binds and a test can swap it. A view module is imported once and keeps whatever was installed the
first time — in practice, the first test's fake, for the rest of the session. That one cost the most time:
the symptom was a league called *"Test League"* appearing in a test that had never heard of it.

---

### 💡 The lesson

> **Moving code between a page and a module changes its semantics, not just its location.**

Three separate mechanisms — script halting, widget identity, import binding — all behave differently in a
re-imported script than in an imported-once module. A diff shows an indent change and a `return`.

And the one worth keeping from the whole cluster: **a count is a symptom; frequency is the cause.** "Reduce
to 10" was satisfiable in an afternoon by making two other pages worse. Ordering by how often each page is
actually needed produced nine, with a reason behind every move.

### 🧪 Tests

1569 green. No new behaviour tests for the moves; **~20 existing tests were rewritten to address widgets by
label rather than by index** — the assumption that quietly breaks every time a page grows.
