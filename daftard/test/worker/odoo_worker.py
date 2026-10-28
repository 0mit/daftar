"""odoo_worker — the garden worker as daftard runs it, for the tests that ask Odoo's calls of it: python/garden_worker.py
and its odoo_rpc.py written into a folder of their own (as daftard writes them into its state folder), started in a
garden of the core (`DAFTAR_KIND=core`), one JSON request a line. Not a suite: the suites import it.

    w = Worker(garden)                                   # or Worker(garden, mutate={'garden_worker.py': (old, new)})
    w.kw('ana', 'hr.department', 'web_search_read', [], domain=[], specification={'name': {}})
    w.call('odoo_asof', {'at': '2026-10-11'})
    w.close()
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PY_DIR = Path(__file__).resolve().parent.parent.parent / 'python'


class Worker:
    def __init__(self, garden, mutate=None, py_dir=PY_DIR, scratch=None, series='17.0', env=None, stderr=None):
        self.dir = Path(tempfile.mkdtemp(prefix='worker-', dir=scratch))
        self.series = series
        for name in ('garden_worker.py', 'odoo_rpc.py', 'register.py'):
            if not (Path(py_dir) / name).is_file():          # a tree from before the module was written
                continue
            src = (Path(py_dir) / name).read_text(encoding='utf-8')
            if mutate and name in mutate:
                old, new = mutate[name]
                if src.count(old) != 1:
                    raise AssertionError(f'the mutation does not apply to {name}: {old!r}')
                src = src.replace(old, new)
            (self.dir / name).write_text(src, encoding='utf-8')
        env = dict(os.environ, DAFTAR_KIND='core', PYTHONUTF8='1', **(env or {}))
        self.p = subprocess.Popen([sys.executable, '-X', 'utf8', str(self.dir / 'garden_worker.py')], cwd=str(garden),
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr or subprocess.DEVNULL,
                                  text=True, encoding='utf-8', env=env)
        self.n = 0

    def call(self, method, params):
        """One request; its result, or {'error': …} where the worker refused or failed."""
        self.n += 1
        self.p.stdin.write(json.dumps({'id': self.n, 'method': method, 'params': params}) + '\n')
        self.p.stdin.flush()
        got = json.loads(self.p.stdout.readline())
        return got.get('result') if got.get('ok') else {'error': got.get('error')}

    def rpc(self, reader, path, payload, asof=None, lang='en_US'):
        """One call of Odoo's client, at its path, as daftard hands it to the worker."""
        return self.call('odoo_rpc', {'path': path, 'reader': reader, 'series': self.series, 'lang': lang,
                                      'payload': payload, **({'asof': asof} if asof else {})})

    def kw(self, reader, model, method, args=(), asof=None, **kwargs):
        """One call_kw of Odoo's client: the model's method, with its args and kwargs."""
        return self.rpc(reader, f'/web/dataset/call_kw/{model}/{method}',
                        {'model': model, 'method': method, 'args': list(args), 'kwargs': kwargs}, asof)

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=60)
