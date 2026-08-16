"""Help — a step-by-step guide to getting the most from MADBOOTS (ADR-068, revamped ADR-111).

Static content only (markdown + expanders): no analytics/data dependency, so it renders even before a
refresh, and no input controls. It complements Home (the short overview) with a deeper recipe + a glossary.
"""

import streamlit as st

from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access

st.set_page_config(**brand.page_config("Help"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Help")
st.title("🧭 Help")
st.caption("A step-by-step guide to getting the most from MADBOOTS. **The analytics decide; the AI only explains** — "
           "and every answer is checked against the underlying data with a **✓/⚠** trust line.")

st.markdown(
    "#### Quick start\n"
    "1. **🧪 Squad Lab** → build your squad → **Use this squad**\n"
    "2. **🧩 My Squad** → manage your team\n"
    "3. **🤖 AI Tips** → get your gameweek plan\n"
    "4. **👑 Captain · 🔄 Transfer · ❤️ Health** → review your decisions\n"
    "5. **💾 Download** your `squad.json` backup\n\n"
    "*Prefer words?* **💬 Ask** lets you do it all in plain English."
)

st.caption("Your team lives on the **🧩 My Squad** tab — switch **My Squad · AI Tips · Captain · Transfer · Chips · "
           "Health** with the buttons at the top; build a new one anytime in **🧪 Squad Lab**. **🏠 Home** shows a "
           "⏳ **live deadline clock** that turns 🟠 then 🔴 as it nears — a reminder to set your captain, transfers "
           "and chips before the gameweek locks.")

with st.expander("1 · Build your squad  →  **🧪 Squad Lab**", expanded=True):
    st.markdown(
        "Build your 15 with:\n"
        "- **Budget & shape** — spend to your budget across 2 GK · 5 DEF · 5 MID · 3 FWD.\n"
        "- **Archetypes** — Cheap · Premium · Differential.\n"
        "- **Players** — include or exclude specific players.\n"
        "- **Bench** — declare your bench.\n"
        "- **Objective** — xP · Points · Value · xGI.\n"
        "- **Build mode** — Balanced · Weekly (a cheap playing bench) · Bench Boost (maximise all 15).\n"
        "- **ⓘ** — every control has an explanation.\n\n"
        "When you're happy: **Use this squad →** makes it your active squad, and/or **💾 Download** the `squad.json` "
        "as a local backup."
    )

with st.expander("2 · Make it yours  →  **🧩 My Squad**", expanded=True):
    st.markdown(
        "Your active squad on a **green formation pitch** — kits GK→FWD, a bench strip, xP chips, the **(C)** "
        "armband and sub-number badges.\n\n"
        "**Player actions** — the **⚙ panel** below the pitch (works on phone too):\n"
        "- **🪪 Player Card** — select any player for their card: photo · a **per-GW xP** row (each of the next "
        "weeks' points over its fixture) · key stats · **Trends** · **set-piece duties** (⚽ pens · 🚩 corners · "
        "🎯 free-kicks).\n"
        "- **⚔️ Boot Battle** — compare them side by side with another **same-position** squad player, the better "
        "stat highlighted.\n"
        "- **👑 Captain** — make them captain.\n"
        "- **🔁 Substitute** — a legal lineup change (only valid swaps are offered).\n"
        "- **Hover** a shirt on desktop for a quick preview; no photo → we show their **club shirt**.\n\n"
        "**Edit your squad:**\n"
        "- **✏️ Rename** your squad.\n"
        "- **🔄 Transfer** — sell a player, buy a legal same-position replacement; filter by **position** or "
        "**Affordable only**; an overspend is **flagged live**; tick **🚑 Include injured/suspended** to plan around "
        "a flagged player.\n"
        "- **🪑 Set bench** — choose all four bench players at once.\n\n"
        "The summary's **Projected XI** includes your **captain's ×2 — for the next gameweek only** (captaincy is "
        "re-picked each week). Your squad is **saved to your account and auto-synced across your devices** — no "
        "manual save (manage it in the **⚙ Your team** panel on My Squad). *(**Substitute** = a lineup change; "
        "**Transfer** = a new player — they're separate.)* Need a new squad? Head back to **🧪 Squad Lab**."
    )

with st.expander("3 · Check its health  →  **My Squad → ❤️ Health**"):
    st.markdown(
        "How your squad is projected to perform over the next **1–10 gameweeks**:\n"
        "- **📈 Projected xP** — your squad's expected points.\n"
        "- **📅 GW breakdown** — the projection for each gameweek.\n"
        "- **⚠️ Weak links** — players worth considering for an upgrade.\n"
        "- **One xP number** — the same engine the CLI uses, so the projection stays consistent."
    )

with st.expander("4 · Plan your week & improve it  →  **My Squad → 🤖 AI Tips · 👑 Captain · 🔄 Transfer · Chips**"):
    st.markdown(
        "Start with **🤖 AI Tips** — your fastest gameweek plan:\n"
        "- **👑** who to captain · **🔁** any lineup change · **🔄** one transfer to consider · **🚑** injuries & "
        "doubts, all **✓/⚠** checked against the data.\n\n"
        "*You always get the full data-driven plan; where a local AI is available it adds a written narration.*\n\n"
        "Then dig deeper:\n"
        "- **🔄 Transfer** — ranks the best single swaps by how much they improve your legal XI. Set your **bank** "
        "with the slider, or ask for a coordinated **2–3 transfer plan**. **Apply** one swap, or **Apply this "
        "plan →** for all at once.\n"
        "- **👑 Captain** — ranks captain & vice-captain by expected points, with opponent · penalty duty · "
        "ownership (💎 differential → 👑 essential). **Set as captain** to keep it.\n"
        "- **Chips** — *when* to play **Triple Captain · Bench Boost · Free Hit · Wildcard**, from your projected "
        "points over the chosen horizon (✓/⚠). Fixture-run based for now; double/blank gameweeks + mini-league "
        "position sharpen it in-season."
    )

with st.expander("5 · Do your research  →  **👟 Players · 📅 Fixtures · 📈 Trending · 📰 News**"):
    st.markdown(
        "- **👟 Players** — explore the full pool: **🔎 filter** by team / position / player, sort, browse; a "
        "**table + top-15 chart**; a **🪪 Player Card** (photo · fixtures · Projected xP · position-adaptive stats) "
        "with **⚔️ Boot Battle** to compare a same-position player side by side; and the stat views "
        "**over/under-performance · Defensive Contribution · Clean Sheets · xG**. A **🟢…🔴 quality rating** shows "
        "how a player compares with those shown. Switch views with the buttons at the top.\n"
        "- **📅 Fixtures** — the next **1–8 GWs** on a colour-coded difficulty ticker; scope it to **your squad**, "
        "or use **🎯 Radar** to find players from the easiest-run teams (filter by position, cap the price, sort by "
        "xP or Val/£m).\n"
        "- **📈 Trending** — what the crowd's doing (most-owned · transferred in/out · in-form) + **Community "
        "Signals** (what r/FantasyPL is talking about — a lens, not truth).\n"
        "- **📰 News** — official FPL injuries, doubts and returns, most serious first."
    )

with st.expander("6 · Ask the assistant  →  the **💬 Ask** tab"):
    st.markdown(
        "Ask in plain English — MADBOOTS routes each question to the right source:\n"
        "- **📊 Squad & player** — answered from the analytics, with a **✓/⚠** trust line.\n"
        "- **👑 Captain & transfer** — includes **Confidence** (a heuristic, e.g. *72/100 · Medium*) plus "
        "**Edge ✓** and **Risk ⚠**, all computed from the data.\n"
        "- **📖 FPL rules** — from a curated knowledge base (also **✓**).\n"
        "- **ℹ️ General tactics** — useful advice, clearly marked *not checked against your data*.\n\n"
        "Things to try (copy-paste):"
    )
    st.code(
        'build me a squad for £100m with 3 differentials\n'
        'best differential midfielders under £8m\n'
        'is Haaland worth the money?\n'
        "Haaland's history                   # a player's season record (past seasons + per-GW from GW1)\n"
        'what should I do this week for my-team?\n'
        'who should I captain from my-team?\n'
        'how does bench boost work?          # a rules question → ✓ from the knowledge base\n'
        'how do transfers and hits work?     # a rules question → ✓\n'
        'when does Arsenal play next?',
        language=None,
    )
    st.markdown(
        "A **build** answer offers **Use this squad →** so it drops into *My Squad* to tweak. After any "
        "recommendation, try *\"Why?\"*, *\"What's the risk?\"* or *\"Who's second best?\"*."
    )

with st.expander("7 · Your team  →  **🔄 Synced · 💾 Backup · 🔢 Import**"):
    st.markdown(
        "Everything to do with your team lives in **one place** — the **⚙ Your team** panel on **My Squad**:\n"
        "- **🔄 Synced to your account** — when you're signed in, your team **follows you across devices** and "
        "**every edit saves automatically** — no manual save, nothing to remember.\n"
        "- **🔢 Import by Manager-ID** — load your real FPL team by its numeric ID (from your team's URL); "
        "available after the **GW1 deadline (2026-08-21)**, when picks become public.\n"
        "- **📤 Upload** — restore a saved `squad.json`.\n"
        "- **💾 Download** `squad.json` — a portable local backup (re-upload it any time, or on another device).\n\n"
        "*Whatever you import, upload or build **becomes your team** and syncs to your account. `squad.json` is your "
        "portable backup and safety net.*"
    )

with st.expander("8 · Tell us what you think  →  the **📣 Feedback** tab"):
    st.markdown(
        "Testing the beta? We'd love to hear from you — the **📣 Feedback** tab (bottom of the sidebar) is a quick "
        "form:\n"
        "- **👍 What worked? · 🐛 What broke? · 💡 What should we add?**\n"
        "- Leave your **email** for a reply or to join the founding-tester list.\n"
        "- Prefer **🐙 GitHub**? You can still open an issue."
    )

with st.expander("9 · MadBoots Explainer  →  a plain-English glossary"):
    # ADR-111: one expander with category subheaders — everything visible so Ctrl-F finds any term (Streamlit
    # expanders can't nest). The terms are reconciled to the app's real meanings.
    st.caption("A plain-English guide to the terms, stats and tools in MADBOOTS. Use your browser's find (⌘/Ctrl-F) "
               "to jump to a term.")
    st.markdown(
        "**⚽ FPL basics**\n"
        "- **GW — Gameweek** — one round of Premier League fixtures.\n"
        "- **Squad** — your 15 players: 2 GK · 5 DEF · 5 MID · 3 FWD.\n"
        "- **XI** — the 11 who start your gameweek.\n"
        "- **Bench** — your four substitutes.\n"
        "- **Captain (C)** — scores double points.\n"
        "- **Vice-Captain (VC)** — takes over if your captain doesn't play.\n"
        "- **Ownership** — the % of FPL teams that own a player.\n"
        "- **Differential 💎** — a relatively low-owned player.\n"
        "- **Essential 👑** — a highly-owned or strongly-recommended player.\n"
    )
    st.markdown(
        "**📊 Stats & analytics**\n"
        "- **xP — Expected Points** — MADBOOTS' projection of a player's FPL points.\n"
        "- **xG — Expected Goals** — the quality + quantity of a player's goal-scoring chances.\n"
        "- **xA — Expected Assists** — the chances they create for teammates.\n"
        "- **xGI — Expected Goal Involvement** — xG + xA.\n"
        "- **Value/£m** — expected output relative to price.\n"
        "- **Form** — recent FPL performance.\n"
        "- **Defensive Contribution** — defensive actions that earn extra FPL points.\n"
        "- **Clean Sheet** — the team concedes no goals while the player is on the pitch.\n"
        "- **Projected xP** — expected points for a future gameweek (or group of gameweeks).\n"
        "- **Over/Under-performance** — actual output vs what the underlying numbers suggest.\n"
    )
    st.markdown(
        "**🎯 MadBoots tools & ratings**\n"
        "- **Confidence** — how strongly the data supports a recommendation (a heuristic, not a probability).\n"
        "- **Edge ✓** — the factors *supporting* a recommendation.\n"
        "- **Risk ⚠** — the factors that could work *against* it.\n"
        "- **Quality Rating 🟢🔴** — a *relative* ranking against the players currently shown; it changes as you "
        "filter, the underlying number doesn't.\n"
        "- **Fixture Difficulty** — how favourable a team's upcoming fixtures are.\n"
        "- **Radar 🎯** — finds players from teams with favourable upcoming fixture runs.\n"
        "- **Boot Battle ⚔️** — compares two same-position players side by side, the better stat highlighted "
        "(from any Player Card, on Players and My Squad).\n"
    )
    st.markdown(
        "**🔄 Squad decisions**\n"
        "- **Transfer** — replaces a player in your squad with another.\n"
        "- **Substitute** — changes your starting XI using a player already on your bench.\n"
        "- **Bank** — money available to spend on transfers.\n"
        "- **Legal XI** — a starting XI that satisfies the FPL formation rules.\n"
        "- **Wildcard** — unlimited transfers for a gameweek with no hits.\n"
        "- **Free Hit** — a one-gameweek squad change that reverts afterwards.\n"
        "- **Bench Boost** — all 15 players score that gameweek.\n"
        "- **Triple Captain** — your captain scores triple, not double.\n"
    )
    st.markdown(
        "**🧪 Squad Lab**\n"
        "- **Archetype** — a selection preference: Cheap · Premium · Differential.\n"
        "- **Objective** — what the optimiser maximises: xP · Points · Value · xGI.\n"
        "- **Build mode** — **Balanced** (a balanced squad) · **Weekly** (a cheaper playing bench) · **Bench "
        "Boost** (maximise all 15).\n"
        "- **Declared bench** — tells the optimiser which four players to put on the bench.\n"
    )
    st.markdown(
        "**🤖 AI & trust**\n"
        "- **Grounded** — the answer is based on MADBOOTS' data, not an AI guess.\n"
        "- **✓ Checked** — checked against the relevant data.\n"
        "- **⚠ Caution** — contains uncertainty or something not fully data-verified.\n"
        "- **Local AI** — MADBOOTS can use a *local* Ollama model to narrate the analytics (available when you run "
        "it yourself). The AI explains the numbers; it doesn't decide them or make them up. The hosted app runs "
        "**data-only** — you get the full plan and numbers without the written narration.\n\n"
        "**The analytics decide. The AI explains. You make the call.**"
    )

st.divider()
st.markdown(
    "#### Good to know\n"
    "- **🕐 Data freshness** — each tab shows *N players · data as of …*, so you can see how current the data is. "
    "The hosted app serves a **committed snapshot** (it updates on redeploy); running **locally**, the sidebar "
    "**🔄 Refresh data** button pulls the latest FPL data on the spot.\n"
    "- **📅 Preseason** — ownership works now; **transfer momentum, in-season form and live picks light up at GW1 "
    "(2026-08-21)**.\n"
    "- **👥 Crowd signals** — useful context, not truth. The analytics decide; the crowd is context.\n"
    "- **🟢🔴 Ratings** — on **Players → Clean sheets / xG**, the rating is *relative to the players shown* (best "
    "20% 🟢 … worst 20% 🔴) and re-scales as you filter; the raw number is always the truth.\n"
    "- **🏠 New here?** The **Home** tab has the one-screen overview."
)
