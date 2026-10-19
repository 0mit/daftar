#!/usr/bin/env python3
"""transfer — a copy, a move or a verification of data as a course on the storage profile's walk `walk-transfer`, kept
in a store beside the holdings it makes (core 2.19; assets/storage/README.md).

    python3 assets/storage/bin/transfer.py setup --by <being>               the walk written into this garden's mappings
    python3 assets/storage/bin/transfer.py start --store S --to <being> --dataset <blake3> [--from <being>]
                                             [--total <bytes>] [--note T] [--by B]   a course: its need and its first move
    python3 assets/storage/bin/transfer.py move <course> <step> [--as R] [--why W] [--done N] --store S
    python3 assets/storage/bin/transfer.py show [<course>] --store S [--json]       each course, its step and what is left

A TRANSFER IS A COURSE (MODEL.md, Lines; the same shape as a run's, bin/run.py). What it fills — a volume, a folder —
is placed on the walk, `be: { id: <course>, by: <destination>, at: walk-transfer, as: order }`, and needs the dataset it
is to hold, `need: { id: <course>-need, by: <destination>, of: store:content:<c-…>, from: <source> }`, the content of the
manifest being copied (core/law/formats.yaml `checksums`). Each step it reaches is a `move`, and when it is verified the
course meets its need, `meet: { by: <destination>#<course>, of: <destination>#<course>-need }`. The work is done by runs
(bin/run.py): a course outlives a run, a reboot and an unplugged disk, and where it stands is read from its last move.
How far it has come — bytes done of bytes in all — is its detail `transfers.<course>`, which a page shows. The walk:

    queued      asked for: waits for its source and its destination               -> copying
    copying     the dataset's contents are written to the destination             -> verifying, paused, failed, stopped
    verifying   every content written is read back and its digest compared       -> done, copying, failed
    paused      its source or its destination is gone, or a person asked (a pause: it returns to where it was)
    done        every content of the dataset is held at the destination, found whole   (final)
    failed      mismatch, target-full, raised                                     (a way out, final)
    stopped     asked                                                             (a way out, final)

It writes only to the store named and, with `setup`, the garden's mappings; it copies nothing itself.
"""
import argparse
import json
import os
import re
import secrets
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'bin')]
import parse as dmparse  # noqa: E402,F401 — UTF-8 on stdout and stderr
import store as dmstore  # noqa: E402

WALK = 'walk-transfer'
STEPS = {   # the walk, as mappings/walk-transfer.md says it
    'queued': {'to': ['copying']},
    'copying': {'to': ['verifying', 'paused', 'failed', 'stopped']},
    'verifying': {'to': ['done', 'copying', 'failed']},
    'paused': {'resumes': True, 'reasons': ['asked', 'source-gone', 'target-gone']},
    'done': {'final': True},
    'failed': {'exit': True, 'final': True, 'reasons': ['mismatch', 'target-full', 'raised']},
    'stopped': {'exit': True, 'final': True, 'reasons': ['asked']},
}
STEP_SAYS = {
    'queued': 'asked for: it waits for its source and its destination to be there',
    'copying': "the dataset's contents are written to the destination, each from a holding of it",
    'verifying': 'every content written is read back and its digest compared with its name',
    'paused': "its source or its destination is gone, or a person asked; it returns to where it was",
    'done': 'every content of the dataset is held at the destination, found whole: its need is met',
    'failed': 'a content read back differs from its name, the destination is full, or the work raised',
    'stopped': "it was ended at someone's word",
}
MACHINE = (os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'host')).split('.')[0].lower()


class Refused(Exception):
    pass


def moment(t=None):
    t = time.time() if t is None else t
    lt = time.localtime(t)
    off = lt.tm_gmtoff // 60
    return time.strftime('%Y-%m-%dT%H:%M:%S', lt) + f".{int(t * 1000) % 1000:03d}{'+' if off >= 0 else '-'}" \
        f"{abs(off) // 60:02d}:{abs(off) % 60:02d}"


def walk_mapping(by, owner):
    """mappings/walk-transfer.md as this tool writes it: the steps and reasons of STEPS, made by `by`, owned by `owner`."""
    q = json.dumps
    lines = [f'  - make: {{ by: {by}, at: now, note: "written by assets/storage/bin/transfer.py setup: the storage '
             f'profile\'s walk of a transfer" }}', f'  - own: {{ id: own, by: {owner}, of: self }}']
    for st, d in STEPS.items():
        roles = [f'id: {st}', f'as: {q(STEP_SAYS[st])}']
        if d.get('to'):
            roles.append(f"to: [{', '.join(d['to'])}]")
        w = {k: ('"true"' if v is True else '[' + ', '.join(v) + ']') for k, v in d.items() if k != 'to'}
        if w:
            roles.append('walk: { ' + ', '.join(f'{k}: {v}' for k, v in w.items()) + ' }')
        lines.append(f"  - step: {{ {', '.join(roles)} }}")
    return ('---\nbean: walk-transfer\nkind: procedure\ntitle: "walk-transfer — how a copy, a move or a verification of '
            'data goes, from asked to held"\nsummary: "The storage profile\'s walk (assets/storage/bin/transfer.py): '
            'queued, copying, verifying, perhaps paused, then done, failed or stopped. What a transfer fills is placed on '
            'this walk as a course, needing the dataset it is to hold."\nstatements:\n' + '\n'.join(lines) +
            '\n---\n\nThe steps of a transfer, as assets/storage/bin/transfer.py holds them (`STEPS`). A course on this '
            'walk is a `be` of the being it fills, `as: order`; it needs the dataset it is to hold, and meets that need '
            'when every content is found whole there. Its work is done by runs, so it outlives each of them.\n')


def setup(root, by, owner):
    """The walk in this garden: written where it has none, else its steps checked against STEPS."""
    p = os.path.join(root, 'mappings', 'walk-transfer.md')
    vocab = os.path.join(root, 'VOCAB.md')
    if not re.search(r'kind:\s*procedure\b', open(vocab, encoding='utf-8').read() if os.path.isfile(vocab) else ''):
        raise Refused('setup needs, first, the kind of a walk in VOCAB.md (a RULE-CHANGE, saved as one): '
                      'kinds: - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }')
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(walk_mapping(by, owner))
        return p, 'written: save it with its journal entry (bin/save.py)'
    from core import engine
    b = engine._bean(p, WALK)
    have = {r.get('id'): r for _i, v, r in b.items if v == 'step'}
    differ = sorted(set(have) ^ set(STEPS)) + sorted(s for s in set(have) & set(STEPS)
                                                    if list(have[s].get('to') or []) != STEPS[s].get('to', []))
    if differ:
        raise Refused(f"{p} holds another walk: its steps {', '.join(differ)} differ from this tool's")
    return p, 'the same walk: nothing to write'


class Transfers:
    """The courses of a store on walk-transfer, read and written through bin/store.py (one universe)."""

    def __init__(self, store, root=ROOT):
        self.S = dmstore.open_store(store, root=root) if not os.path.sep in store else dmstore.Store(store, root=root)

    def courses(self):
        """{course: (destination, note)} of every course on the walk the store keeps."""
        out = {}
        if 'be' not in self.S.verbs():
            return out
        for being, sid, roles in self.S.statements_of('be'):
            if roles.get('at') == WALK and roles.get('as') == 'order':
                out[sid] = (being, roles.get('note'))
        return out

    def moves(self, course):
        dest = self.courses().get(course, (None,))[0]
        if dest is None:
            raise Refused(f"{course}: no course on {WALK} in this store")
        out = []
        for _v, r, _a in [x for x in self.S.get(dest) if x[0] == 'move']:
            if r.get('through') == f'{dest}#{course}':
                at = r.get('at') or []
                out.append({'at': at[0] if at else None, 'step': str(at[1]).split('#')[-1] if len(at) > 1 else None,
                            'as': r.get('as'), 'why': r.get('why'), 'by': r.get('by')})
        return sorted(out, key=lambda m: str(m['at']))

    def start(self, dest, dataset, source=None, total=None, note=None, by=None):
        cid = f"tr-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"
        if not re.fullmatch(r'[0-9a-f]{64}', str(dataset)):
            raise Refused(f"{dataset!r}: a dataset is named by the BLAKE3 of its manifest, 64 lowercase hex digits")
        cont = 'c-' + dataset[:24]
        with self.S.batch():
            self.S.being(MACHINE, 'host') if not self.S.has_bean(MACHINE) and not self.S.kind_of(MACHINE) else None
            self.S.being(dest)
            if not self.S.has_bean(cont) and not self.S.kind_of(cont):
                self.S.being(cont, 'content')
            self.S.put(dest, 'make', {'id': f'{cid}-made', 'by': MACHINE, 'at': moment()}, judge=False)
            self.S.put(dest, 'be', {'id': cid, 'by': dest, 'at': WALK, 'as': 'order',
                                    **({'note': note} if note else {})}, act=f'{dest}#{cid}-made', judge=False)
            need = {'id': f'{cid}-need', 'by': dest, 'of': cont}
            if source:
                need['from'] = source
            self.S.put(dest, 'need', need, act=f'{dest}#{cid}-made', judge=False)
            self.S.detail(dest, f'transfers.{cid}', {'dataset': dataset, 'total': total, 'done': 0})
        self.move(cid, 'queued', by=by, why='asked')
        return cid

    def move(self, course, step, reason=None, why=None, done=None, by=None):
        if step not in STEPS:
            raise Refused(f"{step!r} is no step of {WALK}: one of {', '.join(STEPS)}")
        if reason is not None and reason not in STEPS[step].get('reasons', ()):
            raise Refused(f"{reason!r} is no reason {step} lists: {', '.join(STEPS[step].get('reasons', ())) or 'none'}")
        dest = self.courses().get(course, (None,))[0]
        if dest is None:
            raise Refused(f"{course}: no course on {WALK} in this store")
        prev = self.moves(course)
        last = prev[-1]['step'] if prev else None
        if last and STEPS[last].get('final'):
            raise Refused(f"{course} has ended ({last}): no move follows a final step")
        if last and step not in STEPS[last].get('to', []) and not STEPS[step].get('resumes') \
                and not STEPS[step].get('exit') and last != 'paused':
            raise Refused(f"{course} is at {last}: it goes on to {', '.join(STEPS[last].get('to', []))}, a pause or a way "
                          f"out, not {step}")
        roles = {'of': dest, 'through': f'{dest}#{course}', 'at': [moment(), f'{WALK}#{step}']}
        if by and (self.S.has_bean(by) or self.S.kind_of(by)):
            roles['by'] = by
        elif by:
            why = f'by {by}' + (f': {why}' if why else '')
        if reason:
            roles['as'] = reason
        if why:
            roles['why'] = why
        with self.S.batch():
            self.S.put(dest, 'move', roles, act=f'{dest}#{course}-made', judge=False)
            d = self.S.detail(dest, f'transfers.{course}') or {}
            if done is not None:
                d['done'] = int(done)
            if step == 'done':
                d['done'] = d.get('total') or d.get('done')
                self.S.put(dest, 'meet', {'id': f'{course}-met', 'by': f'{dest}#{course}', 'of': f'{dest}#{course}-need'},
                           act=f'{dest}#{course}-made', judge=False)
            self.S.detail(dest, f'transfers.{course}', d)

    def show(self, course=None):
        out = []
        for cid, (dest, note) in sorted(self.courses().items()):
            if course and cid != course:
                continue
            ms = self.moves(cid)
            d = self.S.detail(dest, f'transfers.{cid}') or {}
            out.append({'course': cid, 'to': dest, 'note': note, 'step': ms[-1]['step'] if ms else None,
                        'since': ms[-1]['at'] if ms else None, 'dataset': d.get('dataset'), 'done': d.get('done'),
                        'total': d.get('total'), 'moves': ms})
        return out


def main(argv):
    ap = argparse.ArgumentParser(prog='transfer.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('setup')
    x.add_argument('--by', required=True, help='who writes the walk: a being of this garden')
    x.add_argument('--owner', default=None)
    x = sub.add_parser('start')
    x.add_argument('--store', required=True)
    x.add_argument('--to', required=True)
    x.add_argument('--dataset', required=True)
    x.add_argument('--from', dest='source')
    x.add_argument('--total', type=int)
    x.add_argument('--note')
    x.add_argument('--by')
    x = sub.add_parser('move')
    x.add_argument('course')
    x.add_argument('step')
    x.add_argument('--store', required=True)
    x.add_argument('--as', dest='reason')
    x.add_argument('--why')
    x.add_argument('--done', type=int)
    x.add_argument('--by')
    x = sub.add_parser('show')
    x.add_argument('course', nargs='?')
    x.add_argument('--store', required=True)
    x.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'setup':
            p, what = setup(os.getcwd(), a.by, a.owner or a.by)
            print(f"{p}: {what}")
            return 0
        T = Transfers(a.store, root=os.getcwd())
        if a.cmd == 'start':
            print(T.start(a.to, a.dataset, a.source, a.total, a.note, a.by))
        elif a.cmd == 'move':
            T.move(a.course, a.step, a.reason, a.why, a.done, a.by)
        else:
            rows = T.show(a.course)
            if a.json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            for r in [] if a.json else rows:
                left = '' if not r['total'] else f" · {r['done'] or 0:,} of {r['total']:,} bytes"
                print(f"{r['course']}  {r['step'] or '?':10} to {r['to']}{left}  {r['note'] or ''}")
        return 0
    except (Refused, dmstore.StoreError) as e:
        print(f"transfer: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
