# Sprint 228: Retire Ask — and the promise that went with it (ADR-168)

**Dates:** 2026-08-29
**Status:** ✅ Complete — ADR-168. 1575 → 1578 tests, ruff clean. Sidebar 9 → 8.

> **Owner:** *"Ask is not being used… maybe I could have it as a tab in Admin so I could test with my local
> Ollama."* · *"Agreed, retire Ask and change the mantra in the same commit."*

---

### 🔧 What shipped

**Ask is retired as a page.** Fourteen of its sixteen intents duplicated a tab — and the tab version is
better, with photos, sorting and filters. AI Tips *is* `ask.answer("what should I do this week")`; Chips *is*
`ask.answer("which chip")`. Same engine, question pre-asked.

It survives in **Admin**, owner-gated and off by default, to answer one question: *is the narration worth a
hosted model?* Locally it shows what a paid model would add; on Cloud it shows the data-only answer testers
already saw. **Decision trigger: the GW4–6 calibration** — an experiment without an end date is a parked page.

**Help gained the FPL rules.** `fpl_rules.RULES` holds 21 curated topics and the only way to read them was to
type a question — a strange place for a reference, since you had to know what to ask before you could find
out. Testers gain rather than lose.

**And the mantra changed in the same commit**, which was the owner's condition:

> The analytics decide. ~~The AI explains.~~ **Every answer shows its working.** You make the call.

---

### 💡 The lesson

> **The unused feature was the symptom; the unbacked promise was the disease.**

The question was how to make Ask more powerful. The finding was that its one distinguishing feature —
narration — **had never existed in production**: there is no Ollama on Cloud, `DEPLOY.md` says so plainly, and
the brand line had been promising it anyway. Help disclosed the gap honestly; the mantra did not. madboots.com
had already dropped the clause on its own, so the in-app wording was the last place still claiming it.

A feature nobody uses is cheap to carry. **A claim you cannot keep is not.**

> **When you remove a capability, remove the promise in the same commit.**

The owner reached that before I did. Copy outlives code by default — three times in a month now (Home's tour,
the Feedback picker, the madboots.com grid). The fix is to treat the sentence as part of the feature.

### 🧪 Tests

**+3, six removed.** The six were page-level Ask tests, retired with the page; the engine keeps its coverage
in `test_ask.py`. Added: Help carries the rules; the app no longer promises narration it cannot deliver
(checked in `brand` *and* every page that renders it); Ask is owner-only and off by default.
