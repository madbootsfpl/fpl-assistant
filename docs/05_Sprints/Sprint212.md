# Sprint 212: The extraction model is its own choice — and the resolver stops matching non-players (ADR-157)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-157. 1485 → 1496 tests, ruff clean.

> **Claude, pitching the sprint:** *"`qwen3:8b` found 16 events where `llama3.2` found 7."*
> **Re-measured on the same 112 headlines: 13 and 13.**

---

### 🔧 What shipped

**Extraction got its own knobs** — `OLLAMA_EXTRACT_MODEL` / `_TIMEOUT` / `EXTRACT_BUDGET_SECONDS`. One
constant was choosing for two jobs that want opposite things: narration runs while a person waits, extraction
runs once, unattended, in `refresh`. Set to `qwen3:8b` — half the speed of `llama3.2`, and none of its
mislabels (it called a *return* a *transfer*, which is the exact input the departure rule consumes).

**The resolver stopped matching non-players.** Checking which players the events attached to:

| headline | resolved to |
|---|---|
| €135m **Bradley** Barcola | Conor Bradley, Liverpool |
| **Enzo** Maresca | Enzo Fernández — a **manager's** first name |
| **David** Ornstein | a player called David — **the journalist we cite as a source** |

ADR-152's span consumption beats "James Maddison" vs Reece James *because we hold both names*. It can't help
when the longer name belongs to someone outside the league — or to someone who isn't a player. A bare surname
followed by another capitalised word is now not a mention. **Measured: 45 → 40, all five rejected wrong, none
of the 40 good ones touched.**

**A truncated read says so.** The budget stopped cleanly and silently, so a feed that outgrew it read exactly
like a quiet news day. And it went 180s → 300s, from the measured ~75s read.

**Live:** 12 events, none false. Watkins → Al-Hilal still flagged, the Spurs team news correctly a *return*.

⚠️ **Not on Cloud yet** — `seed.db` still holds the six llama3.2-era events. Reaches Cloud on the next
**reseed**, which is the owner's call.

---

### 💡 The lesson

> **A remembered measurement is not a measurement.**

I pitched this sprint on "16 vs 7", from my own note about a spike, and Tony approved it on my say-so.
Re-running it gave 13 vs 13. The work turned out worth doing for reasons neither of us knew at the gate — and
had the numbers gone the other way, we'd have spent a sprint on nothing. A remembered number is a hypothesis
with a figure attached; re-run it before using it to justify work, and especially before quoting it to the
person deciding whether to fund that work.

I also nearly shipped a second bad number: the first timing run said `qwen3` was 6.8× *faster*, which was a
full `pytest` run overlapping the other model's leg. Clean, `llama3.2` is the quicker one.

> **I went looking for a better model and found a worse resolver.**

The worst defect in the pipeline wasn't in the part that guesses — it was in the deterministic code deciding
who the guess was *about*. Investigating the suspect component is a good way to discover that the reliable one
beside it was never checked.

### 🧪 Tests

**+11.** Extraction and narration read different models and different timeouts; an explicit model still wins;
extraction asks for determinism and no thinking; a missing model costs only the answer; a truncated read says
so and a complete one doesn't; plus five resolver cases — the foreign player's first name, the manager, the
journalist, a full name surviving a following capital, and an ordinary mention left alone.
