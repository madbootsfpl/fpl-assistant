"""The swipe's forward limit is one number, declared twice (ADR-298).

⚠️⚠️⚠️ **This exists because the two halves already disagreed once.** The app walks five pages forward
(`kForwardWeeks`); the server decides how many weeks of projection to send (`SWIPE`). They are the same
fact, written in two languages, in two repositories' worth of directory — and the first version shipped
with the server one week short, so the app's last forward page drew fifteen dashes and an empty total.

⭐ *Neither side can catch this alone.* The Dart tests pass against a sample that carries whatever the
server last sent, and the Python tests pass against a constant that no Dart file can see. The only place
the disagreement is visible is here, in a test that reads both.
"""

import pathlib
import re

from src.service.inputs import SWIPE

MOBILE = pathlib.Path(__file__).resolve().parents[1] / "mobile"
SEASON = MOBILE / "lib" / "season_view.dart"


def test_the_app_and_the_service_agree_on_how_far_forward_the_swipe_goes():
    found = re.search(r"const int kForwardWeeks = (\d+);", SEASON.read_text())
    assert found, f"{SEASON.name} no longer declares kForwardWeeks — this guard has gone blind"
    forward = int(found.group(1))

    # ⭐ **The +1 is the whole arithmetic, and it is the bit that was wrong.** A window includes the week
    # you are standing on: the live page reads `SWIPE`'s first week, and the five pages after it read the
    # rest. ⚠️ *Asserting equality here would re-introduce the bug it was written to stop.*
    assert SWIPE == forward + 1, (
        f"the app swipes {forward} weeks forward, which needs {forward + 1} weeks of projection "
        f"(the live one and each page after it) — the service sends {SWIPE}, so "
        f"{'the last page(s) will be blank' if SWIPE < forward + 1 else 'a week is fetched and never shown'}"
    )
