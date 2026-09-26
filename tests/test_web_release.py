"""The web deploy cannot quietly serve yesterday's app (ADR-304).

⚠️⚠️⚠️ **This shipped, and the owner found it.** Ask was in the deployed bundle and his browser was
running an app from before it existed. Two caches stacked: a Cloudflare zone setting rewrites
`Cache-Control` to `max-age=14400` on the custom domain for `.js` and `.apk` — the Pages origin honours
the `no-cache` that `_headers` asks for and the zone does not — and a service worker cached the app shell
through reloads on top of that.

⭐ Everything below guards a step that is invisible when skipped, which is the only kind of step worth a
test in a deploy script.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "release_web.sh"
ANDROID = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "release_android.sh"


def test_the_web_build_ships_no_service_worker():
    """⭐⭐ Flutter's own bootstrap calls it *"deprecated and will be removed in a future Flutter
    release"*, and this app cannot do one useful thing offline — every screen is an API call. ⚠️ *A cache
    layer for an app that cannot work offline is all of the staleness and none of the benefit.*"""
    # ⚠️⚠️ **On the build command, not merely in the file.** The first version of this test asserted the
    # flag appeared *anywhere* in the script — and passed when a mutation deleted it from the command,
    # because the comment above it mentions it by name. ⭐ *A guard satisfied by the prose explaining the
    # guard is a guard that has stopped reading the code.*
    build = next(
        (line for line in SCRIPT.read_text().splitlines()
         if "flutter build web" in line and not line.lstrip().startswith("#")),
        None,
    )
    assert build, "the script no longer builds for web"
    assert "--pwa-strategy=none" in build, (
        f"the web build registers a service worker again — it will cache the app shell through "
        f"reloads:\n    {build.strip()}"
    )


def test_a_kill_switch_retires_the_workers_already_installed():
    """⚠️⚠️ **Turning the worker off does not remove the ones already out there.** A registration
    survives until it unregisters itself or its script stops being servable — and ⭐ *Pages does not 404 a
    missing file, it serves the index page*, which a browser cannot parse as a worker and therefore
    treats as "no update"."""
    body = SCRIPT.read_text()
    assert "flutter_service_worker.js <<" in body or "flutter_service_worker.js <<'SW'" in body, (
        "no kill switch is written; deleting the file would leave old workers alive, not remove them"
    )
    assert "registration.unregister()" in body
    assert "caches.delete" in body, "the old worker's caches are never cleared"


def test_the_app_urls_are_stamped_with_the_build():
    """⭐ *A URL that has never been requested cannot be stale* — ADR-282's fix, applied to the web.

    ⚠️ `index.html` is the hook because it is the one file the zone does **not** override: it still
    carries `max-age=0, must-revalidate`, so whatever it points at gets fetched.
    """
    body = SCRIPT.read_text()
    assert 'flutter_bootstrap.js?v=' in body, "the bootstrap is not cache-busted"
    assert 'main.dart.js?v=' in body, (
        "main.dart.js is not cache-busted — Flutter does not hash it into the filename, so the name is "
        "stable while the contents change, which is exactly what a long max-age gets wrong"
    )


def test_the_stamp_fails_loudly_if_flutter_changes_its_output():
    """⚠️ Both substitutions are asserted in the script itself. ⭐ *A silent no-op in a cache-busting step
    is the same bug it was written to fix*, and Flutter regenerates both files on every build."""
    body = SCRIPT.read_text()
    assert body.count("assert ") >= 2, "the stamping step can no-op without saying so"


def _merged_headers(initial: str | None) -> str:
    block = re.search(r"python3 - \"\$SITE\" <<'PY'\n(.*?)\nPY\n", ANDROID.read_text(), re.S)
    assert block, "the release script no longer writes _headers via an inline python block"
    site = pathlib.Path(tempfile.mkdtemp())
    if initial is not None:
        (site / "_headers").write_text(initial)
    subprocess.run(["python3", "-c", block[1], str(site)], check=True)
    return (site / "_headers").read_text()


def test_the_headers_ask_for_no_cache_on_the_files_that_announce_a_new_build():
    """⭐ These are correct at the origin and overridden by the zone — ⚠️ *which is a reason to keep them,
    not to drop them*: they become sufficient the moment Browser Cache TTL is set to respect headers, and
    the next reader can see what the deploy intends."""
    out = _merged_headers(None)

    for path in ("/app/web/index.html", "/app/web/flutter_service_worker.js",
                 "/app/web/flutter_bootstrap.js", "/app/web/main.dart.js"):
        assert path in out, f"{path} has no cache rule:\n{out}"
    assert out.count("Cache-Control: no-cache") == 4, out
    # ⭐ And the APK rule it already owned is still there.
    assert "application/vnd.android.package-archive" in out


def test_the_merge_still_leaves_other_peoples_rules_alone():
    """⚠️ *A release script that flattens someone else's configuration is a release script people stop
    running* — and it must still update the rules it owns."""
    out = _merged_headers("/custom\n  X-Mine: keep\n\n/app/web/main.dart.js\n  Cache-Control: max-age=999\n")

    assert "X-Mine: keep" in out, "a foreign rule was flattened"
    assert "max-age=999" not in out, "the script did not correct a rule it owns"
    assert out.count("/app/web/main.dart.js") == 1, f"the rule was duplicated:\n{out}"
