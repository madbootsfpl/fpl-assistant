# ADR-326 — The document that orients you

*The ADR index at 509 KB and PROJECT_STATUS at 84.5 KB, both loaded before anything is read.*

**Date:** 2026-09-28
**Status:** Accepted
**Completes:** ADR-294/295's principle — *a document that orients you is the one worst placed to be out of date*
**From:** a whole-project health check, whose own commits made this worse before fixing it

---

## Context

ADR-294 named the failure and ADR-295 wrote tests for it. Neither addressed the reason it keeps happening:
**the orienting documents had grown past the point where anyone re-reads them.**

| | was | now |
|---|---|---|
| `ADR-000-index.md` | **509,085** bytes | **91,729** |
| `PROJECT_STATUS.md` | **84,531** bytes | **5,158** |

🔴 **And this session added 18 KB to them before noticing.** Two enormous index rows and a 3,272-character
sprint line — written by me, into the files I had just diagnosed. ⭐⭐ *The habit that produces the problem is
the habit of recording work carefully, which is why it does not feel like a mistake while you are doing it.*

### What was actually in them

**The index** carried the reasoning for each decision in its row: mean 1,526 characters, longest **18,600**.
It was accurate — 321 rows against 322 files — which is why nothing caught it. ⚠️ *An index is a finding aid.
At 509 KB it is the thing you need a finding aid for.*

**`PROJECT_STATUS.md` was 12 lines, and line 10 was 72,767 bytes — 86% of the file.** A `·`-separated log of
**69 sprint entries** that had been appended to a field beginning `Tests: … ADRs: … CI: …`. ⭐⭐ *A running log
appended to a status field stops being a status and becomes an archive nobody retired.*

## Decision

### 1. Index rows become one line; the reasoning stays in the ADR

**209 of 325 rows** rewritten. Not all of them, and the arithmetic is the reason: after 180, the remaining
rows averaged **466 characters against a compressed mean of 331**, with 79 already under 400. Only 29 still
exceeded 700 — one contiguous block, ADR-080 to 111. ⭐ *Compressing a row that is already a one-liner is
churn dressed as progress*, so the last batch was those 29 and then stop.

🔴 **Verify before transform, and it was not ceremony.** **Seven facts existed nowhere but the index** and
would have been deleted: ADR-191's `+2.6`/`+9.3` transfer-cliff measurements and its lesson that *a primitive
can be correct everywhere and still be missing from the one place people read*; ADR-204's `−14.5%` MAE result;
ADR-210's `next_deadline`/`sqlite3.Row` dataclass bug; ADR-282's `12/12` mutations; ADR-322's bump-ordering
note; ADR-190's clean-sheet ρ of `0.981`; and ADR-226's pointer to its guarding test. Each moved into its ADR
under a section naming where it came from.

⭐⭐ **All seven came from the longest rows.** Batches 3 to 6 produced none. *The risk was in the outliers, not
spread evenly* — worth knowing before anyone does this again.

**100 of the 209 summaries were hand-written.** A mechanical first-sentence cut only lands when a row opens
with a short descriptive sentence: 13 of 40 needed hand-writing in the newest batch, 20 of 40 four batches
back. ⚠️ A 230-character cut left nine rows ending mid-sentence, which **reads as a bug rather than a
summary**, so those were rewritten from their ADRs.

⚠️ **ADR-211 was the most interesting row, and I had already compressed it.** Its row stayed **14,598
characters** with a one-line summary at the front, because its **Status cell alone was 14,266** — against a
mean of **53**. An essay in a column that holds a state, and compression preserved statuses verbatim by
design, so it sailed through untouched. Its content was already in the ADR bar one thing: the date its exit
criterion falls due, which the Roadmap carried and the ADR did not. That moved first. The row is 401 now.

### 2. The status file says what is true, and nothing else

The 69-entry log is **closed**, not deleted, into `docs/00_Project/Status_Log_Archive.md` — the
`Feedback_Log.md` precedent (ADR-317's retirement notice). Verbatim; only the line breaks are new, because
one 71,000-character line cannot be read.

The six orienting fields were compressed from **7,604 characters to 1,973**, and the detail they carried is in
the ADRs they cite. ⭐ *A status line that restates its ADR is a second copy of it, and this one was the copy
that goes stale.*

🔴 **Fixing the file found it lying.** The `Web UI:` line described **"7 tabs"** and a *Squads* tab holding
Build and My Squad — a structure **ADR-105 split and ADR-228 superseded**. The app has **nine pages**. That
claim had been wrong for weeks, in the file that orients every session, and no reader had got far enough down
a 2,528-character line to notice. It now lists the nine page names, derived from `src/web_streamlit/pages/`,
and points at the app for what they do: ⭐⭐ *a feature inventory in a status file is a second copy of the app,
and the app is the one that changes.*

### 3. Guarded by size, because prose guards did not hold

`tests/test_orientation_docs_are_current.py` gains a size ceiling per orienting document and per field.
⚠️ **Not a style rule** — the existing tests already check claims against the repo and they all passed while
the file grew to 84.5 KB, because *no individual sentence in it was false*. ⭐⭐⭐ *The failure was never a wrong
claim; it was a document too long to re-read, which is a property of the whole and invisible to any test of
the parts.*

## Consequences

**Good:** the two documents CLAUDE.md loads are 97 KB rather than 594 KB. Nothing was deleted — seven facts
and 69 log entries were relocated and can be found from where they used to be.

**Costs:** the index no longer answers *"why?"* without opening a file. That is the trade, taken on purpose:
one click against a table nobody could read.

⚠️ **Open:** `docs/04_Roadmap/Roadmap.md` is still **105 KB** and is the third orienting document. It is a
forward plan rather than a log, so it did not get the same treatment — but it grew 5 KB this session too, and
the ceiling added here does not yet cover it at its current size.
