"""Reading a form-relay's answer — shared by both feedback routes.

⭐⭐ **This lives outside `web_streamlit/` because the API needs it and the API image does not ship that
package.** It began life next to the Streamlit feedback page, and the mobile endpoint imported it from
there. That import was invisible locally — the package is right there in the repo — and fatal in the
container, where `.dockerignore` excludes it: every mobile feedback POST answered **HTTP 500**.

⚠️ *A function being pure is not the same as a function being reachable.* `relay_result` never touched
Streamlit; it was still unimportable from the one place that mattered, because the deployed unit is not
the repo.
"""


def relay_result(response) -> tuple[bool, str]:
    """Interpret a form-relay POST response as `(ok, note)` — so the caller shows the *real* result, not a
    blind "sent" (the bug that hid a stalled relay).

    A **form-to-email relay** (FormSubmit's `/ajax/` endpoint, Web3Forms) replies `{"success": true/"true",
    "message": …}`; a `success` that isn't truthy means it **didn't** forward — most often the target address
    isn't **activated** yet (FormSubmit emails a one-time confirmation link that must be clicked). We surface
    that `message` instead of a false success. A **non-JSON 2xx** (a Google-Sheet Apps Script returning "ok")
    counts as sent; a **4xx/5xx** is a failure. Pure — no Streamlit, and now no Streamlit *package* either.
    """
    status = getattr(response, "status_code", 200)
    if status >= 400:
        # ⚠️⚠️ **The relay explains itself in the body, and this used to throw it away.** ADR-231's whole
        # claim is that the relay's *own verdict* comes back — and that held for a 200 carrying
        # `success: false` while a 4xx was flattened to its status code. ⭐ *The one response we could not
        # diagnose was the one that had already been diagnosed for us*: FormSubmit answers a server-side
        # POST with 403 **and a sentence naming the reason**, which never reached anyone (ADR-262).
        return False, f"the service returned HTTP {status}{_why(response)}"
    try:
        data = response.json()
    except Exception:
        return True, ""                                  # non-JSON 2xx (e.g. a Sheet sink) → treat as sent
    if isinstance(data, dict) and "success" in data:
        ok = str(data.get("success")).strip().lower() == "true"
        return ok, "" if ok else str(data.get("message") or "the relay didn't accept the submission")
    return True, ""                                      # 2xx JSON with no success flag → treat as sent


def _why(response) -> str:
    """The relay's own explanation of a refusal, as a trailing clause — or nothing if it did not give one.

    ⚠️ **Defensive on purpose.** This runs on the failure path, where the body is least predictable: JSON,
    HTML, empty, or a megabyte of proxy boilerplate. ⭐ *A diagnostic that can itself fail turns a reported
    error into a hidden one* — so anything unreadable degrades to the bare status code we had before.
    """
    for read in (lambda: response.json(), lambda: response.text):
        try:
            data = read()
        except Exception:
            continue
        if isinstance(data, dict):
            said = data.get("message") or data.get("error") or data.get("detail")
        else:
            said = data
        said = " ".join(str(said or "").split())
        if not said:
            continue
        # ⚠️ An HTML error page is boilerplate, not an explanation — saying nothing beats saying `<html>`.
        # ⭐⭐ **But "nothing" was itself a wrong answer here.** A relay behind Cloudflare answers a blocked
        # server with an HTML challenge page, so suppressing markup suppressed the whole diagnosis: the app
        # said *"HTTP 403"* and stopped, when the page it was holding named the cause (ADR-262). So HTML is
        # **classified**, not echoed.
        if said.lstrip().startswith("<"):
            if (blocked := _challenge(said)) is not None:
                return f" — {blocked}"
            continue
        return f" — {said[:300]}"
    return ""


#: ⭐ Markers from the front doors that sit in front of form relays. ⚠️ Matched against an HTML body we
#: deliberately never show, purely to name *who* refused — a CDN blocking a datacenter IP is a completely
#: different problem from a form that is not activated, and the status code alone cannot tell them apart.
_CHALLENGES = (
    ("cloudflare", "the relay's CDN (Cloudflare) blocked this server, not the form itself — hosts on "
                   "datacenter IPs are refused before the request reaches the relay"),
    ("attention required", "the relay's CDN challenged this request as automated traffic"),
    ("just a moment", "the relay's CDN challenged this request as automated traffic"),
    ("access denied", "the relay's front door refused this server outright"),
)


def _challenge(html: str) -> str | None:
    """Name the CDN that refused us, from a page we will never show. `None` if it is ordinary boilerplate."""
    low = html.lower()
    for marker, said in _CHALLENGES:
        if marker in low:
            return said
    return None

