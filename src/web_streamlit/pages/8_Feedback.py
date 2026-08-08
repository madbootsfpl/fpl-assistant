"""Feedback — a low-friction way for beta testers to tell us what worked / broke (Sprint 102, ADR-087).

An in-app form that POSTs to the owner's own sink (`FPL_FEEDBACK_WEBHOOK` — e.g. a Google Apps Script), so
non-devs don't need a GitHub account. Best-effort: it degrades to a GitHub-issue link when the webhook isn't
configured or the POST fails. A "Join the beta" link points to the owner's signup form (`FPL_SIGNUP_URL`) for
the founding-tester email list. No user data is persisted on our infra — the POST goes to the owner's sink.
"""

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

import requests
import streamlit as st

from src.web_streamlit.access import require_access, secret

_GITHUB_ISSUE = "https://github.com/tesheridan/fpl-assistant/issues/new"
# The pages a tester might be reporting about (US-306) — so feedback carries where it happened.
_PAGES = ("(not sure)", "Home", "Players", "Fixtures", "Squads", "Ask", "News", "Trending", "Help")


def _app_version() -> str:
    """The installed app version (pyproject), or 'unknown' if the package metadata isn't found."""
    try:
        return version("fpl-assistant")
    except PackageNotFoundError:
        return "unknown"

st.set_page_config(page_title="Feedback · FPL Assistant", page_icon="⚽", layout="wide")
require_access()          # opt-in beta gate (ADR-087)
st.title("📣 Feedback")
st.caption("Testing the beta? Tell us what worked, what broke, or what you'd love next — it goes straight to "
           "the team. Thank you 🙏")

signup = secret("FPL_SIGNUP_URL")
if signup:
    st.link_button("✋ Join the beta (founding testers)", signup,
                   help="Sign up with your email — founding testers get free access as the app grows.")

with st.form("feedback", clear_on_submit=True):
    message = st.text_area("Your feedback", placeholder="What worked? What broke? What would you add?",
                           height=140)
    page = st.selectbox("Which page?", _PAGES,
                        help="Where did this happen? Helps us find it faster.")
    email = st.text_input("Email (optional)",
                          help="Only if you'd like a reply, or to join the founding-tester list.")
    sent = st.form_submit_button("Send feedback")

if sent:
    if not message.strip():
        st.warning("Add a note first, then send.")
    else:
        webhook = secret("FPL_FEEDBACK_WEBHOOK")
        if not webhook:
            st.info(f"In-app feedback isn't wired up yet — please [open a GitHub issue]({_GITHUB_ISSUE}) "
                    "instead. Thanks!")
        else:
            # US-306: enrich with where/when/what-version so a report carries context (ADR-087 intent).
            payload = {
                "message": message.strip(),
                "email": email.strip(),
                "source": "fpl-assistant-beta",
                "page": page,
                "version": _app_version(),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            try:
                requests.post(webhook, json=payload, timeout=6)
                st.success("Thanks — your feedback was sent! 🎉")
            except requests.RequestException:
                st.error(f"Couldn't send just now — please [open a GitHub issue]({_GITHUB_ISSUE}) instead.")

st.caption(f"Prefer GitHub? You can also [open an issue]({_GITHUB_ISSUE}).")
