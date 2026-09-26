# ADR-309 — A microphone, and what is behind it

**Date:** 2026-09-26
**Status:** ⏳ **Gate — verified in code, not built.** Sequence agreed; one decision deferred with a £ in it.
**From:** the owner's own question — *"Can we add a microphone to speak a question into Ask?"* — and a full
conversational-Ask design brought back from ChatGPT for review.
**Follows:** [ADR-307](ADR-307-twenty-questions-and-what-ask-does-with-them.md) (measured),
[ADR-308](ADR-308-the-qualifier-is-the-question.md) (built), [ADR-034](ADR-034-ask-command-grounded-nl.md) (the narrator is optional),
[ADR-047](ADR-047-conversational-ask-follow-ups.md) (follow-ups), [ADR-152](ADR-152-resolving-a-player-name.md) (name resolution).

---

## The decision

**Four of the design's phases need no AI at all, and three of those are already built and unreachable. Do
those first.** The LLM goes *behind* the phrase router as a fallback, never in front of it as the router.
Voice **in** ships first because it is the cheapest item on the list; voice **out** is declined.

⭐ The design's own closing question was *"exactly how is our existing Llama implementation wired today?"*
— so it was answered in the code rather than from memory, ⭐⭐ *because the answer moves the cost of the
whole project.*

## What the design got right

⭐⭐ **The spine is correct, and it is already this project's own principle.** The brief states it as
*"Llama understands what the manager is asking; MadBoots calculates the answer."* `src/ask.py:573` has said
the same thing for months:

> **"Analytics DECIDE the captain (never the LLM)"**

The narrator already receives `facts` plus a `task` string ending *"using ONLY the facts"*, and returns
`None` on any failure so the decision survives without it. ⭐ *An independent rediscovery of an ADR is the
cheapest possible confirmation of it* — and this one is load-bearing, not decorative (see **§Marketing**).

Also right, and worth keeping: **the product definition** (*"Ask MadBoots about your FPL team"*, not *"ask
an AI about football"*), and the observation that **voice is an interface, not intelligence**.

## 🔴 The premise that carries the cost is wrong

> *"We have already been using Llama in MadBoots. Therefore we don't necessarily need to introduce another
> AI/LLM technology just to build Ask."*

⚠️⚠️⚠️ **True on the dev machine. False in the product nine testers use.** `src/service/http/app.py:721`,
written deliberately:

> *"**No LLM prose.** `ask.answer` narrates through **Ollama on localhost**, and there is none here — so the
> narrator is silenced rather than left to time out per request."*

`config.py` points at `localhost:11434`; Render has no Ollama; `ask_question` passes
`narrator or (lambda *a, **k: None)`. ⭐ **Every Ask answer on Android, iPhone and web today is pure
analytics with templated prose.**

So the missing piece is **not wiring — it is an inference host**, and that is a £-and-latency decision of
exactly the shape of the one [ADR-303](ADR-303-a-schedule-that-lies.md) left open. ⭐ *A layer that exists on one machine is not a layer the
product has.*

⚠️ **And the latency is already measured.** `src/llm.py:23`: with no Ollama `ask.answer` returns in
**~120 ms**; with `qwen3:8b` attached it narrates for **27-86 s**, and `OLLAMA_TIMEOUT = 240`. The design
adds a **routing** call before the analytics and an **explanation** call after — *two* inference round-trips
per question. ⭐⭐ *On a phone, over a network, that is not a feature.* A hosted small model answers in ~1 s;
a Render instance large enough to self-host qwen3:8b costs more than the rest of the stack.

## 🔴 The one part of the design that is rejected: the LLM must not route

The brief has Llama decide which function to call. ⚠️ Today that is a deterministic phrase table —
`_INTENT_KEYWORDS`, `src/ask.py:96`, fifteen intents, whose own comment reads **"the LLM decides none of
this."** Replacing it trades the wrong way:

- **It cannot be measured the same way.** ADR-307 ran all **31** questions through the live router; ADR-308
  killed **15/15** mutants. ⭐ *A phrase table can be pinned; a model's choice of tool cannot.*
- ⚠️⚠️⚠️ **It reintroduces the failure this project's own corpus singled out.** `src/ask.py:170`, on why a
  bare *"strategy"* is left deliberately unroutable:

  > *"guessing an intent for it would trade an honest miss for a confident wrong answer — **the one failure
  > the routing corpus measured as actually harmful**."*

  ⭐⭐⭐ **An LLM router never returns "I don't know."** It always picks a tool. It converts honest misses
  into confident wrong answers — *precisely* what ADR-307 counted twenty-one times out of thirty-one and
  called the thing this project least wants to ship.

✅ **Decided instead: the LLM sits behind the table, as a fallback.** The phrase table wins when it matches;
the model sees only the questions that today return *"I could not understand that."* ⭐ That is measurable
against a corpus which already exists, **it can only improve the miss rate**, and a bad LLM route is visible
*because the deterministic path was silent there.*

## ⭐⭐ Two of the design's later phases are already built and unreachable

**§5, "the really powerful version" — the gameweek briefing — exists.** `"what should i do"` routes to the
`gameweek` intent. On the owner's real squad, with no LLM anywhere:

```
This week (squad 'yours'): captain Haaland
Confidence: 40/100 (Low)
  Why 40? 64 for your captain, minus 24 for 3 flagged players.
    · Worth 8: João Pedro is flagged — replace him — you have no cover on your bench
    · Worth 8: Ndiaye is flagged — bench or replace him — benching him fields Tzolis (11.8 xP)
    · Worth 8: Maguire is flagged — bench or replace him — benching him fields N.Williams (17.2 xP)
    Ceiling this week is 64 — your captain's own number; lifting it means a different captain,
    not a different week.
```

⭐ The brief's mockup is bare bullets. The real thing shows **the confidence arithmetic**, **costs each flag
in points**, **names the replacement each bench would field**, and **explains its own ceiling**. So the
work is *not building the briefing — it is surfacing it on the phone*: one screen, no AI.

**§6, conversation context, exists too.** `converse()` (`src/ask.py:2087`) carries a `Context`, resolves
pronouns, and handles three follow-up kinds — **"why"** (re-narrates the same decision in more depth),
**"next"** (walks the rank), **"what about X"** (ADR-047). ⚠️⚠️ But `ask_question` calls
`ask_engine.answer(...)`, **not** `converse(...)`, so **the phone is stateless and the machinery is
unreachable** — ⭐ *the same shape of finding as the swipe and Chatter this month: the feature was built, and
only one client could see it.* Making *"Why?"* work is plumbing a context object through the contract, not
an LLM feature.

📌 This is now the **third** time an existing capability turned out to be client-locked. ⭐ *Worth a habit:
before designing a feature, ask whether it is already written and merely unreachable.*

## ⭐⭐⭐ This was already tested, and keywords won

⚠️⚠️⚠️ **The LLM router is not a new proposal — it was asked for, measured, and largely declined on
2026-08-30** ([ADR-168](ADR-168-retire-ask-and-the-promise-with-it.md) §🧪). Discovering that *after* forming the
objection above is the useful part: ⭐ *the argument was reasoning; this is evidence.*

```
baseline   20/25 routable correct · 3 missed · 2 "wrong"
verified   …of those 2, ONE was my label being wrong
actual     1 genuinely harmful mis-route in 30:
           "wildcard now or wait?" → build_squad → built a squad, "Confidence 95/100"
after      24/25 routable · 0 missed — from FOUR keyword additions
```

⭐⭐ **Four keywords beat the classifier**, and the corpus became a standing check —
`tests/test_route_corpus.py`, **35 tests, green today**. ⚠️ The corpus was built *before* the measurement
and weighted toward phrasings the table should already get, ⭐ *so a bad score would have indicted the corpus
rather than the router* — which is why the result is worth trusting.

⭐ And the decisive argument then was the same one this ADR reaches independently now: **deployment.** There
was no model on Cloud, so a classifier could only ever have helped the owner-only Admin surface.

🔴 **The revisit condition was pre-registered, and it is still not met.** The roadmap says: *"Revisit only
with real tester questions that keywords cannot fix."* ⚠️⚠️ ADR-307's 31 questions came from **the owner**,
not from testers — and **ADR-308 fixed the captaincy half with vocabulary and a lens, i.e. keywords again.**

⭐⭐⭐ **That is now three consecutive times the phrase table has been the cheaper answer.** So the fallback
router in the sequence below is **item 6 of 7 and gated on evidence that does not yet exist**, not a planned
build. ⭐ *A decision already taken on measurement should not be reopened by a new design document that
contains none.*

## Voice — the question actually asked, and the cheapest item here

⚠️ The brief sequences voice at **Phase 4-5, behind all the LLM work.** It needs none of it. Platform STT
(`speech_to_text` → iOS Speech, Android SpeechRecognizer, Web Speech API) is **on-device, free, no server,
no Whisper, no Render bill**, and it fills the same text box the keyboard fills. It would be the app's
**fifth** dependency (currently four, each documented as earned rather than anticipated).

⭐ The phrase table is unusually well suited to dictation, because it matches **phrases**, not exact strings.

Two things to settle before building it — ⭐ *these are the actual engineering in voice input, and the
plugin is not:*

- ⚠️⚠️ **STT will mangle player names.** "Semenyo", "Ndiaye", "Cunha" are in no dictionary. `build_index` /
  `find_mentions` (ADR-152) is the right place to absorb it, probably with a fuzzy pass — and **ADR-308 just
  made every captaincy comparison depend on that resolution**, so this hardens something already load-bearing.
- 🔴 **iOS may send audio to Apple** for recognition. Needs `NSMicrophoneUsageDescription` +
  `NSSpeechRecognitionUsageDescription` (Android: `RECORD_AUDIO`). ⭐ *Given this project hardened Supabase
  over exactly this class of thing, a plugin default is not a decision.*

## ✗ Declined: text-to-speech

⚠️⚠️ Read that briefing aloud and it takes a minute, **and audio cannot be skimmed.** The briefing's value
**is** its structure — a thing you scan, with the arithmetic visible. ⭐⭐ *Voice in is a convenience for a
question; voice out fights the product.* If it ever arrives it suits only the one-line answers
(*"Captain Haaland"*), never the analysis.

## The agreed sequence

| # | what | LLM? | note |
|---|---|---|---|
| **1** | **Microphone into the existing text box** | no | one dependency; the owner's own question, and the cheapest thing here |
| **2** | **Surface the gameweek briefing** | no | it exists, and it is better than the mockup — this is UI |
| **3** | **Plumb context: *"Why?"*, *"and the next?"*** | no | exists since ADR-047; unreachable from the phone |
| **4** | **Harden name resolution for dictation** | no | the real work in voice, and ADR-308 depends on it too |
| **5** | 📌 **Decide the inference host** | — | 🔴 the actual gate: £, latency, privacy |
| **6** | LLM as **fallback router only** | yes | 🔴 **gated on ADR-168's unmet revisit condition** — real tester questions keywords cannot fix. Three times now, keywords were cheaper |
| **7** | LLM prose over facts | yes | already designed for — `facts` + `task` are waiting |
| — | ✗ text-to-speech | — | declined above |

⭐⭐⭐ **1-4 deliver most of the felt improvement with no AI decision at all**, and the brief has three of
them sitting *behind* the LLM work.

## §Marketing — sharper than positioning

The brief's *"don't make the marketing dependent on AI"* is **load-bearing in the code**, not a stance: the
narrator returns `None` and everything still works (ADR-034). ⭐ *That property is precisely what makes
items 1-4 shippable before the AI question is answered* — and it is the thing to protect when an LLM does
arrive. ⚠️ A hosted model that becomes required turns a graceful degradation into an outage.

## Consequences

- ✅ **The tool surface for §4 already exists** — **20 answer functions** behind **26 contract-tested
  endpoints** in `src/service/`. ⭐ If tool-calling ever happens, the tools are the part that needs no design.
- 📌 **Deferred, deliberately: the inference host.** Until it is chosen, items 6-7 cannot be costed, and
  ⭐ *a plan whose first step is the expensive one is a plan that does not start.*
- 📌 **Not decided here:** whether the briefing gets its own screen or becomes the Ask default answer.
- 🔴 **Open risk if the fallback router ever ships:** it must be measured against **both** corpora —
  `tests/test_route_corpus.py` (30 questions, standing) and ADR-307's 31 — *before* it is allowed to answer,
  because the failure mode it introduces is invisible by construction: ⚠️⚠️ *a confident wrong answer looks
  exactly like a right one until somebody checks.*
- ⭐⭐ **The habit worth keeping from writing this ADR:** the design was reviewed against the code, and the
  code contained **a prior experiment that had already answered the central question**. ⚠️ *A proposal that
  cites no measurement is not evidence that none exists* — and this project keeps its measurements in ADRs
  and standing tests precisely so the next design can be checked against them.
