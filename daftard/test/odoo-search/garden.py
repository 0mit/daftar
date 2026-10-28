#!/usr/bin/env python3
"""garden — the scratch garden the acceptance serves: grown from a daftar tree by that tree's own test/grow.py, kept by
Sam, with nothing in it but its gardener. Odoo's views and fields are laid in its captures folder by the runner, test
by test, where daftard reads a garden's captured views.

    python3 test/odoo-search/garden.py <daftar tree> <folder>      # prints the garden's path
"""
import os
import sys

tree, folder = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(tree, 'test'))
import grow  # noqa: E402

rel = grow.release(os.path.join(folder, 'release'))
g = os.path.join(folder, 'garden')
r = grow.garden(rel, g, 'sam', '--gardener-name', 'Sam')
if r.returncode:
    sys.exit('garden: the garden did not grow: ' + r.out[-600:])
print(g)
