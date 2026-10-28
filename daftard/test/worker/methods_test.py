#!/usr/bin/env python3
"""Every method of the worker over one garden, as daftard calls it: each answers, or refuses with what the person is
told — none fails (status 500, a traceback). The garden is cloned first, with a hub of its own, so nothing is written
in it, and nothing leaves the machine: what a method writes (a save, a decision, a sync step) is written in the clone.

    python3 test/worker/methods_test.py [<garden> | <daftar tree>] [--kind core|board] [--tools <tree>] [--json <file>]

A garden of the core is `core`; a garden served by another tree's board is `board`, with `--tools` that tree (its
board/model.py and exchange/). Given a daftar tree (default ~/daftar), as the README's loop gives every test, a garden
is grown from it by its own test/grow.py, with a need waiting on its gardener. Each method's answer is printed with its
time; `--json` keeps them.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, '..', '..', 'python', 'garden_worker.py')


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


class Worker:
    def __init__(self, root, kind, tools):
        env = dict(os.environ, DAFTAR_KIND=kind, DAFTARD_NOTIFY='off', PYTHONUTF8='1')
        if tools:
            env['DAFTAR_TOOLS'] = tools
        self.p = subprocess.Popen([sys.executable, os.path.abspath(WORKER)], cwd=root, env=env, text=True,
                                  encoding='utf-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)
        self.n = 0

    def call(self, method, params=None):
        self.n += 1
        t = time.monotonic()
        self.p.stdin.write(json.dumps({'id': self.n, 'method': method, 'params': params or {}}) + '\n')
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        took = time.monotonic() - t
        if not line:
            return {'ok': False, 'error': {'status': 500, 'message': 'the worker ended', 'kind': 'failed'}}, took
        return json.loads(line), took

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=60)


def grown(tree, tmp):
    """A garden of the core grown from a daftar tree by its own test/grow.py, Sam its gardener, and — where its release
    reads what waits as needs — a need on his bean waiting for him."""
    sys.path.insert(0, os.path.join(tree, 'test'))
    import grow
    rel = grow.release(os.path.join(tmp, 'release'))
    root = os.path.join(tmp, 'grown')
    r = grow.garden(rel, root, 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    assert r.returncode == 0, r.out[-600:]
    if os.path.isfile(os.path.join(root, 'bin', 'waiting.py')):
        p = os.path.join(root, 'beans', 'sam.md')
        text = open(p, encoding='utf-8').read()
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text.replace('\n---\n', '\n  - need: { id: roof-mended, by: self, of: "the roof mended before winter", '
                                            'from: sam, note: "class D" }\n  - say: { by: sam, of: [roof-mended], at: now }'
                                            '\n---\n', 1))
        r = grow.run(sys.executable, 'bin/save.py', 'sam', 'a need waiting on Sam', '--body',
                     '- action: [[sam]] needs the roof mended before winter', cwd=root)
        assert r.returncode == 0, r.out[-600:]
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('garden', nargs='?', default=os.path.expanduser('~/daftar'))
    ap.add_argument('--kind', default='core', choices=('core', 'board'))
    ap.add_argument('--tools')
    ap.add_argument('--json')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='worker-methods-')
    root, hub = os.path.join(tmp, 'garden'), os.path.join(tmp, 'hub.git')
    try:
        src = os.path.abspath(a.garden)
        if not os.path.isfile(os.path.join(src, 'GARDEN.md')) and os.path.isfile(os.path.join(src, 'test', 'grow.py')):
            src = grown(src, tmp)
        subprocess.run(['git', 'clone', '-q', src, root], check=True)
        git(root, 'switch', '-q', '-C', 'measure')
        git(root, 'remote', 'remove', 'origin')
        subprocess.run(['git', 'clone', '-q', '--bare', root, hub], check=True)
        git(root, 'remote', 'add', 'origin', hub)
        git(root, 'fetch', '-q', 'origin')
        git(root, 'branch', '-q', '-u', 'origin/measure', 'measure')
        if os.path.isfile(os.path.join(root, 'bin', 'install.py')):    # its gate, as every clone daftard serves has it
            subprocess.run([sys.executable, 'bin/install.py'], cwd=root, check=True, capture_output=True)
        w = Worker(root, a.kind, a.tools and os.path.abspath(a.tools))
        got = []

        def call(method, params=None):
            r, took = w.call(method, params)
            e = r.get('error') or {}
            dirty = git(root, 'status', '--porcelain')
            verdict = 'ok' if r.get('ok') else ('failed' if e.get('status', 500) >= 500 and e.get('kind') != 'clock'
                                                else 'refused')
            said = json.dumps(r.get('result'), ensure_ascii=False, default=str) if r.get('ok') else \
                f"{e.get('status')} {e.get('message', '')}"
            if dirty and verdict != 'failed':      # what a method writes is committed, or put back: never left
                verdict, said = 'failed', 'left uncommitted: ' + ' '.join(dirty.split())[:200]
                subprocess.run(['git', 'stash', '-q', '-u'], cwd=root)
            got.append({'method': method, 'verdict': verdict, 'seconds': round(took, 3), 'said': said[:160],
                        'diagnostic': (e.get('diagnostic') or said or '')[-1200:] if verdict == 'failed' else ''})
            print(f"{verdict:8} {took:7.3f}s  {method:16} {said[:110]}")
            return r.get('result') if r.get('ok') else None

        me = call('hello') or {}
        gardener = ((me.get('identity') or me) if isinstance(me, dict) else {}).get('gardener') or ''
        call('session_info')
        call('payload')
        call('books')
        call('history', {'ref': gardener})
        call('calendar')
        call('view_html')
        pages = (call('view_pages', {}) or {}).get('pages') or []
        first = next((p.get('bean') for p in pages if isinstance(p, dict) and p.get('bean')), '')
        call('view_page', {'page': first, 'lang': 'en', 'reader': gardener})
        call('view_style', {'page': first})
        call('view_write', {'reader': gardener, 'body': {}})
        call('view_act', {'reader': gardener, 'body': {}, 'lang': 'en'})
        call('prefs_check', {'prefs': {}})
        call('prefs_zones')
        call('prefs_bean', {'reader': gardener, 'prefs': {}})
        call('prefs_from_bean', {'text': ''})
        call('save', {'body': {}})
        call('follow_up', {'actor': gardener, 'act': 'write', 'bean': gardener})
        leads = call('leads') or []
        kinds = [('need' if x.get('kind') == 'pending' and '.' in str(x.get('id')) else x.get('kind'))
                 for x in leads if isinstance(x, dict)]
        print(f"         leads: {len(leads)} ({', '.join(f'{k} {kinds.count(k)}' for k in sorted(set(kinds)))})")
        queued = next((x for x in leads if x.get('kind') == 'pending' and '.' not in x['id']), None)
        p = call('pending', {'id': queued['id'] if queued else 'nothing-waits'})
        call('decide_pending', {'id': queued['id'] if queued else 'nothing-waits', 'decision': 'acked',
                                'digest': (p or {}).get('digest', ''), 'words': 'measured', 'request': 'f' * 32})
        needs = [x for x in leads if x.get('kind') == 'pending' and '.' in x['id']]
        need = next((x for x in needs if not x.get('blocked_by') and gardener in x.get('for', '').split(', ')), None)
        if need:                       # a need not met: its landing, its bean's list, and the gardener meeting it
            p = call('pending', {'id': need['id']})
            call('pending', {'id': need['about']})
            call('decide_pending', {'id': need['id'], 'decision': 'answered', 'digest': (p or {}).get('digest', ''),
                                    'words': 'measured', 'request': 'b' * 32})
            call('decide_pending', {'id': need['id'], 'decision': 'acked', 'digest': (p or {}).get('digest', ''),
                                    'words': 'measured «here»', 'request': 'a' * 32})
            for ln in git(root, 'show', '--format=%s', 'HEAD').splitlines():
                if ln.startswith(('+  - meet:', '+  - say:')) or ln.startswith('Met '):
                    print('         wrote ' + ln)
            after = call('leads') or []
            left = sum(1 for x in after if x.get('kind') == 'pending' and '.' in x['id'])
            print(f"         needs: {len(needs)} before the meet, {left} after")
            assert left == len(needs) - 1 and not any(x['id'] == need['id'] for x in after), (len(needs), left)
        call('proposal', {'id': 'PROPOSAL-none'})
        call('take_proposal', {'id': 'PROPOSAL-none', 'fingerprint': '', 'request': 'e' * 32})
        call('person', {'id': gardener})
        call('clock')
        call('may_send', {'party': gardener})
        call('action', {'id': 'nothing.waits'})
        call('courses', {'id': gardener})
        call('act', {'id': 'nothing.waits', 'do': 'ratify', 'who': gardener})
        call('served_person', {'id': gardener})
        call('served_read', {'person': gardener, 'id': gardener})
        mapping = next((n[:-3] for n in sorted(os.listdir(os.path.join(root, 'mappings')))
                        if n.endswith('.md')), None) if os.path.isdir(os.path.join(root, 'mappings')) else None
        if mapping:                    # a mapping is a bean of the garden too: read by the gardener, its courses drawn
            r = call('served_read', {'person': gardener, 'id': mapping})
            call('courses', {'id': mapping})
            assert (r or {}).get('id') == mapping, r
        call('served_leads', {'person': gardener})
        call('served_forms', {'person': gardener})
        call('served_submit', {'person': gardener, 'id': 'nothing', 'answers': {}})
        call('form_answers', {'id': 'nothing.nobody.20261028T000000'})
        call('take_form', {'id': 'nothing.nobody.20261028T000000', 'request': 'd' * 32})
        call('served_passkeys', {'person': gardener})
        call('passkey_lay', {'person': gardener, 'anchor': {}})
        call('passkey_laid', {'id': 'nobody.20261028T000000'})
        call('take_passkey', {'id': 'nobody.20261028T000000', 'request': 'c' * 32})
        call('odoo_session', {'series': '17.0', 'reader': gardener, 'lang': 'en'})
        call('odoo_rpc', {'series': '17.0', 'reader': gardener, 'path': '/web/dataset/call_kw',
                          'payload': {'params': {'model': 'res.partner', 'method': 'search_read', 'args': [],
                                                 'kwargs': {}}}})
        call('odoo_asof', {'at': 'HEAD'})
        call('routines_tick')
        call('probe_round', {'every': 30})
        os.mkdir(os.path.join(tmp, 'probes'))
        call('probe_round', {'every': 30, 'dir': os.path.join(tmp, 'probes')})
        call('routines_cross', {'readings': []})
        call('exchange_round')
        call('sync_step')
        call('sync_merge', {'who': gardener})
        w.close()
        if a.json:
            with open(a.json, 'w', encoding='utf-8') as f:
                json.dump(got, f, ensure_ascii=False, indent=1)
        src = open(WORKER, encoding='utf-8').read()          # every method of the worker's table, and none left out
        table = re.search(r'^METHODS = \{f.__name__: f for f in \((.*?)\)\}', src, re.S | re.M).group(1)
        unasked = sorted(set(re.findall(r'[a-z_]+', table)) - {x['method'] for x in got})
        for m in unasked:
            got.append({'method': m, 'verdict': 'failed', 'seconds': 0, 'said': 'never asked here',
                        'diagnostic': f'{m} is in the worker\'s METHODS and this test asks it nothing'})
        failed = [x for x in got if x['verdict'] == 'failed']
        for x in failed:
            print(f"--- {x['method']}\n{x['diagnostic']}")
        print(f"{'FAIL' if failed else 'PASS'}: worker methods ({a.kind}) — {len(got)} called, "
              f"{sum(x['verdict'] == 'ok' for x in got)} answered, {sum(x['verdict'] == 'refused' for x in got)} "
              f"refused, {len(failed)} failed")
        return 1 if failed else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
