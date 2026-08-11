"""Tests for the feedback helpers — the mailto builder (US-307) + the relay-result reader (US-308 fix)."""

from urllib.parse import parse_qs, urlparse

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
    href = feedback_mailto("fpl.assistant@proton.me")
    assert href.startswith("mailto:fpl.assistant@proton.me?")
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
