"""Does Streamlit's session survive a redirect away and back?

⭐ **This is the real question under Stage C, and it is not the one I first named.** PKCE solves the URL
fragment problem (the code arrives as `?code=`, which a server can see). What it does NOT solve is *state*:
PKCE requires the app to remember a `code_verifier` it generated BEFORE the redirect, and prove it AFTER.

If Streamlit treats the return trip as a fresh session, `st.session_state` is empty and the verifier is gone
— so the exchange cannot be completed and the whole flow is dead regardless of how well the database half
works. Nothing about the database proves or disproves this; it has to be run in a browser.
"""
import streamlit as st

st.title("session probe")

# A value planted before the redirect. If the session survives, it is still here afterwards.
if "planted" not in st.session_state:
    st.session_state["planted"] = None

st.write("**st.session_state['planted']:**", repr(st.session_state["planted"]))
st.write("**st.query_params:**", dict(st.query_params))

if st.button("Plant a verifier"):
    st.session_state["planted"] = "verifier-abc123"
    st.rerun()
