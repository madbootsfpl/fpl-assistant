# ADR-311 — The name was three layers deep

**Date:** 2026-09-27
**Status:** ✅ **Built.** `AskRequest.squad_name`, the scope label, the pitch header, Settings.
**From:** the owner's list — *"can we incorporate the team name on the current game week, and maybe show
it in settings too"* and *"Ask also responds with (squad 'yours') rather than the team name."*

---

## The decision

**The team's own name travels with the question, and every answer says it.** *"Captain pick (The 4-4-2
Towers)"*, not *"Captain pick (squad 'yours')"*.

## ⭐⭐⭐ Nothing needed fetching

The name was never missing. It was **three layers deep and displayed nowhere**:

| layer | what it already did |
|---|---|
| FPL | returns it as `entry["name"]` |
| `src/manager.py` | reads it — *"Imported **The 4-4-2 Towers** — GW5 squad."* |
| `my_team` | returns it as `squad.name` |
| `mobile/lib/api/models.dart` | **parses it into `MyTeam.squadName`** |
| everywhere else | ignored it |

⚠️⚠️ `MyTeam.squadName` was parsed, stored, and carried through `withArmbands` — and referenced by **no
other line in the app**. Meanwhile `ask_question` hard-coded `"name": "yours"`, because `AskRequest` had no
field to carry one.

⭐ *The API knew the name and the answer did not.* 📌 That is the **fourth** capability this month that
turned out to be built and merely unreachable (the swipe, Chatter, `converse()`'s follow-ups, and now
this) — ⭐⭐ **worth a habit: before building, check whether the thing already exists one layer away.**

## Two changes, not one

**1 — a field.** `AskRequest.squad_name`, optional and capped at 60 characters. Optional because the engine
names the scope in *every* headline, so a caller that sends none must still get a sentence that reads — it
falls back to `"yours"`. Capped because it is **printed verbatim into a headline**: ⚠️ *a label the caller
chooses is a label the caller could make ten thousand characters long.* FPL's own limit is 20.

**2 — the wrapper goes.** Passing the real name through the old format produced *"Captain pick (squad 'The
4-4-2 Towers')"* — a stutter. ⭐⭐ The `squad '…'` wrapper existed to make a **placeholder** sound like a
label; it is *scaffolding for a stand-in, kept after the real thing arrived.* Now `scope_label()`, one
function behind five call sites in `ask.py` plus three detail renderers in `src/ui/`, and a name is just a
name — saved squads on the web read the same way, *"(Demo XI)"*.

⚠️ One place keeps its quotes: `ui/captain.py`'s *"no such squad 'X'"* error, where quoting what the user
typed is the entire point.

## Where it shows

- **The live gameweek** — a compact line above `GW5`. ⚠️⚠️ **Portrait only, and a test made me prove it:**
  the line costs ~16pt and in landscape `pitch_layout_test`'s *"the bench never outgrows the eleven"* went
  from **15 to 4**. ⭐ ADR-253 already found this header to be the screen's most expensive space, and
  landscape is where it is most expensive. 📌 Live page only for the same reason — *identity belongs where
  you land, not on every page you swipe past.*
- **Settings**, under *"FPL manager id"*. ⭐ *An id on its own is only verifiable by pasting it somewhere
  else.*

## Verification, and a test that was asking the wrong question

Python: the full suite, plus the phrasing change rippling into **six** assertions across five files — each
of which was asserting `squad 'X'` when its actual claim was *scoped, not global*. ⭐ The updates say the
name and nothing about the format.

Dart: **458 tests**, six new. ⚠️⚠️ The first version of the pitch tests sized a `SizedBox` and every case
reported **landscape**, because `MediaQuery.orientationOf` reads **the window** and the harness's default
surface is 800×600. ⭐⭐ *A test that sizes the widget instead of the screen is testing a different question
than the one the code asks* — they set `tester.view.physicalSize` now.

## Consequences

- ⭐ **No new data, no new call.** One optional request field and a label function.
- 📌 An older client that sends no `squad_name` still reads correctly — the fallback is the old word.
- 📌 The web/Streamlit surfaces get the same phrasing, since `scope_label` is shared.
