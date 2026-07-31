# FPL Assistant Development Journal

## Session 1 -- Environment Setup

### Goal

Prepare the Mac mini for Python development and create the foundation
for the FPL Assistant project.

## What we installed/configured

### Homebrew

Installed the native Apple Silicon Homebrew.

Verified: - `which brew` → `/opt/homebrew/bin/brew`

### Python

Initially: - `python3 --version` → `3.10.4`

Discovered: - Homebrew Python 3.14 was installed but the shell was still
using the older Python.

Fixed by:

``` bash
hash -r
```

Verified:

``` bash
which python3
python3 --version
```

Expected:

``` text
/opt/homebrew/bin/python3
Python 3.14.6
```

## Project structure

Created:

``` text
~/Projects/fpl-assistant
```

Created a virtual environment:

``` bash
python3 -m venv venv
source venv/bin/activate
```

Verify:

``` bash
which python
python --version
```

## Initial project files

-   app.py
-   README.md
-   requirements.txt
-   .gitignore

Suggested docs folder:

``` text
docs/
    Vision.md
    Backlog.md
    Sprint1.md
    Architecture.md
```

## Git

Initialise:

``` bash
git init
git add .
git commit -m "Initial project structure"
```

## Tips learned

-   Use one Python virtual environment per project.
-   Keep documentation in Git.
-   Commit little and often.
-   Build one user story at a time.
-   Use GitHub Issues as your backlog.
-   Think in sprints rather than giant feature lists.
-   Keep architecture decisions written down.

## Suggested Sprint 1

1.  Create project structure
2.  Connect to FPL API
3.  Download player data
4.  Display player table
5.  Search players
6.  Filter players
7.  Calculate Points per £m
8.  Refresh latest data

## Commands reference

``` bash
python3 -m venv venv
source venv/bin/activate
python app.py
git init
git add .
git commit -m "Initial project structure"
```

## Personal notes

Treat this as a product, not just a coding exercise. The aim is to learn
modern software development while building a useful FPL analytics
platform.