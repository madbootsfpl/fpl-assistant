"""Ask — a chat interface (ADR-052). Each turn is grounded + carries the ✓/⚠ trust line.

The analytics decide; a local LLM (optional) only narrates — without Ollama the answer is the decision
+ facts, exactly like the CLI. History is kept in `st.session_state` for the session.
"""

import streamlit as st

from src import ask
from src.ui.ask import render_ask
from src.web_streamlit.squads import active_squad, set_active_squad
from src.web_streamlit.status import render_data_status

st.set_page_config(page_title="Ask · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("💬 Ask")
st.caption("Captaincy · transfers · your squad · comparisons · build a squad · best players · fixtures. "
           "The analytics decide; the answer is checked against the data.")

_active = active_squad()          # so "captain <its name>" / "analyse my team" use your loaded squad
if _active:
    st.caption(f"Answering about your active squad: **{_active.get('name', 'your squad')}**.")

if "history" not in st.session_state:
    st.session_state.history = []          # [(question, rendered_answer), …]

# A few starter prompts so a new user knows what to type (US-227). Copy one into the box below.
# Expanded until the first question, then it folds away so it doesn't crowd the conversation.
with st.expander("💡 Example questions — copy one into the box below",
                 expanded=not st.session_state.history):
    st.code(
        "what should I do this week for my-team?\n"
        "who should I captain from my-team?\n"
        "best differential midfielders under £8m\n"
        "is Haaland worth the money?\n"
        "what transfer should I make for my-team?\n"
        "which of my-team's teams have the best fixtures?\n"
        "when does Arsenal play next?",
        language=None,
    )

# Replay the conversation so far.
for question, answer in st.session_state.history:
    st.chat_message("user").write(question)
    st.chat_message("assistant").code(answer, language=None)

prompt = st.chat_input("Ask a question…")
if prompt:
    result = ask.answer(prompt, active_squad=_active)
    answer = render_ask(result)
    st.session_state.history.append((prompt, answer))
    # A "build me a squad" answer carries the 15 (ADR-062) — stash it so the adopt button below
    # survives the rerun; a non-build answer clears it (result.squad is None).
    st.session_state["built_squad"] = result.squad
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").code(answer, language=None)

# Adopt a built squad into the session (→ My Squad / Transfer / Captain), like Build Squad's button.
_built = st.session_state.get("built_squad")
if _built:
    if st.button(f"Use this squad → ({_built['name']})"):
        set_active_squad(_built)
        st.session_state["built_squad"] = None
        st.success(f"Set **{_built['name']}** as your active squad — tweak it in My Squad.")
