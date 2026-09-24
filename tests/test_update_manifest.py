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
