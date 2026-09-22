"""The two Info.plist keys a LAN address cannot work without (ADR-239).

⭐⭐ **Both fail silently, and both fail looking like an app bug.** Without
`NSLocalNetworkUsageDescription` iOS 14+ refuses the connection without prompting; without an ATS
exception, cleartext HTTP is blocked before the request leaves the process. Either one produces the same
symptom the owner already hit once and reported as an error in the app: *"Connection refused."*

⚠️ **They are also the kind of thing that disappears without anyone doing it wrong** — a regenerated
`ios/` folder, a merge that takes the upstream plist, a tidy-up of keys nobody recognised. ⭐ *A setting
whose absence produces a plausible bug report needs a test more than one that crashes.*

⚠️⚠️ **NSAllowsArbitraryLoads is the wrong fix and is rejected here deliberately.** It disables transport
security for every host, including the hosted API this is a stepping stone to, and it follows the app to
the App Store. `NSAllowsLocalNetworking` permits cleartext for *local* addresses only.
"""

import plistlib
from pathlib import Path

import pytest

PLIST = Path(__file__).resolve().parents[1] / "mobile" / "ios" / "Runner" / "Info.plist"


@pytest.fixture(scope="module")
def plist():
    if not PLIST.exists():  # pragma: no cover - the iOS folder is committed
        pytest.skip(f"no {PLIST}")
    return plistlib.loads(PLIST.read_bytes())


def test_the_app_says_why_it_wants_the_local_network(plist):
    reason = plist.get("NSLocalNetworkUsageDescription", "")
    assert reason, (
        "NSLocalNetworkUsageDescription is missing. iOS 14+ refuses local-network connections without "
        "it — silently — so the app cannot reach a Mac on the same Wi-Fi and reports 'Connection refused'."
    )
    # ⭐ The string is shown to a person in a system prompt, so it has to read as a sentence rather than
    # a placeholder. A one-word reason is how a prompt ends up saying "MADBOOTS would like to access
    # your local network: network".
    assert len(reason.split()) >= 6, f"the prompt shown to the user reads as a placeholder: {reason!r}"


def test_cleartext_is_allowed_on_the_local_network_only(plist):
    ats = plist.get("NSAppTransportSecurity", {})
    assert ats.get("NSAllowsLocalNetworking") is True, (
        "NSAppTransportSecurity.NSAllowsLocalNetworking is missing. ATS blocks cleartext HTTP by "
        "default, so http://192.168.x.x is refused before the request leaves the app."
    )
    assert not ats.get("NSAllowsArbitraryLoads"), (
        "NSAllowsArbitraryLoads disables transport security for EVERY host — including the hosted API "
        "this is a stepping stone to — and it follows the app to the App Store. "
        "NSAllowsLocalNetworking is the exception that stops at the LAN."
    )
