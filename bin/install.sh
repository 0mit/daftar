#!/bin/sh
# Install this garden's git hooks and semantic merge driver into this clone. The one installer is
# bin/install.py (Python, so it runs where `sh` is not a given); this file hands over to it, run by the Python
# bin/hooks/python.sh chooses — the first that runs and imports yaml, never merely the first name on the PATH.
REPO="$(git rev-parse --show-toplevel)"
. "$REPO/bin/hooks/python.sh"
daftar_choose_python || exit 2
daftar_py "$REPO/bin/install.py" "$@"
