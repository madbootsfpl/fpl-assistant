"""Run the web UI locally: `python -m src.web` (serves http://127.0.0.1:8000).

Read-only and local-only by design (ADR-050) — bound to 127.0.0.1, no auth. `uvicorn` is imported
here (not in the CLI) so the command-line app keeps working without the web dependencies installed.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=False)
