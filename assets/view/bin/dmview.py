#!/usr/bin/env python3
"""dmview — today's name of assets/view/bin/view.py, the `view` profile's tool (v1 part 11): run, it is that tool.

The tools take their verbs' names in v1; this name stays until part 13, so every command written with it still works."""
import os
import runpy
import sys

_TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'view.py')
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(_TOOL))
    runpy.run_path(_TOOL, run_name='__main__')
