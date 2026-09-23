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
        # ⚠️ An HTML error page is boilerplate, not an explanation — saying nothing beats saying `<html>`.
        if said and not said.lstrip().startswith("<"):
            return f" — {said[:300]}"
    return ""
