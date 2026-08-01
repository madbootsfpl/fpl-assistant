"""FPL Assistant entry point.

The real work lives in the layers under src/. This file just launches the
command-line interface (see src/cli.py and ADR-003).
"""

from src.cli import main

if __name__ == "__main__":
    main()
