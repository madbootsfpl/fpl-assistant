"""The answer-block wrapper (ADR-191) — long lines continue under their own content, nothing scrolls.

Owner, on a chip answer: *"could you get the screen to wrap?"* The wildcard line had reached ~230 characters,
which a terminal breaks at column 0 and a `st.code` block does not break at all — so finishing the sentence
meant scrolling a monospace box sideways.
"""

from src.ui._wrap import WIDTH, wrap_block

_WILDCARD = ("  Wildcard:       worth +306.8 xP — a fresh build beats your squad over this window; you keep "
             "only 3 of 15; £4.1m of your squad cannot play. Your weakest stretch GW12–GW14 (avg XI 46.9 xP) "
             "— reset before it  · Confidence 95/100 · High")


def test_nothing_comes_back_wider_than_the_width():
    for line in wrap_block(_WILDCARD).split("\n"):
        assert len(line) <= WIDTH, f"{len(line)} chars: {line!r}"


def test_a_block_that_already_fits_is_returned_byte_identical():
    """⚠️ **The property that makes this safe to apply to every answer instead of chosen ones.**

    If wrapping could perturb a block that already fits, adopting it would mean re-reading every rendered
    output in the app. It cannot, so the only lines that change are the ones that were unreadable.
    """
    short = "Chip strategy — squad 'S' (next 15 GW)\n\n  Free Hit:       GW12 — your weakest week\n\n  Note."
    assert wrap_block(short) == short
    assert wrap_block("") == ""
    assert wrap_block("\n\n") == "\n\n"


def test_continuations_hang_under_the_text_not_under_the_label():
    """⚠️ **The whole point, and the thing a naive wrap gets wrong.**

    Breaking at column 0 would put the Wildcard sentence's continuation in the *label* column, where it reads
    as another chip. The label column has to stay a column.
    """
    lines = wrap_block(_WILDCARD).split("\n")
    assert len(lines) > 1, "this fixture only tests anything while it actually wraps"
    hang = len("  Wildcard:       ")
    for cont in lines[1:]:
        assert cont.startswith(" " * hang), f"continuation must align under the text: {cont!r}"
        assert cont[hang] != " ", f"…and not drift further right: {cont!r}"


def test_the_first_line_keeps_its_own_indent():
    out = wrap_block(_WILDCARD).split("\n")[0]
    assert out.startswith("  Wildcard:       worth"), out


def test_an_unlabelled_line_hangs_at_its_own_indent():
    """Prose lines carry no `Label:` column, so they continue at the indent they started with."""
    line = "            " + ("word " * 40).strip()
    lines = wrap_block(line).split("\n")
    assert len(lines) > 1
    for cont in lines[1:]:
        assert cont.startswith(" " * 12) and cont[12] != " "


def test_a_hyphenated_name_is_never_split_across_lines():
    """`break_on_hyphens` is off on purpose. These blocks are full of hyphenated players — Calvert-Lewin,
    Dewsbury-Hall, Gibbs-White — and a name broken over two lines reads as two players.

    ⚠️ **The fixture has to put the name ON the boundary.** A first version padded with filler and asserted
    the name survived; it passed with hyphen-breaking turned back on, because the name never reached the wrap
    point. ⭐ *A fixture that only exercises the lucky case will confirm a broken mechanism* — so the padding
    here is computed to land the hyphen exactly where the break would fall.
    """
    name = "Calvert-Lewin"
    for pad in range(0, 30):                       # sweep the name across the boundary
        body = "  Transfer:       " + ("x" * pad) + " " + ("y " * 40).strip() + " " + name + " scored"
        for line in wrap_block(body).split("\n"):
            assert not line.rstrip().endswith("Calvert-"), f"split a name at pad={pad}: {line!r}"
            assert not line.lstrip().startswith("Lewin"), f"orphaned a surname at pad={pad}: {line!r}"


def test_a_token_longer_than_the_line_is_left_alone():
    """`break_long_words` is off too. A token wider than the whole line is a URL or an id, and chopping it at
    an arbitrary column makes it unusable — better one over-long line the reader can select than two useless
    halves."""
    long_token = "A" * (WIDTH + 30)
    out = wrap_block(f"  Note:          {long_token} tail")
    assert long_token in out, "a long token must survive whole, even at the cost of one wide line"


def test_wrapping_is_idempotent():
    """Rendering is not always a single pass — an answer can be wrapped and then embedded in another block.
    A second pass must be a no-op, or repeated rendering would slowly shred the indentation."""
    once = wrap_block(_WILDCARD)
    assert wrap_block(once) == once


def test_the_words_survive_exactly():
    """Wrapping may only change whitespace. If it ever drops or reorders a word it would be editing the
    answer, not laying it out — and the figures in these lines are the answer."""
    assert wrap_block(_WILDCARD).split() == _WILDCARD.split()


def test_the_chip_block_is_actually_wrapped():
    """⚠️ **A wrapper nothing calls wraps nothing.**

    Every test above exercises `wrap_block` directly, and all of them passed with the call removed from
    `render_chip_advice` — the mutation that matters most survived the whole file. ⭐ *Testing a component is
    not testing that anything uses it* (ADR-185, twice now). This asserts the rendered chip answer — the
    surface the owner actually reported — comes back inside the width.
    """
    from src.ui.chips import render_chip_advice

    advice = {
        "triple_captain": {"gameweek": 5, "player": {"web_name": "Haaland", "team": "MCI"},
                           "player_xp": 6.3},
        "bench_boost": {"gameweek": 19, "squad_total": 57.1, "bench_points": 6.6},
        "free_hit": {"gameweek": 12, "xi_total": 43.4},
        "wildcard": {"window": (12, 14), "avg_xi": 46.9, "gain": 306.8, "overlap": 3,
                     "squad_size": 15, "idle_spend": 4.1},
    }
    conf = {"triple_captain": {"confidence": 40, "band": "Low"},
            "bench_boost": {"confidence": 42, "band": "Low"},
            "free_hit": {"confidence": 58, "band": "Medium"},
            "wildcard": {"confidence": 95, "band": "High"}}
    out = render_chip_advice(advice, "Madboots", horizon=15, confidences=conf)
    for line in out.split("\n"):
        assert len(line) <= WIDTH, f"the rendered chip block still runs off the screen: {len(line)} {line!r}"
    assert "Wildcard" in out


def test_the_confidence_suffix_is_never_split():
    """⚠️ **Nearly every dynamic line ends `· Confidence 40/100 · Low`, and a plain wrap orphans the band.**

    It happened at 100 columns and again at 110 — widening the block to chase it is whack-a-mole, because the
    next line is always a few characters longer. ⭐ *When a wrap keeps producing the same ugly break, the fix
    is to say what may not be broken, not to move the boundary.* The suffix travels as one token.
    """
    line = ("  Free Hit:       GW9 — your best XI projects only 47.9 xP (your weakest single week)"
            "  · Confidence 40/100 · Low")
    out = wrap_block(line)
    assert len(out.split("\n")) > 1, "this fixture only tests anything while the line actually wraps"
    tail = next(ln for ln in out.split("\n") if "Confidence" in ln)
    assert tail.strip() == "· Confidence 40/100 · Low", \
        f"the whole suffix must move down together, not just its last word: {tail!r}"
    assert "\x00" not in out, "the weld character must never survive into the output"


def test_the_weld_leaves_the_text_untouched():
    """The welding is a wrapping device, not an edit: the words and their spacing come back as they went in."""
    line = "  Free Hit:       GW9 — short  · Confidence 40/100 · Low"
    assert wrap_block(line) == line                       # fits, so untouched
    long_line = "  Free Hit:       " + ("word " * 30).strip() + "  · Confidence 40/100 · Low"
    assert wrap_block(long_line).split() == long_line.split()
