#!/usr/bin/env python3
"""The widgets (assets/view/lib/widgets, the values tree's toolbox, the `view` profile's): `node test/widgets.test.mjs`, whose every check is an
assertion — exact numbers, isolated and escaped values, each reader's digits, separators, calendar and words from CLDR
through Intl, none privileged. Node runs it; a machine with no Node skips it, saying so.

Run: python3 test/widgets.py   (0 = green)
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


node = shutil.which('node')
if not node:
    print("SKIP  widgets: this machine has no Node to run them")
else:
    r = subprocess.run([node, os.path.join(ROOT, 'test', 'widgets.test.mjs')], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', cwd=ROOT)
    check("widgets: " + (r.stdout.strip().splitlines() or ['(nothing printed)'])[-1], r.returncode == 0 and
          r.stdout.startswith('PASS'), r.stdout + r.stderr)
print(f"\nwidgets: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
