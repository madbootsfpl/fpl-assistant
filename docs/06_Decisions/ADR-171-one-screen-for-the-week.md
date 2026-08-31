# Architectural Decision Record: One screen for the week — and the number that unblocked it

**Decision ID:** ADR-171
**Date:** 2026-08-31
**Status:** ✅ **Accepted — owner signed off the two design calls (answer-first · captaincy inline) from a
real-data preview, then "ship it as drawn"** (Sprint 231, 2026-08-31). **1589 → 1642 tests, ruff clean.**
Closes **US-435**, the last open item of the 17-item UX review (US-433-449).
**Superseded By / Replaces:** Corrects the *measurement* behind ADR-166's tab order (not its reasoning).
Holds ADR-135's revert — this adds no gesture and no round-trip. Keeps ADR-165's fragment boundary and
ADR-168's degrade-without-Ollama contract. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"Merge My Squad, AI/Chips and Captain into one screen under the My Squad sub-tab — most of what's needed
> for an informed decision is then on the golden page."* — US-435, 2026-08-28

The item sat open for three days with a note saying it *needed a gate*, because ADR-166 had already refused
the closely-related move. It declined to make **AI Tips** the default tab on a measurement:

> `ask.answer` takes **4.4 s**, so every visit would have paid it before the page showed anything. […]
> Merging chips in eagerly cost another **6.6 s** — an **11-second landing** on the default tab.

An 11-second landing is a good reason not to merge. So the gate came down to one question: **is that number
true on the surface users actually use?**

---

### 🔬 What the measurement found — the number was right, and measured on the wrong machine

Re-measured 2026-08-31 on real data (`data/squads.json`, squad 'TS', 626 players), because ADR-157's lesson is
that a remembered number must be re-run before it justifies work. Streamlit Cloud has **no Ollama** (ADR-168),
so every deployed user takes the degrade path; the dev machine has Ollama, so it does not.

| view | what it computes | **Cloud (no Ollama)** | this machine (qwen3:8b, warm) |
|---|---|---|---|
| My Squad | `decision_xp` over the whole pool, horizon 1 / 5 | **5 / 7 ms** | same |
| Captain | `captain_picks` + `explain_captain` | **<1 ms** | same |
| **AI Tips** | `ask.answer("what should I do this week")` | **123 ms** | **27,300 ms** |
| **Chips** | `ask.answer("which chip")` | **99 ms** | **65,000-86,000 ms** |

Two findings, and the second is the more uncomfortable one.

**1. On Cloud the merged page costs ~230 ms.** The barrier ADR-166 erected does not exist where the users are.
The whole of AI Tips — Edge/Risk/Confidence, the captain pick with its reasoning, the lineup tweak, the
transfer with its gain, the flags — is analytics, and analytics are milliseconds. Only the **prose paragraph**
comes from the LLM, which is exactly what ADR-168 already established is *"the entire difference between local
and Cloud"*. Verified by rendering the degraded output in full, not by assuming it.

**2. Locally it is 6-13× worse than ADR-166 recorded**, and that is a real regression nobody was watching.
`llm.extract` sets `"think": False`; `llm.narrate` does not — so under `qwen3:8b` every narration pays a
thinking pass first. ADR-166's 4.4 s and ADR-168's 4.1 s were taken before that model, and no test could catch
the drift because **CI has no Ollama** (ADR-168 §🔬 found the same blind spot from the other side).

**The general lesson, and it is the reason this ADR exists rather than a one-line tab change:** *a performance
number is only a fact about the machine that produced it.* ADR-166 measured honestly and reasoned correctly
from what it measured; the environment was the unstated variable. **A latency measurement that will be used to
decide a user-facing default must name the environment it was taken in, or it silently becomes a claim about
the developer's laptop.**

---

### ✅ Decision

**1. One rule replaces the per-tab guess.**

> **Render the answer eagerly when it is cheap; put it behind a button when a narrator is attached.**

Decided by a `llm.reachable()` probe — a connect attempt with a tight timeout that returns instantly either
way (refused on Cloud, connected locally) and is cached for the session. Not a hardcoded assumption about
which tab is slow, which is precisely the assumption that went stale.

**2. The sub-tabs go 7 → 5:** `My Squad · Transfer · DNA · Leagues · Lab`.
**AI Tips** and **Captain** stop being destinations and become sections of the golden page. **Transfer**
stays its own tab — US-435 does not ask for it, and it is the one view that is genuinely a different task.

**3. The order — answer-first (owner's call).**

| # | section | why it sits there |
|---|---|---|
| 1 | Team banner · legality · deadline | unchanged chrome |
| 2 | **This week** — the AI Tips block | it is *the answer*, and it now costs 123 ms. ADR-166 put it second on the 4.4 s number alone; with the number corrected the argument goes with it |
| 3 | The xP strip + per-GW toggle | the totals the pitch is about |
| 4 | The pitch + ⚙ Players & lineup | unchanged — this is what the page *is* |
| 5 | **Captaincy** — the ranked 15 + the grounded Why/Risk/Confidence card | **inline, not an expander** (owner's call): an expander is a tab switch wearing a different hat |
| 6 | **Chips** — behind a button | kept a button on **both** paths, and not for latency: a chip is a season decision on a different clock (ADR-166), so it should not fire because someone opened a page |

**4. Captain becomes settable in one place.** It is currently settable in **three** — the ⚙ panel's
`👑 Make X captain`, the Captain tab's selectbox-and-button, and AI Tips recommending one. The merge would put
all three on one screen, where the duplication stops being invisible and starts being a defect. The ⚙ panel's
button survives (it is ADR-135's surviving shape, and it is where the selection already lives); the Captain
tab's setter goes. The ranked table and the grounded card — the half that is actually unique — stay.

---

### 📏 How this gets judged

**Not by widget count.** That is ADR-135's trap: its target was hit *exactly* and the result was worse. The
criteria here are the two things that can actually go wrong:

| | bar | result |
|---|---|---|
| Cloud landing cost | the merged page computes in **< 500 ms** | ✅ **191-195 ms** for the whole screen — answer, pitch, captaincy table and chips button — measured on the real page, steady over repeats |
| Local landing cost | **unchanged** — no narration fires on load while Ollama is reachable | ✅ **121 ms**; the week sits behind `Work out my week →` |
| Captain setters on the page | **1** (from 3) | ✅ pinned by `test_the_squad_has_exactly_one_captain_setter` |
| Scroll length on iPhone | owner's eyes, from a real-data preview | ✅ reviewed and signed off — *"ship it as drawn"* |

*(A note on the first row: the very first page render costs **~4.4 s**, and all of it is Python imports and
Streamlit boot — a one-time process cost, not per-visit. Timing a cold start and quoting it as a landing time
is exactly the error this ADR was written about, so it is named here rather than averaged in.)*

---

### 🔀 Alternatives Considered

- **Leave it; the tabs work.** Rejected: it is the owner's own item, and the only argument against it turned
  out to be an artefact of the dev machine.
- **Merge Transfer in too.** Rejected: not asked for, and it is a genuinely separate task with its own long
  output. The golden page is "what do I do this week", not "everything".
- **Keep AI Tips behind a button on Cloud as well, for consistency.** Rejected: it would cost a click to save
  123 ms, which is charging the user for a problem they do not have.
- **Make the eager/button choice a config flag.** Rejected: a flag is a guess someone has to remember to
  update. The probe answers the question at the moment it is asked.
- **Fix `narrate`'s missing `"think": False` here.** Deferred — it is a real find and it is *not* this change.
  Logged as a follow-up so a page-layout ADR does not quietly become an LLM-tuning ADR.

---

### 🧭 Consequences

**Positive** — closes the last open UX-review item; two fewer tab switches to answer the week's question; the
golden page finally contains the decision *and* the pitch it is about; three captain setters become one; the
eager/button rule is now measured rather than assumed, so it cannot go stale the same way twice.

**Negative / risks (mitigations)** — the page gets longer on mobile (*mitigation:* the merged sections are two
text blocks and one table, not widgets, and the owner reviews a real-data preview **before** code); a Cloud
user now pays 123 ms on every My Squad load that they previously paid only on the AI Tips tab (*mitigation:*
inside a render already costing ~230 ms, and it buys the answer); the `llm.reachable()` probe is one more thing
that can be wrong (*mitigation:* it fails **towards the button**, so a wrong answer costs a click, never a
27-second landing); ADR-166's tab order is partly undone within days (*mitigation:* its *reasoning* is upheld —
order by how often you need it — only its input number was environment-bound, and that is recorded above).

---

### 🧾 Follow-ups

- **`llm.narrate` never sets `"think": False`** while `llm.extract` does — under `qwen3:8b` that is the bulk of
  the 27 s. Own ADR: narration and extraction were deliberately split (ADR-151/157), so re-joining a setting
  across them is a decision, not a tidy-up.
- **A latency number must record its environment.** The two stale numbers here (4.4 s, 4.1 s) were both written
  down carefully and both became wrong silently. Any future perf figure in an ADR names the machine and whether
  Ollama was up.
- **The ADR index is 48 entries stale** — `ADR-000-index.md` stops at 122 while 170 ADRs exist. Found while
  filing this one; a separate backfill, flagged rather than silently half-fixed.


---

### 🔬 What building it found — three things no unit test was looking for

**1. The eager decision was a prediction, and predictions can be contradicted.** The smoke test drove the real
page on both paths and the "Cloud" path landed in **49 seconds**. `narrator_attached()` was choosing the
*layout* while `ask.answer` independently reached for whatever model was installed — so on a machine the probe
misjudged, the page would render eagerly **and** narrate, producing the exact outcome this ADR exists to
prevent. The fix makes the decision **binding**: having judged the answer cheap, `render_this_week` passes
`narrator=None`, so the two halves can no longer disagree. Landing went 49,007 ms → 195 ms.

*This is why the Definition of Done has three parts.* 1,642 unit tests were green across both paths the whole
time, because every one of them runs under `conftest`'s model stub — the state where the bug is invisible by
construction. Only running the thing found it.

**2. A renamed tab silently disabled two tests, and they stayed green.** Streamlit's `set_value()` accepts an
option that does not exist and **keeps the current selection** rather than raising. ADR-166 renamed
*Health* → *DNA*; two tests kept asking for `"Health"` and have since been asserting against the **default
tab**, not the one they name. `_squads_view` now checks the switch actually landed, so a stale tab name fails
loudly. The same class as ADR-168's *"CI has never exercised the narrated path"* — **coverage that leaves
without the suite going red is the expensive kind.**

**3. `test_my_squad_pitch_view_lays_out_the_squad` asserted `len(dataframe) == 0`.** Correct when the pitch was
the whole page; wrong once captaincy joined it. Rewritten to pin what US-187 actually cared about — *the squad
is a pitch, not a table* — by asserting the one table present is the captain candidates. A test that breaks on
a legitimate change was testing the implementation, not the intent.

**Every new guard was mutation-checked** — the behaviour was reverted one at a time and each test was confirmed
red, then green again. Twice before in this project a test passed only because the workaround had been written
into it; a guard nobody has seen fail is a guard nobody should trust.
