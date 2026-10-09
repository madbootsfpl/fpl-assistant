# ADR-345 — External intelligence is parked until there is a problem

**Date:** 2026-10-09
**Status:** Parked — a gate, not a build
**Reviews:** `docs/09_Proposals/External_Intelligence_Architecture_PARKED.md` (ChatGPT, 2026-10-05) and a
Hermes sample run (`~/fpl_staging/evidence_log.json`, 87 runs, 2026-10-05 → 2026-10-09)
**Builds on:** ADR-146 (the unexplained exodus), ADR-151 (headline extraction), ADR-232 (signals, tiered),
spike 206 (there is no corpus)

---

## The question

Should MadBoots add an External Intelligence Layer — continuous collection from news, club and social
sources, LLM claim extraction, sentiment time-series, validation, and features for the analytics layer —
with Hermes Agent as a replaceable enrichment worker?

## The proposal is good, and most of it is already here

⭐ The document is well built and its principles are right: evidence not authority, deterministic
validation, provenance, staging before promotion, backtest before adoption, a cost funnel, prompt injection
treated as hostile input, and *"do not store a single generic AI sentiment number"*.

⚠️⚠️ **But it describes MadBoots as it already is, and does not know it.**

| the proposal asks for | MadBoots already has |
|---|---|
| LLM extraction with a deterministic veto | `headlines.py` (ADR-151) — *"the model proposes, this module decides"*: a vocabulary rule vetoes any claim the text does not support, so a hallucinating model yields **fewer** events, never wrong ones |
| a source-reliability registry (§8) | ADR-232's tiers — `official` → `departure` → `exodus` → `headline`, ordered by evidentiary strength, with each signal carrying its `kind` so a client cannot flatten them |
| AI must not decide (§4.3, §22) | ADR-034/037 — analytics decide, the LLM narrates, and `verify_grounding` checks it |

## 🔴 The sample does not demonstrate the architecture

**71 of the 87 runs contain no AI at all.** `run_extraction.py` is plain Python: fetch `bootstrap-static`,
keep players with news or `status in (i,d,s,u)`, map status through a dict, copy FPL's own `news` string
into `claim_text`, and stamp:

```python
"confidence": 0.95,     # hardcoded, every claim
```

That is **15,724 of the 15,756 claims** — a field rename of a source MadBoots already ingests, with a
constant presented as a model's confidence. The texts are FPL's own: *"Back injury - Unknown return date"*,
*"Has joined Al Hilal permanently"* — the exact field ADR-136 already parses to tell a permanent exit from
a two-week injury.

**The remaining 16 runs are the only LLM path, and they produced two claims, repeated byte-identically 16
times across four days:**

> *Bukayo Saka — "Monitored for muscle tightness ahead of upcoming fixture."*
> *Ezri Konsa — "Passed late fitness test and returned to full training."*

`fpl_worker.txt` instructs the model to *"parse Premier League player news from available sources"* and
**supplies no content**. A schema and a URL went in; claims came out. ⭐⭐ *Real news does not repeat
verbatim for four days — an unchanging prompt does.*

⚠️ So the sample's only AI output violates the proposal's own §4.3: *"AI must NOT be the sole authority for
… whether a player is officially injured."*

## 🔴 And §6's centrepiece was already measured and declined

Spike 206 answered this in August, when the owner asked the same question about sentiment:

| | |
|---|---|
| headlines available (Reddit RSS + media feeds) | **112** |
| total text | **6,227 characters** |
| posts carrying body text | **0** |
| labels | none |

> *"The text is reported fact with named journalists. A sentiment score would invent a dimension the data
> does not have."*

⭐ ADR-151 took the real feature underneath — extraction, not classification — and shipped it. The proposal
rebuilds the framing that spike already rejected, on a corpus it does not know the size of.

## Decision

**Parked. Not dropped — the thinking is kept, the build is not started.**

⭐⭐ **Because no problem has been reported.** Not in the feedback log, not from nine testers, not in the
architecture review. Every real defect this month came from elsewhere: the bank that would not move, the
over-budget 422, the free-transfer cap, three failing endpoints.

⚠️ And the one time an intelligence gap *was* real — ADR-146's *"96,095 sold Watkins and nothing in the
data explains it"* — the story was already in a feed we fetch. ⭐ *The gap was not missing sources; it was
not reading what we had.*

### 📌 The triggers — either one un-parks this

1. **A tester reports a miss** — *"the app didn't tell me he was out"*, or a flag that arrived too late to
   act on. ⚠️ Owner or developer testing does not count; that is the mistake ADR-259's trigger already
   names.
2. **A measured corpus.** ⭐ Spike 206's finding was about *today's* sources. The genuinely valuable idea in
   the proposal is **widening the corpus, not adding AI** — and that is one cheap experiment: pick three or
   four sources you would be comfortable using commercially, collect for two weeks, and count items, total
   text, how many carry bodies, and how many name a player we hold. 📌 **No Hermes, no tables, no ingestion
   API, no LLM** — a collector and a word count. At 200 titles, spike 206 stands. At 5,000 items with
   bodies, the whole document becomes worth designing against real numbers.

### ⭐ What to do instead, and it serves the same user need

**`/squad/signals` is failing 14.7% of calls** — 13 installs, 129 calls, roughly one in seven, on the
**4th most-used endpoint in the app**. People demonstrably want this category of information and the
feature that delivers it is broken for them. ⚠️ *Fixing that is worth more than any new source.* ADR-343
now records status codes, so query 8 will say whether it is ours or an upstream refusing us.

### Adopted from the proposal: one line, no build

Its §22 principle is already how MadBoots works and is worth writing into the architecture docs:

> **External intelligence is evidence, not authority.** Production analytics consume only validated,
> timestamped, provenance-backed features, and must not depend on a particular AI provider or agent
> framework.

## On Hermes specifically

The proposal is right that it must be replaceable, and on this evidence nothing it did could not be done
without it. ⭐ The extraction pattern the document wants — a model proposing, a deterministic rule vetoing
— already runs locally, for free, on the Ollama on the owner's desk.

## Consequences

✅ The document is in the repository rather than a Downloads folder, marked parked, with this ADR as its
front door. ⏳ Nothing is built, no table is created, no dependency is added.

⚠️ **The risk accepted:** if a real intelligence gap opens mid-season, we start from a parked document
rather than a running pipeline. ⭐ *That is the right trade while no tester has reported one* — and the
corpus count is two weeks, not two months, whenever it is wanted.
