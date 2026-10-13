#!/usr/bin/env python3
"""What is held off git is opened only by a grant that NAMES it (RULE-CHANGE 2026-10-12): a sealed statement, like a
held contact, is read and written only by the gardener, or by a reader a grant names it to — its part in `cover`, or the
statement in `of` — never by a grant of the whole bean; and only while the word it is held on stands.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it on a machine whose store keeps
what is held; Ali agrees with Sam on a camera, and Ali's phone is sealed on that store while that agreement stands. Three
readers, each kept under an opaque id, may read Ali's bean whole: the first may also write it whole; the second is
granted the `name` statements of Ali's bean, by name, to read and to write; the third Ali's phone itself, by its id, to
read. Then:

  the law       bin/pass.py `may`, asked with `held`: the phone is opened to Sam, to the second and to the third, never
                to the first, whose grant is of the whole bean; asked without it, the whole bean is opened as before
  the page      the page a host gives each (view_engraved.scoped, asked of the law's own grants): the phone's value to
                Sam, the second and the third; to the first, where it is kept and nothing of it
  the write     the view's one write path: the first, who may write Ali's bean whole, is refused the phone; the second
                changes it, sealed in the store, the commit keeping only the pointer; a host whose own `may` cannot ask
                the held bar (one from before it) has the phone written for the gardener alone
  the consent   the agreement the phone is held on cannot be taken out while it is held on it: the gate refuses it

Run: python3 test/view_held_named.py   (0 = green)
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
A, B, C = 'p-0a0a0a0a', 'p-0b0b0b0b', 'p-0c0c0c0c'
PHONE, NEW = '+15555550100', '+15555550177'


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=grow.ENV)
    out = r.stdout + r.stderr
    if 'Traceback' in out:
        TRACES.append(out[-1200:])
    return r.returncode, out


def put(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def last_json(out):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-held-named-')
REL, G, STORE = os.path.join(T, 'release'), os.path.join(T, 'garden-sam'), os.path.join(T, 'vault')
HOST = socket.gethostname().lower()
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
# the law's answer with and without `held`, for each reader
LAW = """import importlib, json, sys; sys.path.insert(0, 'bin'); dmpass = importlib.import_module('pass')
out = {}
for u in ('sam', %r, %r, %r):
    try:
        out[u] = [dmpass.may(u, 'read', 'ali', positions=['phone'], root='.', held=True).granted,
                  dmpass.may(u, 'read', 'ali', positions=['phone'], root='.').granted]
    except TypeError as e:
        out[u] = 'error: ' + str(e)
print(json.dumps(out))""" % (A, B, C)
# the page a host gives each reader, asked of the law's own grants (as view_serve.Host.may asks it)
SCOPED = """import importlib, json, os, sys, types
sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve, view_serve as vs
vm.init('.', 'page')
dmpass = importlib.import_module('pass')
USERS = ('sam', %r, %r, %r)
def may(user, bean, positions=None, write=False, held=False):
    kw = {'held': True} if held else {}
    a = dmpass.may(user, 'write' if write else 'read', bean, positions=positions, root='.', gardener='sam', **kw)
    return vs.Verdict(a.granted, a.why, a.grants, a.reason_asked)
host = types.SimpleNamespace(cfg={'users': {u: {'bean': u} for u in USERS}}, head='h', gardener='sam', may=may)
out = {}
for u in USERS:
    s = (ve.scoped(host, u).get('sheets') or {}).get('ali') or {}
    out[u] = [x for r in s.get('rows') or [] for x in r['statements'] if x.get('key') == 'name#phone']
print(json.dumps(out, default=str, ensure_ascii=False))""" % (A, B, C)
# a write of the phone by the view's one write path, as `who`; `old` gives a host's `may` from before the held bar
WRITE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_write
who, value, old = sys.argv[1], sys.argv[2], sys.argv[3] == 'old'
may = (lambda act, bean, positions=None: True) if old else None
r = view_write.write('.', who, 'ali', [{'op': 'change', 'key': 'name#phone', 'held': True,
                                        'roles': {'by': 'e164', 'of': 'self', 'as': value}}], may=may)
print(json.dumps({k: r.get(k) for k in ('ok', 'refusals')}))"""


def phone_in_store():
    m = re.search(r'root:vault/[0-9a-f]{32}', get('beans/ali.md'))
    return run(PY, 'bin/held.py', 'resolve', m.group(0))[1] if m else ''


try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    os.makedirs(STORE, exist_ok=True)
    put('VOCAB.md', get('VOCAB.md').replace(
        "namespaces: []\n",
        "namespaces:\n  - { namespace: anchor-hostname, once: \"false\", meaning: \"a machine's own name for itself\" }\n", 1))
    put('beans/laptop.md', f'''---
bean: laptop
kind: host
title: "laptop"
summary: "Sam's laptop: the garden, and the store its held values are kept in."
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
details:
  roots:
    vault: {{ system: unix-filesystem, at: "{HOST}:{STORE}", keeps: special-category, readable_from: this-host }}
---
The laptop.
''')
    put('beans/ali.md', f'''---
bean: ali
kind: person
title: "Ali"
summary: "Ali, who shares a camera with Sam."
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: theone, of: self }}
  - answer: {{ by: self, of: self, as: law }}
  - name:   {{ id: phone, by: e164, of: self, as: "{PHONE}" }}
---
Ali.
''')
    put('beans/camera.md', '''---
bean: camera
kind: contract
title: "camera"
summary: "Sam and Ali bought a camera together"
statements:
  - say:   { by: sam, at: now }
  - own:   { by: theone, of: self }
  - agree: { id: agreed, by: [sam, ali], of: self, through: spoken, at: "2026-09-01" }
---
A camera.
''')
    for rid in (A, B, C):
        put(f'beans/{rid}.md', f'''---
bean: {rid}
kind: person
title: "{rid}"
summary: "a reader of the garden's pages"
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: theone, of: self }}
---
A reader.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "Ali's sheet"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: ali-sheet, by: self, of: [ali], drawing: {{ label: Ali, archetype: sheet, {STORY.format(p="Ali's facts")} }} }}
  - draw: {{ id: page, by: self, of: [ali-sheet], page: {{ fields: [ {{ kind: person, fact: name, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'Ali, the camera, three readers and a page', '--body',
                  f'- action: wrote [[laptop]], [[ali]], [[camera]], [[{A}]], [[{B}]], [[{C}]] and [[page]]. '
                  'RULE-CHANGE: VOCAB.md names the namespace a machine names itself in.')
    check("the garden is saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])
    rc, out = run(PY, 'bin/held.py', 'put', 'ali', 'phone', '--basis', 'camera#agreed')
    rc2, out2 = run(PY, 'bin/save.py', 'sam', "Ali's phone, held off git", '--body', "- action: sealed [[ali]]'s phone",
                    '- held: ali phone added')
    check("Ali's phone is sealed on the machine's store while the camera's agreement stands, and saved",
          rc == 0 and rc2 == 0 and PHONE not in get('beans/ali.md') and 'while: "camera#agreed"' in get('beans/ali.md'),
          out + out2[-800:])
    put('beans/sam.md', get('beans/sam.md').replace('\n---\n', (
        '\n  - grant: { id: a-reads, by: self, to: [%s], of: [ali, page], as: read }\n'
        '  - grant: { id: a-writes, by: self, to: [%s], of: [ali], as: write }\n'
        '  - grant: { id: b-reads, by: self, to: [%s], of: [ali, page], as: read }\n'
        '  - grant: { id: b-names, by: self, to: [%s], of: [ali], as: read, cover: { parts: [name] } }\n'
        '  - grant: { id: b-writes, by: self, to: [%s], of: [ali], as: write, cover: { parts: [name] } }\n'
        '  - grant: { id: c-reads, by: self, to: [%s], of: [ali, page], as: read }\n'
        '  - grant: { id: c-phone, by: self, to: [%s], of: ["ali#phone"], as: read }\n'
        '  - say: { by: sam, of: [a-reads, a-writes, b-reads, b-names, b-writes, c-reads, c-phone], at: now }\n---\n')
        % (A, A, B, B, B, C, C), 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'three readers granted Ali', '--body',
                  f'- action: [[sam]] grants [[{A}]], [[{B}]] and [[{C}]] to read [[ali]] and [[page]]')
    check("the grants are saved: the first reader's of Ali's whole bean, the second's naming `name`, the third's naming "
          "the phone", rc == 0 and '0 error(s)' in out, out[-1500:])

    L = last_json(run(PY, '-c', LAW)[1])
    check("the law: asked with `held`, the phone is opened to Sam, to the reader a grant names `name` to and to the one "
          "a grant names the phone to — never to the reader granted Ali's whole bean",
          L.get('sam') == [True, True] and L.get(B) == [True, True] and L.get(C) == [True, True]
          and L.get(A) == [False, True], L)
    P = last_json(run(PY, '-c', SCOPED)[1])
    vals = {u: [((x.get('roles') or {}).get('as'), bool(x.get('held'))) for x in P.get(u) or []] for u in ('sam', A, B, C)}
    check("the page: the phone's value to Sam and to the readers a grant names it to", all(
        vals[u] == [(PHONE, True)] for u in ('sam', B, C)), (vals, P.get('error')))
    check("...and to the reader granted Ali's whole bean, where it is kept and nothing of it", vals[A] == [(None, True)],
          (vals, P.get('error')))

    W = last_json(run(PY, '-c', WRITE, A, NEW, 'new')[1])
    check("the write: the reader who may write Ali's whole bean is refused the phone, and the store keeps it as it was",
          W.get('ok') is False and 'kept off git' in json.dumps(W) and PHONE in phone_in_store(), W)
    W = last_json(run(PY, '-c', WRITE, B, NEW, 'new')[1])
    check("...the reader a grant names `name` to writes it: sealed in the store, the commit keeping only the pointer",
          W.get('ok') is True and NEW in phone_in_store() and NEW not in run('git', 'show', 'HEAD')[1]
          and NEW not in get('beans/ali.md'), (W, phone_in_store()[-200:]))
    W = last_json(run(PY, '-c', WRITE, A, PHONE, 'old')[1])
    check("...a host's `may` from before the held bar (it takes no `held`, and grants all): the phone is not written for "
          "a reader", W.get('ok') is False and NEW in phone_in_store(), W)
    W = last_json(run(PY, '-c', WRITE, 'sam', PHONE, 'old')[1])
    check("...and is written for the gardener alone", W.get('ok') is True and PHONE in phone_in_store(), W)

    before = get('beans/camera.md')
    put('beans/camera.md', before.replace(
        '  - agree: { id: agreed, by: [sam, ali], of: self, through: spoken, at: "2026-09-01" }\n', '', 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'the agreement taken out', '--body',
                  '- action: took out `agreed`, the agree in [[camera]]: the word the phone was held on')
    check("the consent: the agreement the phone is held on is not taken out while the phone is held on it — the gate "
          "refuses it, so the phone is never sent past its word", rc != 0 and 'camera#agreed' in out, out[-600:])
    run('git', 'checkout', '--', '.')
    run('git', 'reset', '-q', '--hard')
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_held_named: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
