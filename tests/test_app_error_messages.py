"""No screen shows a user a raw Dart exception (ADR-233).

⚠️⚠️ **The failure this exists for, reported by the owner:**

    ClientException with SocketException: Connection refused (OS Error: Connection refused,
    errno = 61), address = localhost, port = 49421, uri=http://localhost:8078/api/v1/squad/gameweek-plan

A good message for exactly this already existed — *"The service is not answering on …, start it with …"* —
in `main.dart`, on the landing screen, and **nowhere else**. Six other screens rendered `'${snapshot.error}'`
verbatim.

⭐⭐ *A fix scoped to where it was noticed is a fix the next screen does not get.* So the message moved into
the client, where the base URL and the meaning of a refused socket both live — and this sweeps for the
pattern rather than checking the screens I happened to remember (ADR-184).

⚠️ **This is a Python test guarding Dart**, like `tests/test_brand_dart.py`. The Dart suite does not run in
CI (ADR-221), so a guard that matters has to sit in the one that does.
"""

import re
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / "mobile" / "lib"

#: Rendering a bare error object. `${snapshot.error}` / `$error` inside a widget is the raw Dart
#: `toString()` — the errno text above.
RAW = re.compile(r"""(?:Text|SelectableText)\s*\(\s*(?:'|")?\$\{?(?:snapshot\.)?error\}?""")


def _dart_files():
    return sorted(p for p in LIB.rglob("*.dart"))


def test_there_are_screens_to_check():
    """⭐ A sweep that finds nothing passes. If the app moves or the glob breaks, every assertion below
    becomes vacuously true with nothing going red."""
    assert len(_dart_files()) >= 8


@pytest.mark.parametrize("path", _dart_files(), ids=lambda p: p.name)
def test_no_screen_renders_a_raw_exception(path):
    """⚠️ `friendlyError(...)` exists so a refused connection reads as *"the service is not answering"*
    with the command to start it. ⭐ Rendering the object instead shows a socket errno to someone who wants
    to know why their team will not load."""
    offenders = [
        f"line {i}: {line.strip()}"
        for i, line in enumerate(path.read_text().splitlines(), start=1)
        if RAW.search(line)
    ]
    assert not offenders, (
        f"{path.name} renders a raw exception:\n  " + "\n  ".join(offenders)
        + "\n\n⭐ Use `friendlyError(snapshot.error)` from `api/client.dart`."
    )


def test_the_unreachable_message_names_the_address_and_the_command():
    """⭐ *"Cannot connect"* without either tells you only that you are stuck. The message has to be
    actionable by the person reading it, who is usually the person who can start the server."""
    client = (LIB / "api" / "client.dart").read_text()
    assert "_notRunning" in client, "the message must live in one place, not per screen"
    assert "uvicorn" in client, "…and name the command that fixes it"
    assert "$baseUrl" in client, "…and the address it tried"


def test_both_ways_a_refused_connection_arrives_are_caught():
    """⚠️ **On web there is no `SocketException`** — a refused connection surfaces as a
    `ClientException`. ⭐ Catching only the first would leave Chrome showing exactly the raw text this
    whole guard is about, on the one target `flutter doctor` says is always available."""
    client = (LIB / "api" / "client.dart").read_text()
    assert "on SocketException" in client
    assert "on http.ClientException" in client
