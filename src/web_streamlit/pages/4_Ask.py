"""Ask — a chat interface (ADR-052). Each turn is grounded + carries the ✓/⚠ trust line.

The analytics decide; a local LLM (optional) only narrates — without Ollama the answer is the decision
+ facts, exactly like the CLI. History is kept in `st.session_state` for the session.
"""

import streamlit as st

from src import ask
from src.ui.ask import render_ask

st.set_page_config(page_title="Ask · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Ask")
st.caption("Captaincy · transfers · your squad · comparisons · build a squad · best players · fixtures. "
           "The analytics decide; the answer is checked against the data.")

if "history" not in st.session_state:
    st.session_state.history = []          # [(question, rendered_answer), …]

# Replay the conversation so far.
for question, answer in st.session_state.history:
    st.chat_message("user").write(question)
    st.chat_message("assistant").code(answer, language=None)

prompt = st.chat_input("Ask a question…")
if prompt:
    answer = render_ask(ask.answer(prompt))
    st.session_state.history.append((prompt, answer))
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").code(answer, language=None)
