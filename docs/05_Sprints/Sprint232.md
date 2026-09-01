# Sprint 232: Say what the app actually does (docs + marketing)

**Dates:** 2026-08-31 → 2026-09-01
**Status:** ✅ Complete — no ADR (no architectural decision; this is documentation and copy).
**1643 → 1655 tests, ruff clean.** Two new guard suites; no product code changed except user-facing strings.

> Started as *"can we rearrange the Home page?"* and became a sweep, because the same defect was everywhere.

---

### 🔧 What shipped

| surface | what was wrong |
|---|---|
| **ADR index** | stopped at **122** while **171** ADRs existed — 49 missing, and scrambled into `…069 068 067 089 122…070 066` |
| **Home** | the "Explore the sidebar" list had **four of eight** entries in the wrong order |
| **Help** | *"switch My Squad · AI Tips · Captain · Transfer · Chips · Health"* — **four of six names wrong**; Squad Lab taught as a sidebar tab; a whole numbered step with nine copy-paste examples for **Ask**, retired |
| **`src/web_streamlit`** | **eight** nav references, including *"build in the **Squad Lab** tab (sidebar)"* printed by a panel that **renders on My Squad**, three inches under the Lab tab |
| **Marketing scripts** | all nine predated the app; six sign-offs on the retired mantra; §8 a full script for Ask; **five shipped differentiators with no marketing at all** |

Also: **madboots.com deployed** (owner), **US-435 closed** (ADR-171, Sprint 231), and §§G/H drafted so every
shipped differentiator now has a script.

---

### 💡 The lesson

> **When navigation changes, the code gets updated and the copy that describes it does not — because nothing
> connects them.**

Five documents in one week were found teaching something untrue. **Every one was found by accident, while
doing something else.** None of them made anything go red, which is why they survived: a stale document does
not fail.

So every fix shipped with a guard rather than a careful edit — `tests/test_adr_index.py` and
`tests/test_navigation_copy.py`, the latter sweeping every module under `src/web_streamlit` for retired
navigation phrases and checking each `My Squad ▸ X` names a real sub-tab.

**⚠️ The guard had to distinguish copy from history, and the first version did not.** A plain text match
flagged `2_FDR.py`'s docstring — *"Split from the combined Team DNA & FDR page (ADR-169)"* — which is correct
and valuable. It now reads **string literals that are not docstrings**, via `ast`, so comments fall out for
free. **A guard that pressures someone into deleting the reasoning to go green is worse than no guard**, and
this project values the reasoning above the code.

**⚠️ Three tests were pinning stale copy.** One asserted Help still mentioned **Ask** and a copy-paste Ask
example — so it would have failed the moment the docs were corrected. One asserted the literal string *"Squad
Lab"* in a caption that was wrong. One asserted `len(dataframe) == 0` on a page that legitimately gained a
table. **A test that fails when you fix the documentation actively defends the error.** All three now assert
the requirement, not the wording.

---

### 📣 Marketing (`docs/08_Marketing/Video_Scripts.md`)

Every script re-cut against the app: **§8 → Leagues & Head-to-Head** (the Ask draft archived as **§8b** with
its GW4-6 trigger, because a parked idea with a recorded reason beats a forgotten one), **§7 → Your Week,
Answered** (its hook improved from *"one tap gives your plan"* to *"before you ask"*, which ADR-171 made
literally true), and **§G Scout** + **§H Team DNA** newly drafted.

**Measured, not assumed — twice.** The produced intro is **159 words in ~80s**, so Maddie reads at **~119
wpm**, while every draft assumed ~150. So every stated duration **and every beat timecode** was optimistic by
25-70%: the "2-minute" hero is **2:27**, and §4's markers stopped at 0:53 for an 87-second script — which
would have misled the edit. All recomputed. §§4-5 became **~90s YouTube pieces** (owner's call): they are
*searched for*, so they compound rather than decay, and cutting them hard would have removed the reasoning
that is the whole point of them.

**Two claims deliberately withheld, written down so they are not re-invented:** Scout is *worth a look*,
**never** *worth points* (two of its signals sit at weight 0); and **no script may offer a win probability** —
ADR-161 measured it as a coin flip and gated it, so marketing it would sell the one thing we refused to ship.

**⚠️ Shot-timing constraint, found by checking rather than assuming:** four of Scout's five boards need 900
minutes, and **0 of 626 players** clear that bar today, so they honestly show **last season** (ADR-126).
Filming §G now captures last-season numbers on four of five boards.

🚨 **Open, and the owner's:** the intro on **madboots.com right now** opens *"AI clarifies the data"* — the
exact clause ADR-168 removed from the mantra, because Cloud has no model. The revised script is ready; it
needs a re-render, a new unlisted YouTube link, and a swap in both `~/madboots-site/index.html` and the
`maddie_videos` row.

---

### 🧪 Tests

**+12** (1643 → 1655) across two new files, **every guard mutation-checked** — and for the nav sweep, checked
in *both* directions: the same phrase in a caption fails, in a docstring passes. That control case is the one
that matters, because it proves the guard distinguishes copy from history rather than banning a string.
