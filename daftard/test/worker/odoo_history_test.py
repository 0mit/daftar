#!/usr/bin/env python3
"""The garden as of a commit, and a record's history in Odoo's chatter (design §10.3, P5.4b): the worker, run as daftard
runs it, over a garden grown from a daftar tree whose law crosses res.company and hr.department, saved in five commits.

    1  Acme and Engineering                       (a day in the past: 2026-09-01)
    2  Engineering renamed; Quality under it       (2026-09-15)
    3  Ana granted Acme, Engineering and Quality   (2026-09-20)
    4  Ana's grant of Quality withdrawn            (2026-09-25)
    5  Engineering needs Betamax, a company closed to Ana; the entry names it   (2026-10-01)

The checks: a day, a moment and a commit name the commit the garden is read as of; every call is answered from the
beans of that commit; the grants are today's — a grant withdrawn closes the past, and one given opens it; a record's
chatter is its bean's history, each change with its journal entry and each statement with the act that knows it, up to
the commit read as of; a reader's chatter names nothing closed to them, withholds an entry that does, and a record
closed to them has none. Then the same with the grant check removed from the reading: the reader's checks fail.

    python3 test/worker/odoo_history_test.py <daftar tree>
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
sys.path.insert(0, str(HERE))
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-900:]))
    if not cond:
        FAILS.append(name)


if not os.path.isfile(os.path.join(TREE, 'core', 'law', 'crosswalks.yaml')):
    print(f"odoo_history: {TREE} has no core/law/crosswalks.yaml — give a tree whose law crosses Odoo's models")
    sys.exit(2)
import grow  # noqa: E402
from odoo_worker import Worker  # noqa: E402

T = Path(tempfile.mkdtemp(prefix='odoo-history-'))
G = T / 'garden'
D = 'hr.department'


def org(bid, title, *st):
    (G / 'beans' / f'{bid}.md').write_text(f'---\nbean: {bid}\nkind: org\ntitle: "{title}"\nstatements:\n'
                                           '  - say: { by: sam, at: now }\n' + ''.join(f'  - {x}\n' for x in st)
                                           + f'---\n{title}.\n', encoding='utf-8')


def save(day, what, body):
    env = dict(grow.ENV, GIT_AUTHOR_DATE=f'{day}T12:00:00+03:00', GIT_COMMITTER_DATE=f'{day}T12:00:00+03:00')
    r = grow.run(sys.executable, 'bin/save.py', 'sam', what, '--body', body, cwd=str(G), env=env)
    head = grow.run('git', 'rev-parse', 'HEAD', cwd=str(G)).stdout.strip()
    return r, head


def edit(bid, old, new):
    p = G / 'beans' / f'{bid}.md'
    text = p.read_text(encoding='utf-8')
    assert text.count(old) == 1, (bid, old)
    p.write_text(text.replace(old, new), encoding='utf-8')


def add(bid, *statements):
    """Statements added to a bean already saved, with the act that knows them, as the cookbook adds them."""
    edit(bid, '\n---\n', '\n' + ''.join(f'  - {x}\n' for x in statements) + '---\n')


import hashlib  # noqa: E402


def num(model, bean):
    return int.from_bytes(hashlib.sha256(f'{model}:{bean}'.encode()).digest()[:4], 'big') & 0x7fffffff


try:
    rel = grow.release(str(T / 'release'))
    r0 = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam')
    org('acme', 'Acme', 'represent: { by: sam, of: self, as: "keeps its garden" }')
    org('beta', 'Betamax', 'represent: { by: sam, of: self, as: "keeps its books" }')
    org('eng', 'Engineering', 'part: { by: self, of: acme }')
    r1, c1 = save('2026-09-01', 'Acme, Betamax and Engineering', '- action: wrote [[acme]], [[beta]] and [[eng]]')
    edit('eng', 'title: "Engineering"', 'title: "Engineering and Design"')
    org('qa', 'Quality', 'part: { by: self, of: eng }')
    r2, c2 = save('2026-09-15', 'Engineering renamed; Quality under it', '- action: renamed [[eng]] (its title); wrote [[qa]]')
    (G / 'beans' / 'ana.md').write_text('---\nbean: ana\nkind: person\ntitle: "Ana"\nstatements:\n'
                                         '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
                                         '  - answer: { by: self, of: self, as: law }\n---\nAna.\n', encoding='utf-8')
    (G / 'beans' / 'ana-consent.md').write_text(
        '---\nbean: ana-consent\nkind: contract\ntitle: "Ana agrees to be kept here by name"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
        '  - agree: { id: ana-agrees, by: ana, of: "kept here by name", through: spoken }\n'
        '  - agree: { id: sam-agrees, by: sam, of: "kept here by name", through: spoken }\n---\nHer word.\n',
        encoding='utf-8')
    add('sam', 'grant: { id: ana-reads, by: self, as: read, of: [acme, eng, qa], to: [ana] }',
        'say: { by: sam, of: [ana-reads], at: now }')
    r3, c3 = save('2026-09-20', 'Ana reads Acme, Engineering and Quality',
                  '- action: wrote [[ana]] (on her word, [[ana-consent]]); [[sam]] opens Acme, Engineering and Quality '
                  'to her (ana-reads)')
    text = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    gone = [ln for ln in text.splitlines(keepends=True) if 'ana-reads' in ln]
    (G / 'beans' / 'sam.md').write_text(''.join(ln for ln in text.splitlines(keepends=True) if ln not in gone),
                                         encoding='utf-8')
    add('sam', 'grant: { id: ana-reads-less, by: self, as: read, of: [acme, eng], to: [ana] }',
        'say: { by: sam, of: [ana-reads-less], at: now }')
    r4, c4 = save('2026-09-25', "Ana's grant of Quality withdrawn",
                  '- action: [[sam]] took out the grant ana-reads and the `say` of it; ana-reads-less opens Acme and '
                  'Engineering to Ana, not Quality')
    add('eng', 'need: { id: needs-beta, by: self, of: beta }', 'say: { by: sam, of: [needs-beta], at: now }')
    r5, c5 = save('2026-10-01', 'Engineering needs Betamax', '- action: [[eng]] needs [[beta]] (needs-beta)')
    check('a garden saved in five commits, a month apart, passes its gate at each',
          all(r.returncode == 0 for r in (r0, r1, r2, r3, r4, r5)) and len({c1, c2, c3, c4, c5}) == 5,
          [r.out[-400:] for r in (r1, r2, r3, r4, r5) if r.returncode])
    cap = G / 'captures' / 'views' / 'odoo-17.0'
    fields = {D: {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                  'complete_name': {'type': 'char'}, 'active': {'type': 'boolean'},
                  'parent_id': {'type': 'many2one', 'relation': D},
                  'company_id': {'type': 'many2one', 'relation': 'res.company'}},
              'res.company': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'}}}
    for m, f in fields.items():
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps(f), encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "17.0"}\n', encoding='utf-8')

    def names(w, reader, asof=None):
        got = w.kw(reader, D, 'web_search_read', [], asof=asof, domain=[], specification={'name': {}})
        return sorted(x['name'] for x in got['records']) if isinstance(got, dict) and 'records' in got else got

    def chatter(w, reader, bean, asof=None):
        got = w.rpc(reader, '/mail/thread/messages', {'thread_model': D, 'thread_id': num(D, bean), 'limit': 30}, asof)
        return got.get('messages') if isinstance(got, dict) and 'messages' in got else got

    def c_asof(w):
        a1, a2 = w.call('odoo_asof', {'at': c1}), w.call('odoo_asof', {'at': '2026-09-16'})
        a3, a4 = w.call('odoo_asof', {'at': '2026-09-20 11:00+03:00'}), w.call('odoo_asof', {'at': '2026-08-01'})
        return (a1.get('commit') == c1 and a2.get('commit') == c2 and a3.get('commit') == c2 and 'error' in a4
                and w.call('odoo_asof', {'at': ''}) == {}), (a1, a2, a3, a4)

    def c_as_of_a_commit(w):
        return (names(w, 'sam', c1) == ['Engineering'] and names(w, 'sam', c2) == ['Engineering and Design', 'Quality']
                and names(w, 'sam') == ['Engineering and Design', 'Quality']), (names(w, 'sam', c1), names(w, 'sam', c2))

    def c_grants_as_of_now(w):
        got = (names(w, 'ana', c3), names(w, 'ana', c1), names(w, 'ana'))
        return got == (['Engineering and Design'], ['Engineering'], ['Engineering and Design']), got

    def c_timeline(w):
        sam = chatter(w, 'sam', 'eng')
        tv = [(t['changedField'], t['oldValue']['value'], t['newValue']['value']) for m in sam for t in m['trackingValues']]
        return (len(sam) == 3 and [m['id'] for m in sam] == sorted((m['id'] for m in sam), reverse=True)
                and ('title', 'Engineering', 'Engineering and Design') in tv
                and any(f == 'part' and o == '' and 'of: acme' in v and 'said by sam' in v for f, o, v in tv)
                and any(f == 'need' and 'of: beta' in v and 'said by sam' in v and '2026' in v for f, o, v in tv)
                and 'needs [[beta]]' in sam[0]['body'] and sam[0]['author']['name'] == 'sam'
                and sam[-1]['date'].startswith('2026-09-01')), sam

    def c_timeline_as_of(w):
        return len(chatter(w, 'sam', 'eng', c1)) == 1 and len(chatter(w, 'sam', 'eng', c2)) == 2, chatter(w, 'sam', 'eng', c1)

    def c_reader_timeline(w):
        ana = chatter(w, 'ana', 'eng')
        text = json.dumps(ana)
        return (len(ana) == 3 and 'of: beta' not in text and '[[beta]]' not in text and 'Betamax' not in text
                and 'said by sam' in text and '(closed)' in text and 'closed to you' in ana[0]['body']
                and 'Engineering and Design' in text), ana

    def c_closed_record(w):
        return chatter(w, 'ana', 'qa') == [] and len(chatter(w, 'sam', 'qa')) == 1, chatter(w, 'ana', 'qa')

    def c_thread_data(w):
        d = w.rpc('ana', '/mail/thread/data', {'thread_model': D, 'thread_id': num(D, 'qa'), 'request_list': ['followers']})
        e = w.rpc('ana', '/mail/thread/data', {'thread_model': D, 'thread_id': num(D, 'eng'), 'request_list': ['followers']})
        return d.get('hasReadAccess') is False and e.get('hasReadAccess') is True and e.get('hasWriteAccess') is False, (d, e)

    CHECKS = {'asof': c_asof, 'as of a commit': c_as_of_a_commit, 'grants as of now': c_grants_as_of_now,
              'the timeline': c_timeline, 'the timeline as of a commit': c_timeline_as_of,
              "a reader's timeline names nothing closed to her": c_reader_timeline,
              'a record closed to her has no timeline': c_closed_record,
              'its thread is unreadable to her, and one she may read is read-only': c_thread_data}

    def checks(w):
        out = {}
        for name, fn in CHECKS.items():
            try:
                out[name] = fn(w)
            except Exception as e:                    # an answer of another shape than Odoo's
                out[name] = (False, f'{type(e).__name__}: {e}')
        return out

    w = Worker(G, scratch=str(T))
    got = checks(w)
    w.close()
    for name, (ok, detail) in got.items():
        check(name, ok, detail)
    reading = ("        self.readable = {b for b in G.beans\n"
               "                         if dmpass.may(self.reader, 'read', b, root=str(ROOT), beans=now, gardener=keeper).granted}\n")
    w = Worker(G, {'garden_worker.py': (reading, "        self.readable = set(G.beans)\n")}, scratch=str(T))
    mut = checks(w)
    w.close()
    hers = ['grants as of now', "a reader's timeline names nothing closed to her", 'a record closed to her has no timeline',
            'its thread is unreadable to her, and one she may read is read-only']
    check("with the grant check removed from the reading, each of the reader's checks fails",
          not any(mut[k][0] for k in hers), {k: mut[k][0] for k in hers})
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nodoo_history: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
