"""Tests for the feedback helpers — the mailto builder (US-307) + the relay-result reader (US-308 fix)."""

from urllib.parse import parse_qs, urlparse

import pytest

from src.web_streamlit.feedback import feedback_mailto, relay_result


class _Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def test_relay_result_reads_formsubmit_success_flag():
    # a stalled relay (address not confirmed) → NOT ok, surface the message (the bug this fixes)
    ok, note = relay_result(_Resp(200, {"success": "false", "message": "Please confirm your email address"}))
    assert ok is False and note == "Please confirm your email address"
    # delivered — success as a string or a bool
    assert relay_result(_Resp(200, {"success": "true"}))[0] is True
    assert relay_result(_Resp(200, {"success": True}))[0] is True


def test_relay_result_treats_non_json_2xx_as_sent_and_4xx_as_failure():
    assert relay_result(_Resp(200, None))[0] is True                 # a Sheet sink returning "ok" (non-JSON)
    ok, note = relay_result(_Resp(404, None))
    assert ok is False and "404" in note


def _parts(href):
    u = urlparse(href)
    q = parse_qs(u.path.split("?", 1)[1]) if "?" in u.path else parse_qs(u.query)
    return u, q


def test_mailto_targets_the_inbox_with_a_template_when_empty():
    href = feedback_mailto("hello@madboots.com")
    assert href.startswith("mailto:hello@madboots.com?")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["MADBOOTS beta feedback"]          # no page → plain subject
    assert "What worked" in q["body"][0]                             # a template body to fill in


def test_mailto_prefills_message_page_and_version():
    href = feedback_mailto("a@b.com", "Target list is great", page="Fixtures", version="0.0.1")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["MADBOOTS beta feedback — Fixtures"]
    body = q["body"][0]
    assert "Target list is great" in body                           # the typed message
    assert "page: Fixtures" in body and "version: 0.0.1" in body    # the footer


def test_mailto_ignores_the_not_sure_page_sentinel():
    href = feedback_mailto("a@b.com", "hi", page="(not sure)", version="0.0.1")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["MADBOOTS beta feedback"]          # no "— (not sure)" in the subject
    assert "page:" not in q["body"][0] and "version: 0.0.1" in q["body"][0]


def test_mailto_url_encodes_spaces_and_newlines():
    href = feedback_mailto("a@b.com", "line one\nline two with spaces")
    assert " " not in href and "\n" not in href                     # everything is percent-encoded


# ---- a refusal must carry the relay's own words too (ADR-262) ----------------

class _Refusal:
    """A relay that says no *and says why* — which is the normal case, not an edge one."""

    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


def test_a_refusal_carries_the_reason_the_relay_gave():
    """⭐⭐ **ADR-231 promised the relay's own verdict, and delivered it only on success.**

    A 200 carrying `success: false` surfaced its `message`; a 403 was flattened to its status code. ⚠️ *The
    one response nobody could diagnose was the one that had already been diagnosed for us* — FormSubmit
    answers a server-side POST with 403 **and a sentence naming the cause**, and it never reached anyone.
    """
    ok, note = relay_result(_Refusal(403, {"message": "You are posting from a web server, not a browser."}))
    assert ok is False
    assert "403" in note
    assert "web server" in note, "the status code alone is not a diagnosis"


def test_a_refusal_reads_plain_text_when_there_is_no_json():
    ok, note = relay_result(_Refusal(429, text="Rate limit exceeded for this form."))
    assert ok is False
    assert "Rate limit exceeded" in note


@pytest.mark.parametrize("field", ["message", "error", "detail"])
def test_the_reason_is_found_under_any_of_the_usual_keys(field):
    """⚠️ Relays disagree about what to call it, and guessing one name would work for one vendor only."""
    _, note = relay_result(_Refusal(400, {field: "the form is not activated"}))
    assert "not activated" in note


def test_an_html_error_page_is_not_repeated_as_an_explanation():
    """⚠️ A proxy's HTML is boilerplate, not a reason. ⭐ *Saying nothing beats saying `<html>`.*"""
    _, note = relay_result(_Refusal(502, text="<html><head><title>502 Bad Gateway</title></head></html>"))
    assert "<" not in note
    assert "502" in note


def test_a_body_that_cannot_be_read_at_all_still_reports_the_status():
    """⭐ *A diagnostic that can itself fail turns a reported error into a hidden one.*"""

    class _Hostile:
        status_code = 500

        @staticmethod
        def json():
            raise RuntimeError("boom")

        @property
        def text(self):
            raise RuntimeError("boom")

    ok, note = relay_result(_Hostile())
    assert ok is False
    assert "500" in note


def test_a_long_refusal_is_trimmed_rather_than_dumped():
    _, note = relay_result(_Refusal(403, {"message": "x" * 4000}))
    assert len(note) < 400


def test_a_refusal_with_no_explanation_reads_exactly_as_before():
    """⚠️ The old wording is load-bearing — a silent relay must not gain a dangling dash."""
    _, note = relay_result(_Refusal(403, text=""))
    assert note == "the service returned HTTP 403"
