#!/usr/bin/env python3
"""Between gardens in the core (v1 part 8): propose, across, pass, held — and the flow law they read, the held store's
form and its check on the host, and the mark a garden carries when it rehearses.

Builds what it needs, as test/core_read.py does: a release of the core made from this tree (v1.0.0), and TWO gardens
grown from it, ada's and ben's, which meet: each records the other as a `garden` bean named by its id, owned by its
gardener, and both agree to a pact.

law: core/law/flows.yaml is what std-vocab generates, each of today's rows a row of the core or dropped with why; the
law whole with its rules; the nearest row decides, a refusal among equals, `ratified` only for the party a
garden's row grants, and a garden's row never unguards. gate: a `pass` the table grants is saved, one it refuses is
refused by rule `layers`. pass: the layer map and the flow law of a garden of the core, and `may` read from `grant`
statements. held: a statement sealed by its id, its record off git with the day it is to be erased, the hook's check on
this host, `due`, `check`, a person minted opaque in statements, and the sealed statement read back. propose: a proposal
made of statements, read, taken and saved through the gate — its acts known in the garden that made them, `take`
stamped by the save — then a second one fused with what the first brought; a stub found by the names it carries; first
contact and a rehearsal refused until settled. across: a value of the other garden read at a commit it publishes,
where it grants it; refused where it does not. translate: today's `test` on a garden bean is `rehearse`, and a record
stamped with another garden is an act known there.

Run: python3 test/core_between.py   (0 = green; about a minute)
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read, translate  # noqa: E402
from core.law import Law  # noqa: E402
import dmparse, dmpass, dmsafe  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])
HOST = socket.gethostname().lower()


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, stdin=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x', PYTHONIOENCODING='utf-8')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd, env=e,
                            input=stdin))


def text(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def write(path, t):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def save(g, who, what, body):
    return run(PY, 'bin/save.py', who, what, '--body', body, cwd=g)


def add(g, bean, statement, by):
    """A statement added to a bean, with the act at `now` that knows it: what a commit adds, an act it adds knows."""
    sid = re.search(r'\bid: ([a-z0-9-]+)', statement).group(1)
    dmsafe.add_statements(os.path.join(g, 'beans', bean + '.md'), f"- {statement}\n- say: {{ by: {by}, of: [{sid}], at: now }}\n")


def clean(g):
    return run('git', 'status', '--porcelain', cwd=g).out.strip() == ''


T = tempfile.mkdtemp(prefix='core-between-')
REL, A, B, STORE = (os.path.join(T, n) for n in ('release', 'garden-a', 'garden-b', 'vault'))

HOSTBEAN = """---
bean: laptop
kind: host
title: "laptop — the machine this runs on"
summary: "The machine both gardens sit on."
statements:
  - read: { by: %s, at: now }
  - own:  { by: %s, of: self }
  - name: { by: anchor-hostname, of: self, as: %s }
details:
  roots:
    vault: { system: unix-filesystem, at: "%s:%s", keeps: special-category, readable_from: this-host }
    gardens: { system: unix-filesystem, at: "%s:%s" }
---
The laptop.
"""
VOCAB = """---
namespaces:
  - { namespace: anchor-hostname, once: "false", meaning: "a machine's own name for itself" }
---
# the garden's own rows
"""

try:
    # ---- THE RELEASE: v1.0.0 of the core, and two gardens grown from it
    law = dmparse.loads(dmparse.split_front_matter(text(os.path.join(ROOT, 'seed', 'std-vocab.md')))[0])
    os.makedirs(REL)
    for f in dmpass.kept([f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))],
                         dmpass.language(text(os.path.join(ROOT, 'seed', 'LANGUAGE'))), dmpass.offered(law)):
        os.makedirs(os.path.join(REL, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(REL, f))
    for f in ('GARDEN.md.template', 'VOCAB.md.template'):
        shutil.copy2(os.path.join(ROOT, 'core', 'guide', f), os.path.join(REL, 'seed', f))
    for c in (('git', 'init', '-q'), ('git', 'add', '-A'), ('git', 'commit', '-qm', 'the core'), ('git', 'tag', 'v1.0.0')):
        run(*c, cwd=REL)
    for g, who, name in ((A, 'ada', 'Ada'), (B, 'ben', 'Ben')):
        r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), g, '--gardener', who, '--gardener-name', name, cwd=T)
        check(f"{who}'s garden grows from v1.0.0 in the core (core@{VERSION}), the four tools between gardens in it",
              r.returncode == 0 and f'core@{VERSION}' in text(os.path.join(g, 'GARDEN.md'))
              and all(os.path.isfile(os.path.join(g, 'bin', f"{v}.py")) and os.path.isfile(os.path.join(g, 'bin', f"dm{v}.py"))
                      for v in ('propose', 'across', 'pass', 'held')), r.out[-800:])
        run(PY, 'bin/install.py', cwd=g)
    IDA = run(PY, 'bin/propose.py', 'id', cwd=A).out.split('"')[1]
    IDB = run(PY, 'bin/propose.py', 'id', cwd=B).out.split('"')[1]
    check("each garden has an id of its own, which `propose.py id` prints", re.fullmatch(r'[0-9a-f]{12}', IDA) and
          re.fullmatch(r'[0-9a-f]{12}', IDB) and IDA != IDB, (IDA, IDB))

    # ---- THE LAW: the flow law generated, rewritten in the pass's valency, decided by the nearest row
    gen = run(PY, 'core/translate.py', 'flows', cwd=ROOT)
    check("law: core/law/flows.yaml is what std-vocab generates (its methods, rows and metadata)",
          gen.returncode == 0 and gen.out == text(os.path.join(ROOT, 'core', 'law', 'flows.yaml')), gen.out[:300])
    L0 = Law.load()
    old = [f['flow'] for f in law.get('flows') or []]
    core_rows = {f.get('flow') for f in L0.flows}
    check(f"law: each of today's {len(old)} rows is a row of the core or dropped with why ({len(L0.flows)} rows, "
          f"{len(L0.flows_dropped)} dropped: {', '.join(L0.flows_dropped)})",
          all(f in core_rows or f in L0.flows_dropped for f in old) and len(L0.flows) + len(L0.flows_dropped) == len(old)
          and not any('to' in f and isinstance(f['to'], dict) for f in L0.flows), sorted(set(old) - core_rows))
    check("law: today's take-down is the act `say`, pass-on and upgrade `forward` and `adopt`; the methods are a table",
          'take-down' not in L0.methods and {'forward', 'adopt', 'stamp'} <= set(L0.methods)
          and L0.decide('words', 'estate', 'say', 'say')[0] and 'forward' in L0.table('verbs'), sorted(L0.methods))
    r = run(PY, 'core/check.py', '--law', cwd=ROOT)
    check("law: the core's law holds together — the flow law, `rehearse`, the acts' `at`, its rules",
          r.returncode == 0 and '21 rules — 0 error(s)' in r.out, r.out[-400:])
    cases = [
        (("words", "estate", "say", "say"), True, "a person's words taken down: words-to-said"),
        (("self", "estate", "edit", "say"), False, "an agent's own output as a said value: model-output-is-no-word"),
        (("self", "estate", "edit", "make"), True, "prose made where it is written: made-here"),
        (("guide", "estate", "edit", None), False, "an example copied into a bean: examples-are-not-facts"),
        (("clock", "estate", "stamp", None), True, "the clock stamped by the save"),
        (("work", "estate", "stamp", None), False, "a stamp typed: stamped-is-not-typed"),
        (("world", "history", "capture", None), True, "a command's output kept: world-captured"),
        (("held", "public", "publish", None), False, "sealed material published: unsealed"),
        (("other-garden", "estate", "take", None), True, "a proposal taken: peer-taken"),
        (("other-garden", "estate", "edit", None), False, "a hand copy of another garden's facts: peer-copied"),
        (("world", "law", "read", None), False, "no row holds it: closed"),
    ]
    bad = [(m, want, L0.decide(*m)) for m, want, _w in cases if L0.decide(*m)[0] != want]
    check(f"law: the nearest row decides, and of two as near a refusal — {len(cases)} passes, each as the table says",
          not bad, bad)
    d = L0.decide('request', 'remote', 'send')
    check("law: `ratified` is refused until a garden's row grants a party", not d[0] and d[1] == 'ratified', d)
    LG = Law.load(('VOCAB.md', {'flows': [{'flow': 'sent-out', 'from': 'request', 'to': 'remote', 'through': 'send',
                                           'grant': 'granted', 'party': 'clinic', 'basis': 'pact'}]}))
    check("law: a garden's row grants the party it names, with the basis it grants on, and no other party",
          not LG.problems() and LG.decide('request', 'remote', 'send', party='clinic')[0]
          and not LG.decide('request', 'remote', 'send', party='shop')[0], LG.problems())
    LU = Law.load(('VOCAB.md', {'flows': [{'flow': 'mine', 'from': 'self', 'to': 'estate', 'through': 'edit',
                                           'as': 'say', 'grant': 'granted'}]}))
    check("law: a garden's row that grants what the core does not say is `ratified` is refused: no garden unguards it",
          any('never unguards' in m for _r, _w, m in LU.problems()), LU.problems())

    # ---- MEETING: each garden records the other, its gardener, the machine, and a pact both agree to
    PACT = """---
bean: pact
kind: contract
title: "pact — what ada's and ben's gardens share"
summary: "The two gardeners agree to share notes between their gardens."
statements:
  - say:   { by: ada, at: now }
  - name:  { by: garden, of: self, as: "%s/contract:pact" }
  - agree: { by: [ada, ben], of: self, through: spoken, at: 2026-09-01 }
---
The pact.
""" % IDA
    NOTES = """---
bean: notes
kind: document
title: "notes — what the two gardens share"
summary: "Notes ada keeps for both gardens."
statements:
  - say:   { by: ada, at: now }
  - name:  { by: garden, of: self, as: "%s/document:notes" }
  - own:   { by: ada, of: self }
  - part:  { id: chapter, by: self, of: pact }
---
The notes.
""" % IDA
    for g, me, them, gid_them, Them in ((A, 'ada', 'ben', IDB, 'Ben'), (B, 'ben', 'ada', IDA, 'Ada')):
        gid_me = IDA if g == A else IDB
        write(os.path.join(g, 'VOCAB.md'), VOCAB)
        write(os.path.join(g, 'beans', 'laptop.md'), HOSTBEAN % (me, me, HOST, HOST, STORE, HOST, T))
        other = 'garden-b' if g == A else 'garden-a'
        write(os.path.join(g, 'beans', other + '.md'), f"""---
bean: {other}
kind: garden
title: "{other} — {Them}'s garden"
summary: "{Them}'s own daftar garden; what passes between it and this one is proposed, never written."
statements:
  - say:  {{ by: {me}, at: now }}
  - name: {{ by: garden-id, of: self, as: "{gid_them}" }}
  - own:  {{ by: {them}, of: self }}
  - be:   {{ id: repo, by: self, at: "unix-filesystem:root:gardens/{os.path.basename(B if g == A else A)}", as: location }}
---
{Them}'s garden.
""")
        write(os.path.join(g, 'beans', them + '.md'), f"""---
bean: {them}
kind: person
title: "{Them} — the gardener of {other}"
summary: "{Them}, who keeps {other}."
statements:
  - say:  {{ by: {me}, at: now }}
  - name: {{ by: garden, of: self, as: "{gid_them}/person:{them}" }}
  - own:  {{ by: theone, of: self }}
  - answer: {{ by: self, of: self, as: law }}
---
{Them}.
""")
        add(g, me, f'name: {{ id: crossing, by: garden, of: self, as: "{gid_me}/person:{me}" }}', me)
        if g == A:                    # ada's bean is saved once here: the save waits a minute for a bean saved twice
            write(os.path.join(A, 'beans', 'pact.md'), PACT)
            write(os.path.join(A, 'beans', 'notes.md'), NOTES)
            add(A, 'ada', 'grant: { id: ben-reads, by: self, to: [ben], of: [notes], as: read }', 'ada')
            add(A, 'ada', 'name: { id: phone, by: e164, of: self, as: "+15555550100" }', 'ada')
        r = save(g, me, f"RULE-CHANGE: met {other}; the laptop", f"- action: RULE-CHANGE — VOCAB.md adds the namespace "
                 f"anchor-hostname; recorded [[{other}]] and its gardener [[{them}]], named [[{me}]] to cross, and "
                 f"[[laptop]], whose root vault keeps material off git" + ("; wrote [[pact]] and [[notes]], which "
                                                                           "[[ada]] lets ben read" if g == A else ''))
        check(f"meet: {me}'s garden records the other as a `garden` bean named by its id, owned by its gardener",
              r.returncode == 0 and clean(g), r.out[-1500:])

    # ---- THE GATE: a pass the table grants is saved; one it refuses is refused by rule `layers`
    write(os.path.join(A, 'beans', 'reading.md'), """---
bean: reading
kind: document
title: "reading — a meter read"
summary: "What the meter showed, read off it."
statements:
  - read: { id: r1, by: ada, from: laptop, at: now }
  - pass: { id: p1, of: [r1], from: world, to: estate, through: record, as: read }
---
A reading.
""")
    r = save(A, 'ada', "a reading and its pass", "- action: wrote [[reading]]")
    check("gate: a pass the flow table grants (world → estate through record, as read) is saved", r.returncode == 0,
          r.out[-1200:])
    keep = text(os.path.join(A, 'beans', 'reading.md'))
    write(os.path.join(A, 'beans', 'reading.md'), keep.replace('from: world, to: estate, through: record, as: read',
                                                               'from: self, to: estate, through: edit, as: say'))
    r = run(PY, 'bin/check.py', cwd=A)
    write(os.path.join(A, 'beans', 'reading.md'), keep)
    check("gate: an agent's own output passed into the estate as said is refused by rule layers "
          "(model-output-is-no-word)", r.returncode != 0 and any(ln.startswith('layers') and 'model-output-is-no-word'
                                                                 in ln for ln in r.out.split('\n')), r.out[-600:])

    # ---- PASS: the layer map and the flow law of a garden of the core; `may` from grant statements
    r = run(PY, 'bin/pass.py', '--flows', cwd=A)
    check(f"pass: --flows reads the core's flow law (core@{VERSION}), {len(L0.flows)} rows, each with its guard",
          r.returncode == 0 and f"the flow law of core@{VERSION}: {len(L0.flows)} rows" in r.out, r.out[:400])
    r = run(PY, 'bin/pass.py', 'beans/notes.md', 'core/law/flows.yaml', 'captures/x.txt', cwd=A)
    check("pass: a path's layer is core/law/layers.yaml's (estate, law, history)",
          'beans/notes.md: estate' in r.out and 'core/law/flows.yaml: law' in r.out and 'captures/x.txt: history' in r.out,
          r.out)
    may = lambda actor, act, bean: dmpass.may(actor, act, bean, root=A)
    check("pass: may — the gardener may; ben may read the notes, by ada's grant; not the pact; nor write the notes",
          may('ada', 'write', 'pact').granted and may('ben', 'read', 'notes').granted
          and not may('ben', 'read', 'pact').granted and not may('ben', 'write', 'notes').granted,
          [may('ben', 'read', 'notes'), may('ben', 'read', 'pact')])
    add(A, 'ada', 'forbidden: { id: no-reads, of: ben-reads, through: self }', 'ada')
    check("pass: may — a grant the permission square forbids opens nothing", not may('ben', 'read', 'notes').granted,
          may('ben', 'read', 'notes'))
    run('git', 'checkout', '--', 'beans/ada.md', cwd=A)

    # ---- HELD: a statement sealed by its id; its record off git; the hook's check on this host
    r = run(PY, 'bin/held.py', 'put', 'ada', 'phone', '--until', '2026-11-01', cwd=A)
    ptr = re.search(r'root:vault/[0-9a-f]{32}', r.out)
    line = re.search(r'- held: ada phone added', r.out)
    bean = text(os.path.join(A, 'beans', 'ada.md'))
    check("held: put seals a statement by its id — it keeps its verb and id and holds only the pointer; the journal line "
          "is printed", r.returncode == 0 and ptr and line and f'- name: {{ id: phone, held: "{ptr.group(0)}" }}' in bean
          .replace("'", '"') and '+15555550100' not in bean, r.out + bean[-400:])
    rec = run(PY, 'bin/held.py', 'resolve', ptr.group(0) if ptr else 'x', cwd=A).out
    check("held: its record is off git — the bean, the statement's id and verb, what it said, and the day to erase it by",
          'key: phone' in rec and 'verb: name' in rec and '+15555550100' in rec and re.search(r"until: '?2026-11-01", rec)
          and not any('+15555550100' in text(os.path.join(dp, f)) for dp, _d, fs in os.walk(os.path.join(A, 'beans'))
                      for f in fs), rec)
    r = save(A, 'ada', "ada's phone, sealed", "- action: sealed [[ada]]'s phone\n- held: ada phone added")
    check("held: the seal is saved through the core's gate and the hook's check that the store here holds it",
          r.returncode == 0 and clean(A), r.out[-1200:])
    r = run(PY, 'bin/held.py', 'due', '--days', '400', cwd=A)
    check("held: `due` reads the day to erase it by from the store", 'ada: statements[name#phone]' in r.out, r.out)
    r = run(PY, 'bin/held.py', 'check', cwd=A)
    check("held: `check` finds the record where the store is, as the bean says", r.returncode == 0 and '0 error(s)' in
          r.out, r.out)
    dmsafe.add_statements(os.path.join(A, 'beans', 'notes.md'),
                          '- name: { id: fax, held: "root:vault/0123456789abcdef0123456789abcdef" }\n'
                          '- say: { by: ada, of: [fax], at: now }\n')
    r = save(A, 'ada', "a fax, sealed by hand", "- action: [[notes]] fax\n- held: notes fax added")
    check("held: a pointer the commit adds that holds nothing on this host is refused at the commit (the hook)",
          r.returncode != 0 and 'holds nothing here' in r.out, r.out[-800:])
    run('git', 'reset', '-q', 'HEAD', cwd=A)
    run('git', 'checkout', '--', 'beans/notes.md', 'log/journal.md', cwd=A)
    r = run(PY, 'bin/held.py', 'person', 'name=Cem Yilmaz', 'phone=+15555550111', cwd=A)
    pid = re.search(r'p-[0-9a-f]{8}', r.out)
    r2 = save(A, 'ada', "a person held off git", f"- action: wrote [[{pid.group(0) if pid else 'x'}]], a person held off git")
    check("held: a person minted opaque is a bean of statements, its name held off git, saved through the gate",
          pid and r2.returncode == 0 and 'Cem' not in text(os.path.join(A, 'beans', pid.group(0) + '.md')), r.out + r2.out[-800:])
    sys.path.insert(0, os.path.join(A, 'bin'))
    import importlib
    held = importlib.import_module('held')
    un = held.unsealed(dmparse.loads(dmparse.split_front_matter(text(os.path.join(A, 'beans', 'ada.md')))[0]), root=A)
    check("held: a reading made here reads the sealed statement back as it was said; git keeps the pointer",
          any(s.get('name', {}).get('as') == '+15555550100' for s in un.get('statements') or []), un.get('statements'))

    # ---- PROPOSE: ada's garden proposes the notes and the pact to ben's
    run('git', 'commit', '-qm', 'x', cwd=A)
    r = run(PY, 'bin/propose.py', 'make', '--to', 'garden-b', '--under', 'pact', 'notes', 'pact', '--out', T, cwd=A)
    prop = re.search(r'proposal \S+: (\S+)', r.out)
    prop = prop.group(1) if prop else ''
    check("propose: make lays one proposal beside the gardens, of beans in statements, with a stub for each bean they "
          "name and do not carry", r.returncode == 0 and os.path.isfile(prop) and 'daftar-stub ada' in text(prop)
          and 'daftar-stub ben' in text(prop) and os.path.dirname(prop) == T, r.out[-1200:])
    run('git', 'add', '-A', cwd=A)
    save(A, 'ada', 'proposed the notes', '- action: proposed [[notes]] and [[pact]] to [[garden-b]]')
    r = run(PY, 'bin/propose.py', 'read', prop, cwd=B)
    check("propose: read finds each stub by the names it carries, and says what taking it would do — writing nothing",
          r.returncode == 0 and 'stub ada: ada' in r.out and 'stub ben: ben' in r.out and 'notes: NEW' in r.out
          and 'pact: NEW' in r.out and clean(B), r.out[-1500:])
    r = run(PY, 'bin/propose.py', 'take', prop, cwd=B)
    notes_b = text(os.path.join(B, 'beans', 'notes.md'))
    check("propose: take writes the beans, each act known in ada's garden at its moment there, `take` at now",
          r.returncode == 0 and re.search(r"say: \{ ?by: ada, at: \['?[0-9T:+ -]+'?, garden-a\]", notes_b)
          and re.search(r"take: \{ ?id: taken-1, by: ben, of: self, from: garden-a", notes_b), r.out[-800:] + notes_b)
    entry = r.out.split('with the entry:\n', 1)[-1]
    entry = '\n'.join(ln[4:] for ln in entry.split('\n') if ln.startswith('    '))
    r = run(PY, 'bin/save.py', 'ben', 'took the notes from ada', cwd=B, stdin=entry + '\n')
    check("propose: the gardener's save is the ratification: the core's gate grants the acts their moments in ada's "
          "garden, because the commit takes them from it", r.returncode == 0 and clean(B), r.out[-1500:])
    r = run(PY, 'bin/propose.py', 'read', prop, cwd=B)
    check("propose: a proposal is taken once", r.returncode != 0 and 'taken once' in r.out, r.out[-500:])
    # a second proposal, which fuses with what the first brought
    add(A, 'notes', 'part: { id: appendix, by: self, of: pact }', 'ada')
    save(A, 'ada', 'an appendix', '- action: [[notes]] gets an appendix')
    r = run(PY, 'bin/propose.py', 'make', '--to', 'garden-b', '--under', 'pact', 'notes', '--out', T, cwd=A)
    prop2 = re.search(r'proposal \S+: (\S+)', r.out)
    prop2 = prop2.group(1) if prop2 else ''
    run('git', 'add', '-A', cwd=A)
    save(A, 'ada', 'proposed the notes again', '- action: proposed [[notes]] to [[garden-b]] again')
    r = run(PY, 'bin/propose.py', 'take', prop2, cwd=B)
    entry = '\n'.join(ln[4:] for ln in r.out.split('with the entry:\n', 1)[-1].split('\n') if ln.startswith('    '))
    r2 = run(PY, 'bin/save.py', 'ben', 'took the notes again', cwd=B, stdin=entry + '\n')
    nb = text(os.path.join(B, 'beans', 'notes.md'))
    check("propose: a second proposal FUSES with the bean the first brought: only what is new to it is added, and saved",
          r.returncode == 0 and 'FUSES WITH notes, 2 statement(s) new to it' in r.out and r2.returncode == 0
          and nb.count('id: appendix') == 1 and nb.count('id: chapter') == 1 and 'taken-2' in nb, r.out[-900:] + r2.out[-900:])
    # first contact: a garden that has not met the one proposing refuses, and says what to record
    C = os.path.join(T, 'garden-c')
    run(PY, os.path.join(REL, 'seed', 'germinate.py'), C, '--gardener', 'cem', '--gardener-name', 'Cem', cwd=T)
    r = run(PY, 'bin/propose.py', 'read', prop, cwd=C)
    check("propose: a garden refuses a proposal not made for it, from a garden it has not met (first contact, class F)",
          r.returncode != 0 and 'has not met' in r.out and 'it is for the garden' in r.out, r.out[-700:])
    # a rehearsal: ben marks ada's garden as one; what comes from it is taken only as a rehearsal's
    add(B, 'garden-a', 'rehearse: { id: rehearses, by: self, of: "the mycelium, rehearsed" }', 'ben')
    r = save(B, 'ben', "ada's garden is a rehearsal", "- action: [[garden-a]] rehearses")
    check("rehearse: a garden is marked as a rehearsal on its bean, by a statement", r.returncode == 0, r.out[-800:])
    add(A, 'notes', 'part: { id: index, by: self, of: pact }', 'ada')
    save(A, 'ada', 'an index', '- action: [[notes]] gets an index')
    r = run(PY, 'bin/propose.py', 'make', '--to', 'garden-b', '--under', 'pact', 'notes', '--out', T, cwd=A)
    prop3 = re.search(r'proposal \S+: (\S+)', r.out)
    prop3 = prop3.group(1) if prop3 else ''
    r = run(PY, 'bin/propose.py', 'read', prop3, cwd=B)
    r2 = run(PY, 'bin/propose.py', 'read', prop3, '--as-test', cwd=B)
    check("rehearse: what comes from a rehearsing garden is refused, and read clean --as-test",
          r.returncode != 0 and 'comes from a rehearsal' in r.out and r2.returncode == 0, r.out[-500:] + r2.out[-500:])

    # ---- ACROSS: ben's garden reads ada's notes at a commit ada's garden publishes, where it grants it
    head = run('git', 'rev-parse', 'HEAD', cwd=A).out.strip()
    r = run(PY, 'bin/across.py', 'read', 'garden-a', 'notes:name.as', '--commit', head, cwd=B)
    check("across: a value of the other garden, read at a commit it publishes, where it grants this gardener `read`",
          r.returncode == 0 and f"{IDA}/document:notes" in r.out, r.out[-600:])
    r = run(PY, 'bin/across.py', 'read', 'garden-a', 'pact:name.as', cwd=B)
    check("across: refused where the other garden grants nothing over the bean", r.returncode != 0 and 'NotGranted' in r.out,
          r.out[-600:])

    # ---- PART 12b: the tools' other checks, run in gardens of the core
    # across: a commit the other garden never published — on a branch it has not checked out — is never read
    br = run('git', 'rev-parse', '--abbrev-ref', 'HEAD', cwd=A).out.strip()
    run('git', 'checkout', '-q', '-b', 'unpublished', cwd=A)
    write(os.path.join(A, 'beans', 'draft.md'), NOTES.replace('bean: notes', 'bean: draft').replace(
        'document:notes', 'document:draft').replace('id: chapter', 'id: draft-of'))
    save(A, 'ada', 'a draft, not published', '- action: wrote [[draft]] on a branch nobody publishes')
    side = run('git', 'rev-parse', 'HEAD', cwd=A).out.strip()
    run('git', 'checkout', '-q', br, cwd=A)
    r = run(PY, 'bin/across.py', 'read', 'garden-a', 'notes:name.as', '--commit', side, cwd=B)
    check("across: a read at a commit the other garden never published is refused (a garden of the core)",
          r.returncode != 0 and ('NotPublished' in r.out or 'not reachable' in r.out), r.out[-600:])
    # propose: a name used as a file name only in the form of one — a proposal naming a bean `../notes` is refused
    # before anything is read or written
    bad = os.path.join(T, 'bad-proposal.md')
    write(bad, text(prop).replace('daftar-bean notes', 'daftar-bean ../notes', 1))
    r = run(PY, 'bin/propose.py', 'read', bad, cwd=B)
    check("propose: a name a proposal carries is used as a file name only in the form of one: `../notes` refused, "
          "nothing written", r.returncode != 0 and 'never used as a file name' in r.out and clean(B)
          and not os.path.exists(os.path.join(T, 'notes.md')), (r.returncode, r.out[:1500]))
    # propose: a third garden — cem's, on this machine too — meets ben's; what ada's garden said is not passed on to it
    IDC = run(PY, 'bin/propose.py', 'id', cwd=C).out.split('"')[1]
    run(PY, 'bin/install.py', cwd=C)
    for g, me, them, gid_them, Them, other in ((B, 'ben', 'cem', IDC, 'Cem', 'garden-c'),
                                               (C, 'cem', 'ben', IDB, 'Ben', 'garden-b')):
        write(os.path.join(g, 'beans', other + '.md'), f"""---
bean: {other}
kind: garden
title: "{other} — {Them}'s garden"
summary: "{Them}'s own garden, on the same machine; what passes between them is proposed."
statements:
  - say:  {{ by: {me}, at: now }}
  - name: {{ by: garden-id, of: self, as: "{gid_them}" }}
  - own:  {{ by: {them}, of: self }}
---
{Them}'s garden.
""")
        if not os.path.isfile(os.path.join(g, 'beans', them + '.md')):
            write(os.path.join(g, 'beans', them + '.md'), f"""---
bean: {them}
kind: person
title: "{Them} — the gardener of {other}"
summary: "{Them}, who keeps {other}."
statements:
  - say:  {{ by: {me}, at: now }}
  - name: {{ by: garden, of: self, as: "{gid_them}/person:{them}" }}
  - own:  {{ by: theone, of: self }}
  - answer: {{ by: self, of: self, as: law }}
---
{Them}.
""")
    write(os.path.join(B, 'beans', 'pact-c.md'), PACT.replace('bean: pact', 'bean: pact-c').replace(
        f'{IDA}/contract:pact', f'{IDB}/contract:pact-c').replace('by: [ada, ben]', 'by: [ben, cem]').replace(
        'say:   { by: ada', 'say:   { by: ben'))
    r1 = save(B, 'ben', 'met garden-c', '- action: recorded [[garden-c]] and [[cem]]; [[pact-c]] with cem')
    r2 = save(C, 'cem', 'met garden-b', '- action: recorded [[garden-b]] and [[ben]]')
    check("propose: a third garden on the same machine meets ben's: each records the other, two gardens of one machine "
          "apart", r1.returncode == 0 and r2.returncode == 0 and IDC not in (IDA, IDB), r1.out[-600:] + r2.out[-600:])
    r = run(PY, 'bin/propose.py', 'make', '--to', 'garden-c', '--under', 'pact-c', 'notes', 'pact-c', '--out', T, cwd=B)
    prop4 = re.search(r'proposal \S+: (\S+)', r.out)
    r = run(PY, 'bin/propose.py', 'read', prop4.group(1), cwd=C) if prop4 else r
    check("propose: what a third garden said is not passed on — ben's notes hold acts known in ada's garden, refused "
          "before they reach cem's", r.returncode != 0 and 'third garden' in r.out, r.out[-900:])
    # held: an erasure per subject, every pointer to it then `Erased`; a store in cleartext read from afar, warned
    r = run(PY, 'bin/held.py', 'erase', 'ada', cwd=A)
    rec = run(PY, 'bin/held.py', 'resolve', ptr.group(0) if ptr else 'x', cwd=A)
    check("held: an erasure per subject — ada's record goes, and the pointer to it resolves to Erased; git keeps the "
          "pointer, untouched", r.returncode == 0 and re.search(r'erased [1-9]', r.out) and 'erased for its subject'
          in rec.out and clean(A), r.out + rec.out)
    lap = os.path.join(A, 'beans', 'laptop.md')
    keep = text(lap)
    write(lap, keep.replace('readable_from: this-host', 'readable_from: lan'))
    r = run(PY, 'bin/held.py', 'check', cwd=A)
    write(lap, keep)
    check("held: a store that keeps special-category material in cleartext, readable from another party, is warned by "
          "the tool where the store is (the core's gate has no warnings)", 'readable from lan' in r.out, r.out[-600:])

    # ---- TRANSLATE: today's `test` on a garden bean, and a record made in another garden
    O = os.path.join(T, 'today')
    os.makedirs(os.path.join(O, 'beans'))
    write(os.path.join(O, 'beans', 'peer.md'), """---
bean: peer
genos: garden
title: "peer — another garden"
test: "a rehearsal of the mycelium"
identity: { anchors: [ { key: garden_id, value: "0123456789ab", class: logical, establishing: true } ] }
provenance: { src: asserted-by-human, by: sam, as_of: 2026-09-01 }
---
""")
    ctx = type('C', (), {'root': O})()
    check("translate: a record made in another garden is known there — its `garden` bean here",
          translate.garden_bean(ctx, '0123456789ab') == 'peer' and translate.garden_bean(ctx, 'ffffffffffff') is None)
    rows = Law.load().verbs['rehearse']
    check("translate: today's `test` on a garden bean is `rehearse` (the row replaces it)", 'test' in rows.get('replaces'),
          rows)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_between: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
