#!/usr/bin/env python3
"""register_worker — daftard's own garden worker, its records given by a register in place of the garden's crosswalks:
what the acceptance of Odoo's own search tests runs daftard's worker as (test/odoo-search/README.md).

    python3 register_worker.py [-X utf8] <daftard's garden_worker.py>      (the register: $DAFTAR_ODOO_REGISTER)

daftard starts a garden's worker as `<python> -X utf8 <its garden_worker.py>`; the acceptance gives its garden this
file's wrapper as that python. It loads daftard's own worker, as daftard wrote it into its state folder, and changes
ONE thing: the records a call is answered over (OdooReading.records) are read from the register — the records of the
mock server data of the test being run, as Odoo's own MockServer holds them — instead of from the garden's beans
through the law's crosswalks. Everything else is daftard's: the Odoo origin and its seat, the worker's dispatch, the
views and fields it reads from the garden's captures, the reader's favourites from their own ref, and the answerer
(python/odoo_rpc.py). Odoo's test models (`partner`, `foo`) are no facts of any garden, and the law has no crosswalk
for them; carrying them through invented statements would test invention. That the crosswalks read a garden's beans
as Odoo's models, and that grants narrow every answer, is proved where it is real: test/worker/records_test.py,
odoo_grants_test.py, and test/render/odoo_hr.mjs over the law's own tables.
"""
import importlib.util
import json
import os
import sys

script = sys.argv[-1]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
spec = importlib.util.spec_from_file_location('garden_worker', script)
gw = importlib.util.module_from_spec(spec)
sys.modules['garden_worker'] = gw
spec.loader.exec_module(gw)          # its module level only: its main() runs below, as its own __main__ would

REGISTER = os.environ.get('DAFTAR_ODOO_REGISTER') or ''
_seen = {'stamp': None, 'models': {}}


def register():
    """{model: {fields, records}} the register holds now, read again when it changed."""
    try:
        stamp = os.stat(REGISTER).st_mtime_ns
    except OSError:
        return {}
    if stamp != _seen['stamp']:
        with open(REGISTER, encoding='utf-8') as fh:
            _seen['models'] = json.load(fh).get('models') or {}
        _seen['stamp'] = stamp
    return _seen['models']


def as_odoo(model, rec, models):
    """A mock server's record as Odoo's server reads it, and as the crosswalks give records: a many2one as
    [id, display name], an x2many its ids."""
    out = dict(rec)
    for name, f in ((models.get(model) or {}).get('fields') or {}).items():
        if f.get('type') == 'many2one' and name in out:
            v = out[name]
            v = v[0] if isinstance(v, list) and v else v
            target = next((r for r in (models.get(f.get('relation')) or {}).get('records') or [] if r.get('id') == v), None)
            out[name] = [v, (target or {}).get('display_name') or (target or {}).get('name') or str(v)] if v else False
        elif f.get('type') in ('one2many', 'many2many') and name in out and not isinstance(out[name], list):
            out[name] = []
    return out


class RegisterReading(gw.OdooReading):
    """A reading whose records are the register's."""

    def records(self, model):
        if model not in self._records:
            models = register()
            self._records[model] = [as_odoo(model, r, models) for r in (models.get(model) or {}).get('records') or []]
        return self._records[model]

    def bean_of(self, model, record_id):
        return None


gw.OdooReading = RegisterReading
os.environ.setdefault('PYTHONUTF8', '1')
gw.main()
