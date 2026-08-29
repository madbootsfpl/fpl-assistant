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

### 💡 The lesson

**The unused feature was the symptom; the unbacked promise was the disease.** The question asked was how to
make Ask more powerful. The answer was that its distinguishing feature — narration — had never existed in
production, and the brand line had been promising it anyway. **A feature nobody uses is cheap to carry; a
claim you cannot keep is not.**

The second, which the owner reached first: **when you remove a capability, remove the promise in the same
commit.** Copy outlives code by default — we have now watched it happen three times in a month (Home's tour,
the Feedback picker, the madboots.com grid). The only reliable fix is to treat the sentence as part of the
feature, not as documentation of it.
