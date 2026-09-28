"""Answers about the app rather than the football.

`feedback` relays a tester's message to the sink (ADR-262).
"""


from src.service.requests import (
    FeedbackRequest,
)

#: ⚠️ **Six seconds was sized for a form relay and is too tight for the sink we can actually use.** A
#: Google Apps Script web app cold-starts, follows a redirect, and may send mail before answering — well
#: past six. ⭐ *A timeout tuned to a dependency we no longer have would report a working sink as
#: unreachable*, which is the most misleading failure available here (ADR-262).
#:
#: ⚠️ Deliberately not larger: this is a phone waiting on a spinner, and the caller must learn something
#: before a tester gives up on it.
_RELAY_TIMEOUT = 15


def feedback(request: FeedbackRequest) -> dict:
    """Relay a tester's note to the owner's own sink (ADR-231).

    ⭐⭐ **This exists because the secret cannot live in the client.** The web form POSTs straight to
    `FPL_FEEDBACK_WEBHOOK`; a phone holding that would ship it to every tester. So the server holds it and
    the phone holds nothing — which is the same reasoning that keeps the `service_role` key out of a mobile
    binary (ADR-211).

    ⚠️⚠️ **It never reports a blind "sent".** `relay_result` exists because that was a real bug: the form
    said *sent* while a relay silently refused, because the target address had never been activated. ⭐ *A
    success message that cannot fail is not a success message* — so the relay's own verdict comes back, and
    an unconfigured sink is reported as unconfigured rather than as success.

    ⚠️ **No rate limit, and that is a real gap while the API is unreachable and not after.** On localhost
    the only caller is the owner. The day this is hosted it becomes an open relay to his inbox, and a limit
    has to arrive with the hosting — noted in the ADR rather than left to be discovered.
    """
    request.validate()
    import os
    from datetime import UTC, datetime

    import requests

    from src.relay import relay_result

    webhook = os.environ.get("FPL_FEEDBACK_WEBHOOK")
    inbox = os.environ.get("FPL_FEEDBACK_EMAIL", "hello@madboots.com")
    if not webhook:
        # ⭐ An honest failure with a way through, not a shrug: the client can offer an email instead.
        return {"sent": False, "reason": "no feedback sink is configured on the server", "email": inbox}

    payload = {
        "message": request.message.strip(),
        "email": request.contact.strip(),
        "source": "madboots-mobile",
        "page": request.screen or "(not sure)",
        "version": request.version,
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        # ⚠️ **Both spellings, because the two relays disagree and the wrong one is silently ignored.**
        # FormSubmit reads `_subject`; Web3Forms reads `subject`. ⭐ *A field a relay does not recognise
        # does not fail — it just quietly produces an untitled email*, which is the kind of defect nobody
        # reports because the message still arrives (ADR-262).
        "_subject": f"MADBOOTS mobile feedback — {request.screen or 'general'}",
        "subject": f"MADBOOTS mobile feedback — {request.screen or 'general'}",
    }
    if key := os.environ.get("FPL_FEEDBACK_KEY"):
        payload["access_key"] = key
    origin = os.environ.get("FPL_FEEDBACK_ORIGIN", "https://madboots.streamlit.app")

    try:
        response = requests.post(webhook, json=payload,
                                 headers={"Origin": origin, "Referer": origin}, timeout=_RELAY_TIMEOUT)
    except requests.RequestException as exc:
        return {"sent": False, "reason": f"could not reach the feedback service ({exc.__class__.__name__})",
                "email": inbox}

    ok, note = relay_result(response)
    return {"sent": ok, "reason": note, "email": inbox}
