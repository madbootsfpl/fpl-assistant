"""Run the Streamlit UI: `python -m src.web_streamlit` (→ http://localhost:8501).

Launches `streamlit run app.py` with the **project root on PYTHONPATH**, so every page's
`from src import …` resolves cleanly — no `sys.path` hack in the app/page files (ADR-052). This is the
edge's only knowledge of Streamlit's run quirk; `streamlit` is a web-only extra, so the CLI runs without
it (the import lives inside `main`, not at module top).
"""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]           # the project root
_APP = Path(__file__).resolve().parent / "Home.py"    # the entrypoint (its filename = the sidebar "Home")


def main() -> int:
    env = {**os.environ,
           "PYTHONPATH": os.pathsep.join(filter(None, [str(_ROOT), os.environ.get("PYTHONPATH", "")]))}
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(_APP)], env=env)


if __name__ == "__main__":
    sys.exit(main())
