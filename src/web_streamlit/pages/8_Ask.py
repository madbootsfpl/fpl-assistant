"""Ask — a chat interface (ADR-052). Each turn is grounded + carries the ✓/⚠ trust line.

The analytics decide; a local LLM (optional) only narrates — without Ollama the answer is the decision
+ facts, exactly like the CLI. History is kept in `st.session_state` for the session.
"""

import streamlit as st

from src import ask
from src.ui.ask import render_ask
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status

st.set_page_config(page_title="Ask · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("Ask")
st.caption("Captaincy · transfers · your squad · comparisons · build a squad · best players · fixtures. "
           "The analytics decide; the answer is checked against the data.")

_active = active_squad()          # so "captain <its name>" / "analyse my team" use your loaded squad
if _active:
    st.caption(f"Answering about your active squad: **{_active.get('name', 'your squad')}**.")

if "history" not in st.session_state:
    st.session_state.history = []          # [(question, rendered_answer), …]

# Replay the conversation so far.
for question, answer in st.session_state.history:
    st.chat_message("user").write(question)
    st.chat_message("assistant").code(answer, language=None)

prompt = st.chat_input("Ask a question…")
if prompt:
    answer = render_ask(ask.answer(prompt, active_squad=_active))
    st.session_state.history.append((prompt, answer))
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").code(answer, language=None)
