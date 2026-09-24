"""The update manifest is a contract between a shell script and a Dart file (ADR-282).

⚠️⚠️ **Nothing else in the build would notice these two drifting apart.** `scripts/release_android.sh`
writes `version.json`; `mobile/lib/update_check.dart` reads it. They share no code, no types and no
language — ⭐ *the only thing holding them together is that someone remembered, and this file is what
replaces remembering.*

The failure is quiet in the worst way: renaming the field to `buildNumber` in one place leaves every
tester's app reading a missing key, deciding there is no update, and saying nothing.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_android.sh"
CHECK = ROOT / "mobile" / "lib" / "update_check.dart"


def _manifest_written() -> dict:
    """The JSON the release script writes, with its shell variables filled in."""
    body = re.search(r"cat > \"\$SITE/app/version\.json\" <<JSON\n(.*?)\nJSON", SCRIPT.read_text(), re.S)
    assert body, "the release script no longer writes version.json in a JSON heredoc"
    filled = re.sub(r"\$\{?(\w+)\}?", lambda m: {"next": "2", "code": "2002"}.get(m[1], "x"), body[1])
    return json.loads(filled)


def test_the_script_writes_every_field_the_app_reads() -> None:
    written = _manifest_written()
    read = set(re.findall(r"json\['(\w+)'\]", CHECK.read_text()))

    assert read, "update_check.dart reads no fields — the parser has moved somewhere else"
    assert read <= set(written), (
        f"the app reads {sorted(read - set(written))}, which the release script never writes"
    )


def test_build_is_a_number_because_the_app_compares_it() -> None:
    # ⚠️ Quoting it in the heredoc would make `(json['build'] as num?)` null, and a null build is read
    # as "no update" — ⭐ *the one wrong answer that looks exactly like a working check.*
    assert isinstance(_manifest_written()["build"], int)


def test_the_app_looks_where_the_script_puts_it() -> None:
    # ⚠️ The **default**, not the `--dart-define` name. A build override is for seeing the banner fire
    # locally; ⭐ *the shipped value is the only one nine testers will ever use.*
    src = CHECK.read_text()
    assert "const String kManifestUrl" in src, "kManifestUrl is gone"
    url = re.search(r"defaultValue: '([^']+)'", src) or re.search(
        r"const String kManifestUrl = '([^']+)'", src
    )
    assert url, "kManifestUrl has no literal url to check"
    # The script writes into "$SITE/app/"; the app must ask for that same path.
    assert url[1].endswith("/app/version.json"), url[1]


def test_the_script_runs() -> None:
    """⭐ A syntax error here is only ever found mid-release, with the keystore already loaded."""
    assert subprocess.run(["bash", "-n", SCRIPT], capture_output=True).returncode == 0


def test_the_release_script_declares_the_apk_content_type() -> None:
    """⚠️⚠️ **Cloudflare Pages does not know what a `.apk` is.**

    With no `Content-Type` it sends none at all, and Chrome renders 18MB of zip as text. ⭐ *The
    download does not fail — it succeeds into a wall of mojibake*, which reads as a broken site rather
    than a missing header, and it was a tester who found it, not the build.

    The fix is one `_headers` rule, and ⭐ *a one-line fix on a path nobody revisits is exactly the kind
    that vanishes in the next site rebuild* — so the script writes it and this pins that it still does.
    """
    script = SCRIPT.read_text()

    assert "_headers" in script, "the release script no longer writes a Cloudflare _headers file"
    assert "application/vnd.android.package-archive" in script, (
        "the APK content type is gone — Chrome will display the APK instead of downloading it"
    )
    # ⚠️ At the site root. Cloudflare reads `_headers` from the deploy root and nowhere else; one
    # written into `app/` is a file Cloudflare never looks at.
    assert 'root / "_headers"' in script or '"$SITE"' in script, (
        "_headers must be written at the site root, not beside the APK"
    )


def _merge_headers(initial: str | None) -> str:
    """Run the release script's `_headers` merge against a throwaway site folder."""
    block = re.search(r"python3 - \"\$SITE\" <<'PY'\n(.*?)\nPY\n", SCRIPT.read_text(), re.S)
    assert block, "the release script no longer writes _headers via an inline python block"
    site = Path(tempfile.mkdtemp())
    if initial is not None:
        (site / "_headers").write_text(initial)
    subprocess.run(["python3", "-c", block[1], str(site)], check=True)
    return (site / "_headers").read_text()


def test_headers_merge_writes_the_rule_from_nothing() -> None:
    assert "application/vnd.android.package-archive" in _merge_headers(None)


def test_headers_merge_updates_its_own_outdated_rule() -> None:
    """⭐⭐ **"Leave other people's config alone" must not become "never fix my own."**

    The first version skipped entirely when `/app/*.apk` was already present, so it kept serving a stale
    `filename=` it had written itself — ⚠️ *the same shape of bug as a cache that will not invalidate,
    and invisible for the same reason: the file looked configured.*
    """
    out = _merge_headers('/app/*.apk\n  Content-Type: text/plain\n  Content-Disposition: attachment; filename="old.apk"\n')

    assert "text/plain" not in out, out
    assert 'filename="old.apk"' not in out, out
    assert out.count("/app/*.apk") == 1, f"the rule was duplicated rather than replaced:\n{out}"


def test_headers_merge_keeps_rules_it_does_not_own() -> None:
    # ⚠️ A release script that flattens someone else's configuration is one people stop running.
    out = _merge_headers("/*\n  X-Frame-Options: DENY\n\n/app/*.apk\n  Content-Type: text/plain\n")

    assert "X-Frame-Options: DENY" in out, out
    assert "text/plain" not in out, out


def test_headers_merge_is_idempotent() -> None:
    """⭐ Two releases in a day must not leave the rule written twice."""
    once = _merge_headers(None)
    assert _merge_headers(once) == once


def test_the_apk_url_carries_the_build_number() -> None:
    """⚠️⚠️ **Cache invalidation avoided rather than managed.**

    Cloudflare cached `madboots.apk` for four hours *before* the content-type rule existed and kept
    serving the headerless copy after the redeploy — ⭐ *a fix that is live but invisible is
    indistinguishable from a fix that did not work, and the person looking at it is a tester.*

    A URL that has never been requested cannot be stale. ⭐ *The release that needs a manual cache purge
    is the release someone ships without one.*
    """
    script = SCRIPT.read_text()
    # ⚠️ The **copy** line specifically. A bare substring check passed while the APK was staged
    # unversioned, because the manifest and the link two lines below still mentioned the versioned name —
    # ⭐ *a test satisfied by a neighbour is not a test of the thing it names.*
    assert re.search(r'cp "\$APK" "\$SITE/app/madboots-\$next\.apk"', script), (
        "the published APK filename no longer carries the build number"
    )
    assert '"url": "https://madboots.com/app/madboots-$next.apk"' in script, (
        "version.json points somewhere other than the versioned APK"
    )
    assert 'href="madboots-$next.apk"' in script, "the install page links to an unversioned APK"


def _write_redirects() -> str:
    """Run the release script's `_redirects` block against a throwaway site folder."""
    block = re.search(
        r'python3 - "\$SITE" <<\'PY\'\nimport pathlib, sys\np = pathlib\.Path\(sys\.argv\[1\]\) / "_redirects"(.*?)\nPY\n',
        SCRIPT.read_text(),
        re.S,
    )
    assert block, "the release script no longer writes _redirects"
    site = Path(tempfile.mkdtemp())
    body = 'import pathlib, sys\np = pathlib.Path(sys.argv[1]) / "_redirects"' + block[1]
    subprocess.run(["python3", "-c", body, str(site)], check=True)
    return (site / "_redirects").read_text()


def test_the_legacy_apk_url_bounces_to_the_install_page() -> None:
    """⭐ A link that used to work should land somewhere that still does.

    Versioned filenames make yesterday's url a dead path, and a tester reaching it from history or
    autocomplete would get the site's index served as a download.
    """
    assert "/app/madboots.apk" in _write_redirects()


def test_the_redirect_cannot_swallow_the_current_apk() -> None:
    """⚠️⚠️ **This was nearly shipped as `/app/madboots-*.apk`.**

    That glob matches the APK the same release just published, so the download would have bounced to the
    install page and never downloaded anything — ⭐ *a redirect that catches the file it is protecting is
    worse than the dead link it replaces.*
    """
    rules = _write_redirects()

    assert "*" not in rules, f"a glob would match the versioned APK:\n{rules}"
    for build in (2, 3, 17):
        assert f"/app/madboots-{build}.apk" not in rules, rules


def test_the_redirect_survives_being_written_twice() -> None:
    assert _write_redirects() == _write_redirects()
