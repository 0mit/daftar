#!/usr/bin/env python3
"""reckon — the one reckoner, in the core since core 3.0 (core/reckon.py): this path runs it, and `import reckon` is it.

    python3 bin/reckon.py <bean>:<selection> [--input name=value ...] [--at <commit> --moment <moment>]
    python3 bin/reckon.py --ad-hoc <file.yaml> [--bean <bean>] [--input name=value ...]

(`python` on Windows.) Every word of what it does is core/reckon.py's; nothing is stated here."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import reckon as _reckon  # noqa: E402

if __name__ == '__main__':
    sys.exit(_reckon.main(sys.argv[1:]))
sys.modules[__name__] = _reckon        # a tool's `import reckon` is the core's one module, its caches and all
