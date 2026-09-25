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


def _install_page() -> str:
    """The install page the release script writes, with its shell variables filled in."""
    body = re.search(
        r'cat > "\$SITE/app/index\.html" <<HTML\n(.*?)\nHTML\n', SCRIPT.read_text(), re.S
    )
    assert body, "the release script no longer writes an install page"
    return body[1].replace("$name", "1.0.0").replace("$next", "5")


def test_the_install_page_explains_how_to_find_an_fpl_id() -> None:
    """⭐⭐ **The app is unusable without this number and nothing told anyone where to get it.**

    ⚠️ It is asked for on first launch, which is the worst moment to go looking — *a first run that stops
    on a question the product never answers is a first run that ends there.*
    """
    page = _install_page()

    assert 'id="fpl-id"' in page, "the explainer anchor is gone"
    # ⚠️ The **example block**, not the word "/entry/" — which also appears in the sentence below it, so
    # a bare substring check passed with the example deleted. ⭐ *A test satisfied by a neighbour is not a
    # test of the thing it names* — the second time that exact trap has caught me in this ADR.
    example = re.search(r'<div class="url">(.*?)</div>', page, re.S)
    assert example, "the example url block is gone"
    assert "/entry/" in example[1], example[1]
    # ⭐ The id is picked out rather than described, so the reader can match it against their own bar.
    assert re.search(r"<b>\d+</b>", example[1]), example[1]
    assert "not your league ID" in page, "the tip that heads off the usual mistake is gone"


def test_the_install_steps_reach_the_explainer() -> None:
    """⚠️ A section nothing links to is a section nobody scrolls to."""
    page = _install_page()

    assert 'href="#fpl-id"' in page
    # ⭐ **After the install steps, not among them.** You cannot act on this until the app is open, and
    # *a step you cannot do yet is a step that reads as a blocker.*
    assert page.index('href="#fpl-id"') < page.index('id="fpl-id"')
    assert page.index("Tap <b>Install</b>") < page.index('href="#fpl-id"')


def test_the_release_keeps_the_previous_builds() -> None:
    """⚠️⚠️ **A missing APK does not 404 on Cloudflare Pages — it serves the site's index page.**

    And the `_headers` rule then labels 384KB of HTML `application/vnd.android.package-archive`, so a
    tester whose install page is cached one build behind downloads that and gets a parse error from
    Android. ⭐ *The fallback for a stale link should be an older version of the thing, not a corrupt
    version of it.*

    The first version of this script deleted every previous APK to keep the folder tidy.
    """
    script = SCRIPT.read_text()

    assert "rm -f \"$SITE/app\"/madboots*.apk" not in script, (
        "the release script deletes every previous APK again"
    )
    # ⭐ Keeps a bounded number rather than all of them — 18MB each adds up, and the reason to keep one is
    # a stale cache, which does not reach back further than a build or two.
    assert "tail -n +4" in script, "the retention window is gone or unbounded"


def test_the_release_publishes_itself() -> None:
    """⭐⭐ **The step that kept getting skipped** (ADR-290).

    Cutting a release and shipping it were two actions with a human in between, and the human one is the
    one that does not happen — the live build sat **three releases behind** while this very script was
    being improved. ⚠️ *A publish step a person has to remember is a publish step that measures how busy
    they are.*
    """
    script = SCRIPT.read_text()

    assert "wrangler" in script, "the release no longer publishes"
    assert "pages deploy" in script
    # ⚠️ The staged folder, not some other path — the APKs and the manifest are in it.
    assert 'pages deploy "$SITE"' in script


def test_a_missing_token_is_not_an_error() -> None:
    """⭐ *A release tool that refuses to run without a secret is a release tool you stop running.*

    Without credentials the script must still bump, build, stage and **say how to turn publishing on**.
    """
    script = SCRIPT.read_text()

    assert 'if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then' in script, (
        "publishing is no longer gated on the token being present"
    )
    # ⚠️ And the else branch has to tell the reader what to do, not just fall silent.
    assert "not published" in script
    assert "drag $SITE to Cloudflare Pages" in script


def test_the_token_is_only_ever_read() -> None:
    """⚠️⚠️ **A secret that reaches a file reaches the repo eventually.**

    The token is an environment variable and must stay one: never written to disk, never echoed, never
    passed as a command-line argument where it would sit in shell history and `ps`.
    """
    # ⚠️ **Expansions, not mentions.** The instructions print the variable's *name* so the reader knows
    # what to export — ⭐ *a test that cannot tell `$TOKEN` from the word "TOKEN" forbids the
    # documentation along with the leak*, which is how a guard gets deleted rather than satisfied.
    expansions = re.findall(r"\$\{?CLOUDFLARE_API_TOKEN[^}]*\}?", SCRIPT.read_text())

    # ⚠️ **Every** expansion must be the presence-check form — not "there is exactly one of them". The
    # script legitimately asks twice (whether to publish, and what to print at the end), and pinning the
    # count made the guard fail on a change that was entirely safe. ⭐ *A security test that counts
    # occurrences instead of judging them fails on growth and gets loosened by whoever is in a hurry.*
    assert expansions, "the presence check is gone — publishing may be unguarded"
    assert set(expansions) == {"${CLOUDFLARE_API_TOKEN:-}"}, (
        f"the token's value is expanded outside a presence check: {set(expansions)}"
    )


def test_no_credential_file_is_tracked() -> None:
    """⭐ The same rule the keystore has (ADR-278): the repo must not be able to hold the secret."""
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()

    for name in tracked:
        assert ".wrangler" not in name, name
        assert not name.endswith((".dev.vars", "wrangler.toml.local")), name


def test_the_closing_line_knows_whether_it_published() -> None:
    """⭐ *A closing instruction that tells you to do the thing the script just did is how a reader learns
    to stop reading them.*

    The first run of ADR-290 deployed successfully and then printed "NEXT: drag $SITE to Cloudflare
    Pages" — ⚠️ *the release was correct and its last word was wrong*, which is the half of a change that
    tests do not usually reach.
    """
    script = SCRIPT.read_text()
    tail = script[script.index("NEXT:") - 400:]

    assert 'if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then' in tail, (
        "the closing instruction no longer depends on whether it published"
    )
    assert "Testers already have it" in script
    assert "drag $SITE to Cloudflare Pages, then commit" in script, (
        "the manual fallback instruction is gone for people without a token"
    )
