#!/bin/sh
# Grow a new garden from this seed. The implementation is seed/germinate.py — Python, because a garden is grown
# on Windows too, where `sh` is not a given but the Python that runs the gate is. This file remains for the hand
# that types `sh seed/germinate.sh` and hands over.
SEED=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY=$(command -v python3 || command -v python) || { echo "germinate: python3 is required" >&2; exit 2; }
exec "$PY" "$SEED/germinate.py" "$@"
