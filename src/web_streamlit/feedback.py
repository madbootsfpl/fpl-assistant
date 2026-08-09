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


def relay_result(response) -> tuple[bool, str]:
    """Interpret a form-relay POST response as `(ok, note)` — so the form shows the *real* result, not a
    blind "sent" (the bug that hid a stalled relay).

    A **form-to-email relay** (FormSubmit's `/ajax/` endpoint, Web3Forms) replies `{"success": true/"true",
    "message": …}`; a `success` that isn't truthy means it **didn't** forward — most often the target address
    isn't **activated** yet (FormSubmit emails a one-time confirmation link that must be clicked). We surface
    that `message` instead of a false success. A **non-JSON 2xx** (a Google-Sheet Apps Script returning "ok")
    counts as sent; a **4xx/5xx** is a failure. Pure — no Streamlit."""
    status = getattr(response, "status_code", 200)
    if status >= 400:
        return False, f"the service returned HTTP {status}"
    try:
        data = response.json()
    except Exception:
        return True, ""                                  # non-JSON 2xx (e.g. a Sheet sink) → treat as sent
    if isinstance(data, dict) and "success" in data:
        ok = str(data.get("success")).strip().lower() == "true"
        return ok, "" if ok else str(data.get("message") or "the relay didn't accept the submission")
    return True, ""                                      # 2xx JSON with no success flag → treat as sent
