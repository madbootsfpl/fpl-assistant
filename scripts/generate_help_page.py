"""Write `site/help.html` — the help that used to live on Streamlit (ADR-319).

⭐⭐ **The owner's reason, and it is the right one:** *"driving users to the streamlit.app is not the best
user experience."* The app's own Help row said **"Opens madboots.streamlit.app"** — a tester tapped a menu
item and landed in a different product with different navigation.

⭐⭐⭐ **The rules section is GENERATED from `src/fpl_rules.RULES`**, the same 21 topics Ask answers from.
⚠️ *A help page that restates the rules in its own words is a second copy of the rules* — and the copy that
is not executed is the one that goes stale. Change a rule once; the page follows.

⚠️ **The videos are NOT generated.** They are fetched in the browser from the `maddie_videos` table the
owner already curates from the Supabase dashboard — ⭐ *so adding or replacing a video stays what it is
today: a row, no deploy.* The publishable key is safe here for the reason ADR-216 gives for the app
binary: that table is `SELECT`-only for `anon` and holds public marketing content.

Run: `venv/bin/python scripts/generate_help_page.py`
"""

import html
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fpl_rules import RULES  # noqa: E402
from src.web_streamlit import brand  # noqa: E402

OUT = ROOT / "site" / "help.html"

#: ⭐ Written for **the app people actually use**, not ported verbatim. The Streamlit text described
#: *"My Squad ▸ Lab"* and a ⚙ panel; the phone has a bottom bar and a More tab, and ⚠️ *help that names
#: controls the reader cannot find is worse than no help — it makes them doubt they are in the right app.*
STEPS = [
    ("Put your team in", [
        "Open <b>Settings</b> and enter your <b>FPL manager id</b> — the number in your team's URL on "
        "fantasy.premierleague.com. Everything else follows from it.",
        "Your squad, your captain, your bank and your free transfers all arrive on their own. Nothing to "
        "type in twice.",
    ]),
    ("Read your week", [
        "<b>My Team</b> is the pitch: your eleven in formation, the bench under it, projected points on "
        "each shirt and the captain's armband where it is.",
        "<b>Swipe right</b> to walk back through the season — every past gameweek as it actually was, with "
        "the real points, the goals and cards, and how your overall rank moved.",
        "<b>Swipe left</b> for the weeks ahead, projected from the fixtures.",
        "Tap any player for their card: the per-gameweek projection, the form, the set-piece duties.",
    ]),
    ("Ask it something", [
        "<b>More ▸ Ask</b> takes a question in plain English — <i>who should I captain?</i>, "
        "<i>what should I do this week?</i>, <i>can I still play my bench boost?</i>",
        "Tap the <b>microphone</b> and say it instead of typing.",
        "Ask <b>“why?”</b> after any answer and it shows the reasons behind the pick — what is for it, what "
        "is against it, and how confident it is.",
        "It answers from the numbers, never from a guess. When it cannot answer something it says so "
        "rather than inventing a reply.",
    ]),
    ("Plan the moves", [
        "<b>This week</b> gives you the gameweek in one block: captain, lineup changes, the transfer worth "
        "making, and what is holding your confidence down.",
        "<b>More ▸ Chips</b> says when each chip is best across your run — and marks the ones you have "
        "already played.",
        "<b>More ▸ Squad Lab</b> builds a fresh fifteen to a budget, if you are wildcarding.",
    ]),
    ("Look wider", [
        "<b>Signals</b> — what the community is talking about, and the news that moved players.",
        "<b>More ▸ Fixture Difficulty Rating</b> — every club's run, week by week.",
        "<b>More ▸ Team DNA</b> — how strong each club is at both ends.",
        "<b>More ▸ Mini-leagues</b> — your rivals, and where the gap actually is.",
    ]),
]

FAQ = [
    ("Where does the data come from?",
     "The official Fantasy Premier League API, refreshed through the day. Nothing is scraped and nothing "
     "is invented."),
    ("Is this affiliated with FPL?",
     brand.DISCLAIMER),
    ("Why does it say a number is a heuristic, not a probability?",
     "Because it is. Confidence measures how clearly one option beats the others on the signals we hold — "
     "it does not mean you are that likely to be right. We would rather say so than let a score out of 100 "
     "imply something it cannot support."),
    ("Do I need an account?",
     "No. Your manager id is enough, and it is public. Nothing you type is needed to make the app work."),
    ("How do I report something?",
     "<b>More ▸ Tell us something</b>, inside the app — it sends the screen and the build number with it, "
     "so nobody has to remember which version they were on."),
]


def rules_html() -> str:
    """The 21 curated topics, straight from the module Ask answers from."""
    blocks = []
    for rule in RULES:
        title = rule["topic"].replace("_", " ").title()
        # ⭐ The facts are plain text with bullet lines; keep the shape, escape the content.
        lines = [html.escape(line.strip()) for line in rule["fact"].split("\n") if line.strip()]
        head, *rest = lines
        body = "".join(f"<li>{line.lstrip('• ')}</li>" for line in rest)
        blocks.append(
            f'<details class="rule"><summary>{html.escape(title)}</summary>'
            f'<p>{head}</p>{f"<ul>{body}</ul>" if body else ""}</details>'
        )
    return "\n".join(blocks)


def steps_html() -> str:
    out = []
    for n, (title, points) in enumerate(STEPS, start=1):
        items = "".join(f"<li>{p}</li>" for p in points)
        out.append(f'<section class="step"><h3><span class="n">{n}</span>{html.escape(title)}</h3>'
                   f"<ul>{items}</ul></section>")
    return "\n".join(out)


def faq_html() -> str:
    return "\n".join(
        f"<details class='rule'><summary>{html.escape(q)}</summary><p>{a}</p></details>"
        for q, a in FAQ
    )


def render() -> str:
    return TEMPLATE.format(
        name=brand.NAME, tagline=html.escape(brand.TAGLINE), mantra=html.escape(brand.MANTRA),
        disclaimer=html.escape(brand.DISCLAIMER), steps=steps_html(), rules=rules_html(),
        faq=faq_html(), rule_count=len(RULES),
    )


TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Help — {name}</title>
<meta name="description" content="How to use {name}: a step-by-step walkthrough, Maddie's video
explainers, and the FPL rules in plain English.">
<link rel="icon" href="favicon.png">
<link rel="stylesheet" href="help.css">
</head><body>

<header class="top wrap">
  <a class="brand" href="/" aria-label="{name} home"><span class="a">MAD</span><span class="b">BOOTS</span></a>
  <a class="lk" href="/app/web/">Launch the app →</a>
</header>

<main class="wrap">
  <h1>Help</h1>
  <p class="lede">{mantra} Every answer is checked against the data behind it, and says so.</p>

  <nav class="jump" aria-label="On this page">
    <a href="#start">Getting started</a>
    <a href="#videos">Videos</a>
    <a href="#rules">FPL rules</a>
    <a href="#faq">FAQ</a>
  </nav>

  <h2 id="start">Getting started</h2>
  {steps}

  <h2 id="videos">Maddie explains</h2>
  <p class="note">Ninety-second explainers. <span id="v-status">Loading…</span></p>
  <div id="video-list" class="videos"></div>

  <h2 id="rules">FPL rules, in plain English</h2>
  <p class="note">{rule_count} topics — the same ones Ask answers from, so they cannot drift apart.</p>
  {rules}

  <h2 id="faq">Questions</h2>
  {faq}
</main>

<footer class="wrap">
  <p><span class="brand small"><span class="a">MAD</span><span class="b">BOOTS</span></span> · {tagline}</p>
  <p class="discl">{disclaimer}</p>
</footer>

<script src="help-config.js"></script>
<script src="help.js"></script>
</body></html>
"""


def main() -> None:
    OUT.write_text(render())
    print(f"  wrote {OUT.relative_to(ROOT)} ({len(RULES)} rules, {len(STEPS)} steps, {len(FAQ)} questions)")


if __name__ == "__main__":
    main()
