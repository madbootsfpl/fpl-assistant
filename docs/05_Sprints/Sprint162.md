# Sprint 162: UX Sprint C — naming & onboarding (US-398–400)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-398–400, display/copy (+ a byte-identical-CLI `render_ask` markdown mode). 1003 → 1005 tests.
**Capacity:** ~½ session

> **From the audit (Sprint C).** Already done: **rename → "Maddie Explains"** (S160), **empty-state copy** (S160).
> **Dropped per owner:** *sidebar icon labels* — the owner reviewed the sidebar and said "leave as is". Remaining:

---

### 🎯 Scope

**US-398 — Home: one clear primary action.** The value path (build a squad) is buried in a bullet wall; the only
nudge is deadline-gated. Add a **persistent primary CTA** high on Home — **"🧪 Build your first squad → Squad Lab"**
(a `st.page_link`, works on Home the main script) — right under the tagline/countdown, above the "Explore the
sidebar" list. Tidy the callout stack: keep the New-here + Maddie nudges together, move the **beta/Testing** nudge
down to a lighter **footer** (near the disclaimer) to cut mid-page banner-blindness.

**US-399 — Ask: read like a chat, not a terminal.** Render answers with **`st.chat_message(...).markdown(answer)`**
instead of `.code(answer)` (a monospace block contradicts "plain-English chat"; keeps code/tables in fenced blocks
only). Change the seed prompts' **`my-team` → `my squad`** (a friendlier default; update the squad-name
substitution token to match). No engine change — `ask.answer` already takes the squad explicitly.

**US-400 — News: one availability vocabulary.** Every other surface shows the emoji **Fit flag** (⛔🚑❓ via
`fit_flag`), but News shows only text ("Out"/"Injured") + a Chance column. Add the shared **Fit** emoji column as
the leading availability signal (keep Status + Chance as the richer detail News is *for*), so the vocabulary matches
the rest of the app.

**Not this sprint (carried):** the header-sort-vs-pagination honesty item (M); the registration dead-end fallback
(S); the incremental token retro-fit (from Sprint B); Sprint D (My Squad density).

---

### ✅ Definition of Done
1. **Tests:** Home shows a primary "Build your first squad" `page_link` to Squad Lab; the Ask page renders answers
   as markdown (assert no `st.code`/`chat` code element, and the example prompts read "my squad"); News shows a Fit
   column. Full suite green + ruff.
2. **Manual smoke** (owner): Home has one obvious "get started" action up top; Ask answers read as prose; News shows
   the same ⛔🚑❓ flags as the other tabs.
3. **Docs:** this plan + retro; PROJECT_STATUS; the audit's Sprint-C row ticked; memory.

### 📋 Sprint Review

**Delivered — the onboarding/consistency slice.**
- **US-398 Home:** a persistent primary **"🧪 Build your first squad → Squad Lab"** CTA up top (the value path was
  buried in a bullet wall); the beta/Testing nudge moved to a lighter **footer** to cut mid-page banner-blindness.
- **US-399 Ask reads like a chat:** `render_ask` gained a **`markdown` mode** — the web passes it, and the aligned
  plan/facts table is wrapped in a ``` fence so it **keeps monospace alignment** while the prose (question ·
  explanation · ✓/⚠) renders as chat text; the page now `.markdown()`s the answer instead of a raw `.code()` block.
  **CLI/FastAPI stay byte-identical** (the flag defaults off). Seed prompts `my-team` → `my squad` (Ask + Help).
- **US-400 News:** the shared **Fit** emoji column (⛔🚑❓), so availability reads the same as every other surface
  (Status + Chance kept as the detail News is for).
- **Tests:** +2 (Home CTA · News Fit) and re-pointed the Ask tests off `.code`/`my-team` onto markdown/`my squad`.
  **1005 total.**

**Owner smoke (post-deploy):** Home has one obvious "get started" up top; Ask answers read as prose with the plan
table still aligned; News shows the same flags as Players/Trending.

### 🧠 Lessons

- **Verify on real data — it eliminated the obvious approach.** The audit said "render Ask as markdown"; checking
  `render_ask` showed the answers carry **monospace-aligned plan tables** (shared with the CLI) that a naive
  `.markdown()` would mangle. The right fix was a *fenced* markdown mode — prose as chat, table in a code fence —
  not a one-line swap.
- **Add a mode, don't fork the renderer.** A `markdown=False` default kept the CLI/FastAPI output byte-identical
  while the web opts in — one function, two audiences, no divergence to maintain.
- **A cosmetic rename ripples through copy that quotes it.** Changing the Ask example `my-team → my squad` also
  meant the Help page (which quotes the example) and its test — chase the string everywhere it's echoed.
- **`st.page_link` on the main script is fine** (Home CTA) even though it raises in AppTest on a sub-page — the
  distinction from the Sprint-146/160 lesson holds.
