#!/bin/sh
# Install this garden's git hooks and semantic merge driver into this clone. The one installer is
# bin/install.py (Python, so it runs where `sh` is not a given); this file hands over to it.
REPO="$(git rev-parse --show-toplevel)"
PY=$(command -v python3 || command -v python) || { echo "install: python3 is required" >&2; exit 2; }
exec "$PY" "$REPO/bin/install.py" "$@"
