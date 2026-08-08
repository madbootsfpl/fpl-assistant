"""Ask — a chat interface (ADR-052). Each turn is grounded + carries the ✓/⚠ trust line.

The analytics decide; a local LLM (optional) only narrates — without Ollama the answer is the decision
+ facts, exactly like the CLI. It's **conversational** (ADR-047/080): a `Context` is threaded in
`st.session_state`, so follow-ups ("why?", "and the next?") and pronouns ("is **he** worth it?") build on
the last turn. History is kept in `st.session_state` for the session.
"""

import streamlit as st

from src import ask
from src.storage import Storage
from src.ui.ask import render_ask
from src.web_streamlit.access import require_access
from src.web_streamlit.squads import active_squad, set_active_squad
from src.web_streamlit.status import render_data_status

st.set_page_config(page_title="Ask · FPL Assistant", page_icon="⚽", layout="wide")
require_access()          # opt-in beta gate (ADR-087)
render_data_status()
st.title("💬 Ask")
st.caption("Captaincy · transfers · your squad · comparisons · build a squad · best players · fixtures — the "
           "analytics decide and the answer is **checked** against the data (✓). It also explains **FPL "
           "rules** from a curated knowledge base (✓), and answers open **tactics** questions labelled "
           "**ℹ not verified**. Follow-ups build on the last turn — try *\"why?\"* or *\"compare him to …\"*.")

_active = active_squad()          # so "captain <its name>" / "analyse my team" use your loaded squad
if _active:
    st.caption(f"Answering about your active squad: **{_active.get('name', 'your squad')}**.")

if "history" not in st.session_state:
    st.session_state.history = []          # [(question, rendered_answer), …]
if "chat_context" not in st.session_state:
    st.session_state.chat_context = None   # the last conversational turn (ADR-047), threaded to converse

_EXAMPLES = [
    "what should I do this week for my-team?",
    "who should I captain from my-team?",
    "best differential midfielders under £8m",
    "is Haaland worth the money?",
    "what transfer should I make for my-team?",
    "how does bench boost work?",              # a rules question — answered from the curated KB, verified ✓
    "how do transfers and hits work?",         # ↑ (US-259/260, ADR-085)
    "when does Arsenal play next?",
]


def _ask(question):
    """Run a question through the grounded **conversational** pipeline and record the turn — shared by the
    chat box and the example buttons (US-234/248). Threads `chat_context` through `ask.converse`, so
    follow-ups + pronouns build on the last turn (ADR-047/080). A build answer carries the 15 (ADR-062);
    stash it for the adopt button, a non-build answer clears it (result.squad is None)."""
    store = Storage()
    try:
        result, ctx = ask.converse(question, st.session_state.chat_context,
                                    store=store, active_squad=_active)
    finally:
        store.close()
    st.session_state.chat_context = ctx
    st.session_state.history.append((question, render_ask(result)))
    st.session_state["built_squad"] = result.squad


# A few starter prompts — click one to ask it (US-234). Expanded until the first turn, then it folds away.
with st.expander("💡 Example questions — click one to ask it", expanded=not st.session_state.history):
    for i, example in enumerate(_EXAMPLES):
        if st.button(example, key=f"example_{i}", use_container_width=True):
            _ask(example)
            st.rerun()

# Replay the conversation so far. `wrap_lines` wraps long sentences while keeping the aligned tables/blocks
# readable (US-275).
for question, answer in st.session_state.history:
    st.chat_message("user").write(question)
    st.chat_message("assistant").code(answer, language=None, wrap_lines=True)

# Nudge the newest answer into view — the app runs in an iframe with same-origin access, so scroll the parent
# to the bottom after the history renders (US-275). A no-op / invisible when there's no history.
if st.session_state.history:
    st.iframe(
        "<script>setTimeout(function(){try{var w=window.parent;"
        "w.scrollTo({top:w.document.body.scrollHeight,behavior:'smooth'});}catch(e){}}, 120);</script>",
        height=1,
    )

prompt = st.chat_input("Ask a question…")
if prompt:
    _ask(prompt)
    st.rerun()

# Adopt a built squad into the session (→ My Squad / Transfer / Captain), like Build Squad's button.
_built = st.session_state.get("built_squad")
if _built:
    if st.button(f"Use this squad → ({_built['name']})"):
        set_active_squad(_built)
        st.session_state["built_squad"] = None
        st.success(f"Set **{_built['name']}** as your active squad — tweak it in My Squad.")
