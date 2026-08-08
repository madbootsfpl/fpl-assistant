"""Pure helpers for the Feedback page (importable, so they're unit-testable — the page module
`pages/8_Feedback.py` can't be imported directly because of its numeric prefix).

`feedback_mailto` builds a pre-filled `mailto:` link to the feedback inbox (US-307) — the zero-setup
route to the owner's email when there's no webhook (Proton has no free SMTP, so the app can't send
directly). No Streamlit here — just string building.
"""

from urllib.parse import quote


def feedback_mailto(email: str, message: str = "", page: str = "", version: str = "") -> str:
    """A `mailto:` href to the feedback inbox, pre-filled with the message + a page/version footer.

    An empty `message` → a template body the tester fills in their own mail client (the always-available
    route); a submitted message → a one-click "email this to us". `page == "(not sure)"` (the picker's
    default) is treated as no page. Subject and body are URL-encoded, so spaces and newlines are safe.
    """
    subject = "FPL Assistant beta feedback"
    if page and page != "(not sure)":
        subject += f" — {page}"
    footer = " | ".join(part for part in (f"page: {page}" if page and page != "(not sure)" else "",
                                          f"version: {version}" if version else "") if part)
    body = message or "What worked? What broke? What would you add?"
    if footer:
        body += f"\n\n—\n{footer}"
    return f"mailto:{email}?subject={quote(subject)}&body={quote(body)}"
