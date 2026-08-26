# Spike 206 — can we read *events* out of the headlines Signals already fetches?

**Question (owner, 2026-08-26):** *"With all the information we have in Signals, is there a way — TensorFlow,
machine learning — to create a sentiment score: this is what the news/social platforms are signalling, and
this is what we interpret as a signal? And maybe Trending needs blending in."*

**Answer: no model to train, no sentiment to score — but there is a real feature underneath, and it is
extraction rather than classification.** Measured, not argued.

---

## 1. There is no corpus, and no sentiment in it

| | |
|---|---|
| headlines available (Reddit RSS + media feeds) | **112** |
| total text | **6,227 characters** — about two pages |
| median post length | **51 chars** |
| posts carrying body text | **0** (titles only) |
| labels for supervised training | **none** |
| ground truth to evaluate against | **one gameweek** |

Training anything on 6KB of unlabelled titles would produce a random number with a confidence interval.

**And the text is not opinion.** It is reported fact with named journalists:

```
[Romano] Hilal have now agreed all details of deal to sign Ollie Watkins, here we go!
Nicolas Jackson to Aston Villa - David Ornstein
Cole Palmer is Player of the Matchweek for GW1
```

"Player of the Matchweek" is not positive sentiment, it is an event. **A sentiment score would invent a
dimension the data does not have.**

## 2. The thing that matters: the Watkins story was already in the feed

That first headline is the exact story behind ADR-146's *"96,095 sold Watkins and nothing in the data explains
it"* — sitting in an RSS feed the app **already fetches**, and which we reduce to *"Watkins: 13 mentions"*.

ADR-146 said the app could not know about a Saudi transfer. That has now been wrong twice: the owner pointed
out the *transfer data* knew, and this spike shows the *news itself* was in the feed.

## 3. Rules are not good enough — 58% precision, and the errors are the dangerous kind

A deliberately narrow rule-based extractor (`extract.py`) over the 112 headlines produced **12 events**, of
which **7 correct — 58% precision**:

| # | headline | rules said | verdict |
|---|---|---|---|
| 1 | *[Romano] …deal to sign Ollie Watkins* | Watkins, transfer | ✅ |
| 4 | *Palmer in training — **not injured*** | Palmer, **injury** | ❌ **negation** |
| 7 | *Brighton sign Jaouen **Hadjam*** | "Jaouen" (NEW) | ❌ **wrong player** |
| 8 | ***No injury** for Palmer* | Palmer, **injury** | ❌ **negation** |
| 10 | *…for **Enzo Maresca**…* | "Enzo" (CHE) | ❌ **matched the manager** |
| 12 | *…Tottenham …sign Omar Marmoush* | Marmoush, transfer | ✅ |

Recall is weak too — it missed *"Caicedo and Palestra not available"* and two real signings.

**58% would be fatal here.** ADR-146's entire discipline is that the flag never invents a cause; telling a
manager their fit player is injured is worse than saying nothing.

## 4. A local 8B model fixes 4 of the 5 failures, and fails *safe*

`qwen3:8b` via the Ollama already running locally, zero-shot, no training:

| case | rules | qwen3:8b |
|---|---|---|
| "not injured" | ❌ injury | ✅ `none` |
| "No injury for Palmer" | ❌ injury | ✅ `none` |
| "Jaouen Hadjam" | ❌ wrong player | ✅ *"Jaouen Hadjam"*, transfer |
| "Enzo Maresca" | ❌ matched a manager | ✅ Allan = transfer, **Maresca = `none`** |
| "Caicedo…not available" | ❌ missed | ⚠️ `none` (still missed) |
| Watkins / Maddison controls | ✅ | ✅ |

**Every model error was silence, not a false claim** — which is exactly the property this signal needs.

**Throughput: ~1.2 s per headline → the whole 112-headline feed in ~2.2 minutes**, and the feed is cached for
30 minutes, so it is a background job, not a page-load cost.

## 5. The two real obstacles — neither is the model

**a) Name resolution is the actual hard part.** The model returns names as written; FPL uses `web_name`:

```
"Ollie Watkins"  → surname "watkins"  → 1 FPL player  ✅
"James Maddison" → surname "maddison" → 1 FPL player  ✅
"Savinho"        → surname "savinho"  → 0 FPL players ❌
```

Surname matching is what produced the rules' *"Jaouen"* and *"Enzo"* errors in the first place, and this
codebase already has a live example of the collision: **`community_buzz` currently lists "Palmer" twice with
30 mentions each**, because two players share the surname. Extraction is only as safe as resolution, and
**resolution must be allowed to answer "I don't know"** and drop the event.

**b) Deployment.** Ollama is local-only; Streamlit Cloud has no model. Production would need the gated Haiku
path, or the extraction runs as a **local/CLI enrichment step whose output is committed with the data
snapshot** — which fits ADR-056's read-only deployment better than a live model call would.

---

## Recommendation

**Build the extraction, not a sentiment score, and not a trained model.** In this order:

1. **Resolve-then-extract, precision-first.** LLM proposes `{player, kind}`; a strict resolver maps to a
   `web_name` and **drops anything ambiguous**. Target: high precision, low recall. A missed story costs
   nothing; a wrong one costs the credibility of every flag on the page.
2. **Attach it to ADR-146's exodus.** The prize is turning *"96,095 sold him and nothing explains it"* into
   *"…and Romano reports a move to Al-Hilal"*. Same flag, cause attached — and it is checkable, because the
   headline is quoted with its source.
3. **Then, and only then, consider blending with Trending.** Blending needs the *relative weight* of each
   signal, which needs the **evaluation loop** (roadmap, unbuilt): did following the crowd beat xP-only?
   Until that exists, any weighting is a guess with a decimal point.

**Do not build:** a sentiment score (no sentiment in the data), a trained classifier (no labels, 6KB), or a
blended index (no weights yet).

**Bug found on the way:** `community_buzz` double-counts players sharing a surname — "Palmer" appears twice at
30 mentions. Small, separate, worth fixing.
