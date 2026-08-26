# Sprint 207: Reading the headlines we already fetch (ADR-151)

**Dates:** 2026-08-26
**Status:** ✅ Complete — ADR-151. 1444 → 1455 tests, ruff clean.

> **Owner:** *"Yes, build it at refresh time."*

---

### 🔧 What shipped

`refresh` now reads the headlines the app already fetches, resolves them against our own players, and stores
events keyed `(element_id, title)`. ADR-146's flag gains a cause:

> *158,415 managers sold **Watkins** this gameweek — and **Romano reports** a move — "[Romano] Hilal have now
> agreed all details of deal to sign Ollie Watkins, here we go!"*

Signals shows the same, and a snapshot built without a model simply carries no events — every surface reads
exactly as it did before.

---

### 🐛 Three things the build changed, none of them predicted

**1. The verification had a hole, and the weaker model found it.** The design was: model proposes, app
verifies via a closed `kind` set plus a name that resolves to exactly one player. On the corpus **`qwen3:8b`
scored 16/16**. Then the *configured default*, `llama3.2`, produced 22 events including *"Barry scores a
hat-trick"* and *"Cole Palmer is Player of the Matchweek"* — **as transfers**.

Resolution could not catch those: the **names were real**, only the *kind* was invented. So the guard was
strong exactly where a good model needs no help, and absent exactly where a weak one fails.

Added `supports_kind`: **a rule that can veto but never propose.** Rules were never good enough to *find*
events (58% precision, spike 206), but they are perfectly good at noticing a sentence about a hat-trick
contains no transfer language. The same weak model then produced **7 events, all correct**.

> **A weaker model now costs recall, never precision** — the property the ADR claimed and, until the veto,
> did not actually have.

**2. A refresh step needs a time budget, learned by hanging.** An unbudgeted run had to be killed at ten
minutes. 112 headlines × a 60-second per-call timeout is nearly two hours, bolted onto the command whose real
job is the player data. `extract` now takes a budget, stops cleanly, and keeps what it already resolved.

**3. An old guard test earned its keep in one line.** `enrich_headlines` needed the media feeds, which lived
in `web_streamlit/media.py`, and `test_core_never_imports_a_web_edge` failed instantly. The guard was right:
the function had nothing web-specific in it and had been misfiled since ADR-093. Moved to `src/api/media.py`.

---

### 💡 The lesson

> **"The model proposes, the app verifies" is only as good as what you verify.**

The design sentence was right and the implementation of it was incomplete — and it *looked* complete, because
the model I tested with never made the mistake the guard was missing. Two guards checked **who** the event was
about; none checked **whether the event was there at all**. Swapping to a weaker model was the only thing that
exposed it.

Generalising: **test a verification layer with the worst input you can arrange, not the best.** A good model
hides the holes in the checks around it, and the checks are the part that has to survive a bad day — a model
upgrade, a config change, a provider swap.

Second, smaller: **three of this sprint's four findings came from running the thing rather than designing it**
— the hole, the hang, and the misfiled module. The ADR was measured, gated and specific, and still did not
predict any of them.

### 🧪 Tests

**+11.** A hallucinated player resolves to nobody; a kind outside the closed set is dropped; malformed replies
yield nothing rather than raising; a model that errors costs one headline, not the batch; **the veto**, pinned
with the exact hat-trick case; FPL-meta headlines never reach the model at all; the press short-form
("Ollie Watkins") resolves; the same story from two feeds collapses; **the budget stops cleanly and keeps
partial results**; and the source is named with its headline quoted, because *"Romano reports"* is a different
claim from *"someone said"*.
