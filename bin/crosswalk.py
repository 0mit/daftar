#!/usr/bin/env python3
"""crosswalk — another standard's records carried into beans and back, by a crosswalk of the law: today's commands, kept.

    python3 bin/crosswalk.py to fhir <observations.json>      # FHIR R5 Observations -> `measure` statements
    python3 bin/crosswalk.py to dwc <occurrences.csv>          # Darwin Core occurrences -> `be` statements as location
    python3 bin/crosswalk.py back fhir <bean> [<id> ...]       # a bean's measures -> FHIR R5 Observations
    python3 bin/crosswalk.py back dwc <bean> [<bean> ...]      # beans' locations -> Darwin Core occurrences

ONE MACHINERY (2.12). These are `import` and `export` (bin/import.py, bin/export.py) through the crosswalks
`fhir-r5-observation` and `dwc-occurrence` of core/law/crosswalks.yaml, which say every field; this tool knows no
standard's field by name. `to` prints the statements for each bean and writes nothing (`import … --into bean --write`
writes them, with their act); what a record has no place for is listed as `not carried`, in both directions, so a round
trip gives back every field it did not list.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr

ROWS = {'fhir': 'fhir-r5-observation', 'dwc': 'dwc-occurrence'}


def main(argv):
    if len(argv) < 3 or argv[0] not in ('to', 'back') or argv[1] not in ROWS:
        print(__doc__.strip().split('\n\n')[1])
        return 2
    row = ROWS[argv[1]]
    ROOT = os.path.dirname(HERE)
    try:
        if argv[0] == 'to':
            imp = importlib.import_module('import')
            I = imp.Import(ROOT, row, keep='bean')
            I.source(argv[2])
            sys.stdout.write(I.beans_text(with_act=False))
            n = 0
            for at, f, why in I.account.each:
                print(f"not carried: {at}: {f}", file=sys.stderr)
                n += 1
            return 0
        exp = importlib.import_module('export')
        E = exp.Export(ROOT, row)
        if argv[1] == 'fhir':
            out, listed = E.text([argv[2]], ids=argv[3:] or None)
        else:
            out, listed = E.text(argv[2:])
    except Exception as e:                       # noqa: BLE001 — a refusal is said, as the tool always said it
        from core.crosswalk import Refused
        from core import formats
        if isinstance(e, (Refused, formats.Refused)):
            print(f"crosswalk: refused — {e}", file=sys.stderr)
            return 1
        raise
    sys.stdout.write(out)
    for m in listed:
        print(f"not carried: {m}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
