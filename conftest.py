# Root conftest.
#
# Its presence at the repository root tells pytest to add this directory to the
# import path, so tests can do `from src.api.client import FplClient` without any
# extra configuration.

import pytest


@pytest.fixture(autouse=True)
def _no_photo_sweep(monkeypatch):
    """Keep the network out of the test suite (Sprint 098, US-255).

    `badges.photo_url_by_id` checks the CDN for missing player photos via `_missing_photo_codes`; rendering
    any page in an AppTest would fire that sweep. Patch it to "nothing missing" so tests stay offline + fast
    (the photo-vs-shirt logic is covered by a unit test that overrides this with a specific missing set).
    """
    from src.web_streamlit import badges
    monkeypatch.setattr(badges, "_missing_photo_codes", lambda codes: frozenset())
