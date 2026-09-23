#!/usr/bin/env python3
"""converge — several gardens diverge, are packaged, and one remote garden pulls them all back.

WHY THIS EXISTS. Every other suite tests one garden. This is the only one that exercises what the whole
MERGE design is FOR: independent sessions recording the same estate, offline, converging later. Run as a
one-off rehearsal it found four real defects in an afternoon, every one invisible to the other suites:

  * `seed/germinate.sh` never copied `.gitattributes`, so EVERY germinated garden text-merged its beans
    and conflicted on its own append-only journal. The driver was configured in each and invoked in none.
    Git warns neither when an attribute names a missing driver nor when a configured driver is named by
    nothing, so this was silent in both directions.
  * The driver emitted YAML block sequences at the SAME column as their key — legal YAML that defeats
    every indentation-based span finder, so the next edit landed inside the block and the file stopped
    parsing.
  * When a member had to be appended, the anchor member was re-emitted from OUR value rather than the
    merged one, quietly undoing a merge that had just happened.
  * A position where theirs differs but the MERGED RESULT equals ours was still written, handing dmsafe a
    block identical to the text it replaced.

Nothing here is mocked: real germination, real clones, real `git bundle`, real `git merge` through the
driver `.gitattributes` names. Roughly 15 seconds.

Run: python3 test/converge.py   (0 = green)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse
import yaml

results = []


def check(name, ok, detail=''):
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{detail}]" if detail and not ok else ''))


def git(*a, cwd):
    return subprocess.run(('git',) + a, capture_output=True, text=True, cwd=cwd)


def commit(cwd, who, msg):
    subprocess.run([sys.executable, os.path.join(cwd, 'bin', 'dmjournal.py'), 'agent', who,
                    '--body', f"- action: {msg}\n- refs: beans/relay.md"], cwd=cwd, check=True, capture_output=True)
    git('add', '-A', cwd=cwd)
    return git('-c', 'user.name=' + who, '-c', f'user.email={who}@g', 'commit', '-q', '-m', msg, cwd=cwd)


def edit(cwd, fn):
    p = os.path.join(cwd, 'beans', 'relay.md')
    text = open(p, encoding='utf-8').read()          # READ then write; 'w' truncates at call time
    open(p, 'w', encoding='utf-8').write(fn(text))


RELAY = """---
bean: relay
kind: host
title: "relay — the shared mail relay every garden observes"
status: active
summary: "A relay recorded in the origin garden, so gardens cloned from it observe the same object independently and their records must converge on one being rather than three."
identity:
  status: confirmed
  anchors:
    - {{ key: serial, value: "SN-RELAY-001", class: hardware, establishing: true, observed: 2026-08-02 }}
provenance: {{ src: observed, by: "agent/origin", as_of: 2026-08-02 }}
nature: physical
owned_by: {{ legal: {{ external: "the relay's operator, outside every garden that observes it" }} }}
responsibility: {{ legal: {{ external: "the relay's operator" }} }}
owns:
  os: "AlmaLinux 9"
  roles: [relay]
  contact: "noc@example.org"          # NOBODY edits this — it and its comment must survive untouched
---
The shared relay.
"""

TMP = tempfile.mkdtemp(prefix='dmconv-')
ORIGIN = os.path.join(TMP, 'origin')

r = subprocess.run(['sh', os.path.join(ROOT, 'seed', 'germinate.sh'), ORIGIN, '--gardener', 'keeper'],
                   capture_output=True, text=True, cwd=ROOT)
check("an origin garden germinates from the seed", r.returncode == 0, (r.stdout + r.stderr)[-300:])
check("...and it dispatches bean merges to the semantic driver, journal merges to union",
      'daftar' in git('check-attr', 'merge', '--', 'beans/x.md', cwd=ORIGIN).stdout
      and 'union' in git('check-attr', 'merge', '--', 'log/journal.md', cwd=ORIGIN).stdout,
      "`.gitattributes` did not travel — every garden would text-merge its beans")

open(os.path.join(ORIGIN, 'beans', 'relay.md'), 'w', encoding='utf-8').write(RELAY.format())
commit(ORIGIN, 'origin', 'recorded the relay every garden observes')
BASE = git('rev-parse', 'HEAD', cwd=ORIGIN).stdout.strip()

GARDENS = ('site-a', 'site-b', 'site-c')
for g in GARDENS:
    git('clone', '-q', ORIGIN, os.path.join(TMP, g), cwd=TMP)
    subprocess.run(['sh', 'bin/install.sh'], capture_output=True, cwd=os.path.join(TMP, g))

# Three independent migrations. NO VERSION MOVES — the pin stays put, which is also what keeps them
# mergeable at all: a merge across two Tier-0 versions is refused by design.
edit(os.path.join(TMP, 'site-a'), lambda t: t.replace('  os: "AlmaLinux 9"', '  os: "AlmaLinux 9.4"')
     .replace('roles: [relay]', 'roles: [relay, submission]'))
commit(os.path.join(TMP, 'site-a'), 'site-a', 'refined os to 9.4 and added the submission role')

edit(os.path.join(TMP, 'site-b'),
     lambda t: t.replace('roles: [relay]', 'roles: [relay, dkim-signing]\n  site: "Site B DC"'))
commit(os.path.join(TMP, 'site-b'), 'site-b', 'added dkim-signing and site Site B DC')

edit(os.path.join(TMP, 'site-c'), lambda t: t.replace('roles: [relay]', 'roles: [relay]\n  site: "Site C DC"')
     .replace('nature: physical', 'nature: physical\ncapabilities:\n  open-relay: { permission: forbidden,'
                                  ' feasibility: possible, why: "must never accept third-party mail" }'))
commit(os.path.join(TMP, 'site-c'), 'site-c', 'recorded site Site C DC and forbade open-relay')

gates = {g: subprocess.run([sys.executable, 'bin/dmcheck.py'], capture_output=True, text=True,
                           cwd=os.path.join(TMP, g)) for g in GARDENS}
check("each garden passes its OWN gate after its own migration",
      all(r.returncode == 0 for r in gates.values()),
      '; '.join(f"{g}: {r.stdout.strip()[-90:]}" for g, r in gates.items() if r.returncode))

# ---- PACKAGE: a git bundle per garden. Git's own offline transport — one file, no server. -------------
PKG = os.path.join(TMP, 'package')
os.makedirs(PKG)
for g in GARDENS:
    git('bundle', 'create', '-q', os.path.join(PKG, g + '.bundle'), f'{BASE}..HEAD', cwd=os.path.join(TMP, g))
_v = yaml.safe_load(dmparse.read(os.path.join(ORIGIN, 'VOCAB.md'))[0])
check("the package is one self-verifying bundle per garden",
      all(os.path.exists(os.path.join(PKG, g + '.bundle')) for g in GARDENS)
      and all('is okay' in git('bundle', 'verify', os.path.join(PKG, g + '.bundle'), cwd=ORIGIN).stdout
              or git('bundle', 'verify', os.path.join(PKG, g + '.bundle'), cwd=ORIGIN).returncode == 0
              for g in GARDENS))

# ---- PULL BACK: one last remote garden takes all three ------------------------------------------------
REMOTE = os.path.join(TMP, 'remote')
git('clone', '-q', ORIGIN, REMOTE, cwd=TMP)
subprocess.run(['sh', 'bin/install.sh'], capture_output=True, cwd=REMOTE)
drove = []
for g in GARDENS:
    git('fetch', '-q', os.path.join(PKG, g + '.bundle'), f'HEAD:refs/heads/from-{g}', cwd=REMOTE)
    m = git('-c', 'user.name=remote', '-c', 'user.email=r@r', 'merge', f'from-{g}',
            '-m', f'pull back {g}', cwd=REMOTE)
    drove.append((g, m.returncode, m.stdout + m.stderr))

check("every garden PULLS BACK cleanly — no git-level conflict anywhere",
      all(rc == 0 for _g, rc, _o in drove),
      '; '.join(f"{g}: {o.strip()[:150]}" for g, rc, o in drove if rc))
check("...and the semantic driver, not git's text merge, did the work",
      sum('dmmerge:' in o for _g, _rc, o in drove) >= 2,
      '; '.join(o.strip()[:120] for _g, _rc, o in drove))

head, _body = dmparse.read(os.path.join(REMOTE, 'beans', 'relay.md'))
fm = yaml.safe_load(head)
owns = fm['owns']
check("a REFINEMENT subsumes: origin's 'AlmaLinux 9' and site-a's '9.4' resolve to 9.4, not a conflict",
      owns['os'] == 'AlmaLinux 9.4', str(owns['os']))
check("a SET unions across all three gardens",
      sorted(owns['roles']) == ['dkim-signing', 'relay', 'submission'], str(owns['roles']))
check("a genuine DISAGREEMENT keeps both values rather than picking one",
      isinstance(owns.get('site'), dict) and sorted(owns['site']['conflict']) == ['Site B DC', 'Site C DC'],
      str(owns.get('site')))
check("...and the bean is marked unclean, naming the path a human must settle",
      # `status` is deliberately NOT the marker (Phase 5, D22): it is a `single` merged term, so the
      # driver writing its own flag there collided with the algebra on one key. It must survive the merge
      # carrying what the gardens actually said.
      fm.get('merge_open') is True and fm['merge_conflicts'] == ['owns.site']
      and fm.get('status') != 'at-risk',
      f"status={fm.get('status')} conflicts={fm.get('merge_conflicts')}")
check("a top-level key only ONE garden had arrives whole",
      list((fm.get('capabilities') or {})) == ['open-relay'], str(list(fm.get('capabilities') or {})))
check("a fact NOBODY edited is untouched, comment and all",
      owns['contact'] == 'noc@example.org' and 'NOBODY edits this' in head)

jr = open(os.path.join(REMOTE, 'log', 'journal.md'), encoding='utf-8').read()
check("every garden's journal entry survives — the log merges by union, losing none",
      all(g in jr for g in GARDENS) and 'origin' in jr)

g = subprocess.run([sys.executable, 'bin/dmcheck.py'], capture_output=True, text=True, cwd=REMOTE)
check("the converged garden passes its gate", g.returncode == 0, g.stdout.strip()[-200:])
check("...and the gate WARNS about the unresolved conflict rather than staying silent (MERGE.md §10)",
      'left UNCLEAN by a semantic merge' in g.stdout, g.stdout.strip()[-200:])

# ---------------------------------------------------------------- one serial, two spellings (v0.5.1)
# std-vocab 9.0 made the GATE compare serials case- and space-insensitively; v0.5.0 left the MERGE comparing them
# exactly, so two gardens recording one machine as `SN-0042` and `sn-0042 ` still produced two objects.
import dmmerge as M
def _host(garden, bid, serial):
    return [{'garden': garden, 'id': bid, 'fm': {
        'bean': bid, 'kind': 'host', 'nature': 'physical', 'title': bid, 'status': 'active', 'summary': bid,
        'identity': {'status': 'confirmed', 'anchors': [{'key': 'serial', 'value': serial, 'class': 'hardware',
                                                         'establishing': True}]},
        'provenance': {'src': 'observed', 'by': garden, 'as_of': '2026-09-17'}}}]
_seeds = M.merge_gardens([_host('g1', 'box', 'SN-0042'), _host('g2', 'server', 'sn-0042 ')])
_anchors = [a for sd in _seeds.values() for a in sd['identity']['anchors']]
check("two gardens spelling one serial differently merge into ONE object",
      len(_seeds) == 1, sorted(_seeds))
check("...its anchor is stored once, in the compare form, with no disagreement recorded",
      [a['value'] for a in _anchors] == ['SN-0042']
      and not any(sd['identity'].get('anchor_conflicts') for sd in _seeds.values()), str(_anchors))
_one = os.path.join(TMP, 'two-spellings')
subprocess.run(['sh', os.path.join(ROOT, 'seed', 'germinate.sh'), _one, '--gardener', 'keeper'], capture_output=True, cwd=ROOT)
open(os.path.join(_one, 'beans', 'box.md'), 'w').write(
    '---\nbean: box\nkind: host\ntitle: "box"\nstatus: active\nsummary: "a box"\nnature: physical\n'
    'identity:\n  status: confirmed\n  anchors:\n'
    '    - { key: serial, value: "SN-0042", class: hardware, establishing: true }\n'
    '    - { key: serial, value: "sn-0042", class: hardware, establishing: true }\n'
    'provenance: { src: observed, by: "test", as_of: 2026-09-17 }\n'
    'owned_by: { legal: { external: "someone" } }\nresponsibility: { legal: { external: "someone" } }\n---\nA box.\n')
_g = subprocess.run([sys.executable, 'bin/dmcheck.py'], capture_output=True, text=True, cwd=_one).stdout
check("one bean carrying both spellings is not reported as a duplicate of ITSELF (the lowercase one still warns)",
      'same object in one garden' not in _g and "is compared as 'SN-0042'" in _g, _g.strip()[-300:])

# ---------------------------------------------------------------- positions in time (std-vocab 9.3, T2)
# The `time` aspect's order is PARTIAL: a reading is absorbed by a finer one it contains, and every other
# pair stays a disagreement. The order follows the VALUE (a position in gregorian-civil's one form), so it
# holds under any key name.
def _timed(garden, owns):
    g = _host(garden, 'clock', 'SN-CLOCK-1')
    g[0]['fm']['owns'] = owns
    return g

def _merged_owns(a, b):
    sd = list(M.merge_gardens([_timed('g1', a), _timed('g2', b)]).values())[0]
    return sd['facts']['owns']['members']

_o = _merged_owns({'checked': '2026-09-19'}, {'checked': '2026-09-19 22:50+03:00'})
check("T2: a day reading is absorbed by a finer reading inside it, under any key name",
      _o['checked'].get('value') == '2026-09-19 22:50+03:00', json.dumps(_o['checked']))
check("...and the coarser reading is kept in provenance, not dropped",
      [x['value'] for x in _o['checked'].get('subsumed') or []] == ['2026-09-19'], json.dumps(_o['checked']))
_o = _merged_owns({'seen': '2026-09-19'}, {'seen': '2026-09-20 00:10+03:00'})
check("T2: readings that do not nest stay a disagreement for a person",
      'conflict' in json.dumps(_o['seen']), json.dumps(_o['seen']))
_o = _merged_owns({'seen': '2026-09-19 22:00Z'}, {'seen': '2026-09-20 01:00:15+03:00'})
check("T2: containment is judged in the coarser reading's own offset (22:00Z contains 01:00:15+03:00)",
      'conflict' not in json.dumps(_o['seen']) and '01:00:15' in json.dumps(_o['seen']), json.dumps(_o['seen']))
_o = _merged_owns({'seen': '2026-09-19 22:00Z'}, {'seen': '2026-09-19 22:00:15'})
check("T2: a reading with an offset does not contain one that states none — unordered, not guessed",
      'conflict' in json.dumps(_o['seen']), json.dumps(_o['seen']))
_o = _merged_owns({'seen': '2026-09-19 22:00Z'}, {'seen': '2026-09-19 22:00:30Z'})
check("T2: parts are compared, not characters — 22:00Z contains 22:00:30Z though neither string starts the other",
      _o['seen'].get('value') == '2026-09-19 22:00:30Z', json.dumps(_o['seen']))

# ---------------------------------------------------------------- an anchor's PROVENANCE is ranked (20.0)
# `anchor_authority` declared `scanned<operator-asserted<external` and was a second vocabulary for the one
# question `provenance_src` answers. Since 20.0 an anchor carries its own `provenance` where its source differs
# from its bean's, and two records of one anchor that differ only in that are resolved by the `provenance_src`
# rank — the vocabulary deciding rather than arrival order.
def _anchored(garden, prov):
    anc = {'key': 'serial', 'value': 'SN-A1', 'class': 'hardware', 'establishing': True}
    if prov:
        anc['provenance'] = prov
    return [{'garden': garden, 'id': 'box', 'fm': {
        'bean': 'box', 'kind': 'host', 'nature': 'physical', 'title': 'b', 'status': 'active', 'summary': 'b',
        'identity': {'status': 'confirmed', 'anchors': [anc]},
        'provenance': {'src': 'observed', 'by': garden, 'as_of': '2026-09-17'}}}]
_asserted = {'src': 'asserted-by-human', 'by': 'sam (operator)', 'as_of': '2026-09-17'}
_sd = list(M.merge_gardens([_anchored('g1', None), _anchored('g2', _asserted)]).values())[0]
_anc = _sd['identity']['anchors'][0]
check("an anchor's own PROVENANCE survives the merge — a scanned value and an asserted one are not the same fact",
      _anc.get('provenance') == _asserted and '_src' not in _anc, json.dumps(_anc))
check("...and the `provenance_src` rank decides between them, rather than arrival order",
      not _sd['identity'].get('anchor_conflicts'), json.dumps(_sd['identity']))
_sd = list(M.merge_gardens([_anchored('g2', _asserted), _anchored('g1', None)]).values())[0]
check("...in either order, because a rank is not arrival order",
      _sd['identity']['anchors'][0].get('provenance') == _asserted, json.dumps(_sd['identity']['anchors']))
check("a term may now declare any order the merge can APPLY — `instant` on a term is no longer a silent no-op",
      M.leaf_order.__doc__ and 'instant' in M.ORDERS and 'containment' in M.ORDERS, str(M.ORDERS))

# ---------------------------------------------------------------- the src rank is DECLARED (std-vocab 11.3)
# MODEL.md and MERGE.md state the guard; the order that implements it was four numbers in bin/dmmerge.py.
# `provenance_src` declares it now. These pin that the merge READS the declaration, and that reading it
# moved nothing.
def _said(garden, src, owns):
    g = _host(garden, 'witness', 'SN-WIT-1')
    g[0]['fm']['owns'] = owns
    g[0]['fm']['provenance'] = {'src': src, 'by': garden, 'as_of': '2026-09-20'}
    return g
def _owns(a, b):
    return list(M.merge_gardens([a, b]).values())[0]['facts']['owns']['members']
check("the src rank comes from the vocabulary, in the order the constant held",
      M.ranked_order('provenance_src') == ['generated-by-tool', 'inferred', 'observed', 'asserted-by-human'],
      str(M.ranked_order('provenance_src')))
check("...and no copy of it is left in the merge", not hasattr(M, 'SRC_RANK'))
for _pair in ((('g1', 'asserted-by-human', {'os': 'AlmaLinux 9'}), ('g2', 'inferred', {'os': 'AlmaLinux 9.8'})),
              (('g2', 'inferred', {'os': 'AlmaLinux 9.8'}), ('g1', 'asserted-by-human', {'os': 'AlmaLinux 9'}))):
    _o = _owns(_said(*_pair[0]), _said(*_pair[1]))
    check("THE GUARD: a more precise INFERRED value does not swallow an ASSERTED-BY-HUMAN one (%s first)" % _pair[0][1],
          'AlmaLinux 9' in [c.get('value') for c in (_o['os'].get('conflict') or [_o['os']])]
          and _o['os'].get('value') != 'AlmaLinux 9.8', json.dumps(_o['os']))
_o = _owns(_said('g1', 'observed', {'os': 'AlmaLinux 9'}), _said('g2', 'inferred', {'os': 'AlmaLinux 9.8'}))
check("...while below the top of the rank a refinement still subsumes, as it always did",
      _o['os'].get('value') == 'AlmaLinux 9.8', json.dumps(_o['os']))
_o = _owns(_said('g1', 'inferred', {'site': 'IST'}), _said('g2', 'asserted-by-human', {'site': 'IST'}))
check("a value two gardens agree on keeps the HIGHEST src the rank declares",
      _o['site'].get('src') == 'asserted-by-human', json.dumps(_o['site']))

# ---------------------------------------------------------------- generated-by-tool BORROWS its standing (12.0)
# A tool knows nothing of its own, so a generated fact weighs as the weakest src it names in `provenance.from`,
# and at the bottom of the rank when it names none. The label is never rewritten.
def _generated(garden, owns, frm=None):
    g = _said(garden, 'generated-by-tool', owns)
    if frm is not None:
        g[0]['fm']['provenance']['from'] = frm
    return g
_o = _owns(_generated('g1', {'site': 'IST'}), _said('g2', 'inferred', {'site': 'IST'}))
check("12.0: a generated fact that names no basis sits at the bottom — an inference outweighs it",
      _o['site'].get('src') == 'inferred', json.dumps(_o['site']))
_o = _owns(_generated('g1', {'site': 'IST'}, {'a': {'src': 'observed'}}), _said('g2', 'inferred', {'site': 'IST'}))
check("12.0: ...and one computed from OBSERVED facts outweighs the inference, keeping its own label",
      _o['site'].get('src') == 'generated-by-tool' and '_as' not in json.dumps(_o), json.dumps(_o['site']))
_o = _owns(_generated('g1', {'site': 'IST'}, {'a': {'src': 'observed'}, 'b': {'src': 'inferred'}}),
           _said('g2', 'observed', {'site': 'IST'}))
check("12.0: a chain is as strong as its weakest link — observed+inferred inputs weigh as inferred",
      _o['site'].get('src') == 'observed', json.dumps(_o['site']))
_o = _owns(_generated('g1', {'os': 'AlmaLinux 9.8'}, {'a': {'src': 'asserted-by-human'}}),
           _said('g2', 'asserted-by-human', {'os': 'AlmaLinux 9'}))
check("12.0: borrowing never launders UPWARD past the guard's own protection of a stated assertion",
      'AlmaLinux 9' in json.dumps(_o['os']), json.dumps(_o['os']))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nconverge: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
