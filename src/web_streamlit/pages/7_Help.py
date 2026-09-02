"""Help — a step-by-step guide to getting the most from MADBOOTS (ADR-068, revamped ADR-111).

Static content only (markdown + expanders): no analytics/data dependency, so it renders even before a
refresh, and no input controls. It complements Home (the short overview) with a deeper recipe + a glossary.
"""

import streamlit as st

from src.fpl_rules import RULES
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access

st.set_page_config(**brand.page_config("Help"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Help")
st.title("🧭 Help")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)

# US-448 (ADR-166) — 🎥 Maddie Explains folded in here as a second view rather than a second sidebar page.
# Both answer *"how does this app work?"*; the only difference is text versus video, which is a preference,
# not a topic. Two entries for one question is exactly the sidebar bloat the owner asked to reduce — and this
# removes one without pushing anything into a page that is already at its own ceiling.
_help_view = st.segmented_control("How would you like it?", ["📖 Read", "🎥 Watch"], default="📖 Read",
                                  key="help_view",
                                  help="The written walkthrough, or Maddie's 90-second explainers.") or "📖 Read"

if _help_view == "🎥 Watch":
    from src.web_streamlit import maddie

    @st.cache_data(ttl=900, show_spinner=False)
    def _cached_videos():
        return maddie.videos()

    st.caption(f"Short explainers — **90 seconds or less** — from **Maddie**, your MADBOOTS guide. "
               f"{brand.MANTRA} New clips land here as they're made.")
    st.divider()
    _videos = _cached_videos()
    for _i, _v in enumerate(_videos):
        st.subheader(_v["topic"])
        if _v.get("blurb"):
            st.caption(_v["blurb"])
        if _v.get("youtube_url"):
            st.video(_v["youtube_url"])
        else:
            st.info("🎬 Coming soon — this explainer is on its way.")
        if _i < len(_videos) - 1:
            st.divider()
    st.caption("Prefer to read? Switch to **📖 Read** above for the written guide + glossary.")
    st.stop()
st.caption(f"A step-by-step guide to getting the most from MADBOOTS. **{brand.MANTRA}** Every answer is checked "
           "against the underlying data with a **✓/⚠** trust line.")

st.markdown(
    "#### Quick start\n"
    "1. **🧩 My Squad ▸ Lab** → build your 15 → **Use this squad →**\n"
    "2. **🧩 My Squad** → your week on one screen: the answer, the pitch, captaincy, chips\n"
    "3. **🧩 My Squad ▸ Transfer** → the swaps worth making\n"
    "4. **🧩 My Squad ▸ DNA** → how the 15 grade out, and where the risk is\n"
    "5. **💾 Download** your `squad.json` backup"
)

st.caption("Your team lives on the **🧩 My Squad** tab — switch **My Squad · DNA · Leagues · Lab** with "
           "the buttons at the top. The first of those leads with your squad: the projected points, then the "
           "pitch — and under it one selector for **This week · Captain · Transfer · Chips**, so the pitch "
           "stays on screen while you switch between them. **🏠 Home** shows a ⏳ **live deadline "
           "clock** that turns 🟠 then 🔴 as it nears — a reminder to set your captain, transfers and chips before "
           "the gameweek locks.")

with st.expander("🧪 1 · Build your squad  →  **My Squad ▸ Lab**", expanded=True):
    st.markdown(
        "Build your 15 with:\n"
        "- 💷 **Budget & shape** — spend to your budget across 2 GK · 5 DEF · 5 MID · 3 FWD.\n"
        "- 🏷️ **Archetypes** — Cheap · Premium · Differential.\n"
        "- 👥 **Players** — include or exclude specific players.\n"
        "- 🪑 **Bench** — declare your bench.\n"
        "- 🎯 **Objective** — xP · Points · Value · xGI.\n"
        "- ⚙ **Build mode** — **All-round (strong bench)** or **Strong XI (cheap bench)**. Two modes, not "
        "three: playing **Bench Boost**? Use All-round — under the chip all 15 score, so *maximise the XI* and "
        "*maximise all 15* become the same question.\n"
        "- ℹ️ **Every control** has an explanation (the ⓘ tooltips).\n\n"
        "When you're happy: **Use this squad →** makes it your active squad, and/or **💾 Download** the `squad.json` "
        "as a local backup."
    )

with st.expander("✏️ 2 · Make it yours  →  **My Squad**", expanded=True):
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
        "- **🪑 Set bench** — choose all four bench players at once.\n\n"
        "*Bringing in a **new** player is a **transfer**, and that lives on **My Squad ▸ Transfer** — see step 4.*\n\n"
        "The summary's **Projected XI** includes your **captain's ×2 — for the next gameweek only** (captaincy is "
        "re-picked each week). Your squad is **saved to your account and auto-synced across your devices** — no "
        "manual save (manage it in the **⚙ Your team** panel on My Squad). *(**Substitute** = a lineup change; "
        "**Transfer** = a new player — they're separate.)* Need a new squad? Head back to **My Squad ▸ Lab**."
    )

with st.expander("🧬 3 · Grade the 15  →  **My Squad ▸ DNA**"):
    st.markdown(
        "Your squad's fingerprint, and the health check under it — how it is projected to perform over the "
        "next **1–10 gameweeks**:\n"
        "- **📈 Projected xP** — your squad's expected points.\n"
        "- **📅 GW breakdown** — the projection for each gameweek.\n"
        "- **⚠️ Weak links** — players worth considering for an upgrade.\n"
        "- **One xP number** — the same engine the CLI uses, so the projection stays consistent."
    )

with st.expander("🗓️ 4 · Plan your week  →  **My Squad**, one answer at a time"):
    st.markdown(
        "All of it is on the **My Squad** screen, under one selector below the pitch — so the pitch stays on "
        "screen while you move between the four answers.\n\n"
        "**🤖 This week** — the default, and your fastest gameweek plan: **👑** who to captain · **🔁** any lineup "
        "change · **🔄** one transfer to consider · **🚑** injuries and doubts, all **✓/⚠** checked against the "
        "data. *You always get the full data-driven plan; where a local AI is available it adds a written "
        "narration — the hosted app is data-only, which is why the answer appears instantly here and waits "
        "behind a button when you run it yourself.*\n\n"
        "**👑 Captain** — your 15 ranked by expected points, with opponent · penalty duty · "
        "ownership (💎 differential → 👑 essential), and a **Confidence** score with the reasoning. To set one, "
        "tap the shirt on the pitch → **👑 Make … captain**.\n\n"
        "**🎴 Chips** — behind a button: *when* to play **Triple Captain · Bench Boost · Free Hit "
        "· Wildcard**. A chip expires at the end of the half-season, so this looks across **every gameweek left "
        "before that deadline** rather than your chosen horizon — which is why it is a click, not automatic.\n\n"
        "**🔄 Transfer** — the fourth answer, and the biggest: the best single "
        "swaps ranked by how much they improve your legal XI. Set your **bank** with the slider, or ask for a "
        "coordinated **2–3 transfer plan**. **Apply** one swap, or **Apply this plan →** for all at once."
    )

with st.expander("🔎 5 · Do your research  →  **👟 Players · 📅 FDR · 🧬 Team DNA · 📈 Trending · 📡 Signals**"):
    st.markdown(
        "- **👟 Players** — six views, switched at the top. **Pool** (filter by team / position / player, sort, "
        "browse — a table plus a top-15 chart) · **Value** (the whole pool positioned by points-per-pound, not "
        "ranked fifteen deep) · **🪪 Card** (photo · fixtures · Projected xP · position-adaptive stats, with "
        "**⚔️ Boot Battle** to compare a same-position player side by side) · **🎯 Radar** (players from the "
        "easiest-run teams — filter by position, cap the price, sort by xP or Val/£m) · **🔭 Scout** · "
        "**History**. A **🟢…🔴 quality rating** shows how a player compares with those currently shown.\n"
        "- **🔭 Players ▸ Scout** — the five stat boards (**Set pieces · Over/under · DefCon · Clean sheets · "
        "xG · xA**) behind one selector, led by a **worth a look** shortlist of the players standing out on "
        "**two or more** of them at once. *Worth a look, not worth points* — two of those signals are not "
        "priced into xP, so the shortlist points you somewhere, it does not rank the answer.\n"
        "- **📅 FDR** — every club's next **1–8 GWs** on a colour-coded difficulty ticker, easiest run first; "
        "scope it to **your squad**.\n"
        "- **🧬 Team DNA** — how strong every club is at both ends, graded at a glance, and the players to "
        "target there.\n"
        "- **📈 Trending** — what the crowd is **doing**, in numbers: **👀 Worth noticing** first (the patterns "
        "that need two boards at once — in form but still under-owned · a bandwagon forming · the template "
        "breaking up), then the four boards themselves: most-owned · transferred in/out · in-form.\n"
        "- **📡 Signals** — what is being **said**, most reliable first: official FPL injuries and returns · "
        "a sell-off we can't explain · media headlines · r/FantasyPL chatter (a mention count, not truth)."
    )

with st.expander("☁ 6 · Your team  →  **🔄 Synced · 💾 Backup · 🔢 Import**"):
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

with st.expander("📣 7 · Tell us what you think  →  the **Feedback** tab"):
    st.markdown(
        "Testing the beta? We'd love to hear from you — the **📣 Feedback** tab (bottom of the sidebar) is a quick "
        "form:\n"
        "- **👍 What worked? · 🐛 What broke? · 💡 What should we add?**\n"
        "- Leave your **email** for a reply or to join the founding-tester list.\n"
        "- Prefer **🐙 GitHub**? You can still open an issue."
    )

with st.expander("📖 8 · MADBOOTS Explainer  →  a plain-English glossary"):
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
        "- **Scout 🔭** — the five stat boards in one place, led by a shortlist of players standing out on two "
        "or more at once. *Worth a look, not worth points*: some of those signals are not priced into xP.\n"
        "- **Worth noticing 👀** — on Trending: the patterns that need two boards at once, so a player can top "
        "none of the four and still be the name worth your attention. It says what the crowd is **doing**, "
        "never why — the *why* belongs to 📡 Signals, where it is sourced.\n"
        "- **Player DNA 🧬 / Team DNA 🧬** — an eight-axis fingerprint, each axis a percentile against the "
        "relevant pool (players in a position; the 20 clubs). Where a pool cannot rank someone it says so "
        "rather than drawing a shape.\n"
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
        "**🧪 Squad Lab** *(My Squad ▸ Lab)*\n"
        "- **Archetype** — a selection preference: Cheap · Premium · Differential.\n"
        "- **Objective** — what the optimiser maximises: xP · Points · Value · xGI.\n"
        "- **Build mode** — **All-round (strong bench)** maximises all 15, giving you a bench that can actually "
        "play; **Strong XI (cheap bench)** moves that money into the XI and buys a deliberately cheap bench.\n"
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
        f"**{brand.MANTRA}**"
    )

# The "Ask the assistant" step was removed here (ADR-168 retired Ask as a page, and this guide had gone on
# teaching it — with nine copy-paste examples for a tab that is not there). Its two useful halves both have
# homes: the grounded gameweek answer is step 4's **🤖 This week**, and the rules knowledge base is the
# section immediately below, where you can read it without having to guess the question first.
# ---- FPL rules (ADR-168) ---------------------------------------------------------------------------
# `fpl_rules.RULES` carries 21 curated topics — scoring, chips, autosubs, deadlines, price changes. Until now
# the ONLY way to read them was to type a question at Ask, which is a strange place to keep a reference: you
# had to know what to ask before you could find out. Retiring Ask made this necessary; it is also just better.
st.divider()
st.subheader("📖 FPL rules — how the game scores")
st.caption("The rules MADBOOTS checks its answers against. Not our opinion — the game's own scoring, "
           "chip and transfer rules, kept in one place.")

_TOPIC_LABEL = {"scoring": "Scoring", "clean_sheets": "Clean sheets & keepers", "bonus": "Bonus points",
                "defensive_contribution": "Defensive Contribution", "chips": "Chips",
                "chip_limits": "Chips — one per gameweek", "transfers": "Transfers & hits",
                "preseason_transfers": "Preseason transfers", "price_changes": "Price changes",
                "team_value": "Team value", "squad_rules": "Squad rules", "formation": "Formation",
                "captain": "Captain & vice", "autosubs": "Automatic substitutions",
                "bench_points": "Bench points", "deadline": "Deadlines", "gameweeks": "Double & blank gameweeks",
                "flags": "Injury flags", "wildcard_timing": "Wildcard timing", "leagues": "Leagues",
                "ranking": "Ranking"}
for _rule in RULES:
    with st.expander(_TOPIC_LABEL.get(_rule["topic"], _rule["topic"].replace("_", " ").title())):
        st.markdown(_rule["fact"].replace("\n", "  \n"))

st.divider()
st.markdown(
    "#### Good to know\n"
    "- **🕐 Data freshness** — each tab shows *N players · data as of …*, so you can see how current the data is. "
    "The hosted app serves a **committed snapshot** (it updates on redeploy); running **locally**, the sidebar "
    "**🔄 Refresh data** button pulls the latest FPL data on the spot.\n"
    "- **📅 Early season** — some numbers need played gameweeks before they mean anything. A board that "
    "cannot answer yet **says so and names the season it is showing instead**, rather than going blank or "
    "quietly showing you a zero.\n"
    "- **👥 Crowd signals** — useful context, not truth. The analytics decide; the crowd is context.\n"
    "- **🟢🔴 Ratings** — on **Players ▸ Scout ▸ Clean sheets / xG · xA**, the rating is *relative to the "
    "players shown* (best 20% 🟢 … worst 20% 🔴) and re-scales as you filter; the raw number is always the "
    "truth.\n"
    "- **🏠 New here?** The **Home** tab has the one-screen overview."
)
