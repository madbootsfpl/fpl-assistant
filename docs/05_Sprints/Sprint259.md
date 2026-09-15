# Sprint 259: The hero cut, and the retired mantra two videos already speak

**Dates:** 2026-09-15
**Status:** ✅ Complete — **1782 → 1785 tests, ruff clean.** §1 re-cut to **~1:31**; the 2:27 version kept as
**§1b**. ⚠️ **Two shot videos found speaking a mantra ADR-182 retired.**

> **Owner, on the last unshot script:** *"Is it too long or is that OK?"*

---

## The answer to the question asked

**The timing was honest**: 271 spoken words ÷ Maddie's measured **119 wpm** = 137s of speech in a 147s budget.
Not padded, not optimistic.

**But 2:27 is a tour, not a hero.** Its Research and Leagues beats re-tell what §G Scout, §H Team DNA and §8
Leagues already cover in full — all shot. The hero's job is narrower: *what is it, why trust it, what do I do
next*. Cut to **153 words = 77s of speech, ~1:31 finished**, with every timecode computed rather than
estimated. The long version survives as §1b for a YouTube slot.

## The error that mattered more than the length

The script said *"My Squad opens on the answer"*, then put the pitch after it. **[ADR-175](../06_Decisions/ADR-175-value-above-the-fold.md)
reversed that** — strip and pitch first, answer below a divider.

The interesting part is the history. The 2026-08-31 re-cut *created* that wording, correctly: ADR-171 had just
merged the golden page and led with *This week*, and that re-cut specifically fixed the **opposite** error in
the original draft. So the script has chased this one nav **three times**, and every version was accurate the
day it was written.

⭐ **A script is a snapshot of a UI, and nothing tells it when the UI moves.** The file now carries one
canonical order note in the shared production notes, and each claim names the ADR it rests on — so a changed
ADR is a changed line rather than a surprise on camera.

⚠️ Note the two halves that travelled together and expired separately: *This week* **renders on load** (still
true, 123 ms) and sat **at the top** (false since ADR-175). One sentence, one expiry, and the survivor keeps
the sentence looking current.

## ⚠️ What the sweep found — and this is the real result

Checking the file for stale claims turned up **the previous retired mantra still in two closes**:

| script | close read | status |
|---|---|---|
| **§8 Leagues & Head-to-Head** | *"The analytics decide. Every answer shows its working."* | **already shot** |
| **§H Team DNA** | same | **already shot** |
| the `madboots.com` meta description, as recorded here | *"analytics decide, logic explains, working, you make the call"* | doc wrong, **site correct** |

ADR-182 retired *"shows its working"* on 2026-09-09 and the sweep that day replaced it everywhere else. These
two survived, and were recorded.

**Why they survived a deliberate sweep:** the phrase **wraps**. The file stores it as
`…every answer shows` / `> its working.`, so `grep "shows its working"` returns nothing. ⭐⭐ **A claim that
wraps is invisible to a line-by-line search, and prose always wraps.**

The third row is the inverse risk and worth stating: the **live site was always correct** — verified against
`~/madboots-site/index.html`, not from memory. What was wrong was this file's *record* of it, a half-deleted
splice that someone could have "restored" from.

## The guard

`tests/test_video_scripts.py` — the scripts are the copy a viewer *hears*, and `brand.MANTRA` was guarded in
the app while they were not. It normalises whitespace across each blockquote **block** before searching, so it
sees what the reader sees.

⚠️ **Two fixture faults in the guard itself, both caught by mutation:**

1. The first version filtered ⚠-flagged text **line by line**, and a ⚠ note carries its marker only on line
   one — so it read its own warning text as spoken copy. Now it filters by block.
2. A grep-blind mutation of the joiner appeared to **survive**, because a *second* test (the sign-off check)
   failed on the same input and hid it. ⭐ **When two tests cover one input, a sweep that counts failures
   cannot tell you which test caught the mutant** — the run has to name them.

---

## 💡 The lesson

> **The claim you are sweeping for is the one shaped like prose, and prose wraps.**

ADR-184 already taught that a guard against a claim must *sweep* for the claim rather than check the files you
thought of. This is the next layer: the sweep also has to see the claim the way the reader does. A retired
mantra survived an explicit, deliberate, project-wide replacement — not because anyone forgot a file, but
because a newline landed in the middle of the phrase in two of them.

Every search over human text in this repo now has the same weakness unless it normalises first.

---

## Definition of Done

1. **Tests: 1782 → 1785** — three script guards; four mutants, all confirmed red once the masking was
   separated out.
2. **Manual smoke** — the new §1 read against the running app, beat by beat, and the live site's meta
   description checked against the file's record of it.
3. **Docs** — `Video_Scripts.md` (§1 re-cut, §1b demoted, the order note, §0/§2/§7/§8/§H corrections),
   this retro.
