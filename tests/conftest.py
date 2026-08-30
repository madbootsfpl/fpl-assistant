"""Test-wide fixtures — chiefly: **the suite never calls a language model.**

Found 2026-08-30, by changing the narration model. Until then there was no `conftest.py` at all, so every
test reaching `ask.answer` / `ask.converse` called **whatever Ollama happened to be running on the
developer's machine**. That made the suite:

* **non-hermetic** — the same test passed or failed depending on a background service;
* **different locally than on CI** — GitHub Actions has no Ollama, so `narrate` returned `None` in
  milliseconds and every test took the degraded path. CI has therefore only ever exercised the *no-model*
  half of these paths, and nobody could tell, because green is green;
* **slow, and quietly getting slower** — swapping `llama3.2` (~2 s) for `qwen3:8b` (~16-27 s) took the suite
  from **78 s to 354 s** and pushed one AppTest past its 30-second limit. The model change did not break
  that test; it revealed the test had been depending on a fast model all along.

So the model is stubbed **off by default**, making local runs match CI exactly. A test that genuinely wants
narration should pass its *own* `narrator=`; an assertion on a live model's wording is not a test, it is a
sample.
"""

import inspect

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_llm: this test exercises src/llm.py itself, so it opts out of the model stub below",
    )


@pytest.fixture(autouse=True)
def _no_language_model(request, monkeypatch):
    """Force the degraded, model-free path for every test.

    Returning `None` is exactly what `src.llm` does when Ollama is unreachable, so this is the behaviour CI
    has always had — now it is the behaviour everywhere, on purpose rather than by accident.

    **Two seams, because patching the module alone is not enough.** `src/ask.py` declares
    `def answer(..., narrator=llm.narrate)`: a default argument is evaluated **once, when the `def` runs at
    import time**, so it holds a reference to the original function object and never consults `llm.narrate`
    again. Patching only the module would leave every one of those call sites talking to a real Ollama —
    the fixture would look like it worked while doing nothing.

    So the captured defaults are rewritten too, found by **identity** rather than by naming the functions:
    a fourth `narrator=` seam added later is covered automatically, whereas a hand-listed trio would silently
    stop covering the suite the day someone adds one.
    """
    # `tests/test_llm.py` tests the client itself and must see the real functions. It stubs `urlopen`, so
    # it stays offline on its own — the exemption is from the stub, never from being hermetic.
    if request.node.get_closest_marker("real_llm"):
        return

    from src import ask, llm

    real = {llm.narrate, llm.extract}
    stub = lambda *a, **k: None  # noqa: E731 — matches `llm`'s own "unavailable" return

    monkeypatch.setattr(llm, "narrate", stub)
    monkeypatch.setattr(llm, "extract", stub)

    for obj in vars(ask).values():
        if inspect.isfunction(obj) and obj.__kwdefaults__:
            for name, value in list(obj.__kwdefaults__.items()):
                if value in real:
                    monkeypatch.setitem(obj.__kwdefaults__, name, stub)
