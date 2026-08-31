# Sprint 231: One screen for the week (ADR-171)

**Dates:** 2026-08-31
**Status:** ✅ Complete — ADR-171. 1589 → 1642 tests, ruff clean. Closes **US-435**, the last open item of the
17-item UX review (US-433-449).

> **Owner:** *"Merge My Squad, AI/Chips and Captain into one screen under the My Squad sub-tab — most of what's
> needed for an informed decision is then on the golden page."*

---

### 🔧 What shipped

The golden page now carries the whole week, in the order it is decided: **① the answer** · the pitch and ⚙
panel it is about · **② captaincy inline** · **③ chips behind a button**. Sub-tabs went **7 → 5** (My Squad ·
Transfer · DNA · Leagues · Lab). Transfer stayed its own tab deliberately — it is the one view here that is a
genuinely different task, and US-435 did not ask for it.

Captain had become settable in **three** places — the ⚙ panel's *👑 Make X captain*, the Captain tab's
selectbox-and-button, and AI Tips recommending one. On separate tabs that was invisible; on one screen it is a
defect. The ⚙ panel's button survives; the ranked 15 and the grounded card — the genuinely unique half — moved
across intact.

---

### 🔬 The finding that unblocked it

US-435 had sat gated for three days because ADR-166 had already refused the neighbouring move on a
measurement: `ask.answer` cost **4.4 s**, so leading with it meant an 11-second landing. Re-measured before
proposing anything, per the ADR-157 lesson:

| | Cloud — no Ollama | dev machine — qwen3:8b warm |
|---|---|---|
| This week (`ask.answer`) | **123 ms** | **27,300 ms** |
| Chips (`ask.answer`) | **99 ms** | **65,000-86,000 ms** |

**The number was right and it was measured on the wrong machine.** Streamlit Cloud has no Ollama, so every
deployed user takes the degrade path and pays milliseconds; the dev box has one, so it does not. The barrier
did not exist where the users are.

Second finding, uncomfortable and unrelated to layout: locally it is **6-13× worse than ADR-166 recorded**.
`llm.extract` sets `"think": False`; `llm.narrate` does not — so under `qwen3:8b` every narration pays a
thinking pass first. Nothing could catch the drift, because CI has no Ollama. Logged as its own follow-up
rather than folded into a page-layout change.

So the per-tab guess was replaced by one rule asked of the machine: **eager when cheap, a click when a
narrator is attached** (`llm.reachable()` — a connect, not a generation, that resolves ambiguity *towards* the
button so a wrong guess costs a click and never a 27-second load).

---

### 💡 The lesson

> **A latency number is only a fact about the machine that produced it.**

ADR-166 measured honestly and reasoned correctly from what it measured. The environment was the unstated
variable, and it silently turned a measurement into a claim about one laptop — which then cost the golden page
its best section. Any perf figure that will decide a user-facing default now names the machine it came from
and whether a model was attached.

**And the Definition of Done has three parts for a reason.** 1,642 unit tests were green on both paths while
the Cloud path landed in **49 seconds** — because every test runs under `conftest`'s model stub, the exact
state where that bug cannot appear. The smoke test found it in one run. `narrator_attached()` was choosing the
*layout* while `ask.answer` independently reached for whatever model was installed; the decision is now
**binding** (`narrator=None`), so the two halves cannot disagree. 49,007 ms → 195 ms.

---

### 🧪 Tests

**+53** (1589 → 1642), and **every new guard was mutation-checked** — the behaviour reverted one at a time,
each test confirmed red, then green again. Twice before in this project a test passed only because the
workaround had been written into it.

Pinned: the three sections present and in order · sub-nav is exactly the five · the week renders eagerly with
no model and waits behind a button with one · **one** captain setter, never three · the eager path pins its
narrator rather than inheriting the default · `llm.reachable` is False *only* on connection-refused and
guesses "attached" whenever it cannot tell.

**Two tests were repaired rather than accommodated:**

* `set_value()` accepts an option that does not exist and **keeps the current selection** instead of raising.
  ADR-166 renamed *Health* → *DNA*; two tests kept asking for `"Health"` and had been asserting against the
  **default tab** ever since — green, and covering nothing. `_squads_view` now verifies the switch landed.
* `test_my_squad_pitch_view_lays_out_the_squad` asserted `len(dataframe) == 0`, which was right when the pitch
  was the whole page and wrong once captaincy joined it. Rewritten to pin the intent — *the squad is a pitch,
  not a table* — rather than the old element count.

Both are the same species as ADR-168's *"CI has never exercised the narrated path"*: **coverage that leaves
without the suite going red is the expensive kind.**
