"""Feedback — a low-friction way for beta testers to tell us what worked / broke (Sprint 102, ADR-087).

An in-app form that POSTs to the owner's own sink (`FPL_FEEDBACK_WEBHOOK` — e.g. a Google Apps Script or a
form-to-email relay, US-308) so non-devs don't need a GitHub account. When no webhook is set (or a POST fails)
it degrades to a **pre-filled email** to `FPL_FEEDBACK_EMAIL` (US-307) — one click opens the tester's mail app —
with a GitHub-issue link as a last resort. A "Join the beta" link points to the owner's signup form
(`FPL_SIGNUP_URL`). No user data is persisted on our infra — the POST/email goes to the owner's own inbox/sink.
"""

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

import requests
import streamlit as st

from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access, secret
from src.web_streamlit.feedback import feedback_mailto, relay_result

_GITHUB_ISSUE = "https://github.com/tesheridan/fpl-assistant/issues/new"
# FormSubmit (and similar relays) reject requests with no Origin/Referer as an anti-abuse measure — and this
# form POSTs server-side (Streamlit's backend), so it must send one or the relay 403s with a "web server"
# error. Any https origin passes a non-domain-locked form; override via FPL_FEEDBACK_ORIGIN for your app URL.
_DEFAULT_ORIGIN = "https://fpl-assistant.streamlit.app"
# The pages a tester might be reporting about (US-306) — so feedback carries where it happened.
_PAGES = ("(not sure)", "Home", "Players", "Fixtures", "Squads", "Ask", "News", "Trending", "Help")


def _app_version() -> str:
    """The installed app version (pyproject), or 'unknown' if the package metadata isn't found."""
    try:
        return version("fpl-assistant")
    except PackageNotFoundError:
        return "unknown"

st.set_page_config(**brand.page_config("Feedback"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Feedback")
st.title("📣 Feedback")
st.caption("Testing the beta? Tell us what worked, what broke, or what you'd love next — it goes straight to "
           "the team. Thank you 🙏")

feedback_email = secret("FPL_FEEDBACK_EMAIL", "fpl.assistant@proton.me")

signup = secret("FPL_SIGNUP_URL")
if signup:
    st.link_button("✋ Join the beta (founding testers)", signup,
                   help="Sign up with your email — founding testers get free access as the app grows.")

# US-307: an always-available email route — opens the tester's mail app pre-addressed to the inbox.
st.link_button("✉ Email your feedback", feedback_mailto(feedback_email),
               help=f"Opens your mail app, pre-addressed to {feedback_email}.")

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
        # A one-click pre-filled email to the inbox — the fallback when there's no webhook, or a POST fails.
        mailto = feedback_mailto(feedback_email, message.strip(), page, _app_version())
        webhook = secret("FPL_FEEDBACK_WEBHOOK")
        if not webhook:
            st.info("In-app sending isn't set up — one click emails it to us (opens your mail app):")
            st.link_button("✉ Email this feedback", mailto)
        else:
            # US-306: enrich with where/when/what-version so a report carries context (ADR-087 intent).
            payload = {
                "message": message.strip(),
                "email": email.strip(),
                "source": "fpl-assistant-beta",
                "page": page,
                "version": _app_version(),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                # US-308: work with a free form-to-email relay too — FormSubmit reads `_subject`; Web3Forms
                # needs an `access_key` (only when FPL_FEEDBACK_KEY is set). A Google-Sheet sink ignores both.
                "_subject": f"{brand.NAME} beta feedback — {page}",
            }
            access_key = secret("FPL_FEEDBACK_KEY")
            if access_key:
                payload["access_key"] = access_key
            # Send an Origin/Referer so a relay accepts this server-side POST (see _DEFAULT_ORIGIN).
            origin = secret("FPL_FEEDBACK_ORIGIN", _DEFAULT_ORIGIN)
            headers = {"Origin": origin, "Referer": origin}
            try:
                resp = requests.post(webhook, json=payload, headers=headers, timeout=6)
            except requests.RequestException:
                analytics.track("error", component="feedback", page=page)
                st.error("Couldn't reach the feedback service — one click emails it to us instead:")
                st.link_button("✉ Email this feedback", mailto)
            else:
                ok, note = relay_result(resp)   # read the real result, not a blind "sent" (US-308 fix)
                if ok:
                    analytics.track("feedback_submitted", page=page)   # engagement (no message content)
                    st.success("Thanks — your feedback was sent! 🎉")
                else:
                    st.warning(f"The feedback service didn't accept it — **{note}**. "
                               "One click emails it to us instead:")
                    st.link_button("✉ Email this feedback", mailto)
                    st.caption("_Owner: if this says 'confirm your email', check the inbox for a FormSubmit "
                               "activation link and click it once; otherwise check the webhook address._")

st.caption(f"Prefer GitHub? You can also [open an issue]({_GITHUB_ISSUE}).")
