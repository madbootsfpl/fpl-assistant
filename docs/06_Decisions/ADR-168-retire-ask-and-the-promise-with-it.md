# Architectural Decision Record: Retire Ask — and the promise that went with it

**Decision ID:** ADR-168
**Date:** 2026-08-29
**Status:** ✅ **Accepted — discussed and agreed with the owner, built** (Sprint 228, 2026-08-29).
**1575 → 1578 tests, ruff clean. Sidebar 9 → 8.**
**Superseded By / Replaces:** Retires the Phase-4 `Ask` page (ADR-052/047/080) as a *surface*; `ask.answer`
and `ask.converse` remain the engine behind AI Tips, Chips, the CLI and the FastAPI edge. Changes ADR-114's
mantra. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"Ask: most of the items are covered in AI Tips or Chips. How could we make this AI more relevant/powerful
> and what would that mean?"* — and later, decisively: *"Ask is not being used."*

**Two findings, and the second reframed the question.**

**1. Fourteen of sixteen intents duplicated a tab.** `captain · transfer · analyse · start_bench · gameweek ·
chips · build_squad · compare · fixtures · history · trends · price · worth · shortlist` are all clickable
surfaces — and the tab version is better, because it has photos, sorting and filters. AI Tips *is*
`ask.answer("what should I do this week")`; Chips *is* `ask.answer("which chip")`. Same engine, question
pre-asked. Only **`rules`** and **`scoring`** had nowhere else to live.

**2. There is no AI in it on Cloud.** From `docs/DEPLOY.md`:

> **Ask** shows no written paragraph | Expected — no Ollama in the cloud; the decision + facts + trust line
> still show.

So for every tester, Ask was a natural-language **router** to blocks reachable by clicking. *"Make the AI more
powerful"* could not mean better writing, because in production there is none.

**Which exposed something larger than the page.** `MANTRA = "The analytics decide. **The AI explains.** You
make the call."` — a three-part promise the deployed app kept two thirds of. Help disclosed it honestly
(*"The hosted app runs data-only"*), and **madboots.com had already dropped the clause on its own**, running
*"The analytics decide; you stay in control."* The in-app mantra was the last place still claiming it.

---

### ✅ Decision

**1. Ask is retired as a page** and kept in **Admin**, owner-gated and off by default — the owner's proposal:
*"maybe I could have it as a tab in Admin so I could test with my local Ollama, which would mimic a hosted
model, so I can gauge its usefulness."* Run locally it shows what a paid model would add; opened on Cloud it
shows the same data-only answer testers saw. **⏳ Decision trigger: the GW4-6 calibration sitting** — by then
it has been used or it has not, and *"I never opened it"* is a decisive answer. An experiment without an end
date is a parked page, and this project already has two.

**2. Help gained the FPL rules.** `fpl_rules.RULES` carries **21 curated topics** — scoring, chips, autosubs,
deadlines, price changes — and the only way to read them was to type a question, which is a strange place to
keep a reference: you had to know what to ask before you could find out. They are browsable now. **Testers
gain rather than lose.**

**3. The mantra changed in the same commit** — the owner's condition, and the right one:

> The analytics decide. **Every answer shows its working.** You make the call.

Removing the surface while keeping the sentence would have been the worst of both. What replaced the clause
is what the app does everywhere including Cloud: the ✓/⚠ trust line, the named outlet behind a departure, the
reasons under a Scout pick.

### 🧪 Definition of Done

1. **Tests: +3, six removed.** The six were page-level Ask tests, retired with the page; `ask.answer` and
   `ask.converse` keep their own coverage in `test_ask.py`. Added: Help carries the rules; the app no longer
   promises narration it cannot deliver (checked in `brand` *and* in every page that renders it); Ask is
   owner-only and off by default.
2. **Manual smoke** — 8 sidebar pages, Help's rules browsable, Admin's Ask loads on demand.
3. **Docs** — this ADR, Home's tour, the Feedback picker, the marketing deck, PROJECT_STATUS, a retro.

⚠️ **Owner action: madboots.com still lists *"Ask — plain-English questions, grounded answers"*.** The page
source is not in this repo, so it is in `docs/08_Marketing/Homepage_Copy.md` rather than fixed here.

---

### 🔬 First evaluation finding (2026-08-30) — **the constraint is the router, not the prose**

The owner opened the Admin surface with Ollama running and asked:

> *"what's my best strategy for FPL"*

and got the catch-all list of things Ask can answer. His question was whether that meant Ollama needed setting
up. **It did not, and the answer reframes what this experiment is measuring.**

**What actually happened.** That reply is `_FALLBACK` (`ask.py:156`), emitted by `route()` when a question
matches none of the 16 intents. `route()` contains **no LLM reference at all** — routing happens first, and
narration only ever decorates an answer that already exists. **The identical response comes back with a model
running**, which is exactly what he saw.

**What the model does buy**, measured on a question that *does* route (`who should I captain from RoboTS?`,
Ollama up, 4.1 s):

> *"B.Fernandes is a good captain pick this gameweek due to his high expected points, being a penalty taker,
> and set-piece involvement. His away fixture against EVE is the only risk…"*
> ✓ Checked: every figure and name in the explanation traces to the data above.

**That paragraph and its verification line are the entire difference between local and Cloud.** The pick, the
confidence score, the Edge/Risk bullets and the alternatives all render identically with no model.

**So the question this ADR set out to answer — *"is the narration worth a hosted model?"* — is the wrong
one, or at least not the interesting one.** *"What's my best strategy for FPL"* is a reasonable thing to ask
and the app cannot take it, **not because the prose is missing but because no intent covers open strategic
questions**. A hosted model, dropped in as-is, would buy a nicer paragraph on the questions that already
work — and would still fall through on that one.

**The question worth carrying into the GW4-6 decision instead:** would an **LLM intent classifier** — letting
the model *choose* an intent, or synthesise across several — make Ask do something the tabs cannot? That is
already in the backlog under *"More `ask` intents"*, and it is a materially different proposition: routing is
where the ceiling is, and it is the half a language model is genuinely good at.

⚠️ **Recorded before deciding anything.** One question is one data point, and it is the owner's own question
rather than a tester's — nobody else can reach this surface. Treat it as a hypothesis to test at the sitting,
not a finding.

### 🧪 Tested the hypothesis (2026-08-30) — **and it mostly did not hold**

The owner asked for the LLM intent classifier. Built a **30-question corpus** first, deliberately weighted
toward phrasings the keyword table *should* already get, so a bad score would indict the corpus rather than
the router.

```
baseline   20/25 routable correct · 3 missed · 2 "wrong"
verified   …of those 2, ONE was my label being wrong — `rules` answers
           "how many points is a goal worth?" with the exact scoring table
actual     1 genuinely harmful mis-route in 30:
           "wildcard now or wait?" → build_squad → built a squad, "Confidence 95/100"
after      24/25 routable · 0 missed — from FOUR keyword additions
```

The three misses were people talking normally — *"should I bring in X?"*, *"is my team any good?"*,
*"is X overpriced?"* — and the harmful one was a missing bare `"wildcard"` in `chips`, which `build_squad`
had instead.

**So the ceiling was lower than one question suggested, and four keywords raised it.** The corpus is now
`tests/test_route_corpus.py`, a standing check rather than a one-off measurement.

**The decisive argument against the classifier is not the score, though — it is deployment.** There is no
model on Streamlit Cloud, so an LLM router could only ever help the **owner-only Admin surface**, while
keywords work everywhere. Building it would be spending the one thing Ask cannot have in production.

**What would still justify one:** a question that is *genuinely* multi-intent (*"what's my best strategy"*
remains unanswerable, and correctly so), or a corpus of **real tester** questions showing the keyword table
failing in ways keywords cannot fix. Neither exists yet. **Revisit at GW4-6, with the corpus as the evidence.**

### 🔬 Second finding (2026-08-30) — **the prose is either redundant or unverified**

Three answers sampled locally with Ollama up, on the surface that finally works (see the gate fix below).

| question | what the narration added |
|---|---|
| *wildcard now or wait?* (chips) | **nothing.** *"GW3: Triple Captain - M.Sangaré due to highest single-GW ceiling…"* — each clause restates the row directly above it |
| *is Haaland worth the money?* (worth) | **nothing new.** It walks the Edge bullets in order, joins them with *"and"*, appends the Risk bullet after *"However"* |
| *who should I captain?* (captain) | **one clause**: *"his away fixture is the only risk, but it's a relatively low-risk scenario"* — a judgement, not a restatement |

**The pattern, and the mechanism behind it.** The answers that are already a *structured list* — chips,
build, shortlist — leave the model nothing to do but read the table back. The answers that are a *judgement*
— captain, worth, transfer — give it something to synthesise, and that is where it produced its only original
sentence in three samples.

**And that one original sentence is the one thing that cannot be checked.** `verify_grounding` flags
**numbers and names** — nothing else. So *"it's a relatively low-risk scenario"* passes untouched, because it
contains neither. The ✓ line is honestly worded (*"every figure and name in the explanation traces to the data
above"*) and claims exactly what it verifies — but the useful half of the narration sits outside its scope by
construction.

**So the narration is redundant where it is checkable, and unchecked where it is useful.** That is a
materially worse case for a hosted model than *"is the writing nice?"* suggested.

⚠️ **The load-bearing caveat: this was measured on `llama3.2`** — a 2 GB model, 17 months old. A frontier
hosted model would very likely synthesise better, and the redundancy on list-shaped answers might be a
small-model artefact rather than a property of narration. **Three samples, one small model, the owner's own
questions.** It sharpens the question for GW4-6; it does not settle it.

**What it does suggest testing at the sitting:** narrate *selectively* — only the judgement-shaped intents —
rather than paying to narrate everything. That is cheap to try and would have caught two of these three.

### 💡 The lesson

**The unused feature was the symptom; the unbacked promise was the disease.** The question asked was how to
make Ask more powerful. The answer was that its distinguishing feature — narration — had never existed in
production, and the brand line had been promising it anyway. **A feature nobody uses is cheap to carry; a
claim you cannot keep is not.**

The second, which the owner reached first: **when you remove a capability, remove the promise in the same
commit.** Copy outlives code by default — we have now watched it happen three times in a month (Home's tour,
the Feedback picker, the madboots.com grid). The only reliable fix is to treat the sentence as part of the
feature, not as documentation of it.
