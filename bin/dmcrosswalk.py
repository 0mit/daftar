#!/usr/bin/env python3
"""dmcrosswalk — today's name of bin/crosswalk.py, the tool of the verb `crosswalk` (v1 part 7): run, or imported, it is that tool.

The tools take their verbs' names in v1 (`python3 bin/daftar.py crosswalk` runs it too); this name stays until part 13, so
every command and import written with it still works. Imported by name it IS the module `crosswalk`, one object under both
names; loaded from this file under a name of the caller's own (importlib, as a tool loads another garden's copy), it is
a copy of that module of its own, as loading today's file was."""
import importlib.util
import os
import runpy
import sys

_TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crosswalk.py')
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(_TOOL))
    runpy.run_path(_TOOL, run_name='__main__')
elif getattr(sys.modules.get(__name__), '__dict__', None) is not globals():
    with open(_TOOL, encoding='utf-8') as _fh:
        exec(compile(_fh.read(), _TOOL, 'exec'), globals())
else:
    _m = sys.modules.get('crosswalk')
    if getattr(_m, '__file__', None) is None or os.path.abspath(_m.__file__) != _TOOL:
        _spec = importlib.util.spec_from_file_location('crosswalk', _TOOL)
        _m = importlib.util.module_from_spec(_spec)
        sys.modules['crosswalk'] = _m
        _spec.loader.exec_module(_m)
    sys.modules[__name__] = _m
