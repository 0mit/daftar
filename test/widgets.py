#!/usr/bin/env python3
"""The widgets (assets/view/lib/widgets, the values tree's toolbox, the `view` profile's): `node test/widgets.test.mjs`, whose every check is an
assertion — exact numbers, isolated and escaped values, each reader's digits, separators, calendar and words from CLDR
through Intl, none privileged. Node runs it; a machine with no Node skips it, saying so.

Run: python3 test/widgets.py   (0 = green)
"""
import json
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
    # THE WIDGET'S OWN ROWS ARE THE LAW'S: direction.js carries the `orientations` table for a page that brings none, and
    # it may never drift from core/law/profiles.yaml
    import yaml
    law = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'profiles.yaml'), encoding='utf-8'))['orientations']
    want = {r['order']: [r['axis'], int(r['sense']), str(r['follows']) == 'true'] for r in law}
    wantc = {r['order']: r.get('commands') or [None, None] for r in law}
    js = ("const vm=require('vm'),fs=require('fs');const w={document:null};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),"
          "{window:w});const D=w.daftarDirection;console.log(JSON.stringify([D.ORIENTATIONS,D.COMMANDS]))")
    r = subprocess.run([node, '-e', js, os.path.join(ROOT, 'assets', 'view', 'lib', 'widgets', 'direction.js')],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    got, gotc = json.loads(r.stdout) if r.returncode == 0 else ({}, {})
    check("direction.js carries the law's `orientations` rows exactly: every order, its axis, sense and whether it follows the script, "
          "and its commands", got == want and gotc == wantc, (got, want, gotc, wantc))
print(f"\nwidgets: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
