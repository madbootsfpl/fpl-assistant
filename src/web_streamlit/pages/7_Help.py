"""Help — a step-by-step guide to building your team with the assistant (ADR-068).

Static content only (markdown + expanders): no analytics/data dependency, so it renders even before a
refresh, and no input controls. It complements Home (the short overview) with a deeper recipe.
"""

import streamlit as st

st.set_page_config(page_title="Help · FPL Assistant", page_icon="⚽", layout="wide")
st.title("🧭 Help")
st.caption("A step-by-step recipe. The **analytics decide**; a local AI only *narrates* — and every "
           "answer is checked against the data (a ✓/⚠ trust line). Your squad lives in **your session** — "
           "download it to keep it (nothing is saved on the server).")

st.markdown(
    "**Quick start:** open **Squads** → *Build* → **Use this squad** → tweak it in *My Squad* → get your "
    "**AI Tips** for the week → check *Health*, *Transfer* and *Captain* → **Download** your `squad.json`. "
    "Prefer words? Do it all from **Ask**."
)

st.caption("Everything for your team lives on the **Squads** tab — switch **Build · My Squad · AI Tips · "
           "Chips · Health · Transfer · Captain** with the buttons at the top.")

with st.expander("1 · Build your squad  →  **Squads → Build**", expanded=True):
    st.markdown(
        "Pick a **budget** and shape the 15 with the options: **archetypes** (cheap / premium / "
        "differential), **include / exclude** specific players, a **declared bench**, the **objective** "
        "(xp / points / value / xgi), and a **build mode** (*Balanced*, *Weekly* = a cheap playing bench, "
        "*Bench Boost* = maximise all 15). Every ⓘ explains a control.\n\n"
        "When you like it: **Download** the `squad.json` (that file *is* your save) and/or **Use this "
        "squad →** to make it this session's active squad."
    )

with st.expander("2 · Make it yours  →  **Squads → My Squad**", expanded=True):
    st.markdown(
        "Your active squad as a **formation pitch**. Edit it: **rename**, **swap** any player "
        "(legality-checked), set the **bench** (pick 4). Every change updates your session and the "
        "**Download**. New team? Switch back to the **Build** view."
    )

with st.expander("3 · Check its health  →  **Squads → Health**"):
    st.markdown(
        "See your squad's **projected xP over the next 5 gameweeks**, the per-GW breakdown, and the "
        "**weak links** worth upgrading. This is the same engine the CLI uses — one honest xP number."
    )

with st.expander("4 · Plan your week & improve it  →  **Squads → AI Tips · Chips · Transfer · Captain**"):
    st.markdown(
        "**AI Tips** is the fastest answer — one grounded view of who to **captain**, any **lineup** "
        "change, one **transfer** to consider, and any **flagged** players (injuries / doubts), all checked "
        "against the data (a ✓/⚠ line). *(The AI narrates it if a local Ollama is running; otherwise you "
        "still get the full plan.)* Start there, then dig deeper:\n\n"
        "**Transfer** ranks the best single swaps by **XI improvement** (how much a change lifts your best "
        "legal XI) — set your **bank** with the slider, or ask for a **coordinated plan** of 2–3. "
        "**Apply** a swap to your session squad.\n\n"
        "**Captain** ranks who to (vice-)captain this gameweek by expected points, with the opponent + "
        "penalty duty, and a template-vs-differential steer. **Set as captain** to keep it.\n\n"
        "**Chips** tells you **when** to play each chip — **Triple Captain · Bench Boost · Free Hit · "
        "Wildcard** — from your squad's projected points over the chosen horizon (also checked, ✓/⚠). "
        "Fixture-run based for now; double/blank gameweeks and mini-league position sharpen it in-season."
    )

with st.expander("5 · Do your research  →  Players · Fixtures · Trending · News"):
    st.markdown(
        "- **Players** — the whole pool (filter by **team / position / player**, sort, page through all — "
        "the **table first**, a top-15 chart below) **plus** the stat views: over/under-performance · "
        "Defensive Contribution · clean sheets · xG (season-to-date). On **clean sheets / xG** a "
        "**🟢…🔴 quality rating** shows how a player stacks up *vs the players shown*. Switch views with the "
        "buttons at the top.\n"
        "- **Fixtures** — a colour-coded **difficulty ticker** (pick 1–8 gameweeks).\n"
        "- **Trending** — what the crowd's doing (most-owned · transferred in/out · in-form) + "
        "**Community Signals** (what r/FantasyPL is talking about).\n"
        "- **News** — official injury / doubt / return news, most serious first."
    )

with st.expander("6 · Ask the assistant  →  the **Ask** tab (plain English)"):
    st.markdown(
        "Type a question — the analytics answer and the ✓/⚠ line shows it was checked against the data. "
        "Things to try (copy-paste):"
    )
    st.code(
        'build me a squad for £100m with 3 differentials\n'
        'best differential midfielders under £8m\n'
        'is Haaland worth the money?\n'
        'what should I do this week for my-team?\n'
        'who should I captain from my-team?\n'
        'what transfer should I make for my-team?\n'
        'which of my-team\'s teams have the best fixtures?\n'
        'when does Arsenal play next?',
        language=None,
    )
    st.markdown(
        "A **build** answer offers **Use this squad →** so it drops into *My Squad* to tweak. Follow-ups "
        "work too: after a pick, ask *\"why?\"* or *\"and the second best?\"*."
    )

with st.expander("7 · Save your team  →  Download, upload, or import by manager-ID"):
    st.markdown(
        "Your squad is per-session (no accounts). **Download** the `squad.json` to keep it — re-**upload** "
        "it from the sidebar next time, or **import your real FPL team by manager-ID** (the sidebar; your "
        "team's numeric id from its URL — picks are public from the GW1 deadline). The same `squad.json` "
        "loads in the CLI too."
    )

st.divider()
st.markdown(
    "**Good to know.** The *N players · data as of …* caption on each tab shows how fresh the data is (the "
    "player count makes a stale snapshot obvious). This hosted app serves a **committed snapshot** — it "
    "updates when the app is redeployed, not when you refresh your own CLI. Running it **locally**, the "
    "sidebar **🔄 Refresh data** button pulls the latest FPL data on the spot. It's **preseason** now — "
    "ownership works, but **transfer momentum, in-season form and live picks light up at GW1 "
    "(2026-08-21)**. Crowd signals are a **lens, not truth**: the analytics decide, the crowd is context. "
    "On **Players → Clean sheets / xG**, the **🟢…🔴 Rating** is *relative to the players shown* (best 20% "
    "🟢 … worst 20% 🔴) with the percentile — so it re-scales as you filter; the raw number stays the truth. "
    "New here? The **Home** tab has the one-screen overview."
)
