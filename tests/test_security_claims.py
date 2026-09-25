"""Claims the security docs make about the storage key (ADR-297).

⭐⭐ **This exists because a wrong claim was believed twice.** `SUPABASE_RLS.md` said a `sha256(email)`
key was *"not guessable — those users are effectively protected"*, in two places, and the sentence is
true of a random string and false of a hash of something other people know. ⚠️⚠️ *A reassuring sentence
in a security document is load-bearing: it is what lets the next reader stop looking.*
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RLS = ROOT / "docs" / "SUPABASE_RLS.md"
REVIEW = ROOT / "docs" / "00_Project" / "Security_Review.md"


def test_the_key_is_a_pure_function_of_the_email() -> None:
    """⭐ The finding itself, as arithmetic rather than prose.

    If this ever stops holding — a salt, a random token — the claim the docs are forbidden from making
    becomes true again, and this test is where that gets noticed.
    """
    from src.web_streamlit.auth import user_key

    email = "a.tester@example.com"
    assert user_key(email) == hashlib.sha256(email.encode()).hexdigest()[:32]
    # ⚠️ Deterministic across processes, with no secret involved: that is the whole problem.
    assert user_key(email) == user_key(" A.Tester@Example.COM ")


def test_no_document_calls_the_email_key_unguessable() -> None:
    """⚠️ The exact sentence, in any spelling, in either file.

    ⭐ *Two copies of one claim need a test that they agree, or one is already wrong and nobody knows*
    (ADR-281) — and here both copies were wrong together, which is worse: they corroborated each other.
    """
    bad = re.compile(
        r"sha256\(email\)[^.\n]{0,60}(not|un)[- ]?guessable|"
        r"(not|un)[- ]?guessable[^.\n]{0,60}sha256\(email\)",
        re.I,
    )
    for doc in (RLS, REVIEW):
        for line in doc.read_text().splitlines():
            # ⚠️⚠️ **A quotation of the wrong claim is not the wrong claim.** The first version of this
            # fired on the Security Review's own blockquote — the sentence it exists to refute — which
            # is the fourth time this session a guard has caught the prose explaining the guard
            # (ADR-261, ADR-280, ADR-290). ⭐ *A rule that cannot tell a claim from a quotation of it
            # forbids the correction along with the mistake.*
            if line.lstrip().startswith(">") or "🔴" in line or "was wrong" in line:
                continue
            assert not bad.search(line), (
                f"{doc.name} calls the email-derived key unguessable:\n  {line.strip()[:140]}"
            )


def test_the_review_states_what_currently_prevents_it() -> None:
    """⭐ A finding without its mitigation reads as either panic or nothing.

    ⚠️ What stands between this and an exploit is that the publishable key is server-side — and in
    particular **not in the APK**, which is the fact a reader most needs and would otherwise assume.
    """
    body = REVIEW.read_text()

    assert "not in the APK" in body or "not** in the mobile app" in body
    assert "delete_squad" in body, "the irreversible verb is not named"
    assert "Stage C" in body, "the actual fix is not named"


def test_the_review_says_what_it_did_not_cover() -> None:
    """⚠️⚠️ **A security review that lists only findings reads as a clean bill of health.**

    ⭐ *The scope is the most load-bearing paragraph in it* — no pen test, no dependency scan, and it
    read what `sql/setup.sql` says rather than what the live database does.
    """
    body = REVIEW.read_text().lower()

    for uncovered in ("penetration", "dependency", "not what is"):
        assert uncovered in body, f"the review does not say it skipped: {uncovered}"
