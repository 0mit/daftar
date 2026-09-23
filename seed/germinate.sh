#!/bin/sh
# Grow a new garden from this seed. The implementation is seed/germinate.py — Python, because a garden is grown
# on Windows too, where `sh` is not a given but the Python that runs the gate is. This file remains for the hand
# that types `sh seed/germinate.sh` and hands over.
SEED=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# WHICH PYTHON: the first that runs AND imports yaml, chosen as the hooks choose it (bin/hooks/python.sh says why) —
# never merely the first name on the PATH, which on Windows may be the Store's alias that runs no Python. It reads a
# choice the clone this seed lives in recorded, and records none: the new garden's installer records its own.
. "$SEED/../bin/hooks/python.sh"
DAFTAR_PY=$(CDPATH= cd -- "$SEED/.." && daftar_choose_python --no-record && printf '%s' "$DAFTAR_PY") || exit 2
daftar_py "$SEED/germinate.py" "$@"
