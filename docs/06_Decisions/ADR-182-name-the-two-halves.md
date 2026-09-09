# Architectural Decision Record: Name the two halves

**Decision ID:** ADR-182
**Date:** 2026-09-09
**Status:** ✅ **Accepted — built** (Sprint 243, 2026-09-09). **1733 tests, ruff clean.**
**Superseded By / Replaces:** **Replaces the mantra [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md)
wrote.** ADR-168's *reasoning* is untouched and reconfirmed below — only its wording is replaced.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner, relaying tester feedback:

> *"Testers are asking what this means. When you explain it it's OK, but that should not be necessary:
> 'the Fantasy Premier League assistant that shows its working.'"*

That is the strongest evidence a line can produce. **Copy that needs a gloss has already failed** — the gloss
is not available at the moment of reading.

#### Three faults, and the third is the one that decides it

**1. It is a British schoolroom idiom.** *"Show your working"* is what a maths teacher writes on homework.
Americans say *"show your work"*. FPL's audience is international.

**2. "Working" is a noun almost nobody uses.** Outside maths, *working* is a verb or an adjective. A reader
has to first realise it is a noun at all before the sentence can mean anything.

**3. ⭐ Spoken aloud, it is a different sentence.**

```
"Every answer shows its working."     ← what we meant
"Every answer shows it's working."    ← what a listener hears
```

**Identical in speech**, and the second parse arrives first because it is the commoner construction. It
claims only that *the app functions* — a minimum, not a differentiator.

This is not a footnote. **The mantra is the spoken close of all ten marketing videos** (§1, §2, §4, §5, §6,
§7, §8, §G, §H, §9). The most distinctive claim in the product was going to be delivered ten times in a form
whose default hearing is banal. **Nothing had been shot except §0, so the cost of fixing it was zero — and
one video's worth an hour from now.**

---

### 🔬 The rejected alternative, tested rather than assumed

The owner asked whether the pre-ADR-168 line could return:

> *"We had: The analytics decide. AI Explains. You make the call. We changed it cos its not really true — you
> could argue that AI explains the data in human readable form? (maybe)"*

**Checked in the code, not from memory. The argument does not hold.**

`explain_captain` is plain Python. Every reason a tester reads is a hand-written string appended by an `if`:

```python
if top.get("penalty_taker"):
    reasons.append(_penalty_reason(...))
if mins is not None and mins >= _START_MINUTES:
    reasons.append(f"Expected ~{round(mins * 90)} mins")
```

There is no model between the data and the sentence. The one place an LLM *could* speak is gated on
`llm.reachable()` — a socket probe that returns False on Cloud, where no Ollama listens — and **Ask itself is
behind `FPL_ADMIN_KEY`**. So **no tester has ever seen AI output from MADBOOTS**, and *"AI explains"* would
be false for 100% of the people watching the video. ADR-168 stands.

⚠️ **And it would be weaker even if it were true.** The hero script's opening line is *"FPL is drowning in hot
takes and **AI that just… guesses**."* Closing on *"AI explains"* would put the product back in the bucket
the hook just climbed out of. **Everyone claims AI. Almost nobody claims you can check it.**

---

### 🎯 Decision & Justification

**The owner's line, and it is better than the one I proposed:**

> **Analytics decide. Logic explains. You make the call.**

I had recommended *"Every answer shows why"* — shorter than the old line and unambiguous, but merely
*describing* the product. His does something better:

⭐ **It names the two halves of the system, in the order they run.** `decision_xp` decides (ADR-041, one
recipe). `explain.py` explains (ADR-089, the Edge · Risk · Confidence block). **Two modules, two jobs, and
the line names them.** It is a description of the architecture rather than a metaphor about it — which is
precisely why it cannot drift from the truth the way both predecessors did.

*"AI explains"* drifted because the AI went away. *"Shows its working"* drifted because it never named
anything concrete. **A line that names real components is falsifiable, and stays true while they exist.**

It also fixes all three faults: no idiom, no rare noun, and no homophone. And it is **tighter** — dropping
*"The"* makes all three beats verb-led and parallel, which reads better as a spoken close.

**"Logic" is the honest word**, and quietly the differentiating one. It implies determinism, repeatability
and the absence of a black box without claiming any of them, in a market where every competitor says *AI*.

**A descriptor ships with it**, for the *"what is this?"* line the testers were actually quoting:

> **The FPL assistant where analytics decide and logic explains.**

#### ⚠️ The one risk, stated rather than waved through

**"Logic explains" leaves its object implied** — explains *what?* That is the same shape of gap that sank the
previous line, so it deserves naming.

It should survive where the old line did not, because **"explains" is a common verb doing ordinary work**
while *"working"* was a rare noun doing metaphorical work: a listener fills in *the pick* automatically. If
testers ask a second time, the minimal repair is **"Logic explains the pick"** — but spending those words
before there is evidence would be paying for a problem twice.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the line survives being spoken, which is how it is delivered ten times; it describes
  the architecture, so it stays true as long as the architecture does; and it is shorter.
* **Negative Impact / Trade-offs:**
  - **§0 is already rendered**, so its opening line *and* its close both speak the retired wording. The
    script and the video now differ, deliberately and visibly.
  - *"Logic"* is a slightly cold word for a mass audience. Accepted: the whole positioning is
    *"Fantasy Football, Calculated."*
* **Risks & Mitigations:**
  - **Risk:** the implied object confuses testers again. **Mitigation:** *"Logic explains the pick"*, held in
    reserve, not spent now.
  - **Risk:** the site's meta description drifts from the app's. **Mitigation:** `brand.DESCRIPTOR` is the
    single definition and the site edit is written out in `Video_Scripts.md`.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`brand.py`), Tests, Marketing docs, the site *(outside the repo)*
* **Action Items:**
  - [x] `brand.MANTRA` rewritten; **`brand.DESCRIPTOR` added** as the one-line *"what is this?"*
  - [x] Guards rewritten to assert the **requirements** — no "working", "explains" present, three beats —
        rather than pinning a sentence that has now changed twice
  - [x] All ten script closes, plus §0's opening line and the two in-prose uses
  - [x] `Homepage_Copy.md`
  - [x] §0 marked: **the script and the rendered video now differ**, with the re-record sequenced after the
        other nine so the UI re-shoot happens once (`Screenshot_Capture_List.md`)
  - [x] The 2026-09-02 deploy record marked **superseded** rather than left reading as current
  - [ ] **Owner: the site edit** — one line in `~/madboots-site/index.html`, then a Cloudflare Pages deploy

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
No surface moves. The **throughline wording** changes everywhere it appears, which the checklist's spirit
covers: `brand.MANTRA` is the single definition in `src/`, and the two documents the guard cannot sweep —
`Video_Scripts.md` and `~/madboots-site/index.html` — are both handled above, the second by the owner.

---

### 💡 The lesson

> **A slogan that describes the architecture cannot drift; a slogan that describes a feeling always will.**

Three mantras in three weeks. *"The AI explains"* died when the AI turned out not to be deployed. *"Shows its
working"* died because it named nothing checkable, so nobody could tell it was vague until a tester said so.
The third names two modules that exist, and will be exactly as true tomorrow.

And the process point: **the tester's confusion was the whole measurement.** *"When you explain it it's OK"*
is not a partial success — it is the failure, stated precisely.

---

### 🔗 References & Related Artifacts
- **Replaces the wording of:** [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md) (whose reasoning stands)
- **Names:** [ADR-041](./ADR-041-one-xp-metric-and-squad-build-intent.md) (decide) ·
  [ADR-089](./ADR-089-explainability.md) (explain)
- **Production impact:** `docs/08_Marketing/Screenshot_Capture_List.md` — §0's re-cut is sequenced last
