"""Tests for the feedback mailto helper (US-307)."""

from urllib.parse import parse_qs, urlparse

from src.web_streamlit.feedback import feedback_mailto


def _parts(href):
    u = urlparse(href)
    q = parse_qs(u.path.split("?", 1)[1]) if "?" in u.path else parse_qs(u.query)
    return u, q


def test_mailto_targets_the_inbox_with_a_template_when_empty():
    href = feedback_mailto("fpl.assistant@proton.me")
    assert href.startswith("mailto:fpl.assistant@proton.me?")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["FPL Assistant beta feedback"]          # no page → plain subject
    assert "What worked" in q["body"][0]                             # a template body to fill in


def test_mailto_prefills_message_page_and_version():
    href = feedback_mailto("a@b.com", "Target list is great", page="Fixtures", version="0.0.1")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["FPL Assistant beta feedback — Fixtures"]
    body = q["body"][0]
    assert "Target list is great" in body                           # the typed message
    assert "page: Fixtures" in body and "version: 0.0.1" in body    # the footer


def test_mailto_ignores_the_not_sure_page_sentinel():
    href = feedback_mailto("a@b.com", "hi", page="(not sure)", version="0.0.1")
    q = parse_qs(href.split("?", 1)[1])
    assert q["subject"] == ["FPL Assistant beta feedback"]          # no "— (not sure)" in the subject
    assert "page:" not in q["body"][0] and "version: 0.0.1" in q["body"][0]


def test_mailto_url_encodes_spaces_and_newlines():
    href = feedback_mailto("a@b.com", "line one\nline two with spaces")
    assert " " not in href and "\n" not in href                     # everything is percent-encoded
