"""The gate's others and the launcher in a garden of the core (v1 part 10): parse, public, hook, hub, launch — and a
session's pass log in the core's form, which the save traces into and the core's gate holds a commit to.

Builds what it needs, as test/core_between.py does: a release of the core made from this tree (v1.0.0), a GARDEN grown
from it (the shop's), a hub cloned from it, and a writer's clone of the hub signed by a machine's own key.

parse: a document read by its garden's law, every value the text it is written in; a key written twice refused; the
alias is the module. public: a garden of the core guards its names, ids, titles, addresses and roots, and the law's
words stay sayable. hook: a garden of the core is a garden; a commit by hand and a write into another garden refused,
naming the core's tools; installed by one name and removed by the other. hub: the writer found by the `name` its key's
namespace gives; a commit unsigned, by a key no bean names, past a grant, or settling a name that establishes an
identity, refused; one a `grant` opens accepted, the core's gate at the tip. launch: the party granted by a row in the
core's words; each piece logged as a render pass, each request after its send pass, in the core's form; the model's
save traced and committed, its log claimed; a said value from a guide refused by the save; a run captured. The claim:
a pass in today's form, a pass the flow law refuses, a said value with no pass, a log rewritten and a log nobody names,
each refused by rule `layers`.

Run: python3 test/core_gate.py   (0 = green; three or four minutes, since a save waits for the next minute where its
bean was saved in this one)
"""
import http.server, json, os, re, shutil, subprocess, sys, tempfile, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import grow  # noqa: E402 — a release of the core, and the release in today's words
import importlib
import parse as dmparse
dmpass = importlib.import_module('pass')
import safe as dmsafe  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, stdin=None, env=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x', PYTHONIOENCODING='utf-8', **(env or {}))
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e,
                            input=stdin))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def save(what, body=None, root=None, env=None):
    return run(PY, 'bin/save.py', 'sam', what, '--body', body or f"- action: {what}", cwd=root or G, env=env)


def restore(root=None):
    """The copy as its last commit holds it: a refused save leaves its entry written and its files staged."""
    run('git', 'reset', '-q', '--hard', 'HEAD', cwd=root or G)
    run('git', 'clean', '-qfd', '-e', 'captures/runs', cwd=root or G)


T = tempfile.mkdtemp(prefix='core-gate-')
REL, G, HUB, W = (os.path.join(T, n) for n in ('release', 'garden', 'hub.git', 'writer'))
SSH = bool(shutil.which('ssh-keygen')) and \
    'check-novalidate' in run('ssh-keygen', '-Y', 'x', cwd=T).out + run('ssh-keygen', '-?', cwd=T).out

BEAN = """---
bean: %s
kind: %s
title: "%s"
summary: "%s"
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }%s
%s---
%s
"""
LEASE = """---
bean: lease
kind: contract
title: "the shop lease"
summary: "Bea's company lets the shop to Sam."
statements:
  - say:    { by: session-talk, at: now }
  - own:    { by: sam, of: self }
  - agree:  { id: let, by: [sam, bea], of: "%s", at: "%s" }
---
The shop on the corner.
"""
SESSION = """---
bean: session-talk
kind: session
title: "a session taking the lease down"
summary: "An agent's session that takes the lease into the garden."
statements:
  - make: { by: self, at: now, note: "opened by hand for the suite; the session's acts are by this bean" }
  - own:  { id: own, by: sam, of: self }
details:
  status: active
  workspace:
    system: unix-filesystem
    branch: "session/talk"
---
An agent's session that takes the lease down.
"""
TASK = ("Take the shop lease down: the shop on the corner, let from the first of May, agreed by Sam and Corner Lets "
        "on 2026-04-21.")

try:
    # ---- THE RELEASE: v1.0.0 of the core, and the shop's garden grown from it
    grow.release(REL)
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    TOOLS = ('parse', 'public', 'hook', 'hub', 'launch')
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION}), the gate's others and the launcher in it",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md')
          and all(os.path.isfile(os.path.join(G, 'bin', f"{v}.py")) and not os.path.exists(os.path.join(G, 'bin', f"dm{v}.py"))
                  for v in TOOLS), r.out[-800:])
    run(PY, 'bin/install.py')
    write('beans/bea.md', BEAN % ('bea', 'org', 'Corner Lets of Mill Lane', 'The company that lets the shop.', '', '',
                                  'The company that lets the shop.'))
    write('beans/lab.md', BEAN % ('lab', 'org', 'Hilltop Model Lab', "The lab whose model the shop runs.", '', '',
                                  'An invented lab.'))
    write('beans/laptop.md', BEAN % ('laptop', 'host', "the shop's laptop", "The machine the garden is kept on.",
                                     '\n  - name: { by: dns, of: self, as: shop-laptop.example.org }',
                                     'details:\n  roots:\n    shopfiles: { system: unix-filesystem, at: "shop-laptop:/srv/shop" }\n'
                                     '  contact: { address: "10.20.30.40", mail: "till@shop-mill-lane.net" }\n',
                                     'The laptop in the back room.'))
    write('beans/notes.md', BEAN % ('notes', 'document', "the shop's notes", "What the shop keeps written down.", '', '',
                                    "The shop's notes."))
    r = save('the shop: Bea, the lab, the laptop and the notes',
             '- action: wrote [[bea]], [[lab]], [[laptop]] and [[notes]]')
    check("the shop's beans are committed through the core's gate", r.returncode == 0, r.out[-800:])

    # ---- PARSE: a document read by the law its garden runs
    r = run(PY, 'bin/parse.py', 'beans/sam.md')
    check("parse: a bean of the core read by its garden's law, a moment the text it is written in",
          r.returncode == 0 and f'read by core@{VERSION}' in r.out and re.search(r'"at": "\d{4}-\d\d-\d\d', r.out),
          r.out[-600:])
    write('scratch/twice.md', '---\nbean: twice\nkind: org\nkind: person\n---\nx\n')
    r = run(PY, 'bin/daftar.py', 'parse', 'scratch/twice.md')
    check("parse: a key written twice is refused, by line (`daftar parse`)", r.returncode == 1
          and '`kind` is written twice' in r.out, r.out)
    os.remove(os.path.join(G, 'scratch', 'twice.md'))
    r = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import parse, parse; print(parse is parse)")
    check("parse: bin/parse.py, today's name every tool imports, is the module `parse`", r.out.strip() == 'True', r.out)

    # ---- PUBLIC: what a garden of the core says of itself is guarded
    sys.path.insert(0, os.path.join(G, 'bin'))
    import public                                  # noqa: E402 — the garden's own copy
    words = public.estate_words(G, public.public_words(G))
    check("public: a garden of the core's ids, a `name`'s text, a long title, an address and a root are its estate's",
          {'laptop', 'shop-laptop.example.org', 'corner lets of mill lane', '10.20.30.40', 'till@shop-mill-lane.net',
           'shopfiles'} <= words, sorted(words)[:40])
    check("public: the law's own words — the core's kinds and namespaces — stay public", {'person', 'contract',
                                                                                          'openpgp'} <= public.public_words(G))
    repo = os.path.join(T, 'repo')
    os.makedirs(repo)
    write('README.md', "One host, another machine.\n", repo)
    run('git', 'init', '-q', cwd=repo)
    run('git', 'add', '-A', cwd=repo)
    r = run(PY, 'bin/public.py', '--garden', G, '--repo', repo)
    check("public: a repository that names nothing of the garden passes", r.returncode == 0, r.out)
    write('README.md', "Measured on shop-laptop.example.org, of course.\n", repo)
    r = run(PY, 'bin/public.py', '--garden', G, '--repo', repo)
    check("public: one that names a machine by the name its `name` gives is refused (bin/public.py, the alias)",
          r.returncode == 1 and 'shop-laptop.example.org' in r.out, r.out)

    # ---- HOOK: the guards in another maker's loop know a garden of the core
    sys.path.insert(0, os.path.join(G, 'bin'))
    import hook                                    # noqa: E402

    def hookrun(verb, ev):
        return run(PY, 'bin/hook.py', verb, stdin=json.dumps(dict(ev, session_id='abc123def456', cwd=G)))
    check("hook: a garden of the core is a garden", hook.is_garden(os.path.realpath(G)))
    r = hookrun('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'git commit -qm x'}})
    check("hook: a commit by hand is refused, naming the save (bin/save.py)", r.returncode == 2 and 'bin/save.py' in r.out,
          r.out)
    other = os.path.join(T, 'other')
    shutil.copytree(G, other)
    r = hookrun('pre', {'tool_name': 'Write', 'tool_input': {'file_path': os.path.join(other, 'beans', 'x.md')}})
    check("hook: a write into another garden is refused, naming a proposal (bin/propose.py)",
          r.returncode == 2 and 'another garden' in r.out and 'bin/propose.py' in r.out, r.out)
    shutil.rmtree(other, ignore_errors=True)
    r = run(PY, 'bin/hook.py', 'pre', stdin='{not json')
    check("hook: a hook that cannot read its event fails closed (exit 2) — v1 part 12b", r.returncode == 2, r.out)
    write('scratch/plan.txt', "The rent we would never say aloud: nine hundred a month, Mill Lane side.\n")
    r = hookrun('pre', {'tool_name': 'Read', 'tool_input': {'file_path': os.path.join(G, 'scratch', 'plan.txt')}})
    check("hook: a read of a file in no layer is refused (R4)", r.returncode == 2 and 'no layer' in r.out, r.out)
    r1 = run(PY, 'bin/hook.py', 'install', 'claude-code')
    r2 = run(PY, 'bin/hook.py', 'uninstall', 'claude-code')
    check("hook: installed by today's name and removed by the verb's", r1.returncode == 0 and r2.returncode == 0
          and 'hooks' not in json.loads(text('.claude/settings.local.json')), r1.out + r2.out)

    # ---- LAUNCH: a session's copy, an endpoint served here, the party the gardener's to grant
    run('git', 'checkout', '-q', '-b', 'session/talk')
    write('beans/session-talk.md', SESSION)
    r = save("the session's bean", "- action: opened [[session-talk]]")
    check("the session's bean, in statements, is committed on its branch", r.returncode == 0, r.out[-600:])
    SEEN, SCRIPT = [], []

    class Fake(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['content-length'])).decode('utf-8'))
            SEEN.append(body)
            reply = SCRIPT.pop(0) if SCRIPT else {'text': 'done', 'calls': []}
            out = {'content': ([{'type': 'text', 'text': reply['text']}] if reply['text'] else []) +
                   [{'type': 'tool_use', 'id': f"t{len(SEEN)}{i}", 'name': n, 'input': a}
                    for i, (n, a) in enumerate(reply['calls'])]}
            data = json.dumps(out).encode('utf-8')
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.send_header('content-length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    SRV = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Fake)
    threading.Thread(target=SRV.serve_forever, daemon=True).start()
    for k, v in (('endpoint', f"http://127.0.0.1:{SRV.server_port}/v1"), ('wire', 'messages'), ('model', 'fake-model'),
                 ('party', 'lab')):
        run('git', 'config', f'daftar.{k}', v)
    KEY = {'DAFTAR_API_KEY': 'invented-key'}
    LOG = 'captures/passes/talk.jsonl'

    def passes():
        try:
            return [json.loads(ln) for ln in text(LOG).splitlines() if ln.strip()]
        except OSError:
            return []
    r = run(PY, 'bin/launch.py', 'run', TASK, env=KEY)
    check("launch: a party no row of the garden grants is refused, nothing sent, and the row to write is in the core's "
          "words (`flow: sent-out`, `through: send`)", r.returncode == 2 and not SEEN and 'flow: sent-out' in r.out
          and 'through: send' in r.out and not passes(), r.out)
    write('VOCAB.md', text('VOCAB.md').replace('---\n', """---
flows:
  - { flow: sent-out, from: request, to: remote, through: send, grant: granted, party: lab, basis: "the shop's own choice of model, on the lab's published terms", why: "the gardener grants this party" }
""", 1))
    r = save('RULE-CHANGE: the shop grants requests to the lab', '- action: RULE-CHANGE — VOCAB.md grants `send` to [[lab]]')
    check("the gardener's grant of the party, a row in the core's words, is committed", r.returncode == 0, r.out[-600:])
    SCRIPT[:] = [
        {'text': '', 'calls': [('read', {'path': 'beans/notes.md'})]},
        {'text': '', 'calls': [('write', {'path': 'beans/lease.md', 'content': LEASE % (
            "the shop on the corner, let from the first of May", "2026-04-21")}),
            ('save', {'what': 'the shop lease taken down', 'body':
                      "- action: [[lease]] taken down from Sam's words; [[session-talk]] logs its passes"})]},
        {'text': 'Saved.', 'calls': []},
    ]
    r = run(PY, 'bin/launch.py', 'run', TASK, env=KEY)
    ps = passes()
    check("launch: a granted party, the loop runs to its end, its save committed", r.returncode == 0 and len(SEEN) == 3
          and 'the shop lease taken down' in run('git', 'log', '-1', '--format=%s').out, r.out[-800:])
    check("launch: every pass is in the core's form — `through`, never today's `method`",
          ps and all(set(p) <= {'from', 'to', 'through', 'as', 'metadata'} and 'through' in p for p in ps), ps[:3])
    sends = [p for p in ps if p['through'] == 'send']
    render = [p for p in ps if p['through'] == 'render']
    check("launch: each request after its send pass naming the party; each piece one render pass, the task from "
          "`instructions`", len(sends) == 3 and all(p['metadata']['party'] == 'lab' for p in sends)
          and len({p['metadata']['seq'] for p in render}) == len(render)
          and any(p['from'] == {'layer': 'instructions'} for p in render), (sends, render[:3]))
    said = [p for p in ps if p['to'].get('bean') == 'lease']
    check("the save traced each said value — a role of a statement a `say` knows — to the person's words: through "
          "`say`, as `say`", {p['to']['at'] for p in said} == {'agree#let.of', 'agree#let.at'}
          and all(p['through'] == 'say' and p['as'] == 'say' and p['from'] == {'layer': 'instructions'}
                  and p['metadata']['quoted'] >= 1 for p in said), said)
    fm = dmparse.front(os.path.join(G, 'beans', 'session-talk.md'))[0]
    log_files = run('git', 'show', '--name-only', '--format=', 'HEAD').out.split()
    check("the session's bean names its log in `details`, and the commit that took the lease down claims it",
          fm['details'].get('pass_log') == {'requests': {'holds': f'file:{LOG}'}} and LOG in log_files
          and 'beans/lease.md' in log_files, (fm.get('details'), log_files))
    r = run(PY, 'bin/check.py', '--all')
    check("the core's gate over the whole garden: 0 errors", r.returncode == 0 and '— 0 error(s)' in r.out, r.out[-800:])
    # A RE-READ, A FILE IN NO LAYER, A WRITE OUTSIDE (v1 part 12b): each refused to the model, never carried
    write('scratch/plan.txt', "The rent we would never say aloud: nine hundred a month, Mill Lane side.\n")
    gate_before = text('bin/check.py')
    SEEN.clear()
    SCRIPT[:] = [
        {'text': '', 'calls': [('read', {'path': 'beans/notes.md'})]},
        {'text': '', 'calls': [('read', {'path': 'beans/notes.md'}), ('read', {'path': 'scratch/plan.txt'}),
                               ('write', {'path': '../outside.md', 'content': 'x'}),
                               ('write', {'path': 'bin/check.py', 'content': 'x'})]},
        {'text': 'Nothing more to do.', 'calls': []},
    ]
    r = run(PY, 'bin/launch.py', 'run', TASK, env=KEY)
    tr = [blk for m in (SEEN[-1]['messages'] if SEEN else []) for blk in m['content']
          if isinstance(blk, dict) and blk.get('type') == 'tool_result']
    words = json.dumps(tr)
    check("launch: a file read again, unchanged, is refused (`again`)", 'in this request already' in words, words[:1500])
    check("launch: a file in no layer is refused (R4), and its words are never sent",
          'in no layer' in words and not any('nine hundred' in json.dumps(b) for b in SEEN), words[:1500])
    check("launch: a write outside the session's copy, or into the gate, is refused",
          words.count('writes inside its own copy') == 2 and text('bin/check.py') == gate_before
          and not os.path.exists(os.path.join(os.path.dirname(G), 'outside.md')), words[:1500])
    M_ = dmpass.Map.here(G)
    IDX = dmpass.denied_lines(G, M_, dmpass.flows(G), files=['scratch/plan.txt', 'beans/notes.md'])
    check("POST by content: its index holds the lines of a file in no layer, and none of a file a request may carry, and "
          "finds such a line whole in a tool's output", 'scratch/plan.txt' in IDX.values()
          and 'beans/notes.md' not in IDX.values() and dmpass.post_hits(
              "grep:\nThe rent we would never say aloud: nine hundred a month, Mill Lane side.\n", IDX)
          == {'scratch/plan.txt': 1}, IDX)
    restore()

    # ---- THE SAVE, on the session's material: a value found only in a guide is refused before a word is written
    sys.path.insert(0, os.path.join(G, 'bin'))
    import launch                                  # noqa: E402
    S = launch.Session.current(G)
    S.add("Oak Street Lets agreed on 2026-03-02.", {'file': 'README.md'}, 'guide')
    write('beans/lease.md', LEASE % ("the shop on the corner, let from the first of May", "2026-03-02"))
    r = save('a lease whose day came from a guide', '- action: [[lease]] agreed on another day')
    check("the save: a said value found only in a guide is refused (examples-are-not-facts), nothing written",
          r.returncode == 2 and 'examples-are-not-facts' in r.out and '2026-03-02' not in text('log/journal.md'), r.out)
    restore()
    r = run(PY, 'bin/launch.py', 'record', '--keep', 'meter-read', '--', PY, '-c', "print('the meter read 4211')",
            env=KEY)
    cap = [p for p in passes() if p['through'] == 'capture']
    check("record --keep: a run's output captured, its `capture` pass logged from the world in the core's form "
          "(bin/launch.py, the alias)", r.returncode == 0 and cap and cap[-1]['from'] == {'layer': 'world'}
          and len(cap[-1]['metadata']['oid']) == 40, r.out)
    restore()
    S.end()                                        # no session current: what follows is written by hand, for the gate

    # ---- THE CLAIM: what a commit that stages a session's log owes, held by rule `layers`
    def claim(line, lease_day=None):
        with open(os.path.join(G, LOG), 'a', encoding='utf-8', newline='\n') as fh:
            fh.write(json.dumps(line) + '\n')
        if lease_day:
            write('beans/lease.md', LEASE % ("the shop on the corner, let from the first of May", lease_day))
        r = save('a claimed commit', '- action: [[lease]] and [[session-talk]]')
        restore()
        return r
    p_ok = {'from': {'layer': 'instructions'}, 'to': {'bean': 'lease', 'at': 'agree#let.at'}, 'through': 'say',
            'as': 'say', 'metadata': {'quoted': 1}}
    r = claim(dict(p_ok, method='take-down'))
    check("the claim: a pass in today's form is refused, naming the core's `through`", r.returncode != 0
          and 'layers' in r.out and "`through`" in r.out, r.out[-600:])
    r = claim(dict(p_ok, **{'from': {'layer': 'self'}}), '2026-05-01')
    check("the claim: a pass the flow law refuses — the model's own output into a said value — is refused by name",
          r.returncode != 0 and 'model-output-is-no-word' in r.out, r.out[-600:])
    r = claim({'from': {'layer': 'world'}, 'to': {'file': 'captures/runs/x.log'}, 'through': 'capture',
               'metadata': {'characters': 3}}, '2026-05-02')
    check("the claim: a said value the claimed commit adds with no granted pass into it is refused",
          r.returncode != 0 and 'agree#let.at' in r.out and 'no granted pass' in r.out, r.out[-600:])
    r = claim(p_ok, '2026-04-22')
    check("the claim: the same value with its pass from the person's words is committed", r.returncode == 0, r.out[-600:])
    write(LOG, '\n'.join(text(LOG).splitlines()[1:]) + '\n')
    write('beans/notes.md', text('beans/notes.md').replace("The shop's notes.", "The shop's notes, again."))
    r = save('a log rewritten', '- action: [[notes]]')
    check("the claim: a log that does not extend its copy at HEAD is refused — a pass log only grows",
          r.returncode != 0 and 'only grows' in r.out, r.out[-600:])
    restore()
    write('captures/passes/nobody.jsonl', json.dumps(p_ok) + '\n')
    write('beans/notes.md', text('beans/notes.md').replace("The shop's notes.", "The shop's notes, again."))
    r = save('a log nobody names', '- action: [[notes]]')
    check("the claim: a log no session bean names is refused", r.returncode != 0 and 'no session bean names' in r.out,
          r.out[-600:])
    restore()
    run('git', 'checkout', '-q', 'master')

    # ---- HUB: the gate again at the hub, for a garden of the core
    if not SSH:
        print("SKIP  hub: this machine has no ssh-keygen that checks a signature (`ssh-keygen -Y check-novalidate`)")
    else:
        def key(name):
            p = os.path.join(T, name + '-key')
            subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', name, '-f', p], capture_output=True)
            out = subprocess.run(['ssh-keygen', '-lf', p + '.pub'], capture_output=True, text=True,
                                 encoding='utf-8', errors='replace').stdout
            return p, re.search(r'(SHA256:[A-Za-z0-9+/]{43})', out).group(1)

        def signing(where, k):
            for a in (('gpg.format', 'ssh'), ('user.signingkey', k), ('commit.gpgsign', 'true')):
                run('git', 'config', *a, cwd=where)
        SAMK, SAMF = key('sam')
        VIEWK, VIEWF = key('viewhost')
        signing(G, SAMK)
        dmsafe.add_statements(os.path.join(G, 'beans', 'sam.md'),
                              f'- name: {{ id: key, by: ssh, of: self, as: "{SAMF}" }}\n- say: {{ by: sam, of: [key], at: now }}\n')
        write('beans/viewhost.md', BEAN % ('viewhost', 'host', 'the view host', "The machine that serves the shop's pages.",
                                           f'\n  - name: {{ by: ssh, of: self, as: "{VIEWF}" }}', '', 'It serves the pages.'))
        r = save("the keys of the gardener and the view host",
                 '- action: [[sam]] and [[viewhost]] carry their keys; a class F change, the gardener\'s own')
        check("hub: the gardener's and the view host's keys, each a `name` the namespace ssh gives, are committed signed",
              r.returncode == 0 and 'gpgsig' in run('git', 'cat-file', 'commit', 'HEAD').out, r.out[-600:])
        run('git', 'clone', '-q', '--bare', G, HUB, cwd=T)
        r = run(PY, os.path.join(G, 'bin', 'hub.py'), 'install', HUB)
        check("hub: installed in the bare hub (bin/hub.py)", r.returncode == 0 and os.path.isfile(
            os.path.join(HUB, 'hooks', 'pre-receive')) and 'hub.py' in text(os.path.join(HUB, 'hooks', 'pre-receive')),
            r.out)
        run('git', 'remote', 'add', 'hub', HUB)

        def push(where):
            return run('git', 'push', '-q', 'hub' if where == G else 'origin', 'HEAD:master', cwd=where)
        write('beans/notes.md', text('beans/notes.md').replace("The shop's notes.", "The shop's notes, kept by Sam."))
        save('the notes, by the gardener', '- action: [[notes]]')
        r = push(G)
        check("hub: the gardener's signed commit is accepted, the core's gate run at the tip", r.returncode == 0, r.out)
        run('git', 'clone', '-q', HUB, W, cwd=T)
        signing(W, VIEWK)
        for k, v in (('user.name', 'viewhost'), ('user.email', 'view@x')):
            run('git', 'config', k, v, cwd=W)
        run(PY, 'bin/install.py', cwd=W)

        def writer_edit(what, line):
            dmsafe.add_statements(os.path.join(W, 'beans', 'notes.md'), line)
            r = run(PY, 'bin/save.py', 'viewhost', what, '--body', f'- action: [[notes]] {what}', cwd=W)
            return r
        r = writer_edit('a note', '- say: { by: sam, at: now, note: "entered on the view host" }\n')
        r2 = push(W)
        check("hub: the view host, whose key a bean names, is refused a bean no grant opens to it",
              r.returncode == 0 and r2.returncode != 0 and 'notes.md needs a grant of `write`' in r2.out, r.out + r2.out)
        dmsafe.add_statements(os.path.join(G, 'beans', 'sam.md'),
                              '- grant: { id: view-writes, by: self, as: write, of: [notes], to: [viewhost] }\n'
                              '- say: { by: sam, of: [view-writes], at: now }\n')
        r0 = save('the view host may write the notes', '- action: [[sam]] grants [[notes]] to [[viewhost]]')
        r = push(G)
        run('git', 'fetch', '-q', 'origin', cwd=W)
        run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
        writer_edit('a note', '- say: { by: sam, at: now, note: "entered on the view host" }\n')
        r2 = push(W)
        check("hub: once a `grant` of the gardener's opens it, the view host's signed commit is accepted",
              r0.returncode == 0 and r.returncode == 0 and r2.returncode == 0, r0.out[-400:] + r.out + r2.out)
        r = writer_edit('a key', f'- name: {{ id: k2, by: ssh, of: self, as: "{SAMF[:-4]}AAAA" }}\n'
                                 '- say: { by: sam, of: [k2], at: now }\n')
        r2 = push(W)
        check("hub: a name that establishes an identity, settled by a writer, needs `ratify:F` — refused",
              r2.returncode != 0 and 'ratify:F' in r2.out, r.out[-300:] + r2.out)
        # THE HUB RUNS ONLY CODE THE GARDENER LET IN: a writer granted `write` on a bean changes no file that can make a
        # machine run something — the gate, a file a release keeps, `.gitattributes`, a Python file wherever it is
        for path, text in (('bin/check.py', None), ('.gitattributes', None), ('notes/helper.py', 'print("hi")\n')):
            run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
            p = os.path.join(W, *path.split('/'))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'a' if text is None else 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('\n# a writer\'s line\n' if text is None else text)
            run('git', 'add', '-A', cwd=W)
            c = run('git', 'commit', '-q', '--no-verify', '-m', f'changed {path}', cwd=W)
            r2 = push(W)
            check(f"hub: a writer granted `write` on a bean is refused a change to {path}, which needs `ratify:G`",
                  c.returncode == 0 and r2.returncode != 0 and 'ratify:G' in r2.out and path in r2.out, c.out + r2.out)
        run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
        run('git', 'config', 'commit.gpgsign', 'false', cwd=W)
        writer_edit('unsigned', '- say: { by: sam, at: now, note: "entered on the view host" }\n')
        r2 = push(W)
        check("hub: an unsigned commit is refused", r2.returncode != 0 and 'not signed' in r2.out, r2.out)
        stranger, _f = key('stranger')
        run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
        signing(W, stranger)
        writer_edit('by a stranger', '- say: { by: sam, at: now, note: "entered on the view host" }\n')
        r2 = push(W)
        check("hub: a commit signed by a key no bean names is refused", r2.returncode != 0 and 'no bean carries' in r2.out,
              r2.out)
        # A COMMIT WITH NO PARENT names its own writers: a hub that holds the garden refuses it (v1 part 12b)
        run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
        signing(W, VIEWK)
        run('git', 'checkout', '-q', '--orphan', 'stray', cwd=W)
        write('GARDEN.md', re.sub(r'(?m)^gardener: *\S+', 'gardener: viewhost', open(os.path.join(W, 'GARDEN.md'), encoding='utf-8').read(),
                                  count=1), root=W)
        run('git', 'add', '-A', cwd=W)
        run('git', 'commit', '-q', '--no-verify', '-m', 'a garden of my own', cwd=W)
        r2 = run('git', 'push', '-q', 'origin', 'HEAD:refs/heads/stray', cwd=W)
        check("hub: a signed commit with no parent, naming its signer as gardener, is refused by a hub that holds the garden",
              r2.returncode != 0 and 'no parent' in r2.out, r2.out[-800:])
        run('git', 'checkout', '-q', '-f', 'master', cwd=W)
        # OPENPGP, where ssh-keygen cannot check: the hub reads the signature with gpg (v1 part 12b)
        if not shutil.which('gpg'):
            print("SKIP  hub: OpenPGP — no gpg on this machine")
        else:
            os.environ['GNUPGHOME'] = os.path.join(T, 'gnupg')
            os.makedirs(os.environ['GNUPGHOME'], mode=0o700, exist_ok=True)
            subprocess.run(['gpg', '--batch', '--pinentry-mode', 'loopback', '--passphrase', '', '--quick-gen-key',
                            'viewhost <view@example.org>', 'ed25519', 'sign', 'never'], capture_output=True)
            out = subprocess.run(['gpg', '--with-colons', '--list-secret-keys', 'view@example.org'], capture_output=True,
                                 text=True, encoding='utf-8', errors='replace').stdout
            m = re.search(r'^fpr:+([0-9A-F]{40,64}):', out, re.M)
            fpr = m.group(1) if m else ''
            run('git', 'fetch', '-q', 'hub')                # the gardener's clone takes what the view host pushed
            run('git', 'reset', '-q', '--hard', 'hub/master')
            dmsafe.add_statements(os.path.join(G, 'beans', 'viewhost.md'),
                                  f'- name: {{ id: pgp, by: openpgp, of: self, as: "{fpr}" }}\n'
                                  '- say: { by: sam, of: [pgp], at: now }\n')
            r0 = save("the view host's OpenPGP key", "- action: [[viewhost]] carries an OpenPGP key; class F, the gardener's own")
            r1 = push(G)
            run('git', 'fetch', '-q', 'origin', cwd=W)
            run('git', 'reset', '-q', '--hard', 'origin/master', cwd=W)
            for a in (('gpg.format', 'openpgp'), ('user.signingkey', fpr), ('commit.gpgsign', 'true')):
                run('git', 'config', *a, cwd=W)
            writer_edit('signed with OpenPGP', '- say: { by: sam, at: now, note: "entered on the view host, OpenPGP" }\n')
            r2 = push(W)
            check("hub: an OpenPGP key a bean names (`name: { by: openpgp }`) — the view host's commit signed with it is "
                  "read by gpg and accepted", fpr and r0.returncode == 0 and r1.returncode == 0 and r2.returncode == 0,
                  (fpr, r0.out[-300:], r1.out, r2.out[-800:]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_gate: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
