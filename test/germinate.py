#!/usr/bin/env python3
"""germinate — can a stranger grow a working garden from seed/, and does its gate REFUSE?

WHY THIS EXISTS SEPARATELY. `dmcheck.py` exits 0 in three different situations that look identical from
outside: the law is present and satisfied, the law is present and the garden is empty, or the law is
MISSING and half the checks silently did nothing. Only a positive-and-negative test in a real git repo can
tell them apart — and the seven staged-blob rules are wrapped in a bare `except Exception: pass`, so
outside a git repository they never execute at all. A germination test in a tempdir with no `git init`
would therefore certify a gate whose commit-time half was never run.

It asserts BOTH directions, because a garden that accepts everything passes a positive-only test:
  +  germinate -> write a bean -> stage it WITH the journal -> gate 0 -> the commit succeeds
  -  a bean staged WITHOUT the journal is refused (provenance duty)
  -  an undeclared kind is refused                      (this is what promoting kinds to Tier-0 bought)
  -  a nature contradicting its kind is refused
  -  the law removed is an ERROR, not a warning         (there is no fallback)
  -  a pin disagreeing with the vocabulary is an ERROR, not a warning

It is NOT in the pre-commit hook, deliberately: it germinates a child garden and commits inside it, so a
hook that ran it would recurse. It tests machinery, like golden.py — run it by hand before any change to
seed/ lands.

Run: python3 test/germinate.py   (0 = green).  ~2s.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results = []


def check(name, ok, detail=''):
    ok = bool(ok)
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{detail}]" if detail and not ok else ''))


def run(*a, cwd):
    return subprocess.run(a, capture_output=True, text=True, cwd=cwd)


def gate(cwd):
    r = run(sys.executable, os.path.join(cwd, 'bin', 'dmcheck.py'), cwd=cwd)
    return r.returncode, r.stdout + r.stderr


BEAN = """---
bean: ada
kind: person
title: "Ada — the first bean of a germinated garden"
status: active
summary: "A person written into a garden grown from the seed, proving the language travelled: the kind registry, the nature axis, the identity policy and the journal duty all arrive with it."
identity:
  status: confirmed
  anchors:
    - {{ key: person_id, value: "person:ada", class: logical, establishing: true, scope: global, observed: 2026-08-02, authority: operator-asserted }}
provenance: {{ src: asserted-by-human, by: "test/germinate.py", as_of: 2026-08-02 }}
nature: {nature}
---
A person, written to prove a fresh garden can hold one.
"""

TMP = tempfile.mkdtemp(prefix='dmgerm-')
G = os.path.join(TMP, 'newgarden')

r = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), G, cwd=ROOT)
check("germinate.sh grows a garden and its first gate run is clean",
      r.returncode == 0 and '0 error(s)' in r.stdout, (r.stdout + r.stderr)[-400:])
# A NEW GARDEN STARTS QUIET. It started with 11 warnings about Tier-0 relations it had no reason to draw yet,
# which teaches a garden on its first day that warnings are noise (fixed 2026-09-17; those are dmreview's now).
check("...and it starts with ZERO warnings — nothing to learn to ignore on day one",
      ' 0 warning(s)' in r.stdout, [l for l in r.stdout.splitlines() if 'warning(s)' in l or l.startswith('WARN')][:4])
check("it carries the LANGUAGE and no beans — an estate's facts are not the language",
      os.path.isdir(os.path.join(G, 'bin')) and os.path.isfile(os.path.join(G, 'seed', 'std-vocab.md'))
      and os.listdir(os.path.join(G, 'beans')) == [],
      str(os.listdir(G)))
check("it is a git repository with one commit — a garden that cannot commit has not germinated",
      run('git', 'rev-parse', 'HEAD', cwd=G).returncode == 0)
# A RELATIVE TARGET IS RELATIVE TO WHERE YOU STAND, not to the release. v0.3.0 planted the language inside the
# clone when given `garden` instead of `/abs/garden`; every check above used an absolute path, so none saw it.
_rel_cwd = os.path.join(TMP, 'relative-cwd')
os.makedirs(_rel_cwd)
_rr = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), 'rel-garden', cwd=_rel_cwd)
check("a RELATIVE target grows the garden where the caller stands, and nothing lands inside the release",
      _rr.returncode == 0 and os.path.isfile(os.path.join(_rel_cwd, 'rel-garden', 'bin', 'dmcheck.py'))
      and not os.path.exists(os.path.join(ROOT, 'rel-garden')), (_rr.stdout + _rr.stderr)[-300:])

# THE MODEL, THE PROCEDURE, THE QUEUE AND THE SKILL TRAVEL (2026-09-17). Without them a friend's garden had the
# law's data and nothing saying what it meant; the first person bean took three attempts.
_TRAVEL = ('MODEL.md', 'CHECKLIST.md', 'MERGE.md', 'log/pending.md', '.claude/skills/daftar/SKILL.md',
           'AGENTS.md', 'seed/WELCOME.md')
check("MODEL.md, CHECKLIST.md, MERGE.md, log/pending.md and every door for an agent travel",
      all(os.path.isfile(os.path.join(G, f)) for f in _TRAVEL),
      [f for f in _TRAVEL if not os.path.isfile(os.path.join(G, f))])

# THE EXAMPLES IN seed/README.md AND seed/COOKBOOK.md ARE COMMITTED IN A FRESH GARDEN, so the pages cannot drift
# from the law. The cookbook's VOCAB.md fragment is applied too, and the NAS then uses the value it adds.
_ex_tmp = os.path.join(TMP, 'readme-examples')
run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), _ex_tmp, cwd=ROOT)
_examples, _fragments = [], []
for _doc in ('README.md', 'COOKBOOK.md', 'WELCOME.md'):
    _page = open(os.path.join(ROOT, 'seed', _doc), encoding='utf-8').read()
    _examples += re.findall(r'<!-- example: (beans/[a-z0-9-]+\.md) -->\n```markdown\n(.*?)\n```', _page, re.S)
    _fragments += re.findall(r'<!-- example-front-matter: VOCAB\.md -->\n```yaml\n(.*?)\n```', _page, re.S)
# THE NEWCOMER'S FIRST COMMIT, EXACTLY AS seed/README.md TEACHES IT, AND ON ITS OWN. The two beans of the
# "Your first beans" section plus the journal entry printed beside them, committed together and nothing
# else — because that commit is what a stranger's first five minutes actually is, and it is the step they
# fail on. Not for the bean: for the ENTRY, whose heading is a position in time and whose `[[id]]` is what
# satisfies the provenance duty. A page that shows two beans and no entry guarantees a refusal, so the
# entry is now an example too, and this is where it is proved rather than asserted.
_rm = open(os.path.join(ROOT, 'seed', 'README.md'), encoding='utf-8').read()
_first = re.findall(r'<!-- example: (beans/(?:sam|laptop)\.md) -->\n```markdown\n(.*?)\n```', _rm, re.S)
_first_j = re.findall(r'<!-- example: log/journal\.md -->\n```markdown\n(.*?)\n```', _rm, re.S)
check("seed/README.md still shows a first person, a first host AND the journal entry that commits them",
      len(_first) == 2 and len(_first_j) == 1, f"beans={len(_first)} entries={len(_first_j)}")
for _path, _text in _first:
    open(os.path.join(_ex_tmp, _path), 'w', encoding='utf-8').write(_text + '\n')
with open(os.path.join(_ex_tmp, 'log', 'journal.md'), 'a', encoding='utf-8') as _j:
    _j.write('\n' + (_first_j[0] if _first_j else '') + '\n')
run('git', 'add', '-A', cwd=_ex_tmp)
_first_c = run('git', '-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-qm', 'first beans', cwd=_ex_tmp)
check("A STRANGER'S FIRST COMMIT GOES THROUGH: the two beans and the entry, copied from the page as written",
      _first_c.returncode == 0, (_first_c.stdout + _first_c.stderr)[-600:])

for _path, _text in _examples:
    open(os.path.join(_ex_tmp, _path), 'w', encoding='utf-8').write(_text + '\n')
_vp = os.path.join(_ex_tmp, 'VOCAB.md')
for _frag in _fragments:
    _v = open(_vp, encoding='utf-8').read()
    for _key in re.findall(r'^([a-z_]+):', _frag, re.M):          # a key the template holds empty is REPLACED
        _v = re.sub(rf'^{_key}: \[\].*\n', '', _v, count=1, flags=re.M)
    _head, _sep, _rest = _v.partition('\n---\n')                   # insert before the closing fence
    open(_vp, 'w', encoding='utf-8').write(_head + '\n' + _frag + _sep + _rest)
_nas = os.path.join(_ex_tmp, 'beans', 'nas.md')
if _fragments and os.path.isfile(_nas):
    _n = open(_nas, encoding='utf-8').read()
    open(_nas, 'w', encoding='utf-8').write(_n.replace('provides_habitat: linux-baremetal\n', 'provides_habitat: linux-baremetal\nos: nas-os\n', 1))
with open(os.path.join(_ex_tmp, 'log', 'journal.md'), 'a', encoding='utf-8') as _j:
    _j.write('\n## 2026-09-17 10:00+00:00 · human (test) · the README and COOKBOOK examples\n- action: RULE-CHANGE (VOCAB.md adds nas-os); '
             + ', '.join(p for p, _ in _examples) + '\n')
run('git', 'add', '-A', cwd=_ex_tmp)
_ex_c = run('git', '-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-qm', 'examples', cwd=_ex_tmp)
check(f"the {len(_examples)} bean examples and {len(_fragments)} VOCAB fragments in seed/README.md + seed/COOKBOOK.md "
      f"commit in a fresh garden, as written, with 0 errors",
      len(_examples) >= 8 and len(_fragments) == 2 and _ex_c.returncode == 0, (_ex_c.stdout + _ex_c.stderr)[-500:])
_ex_gate = run(sys.executable, os.path.join(_ex_tmp, 'bin', 'dmcheck.py'), cwd=_ex_tmp).stdout
check("...with ZERO warnings, and the banner names the garden and the release it runs",
      ' 0 warning(s)' in _ex_gate and re.search(r'^readme-examples \(daftar [^)]+\): ', _ex_gate, re.M),
      _ex_gate.strip().splitlines()[-1] if _ex_gate.strip() else '')

# THE JOURNAL ENTRY MUST SAY WHAT IT RECORDS (v0.4.0). Each of these was accepted before: any added byte satisfied
# the provenance duty, and a vocabulary change needed no RULE-CHANGE marker.
def _try_commit(mutate, journal_line):
    mutate()
    with open(os.path.join(_ex_tmp, 'log', 'journal.md'), 'a', encoding='utf-8') as _j:
        _j.write(journal_line)
    run('git', 'add', '-A', cwd=_ex_tmp)
    _r = run('git', '-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-qm', 'probe', cwd=_ex_tmp)
    run('git', 'reset', '-q', '--hard', cwd=_ex_tmp)
    return _r.returncode, _r.stdout + _r.stderr
def _append(rel, text):
    return lambda: open(os.path.join(_ex_tmp, rel), 'a', encoding='utf-8').write(text)
_rc, _o = _try_commit(_append('beans/nas.md', 'More about the NAS.\n'), '\nx\n')
check("a bean change whose journal entry does not NAME the bean is refused (the `x` bypass)",
      _rc != 0 and "never names it" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More about the NAS.\n'), '\n## 2026-09-17 10:00+00:00 · human (test) · note\n- action: [[nas]] body\n')
check("...and naming it lets the commit through", _rc == 0, _o[-300:])
_rc, _o = _try_commit(_append('VOCAB.md', '\nMore prose.\n'), '\n## 2026-09-17 10:00+00:00 · human (test) · vocab prose\n- action: VOCAB prose\n')
check("a vocabulary change whose journal entry never says RULE-CHANGE is refused",
      _rc != 0 and "never says RULE-CHANGE" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-17 10:00+00:00 · (fill in who ratified) · [[nas]]\n')
check("a journal entry with an unfilled '(fill in' field is refused", _rc != 0 and "(fill in" in _o, _o[-300:])
# v0.5.0: the release's own files are law in a garden, serials compare case- and space-insensitively, and a local
# addition the standard already carries is named as that.
_rc, _o = _try_commit(_append('MODEL.md', '\nA local note.\n'), '\n## 2026-09-17 10:00+00:00 · human (test) · a note in MODEL.md\n')
check("an edit to a release file (MODEL.md) whose journal entry never says RULE-CHANGE is refused",
      _rc != 0 and "never says RULE-CHANGE" in _o and 'MODEL.md' in _o, _o[-300:])
_rc, _o = _try_commit(_append('bin/dmcheck.py', '\n# a local patch\n'), '\n## 2026-09-17 10:00+00:00 · human (test) · RULE-CHANGE: a local patch to the gate\n')
check("...and a local patch to the gate itself goes through once the entry says RULE-CHANGE", _rc == 0, _o[-300:])
_dup = open(os.path.join(_ex_tmp, 'beans', 'nas.md'), encoding='utf-8').read().replace('bean: nas\n', 'bean: nas-two\n', 1) \
    .replace('"NAS-0042"', '"nas-0042 "', 1).replace('value: "nas", class: network', 'value: "nas-two", class: network', 1)
_rc, _o = _try_commit(lambda: open(os.path.join(_ex_tmp, 'beans', 'nas-two.md'), 'w', encoding='utf-8').write(_dup),
                      '\n## 2026-09-17 10:00+00:00 · human (test) · [[nas-two]]\n')
check("a serial differing only by case and whitespace is the SAME establishing anchor — the duplicate is refused",
      _rc != 0 and 'establishing anchor serial=NAS-0042' in _o, _o[-400:])
check("...and the stored lowercase form is warned about, naming the form it is compared in",
      "is compared as 'NAS-0042'" in _o, _o[-400:])
# THE HEADING IS A POSITION IN TIME (std-vocab 10.0, T3). Only headings a commit ADDS are checked.
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-17 · human (test) · [[nas]]\n')
check("T3: a new journal heading with a date alone is refused", _rc != 0 and "is not a position in time" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-17 10:00 +0300 · human (test) · [[nas]]\n')
check("T3: ...and so is one with a time in the old `+0300` spelling", _rc != 0 and "is not a position in time" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-17 10:00 · human (test) · [[nas]]\n')
check("T3: ...and one with no offset", _rc != 0 and "is not a position in time" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-17 10:00:05.250+03:30 · human (test) · [[nas]]\n')
check("T3: a heading in the calendar form, to any resolution from the minute down, goes through", _rc == 0, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## persian:1405-06-26 10:00+03:30 · human (test) · [[nas]]\n')
check("T3: a heading in ANOTHER calendar the law declares goes through — the journal owns no calendar's form", _rc == 0, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## persian:1405-06-26 · human (test) · [[nas]]\n')
check("T3: ...held to the minute there too", _rc != 0 and "is not a position in time" in _o, _o[-300:])
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## martian:0042-01-01 10:00+00:00 · human (test) · [[nas]]\n')
check("T3: ...and a calendar nobody declared is not one", _rc != 0 and "is not a position in time" in _o, _o[-300:])
_jp = os.path.join(_ex_tmp, 'log', 'journal.md')
_jt = open(_jp, encoding='utf-8').read()
open(_jp, 'w', encoding='utf-8').write(_jt + '\n## 2026-01-01 · human (test) · an old entry written before the law\n')
run('git', 'add', '-A', cwd=_ex_tmp)
run('git', '-c', 'user.name=t', '-c', 'user.email=t@x', 'commit', '-qm', 'history', '--no-verify', cwd=_ex_tmp)
_rc, _o = _try_commit(_append('beans/nas.md', 'More.\n'), '\n## 2026-09-18 09:00+03:00 · human (test) · [[nas]]\n')
check("T3: a heading already in the history is never checked again — only what a commit adds", _rc == 0, _o[-300:])
_vfrag = "\nregistry_additions:\n  operating_systems:\n    - { os: debian, family: unix, path_grammar: unix-filesystem, meaning: x }\n"
def _add_dup_row():
    _v = open(_vp, encoding='utf-8').read()
    _h, _sep, _r = _v.partition('\n---\n')
    _h = _h.replace('registry_additions:\n  operating_systems:\n', 'registry_additions:\n  operating_systems:\n    - { os: debian, family: unix, path_grammar: unix-filesystem, meaning: x }\n', 1)
    open(_vp, 'w', encoding='utf-8').write(_h + _sep + _r)
_rc, _o = _try_commit(_add_dup_row, '\n## 2026-09-17 10:00+00:00 · human (test) · RULE-CHANGE: debian added locally\n')
check("a local registry addition the standard already carries is named as that, with the fix",
      _rc != 0 and "already in std-vocab" in _o and "remove it from registry_additions" in _o
      and 'drifted' not in _o, _o[-400:])

# THE EXECUTABLE BITS TRAVEL. v0.4.0 and v0.4.1 shipped bin/hooks/pre-commit and bin/install.sh WITHOUT them —
# an edit that wrote a new file and renamed it over the old one dropped the mode — and nothing noticed, because
# install.sh chmods the hook as it copies it. A release's own files must carry the modes they are used with.
_modes = run('git', 'ls-files', '-s', 'bin/hooks/pre-commit', 'bin/install.sh', cwd=ROOT).stdout.split('\n')
check("the release's hook and installer are committed executable (mode 100755)",
      len([l for l in _modes if l.startswith('100755')]) == 2, _modes)

# THE MERGE CONFIGURATION TRAVELS. Missing this, a germinated garden text-merges its beans and conflicts
# on its own append-only journal — and nothing says so, because git warns neither when an attribute names
# a missing driver nor when a configured driver is named by nothing. Found by merging three germinated
# gardens for real: the driver was configured in every one and invoked in none.
# WHAT TRAVELS UNDER bin/: `cp -R bin/` once shipped a garden's own private tool — its host names, home
# paths and a LAN address — and, with no .gitignore, 15 .pyc files in the first commit.
_tracked = run('git', 'ls-files', cwd=G).stdout.split()
_bin = [f for f in _tracked if f.startswith('bin/')]
check("only daftar's own tools travel under bin/ — every bin/dm*.py, the hooks and the installer, nothing else",
      _bin and all(re.match(r'^bin/(dm[a-z]*\.py|install\.sh|hooks/[^/]+)$', f) for f in _bin)
      and 'bin/dmcheck.py' in _bin and 'bin/dmsafe.py' in _bin,
      [f for f in _bin if not re.match(r'^bin/(dm[a-z]*\.py|install\.sh|hooks/[^/]+)$', f)][:10])
check("no bytecode is committed, and `.gitignore` travelled to keep it that way",
      not any('__pycache__' in f or f.endswith('.pyc') for f in _tracked) and '.gitignore' in _tracked,
      [f for f in _tracked if f.endswith('.pyc')][:5])

check("`.gitattributes` travels — beans dispatch to the semantic merge, the journal merges by union",
      'daftar' in run('git', 'check-attr', 'merge', '--', 'beans/x.md', cwd=G).stdout
      and 'union' in run('git', 'check-attr', 'merge', '--', 'log/journal.md', cwd=G).stdout,
      run('git', 'check-attr', 'merge', '--', 'beans/x.md', 'log/journal.md', cwd=G).stdout.strip())
check("...and the driver it names is actually configured in the new garden",
      'dmmerge' in run('git', 'config', '--get', 'merge.daftar.driver', cwd=G).stdout)

# the pin is DERIVED from the vocabulary, never typed: the one that was typed sat two majors stale
import re
_sv = open(os.path.join(G, 'seed', 'std-vocab.md'), encoding='utf-8').read()
_ver = re.search(r'(?m)^version:\s*"([^"]+)"', _sv).group(1)
check(f"the pins are interpolated from the vocabulary itself (@{_ver}), not typed into the template",
      all(f'extends: std-vocab@{_ver}' in open(os.path.join(G, f), encoding='utf-8').read()
          for f in ('VOCAB.md', 'GARDEN.md')))

# ---- NEGATIVE: a bean without its journal entry -------------------------------------------------------
bean_path = os.path.join(G, 'beans', 'ada.md')
open(bean_path, 'w', encoding='utf-8').write(BEAN.format(nature='living'))
run('git', 'add', 'beans/ada.md', cwd=G)
rc, out = gate(G)
check("a bean staged WITHOUT a journal entry is refused (provenance duty)",
      rc != 0 and 'journal.md not updated' in out, out.strip()[-300:])

# ---- POSITIVE: the same bean, journalled, commits -----------------------------------------------------
with open(os.path.join(G, 'log', 'journal.md'), 'a', encoding='utf-8') as fh:
    fh.write("\n## 2026-08-02 10:00+00:00 · agent · first bean\n- action: wrote beans/ada.md to prove the garden holds one.\n- refs: beans/ada.md\n")
run('git', 'add', '-A', cwd=G)
rc, out = gate(G)
check("with the journal entry, the gate passes", rc == 0 and '0 error(s)' in out, out.strip()[-300:])
c = run('git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'first bean', cwd=G)
check("and the commit succeeds — the first bean lands", c.returncode == 0, (c.stdout + c.stderr)[-300:])

# ---- NEGATIVE: an undeclared kind. This is exactly what promoting kinds to Tier-0 bought. --------------
def mutate(text):
    open(bean_path, 'w', encoding='utf-8').write(text)
    run('git', 'add', '-A', cwd=G)
    rc, out = gate(G)
    run('git', 'checkout', '-q', '--', '.', cwd=G)
    run('git', 'reset', '-q', cwd=G)
    return rc, out

rc, out = mutate(BEAN.format(nature='living').replace('kind: person', 'kind: wizard'))
check("an UNDECLARED kind is refused — the kind registry travelled with the seed",
      rc != 0 and 'not declared in the vocabulary' in out, out.strip()[-300:])

rc, out = mutate(BEAN.format(nature='physical'))
check("a nature contradicting its kind is refused — the D1 axis travelled too",
      rc != 0 and 'contradicts kind' in out, out.strip()[-300:])

# ---- NEGATIVE: the law itself ------------------------------------------------------------------------
law = os.path.join(G, 'seed', 'std-vocab.md')
saved = open(law, encoding='utf-8').read()
os.remove(law)
rc, out = gate(G)
open(law, 'w', encoding='utf-8').write(saved)
check("the law REMOVED is an ERROR, not a warning — there is no fallback to a second copy",
      rc != 0 and 'no fallback' in out, out.strip()[-300:])

voc = os.path.join(G, 'VOCAB.md')
saved_v = open(voc, encoding='utf-8').read()
open(voc, 'w', encoding='utf-8').write(saved_v.replace(f'std-vocab@{_ver}', 'std-vocab@0.1', 1))
rc, out = gate(G)
open(voc, 'w', encoding='utf-8').write(saved_v)
check("a pin DISAGREEING with the installed vocabulary is an ERROR, not a warning",
      rc != 0 and 'pins std-vocab@0.1' in out, out.strip()[-300:])

# ---- AND IT MERGES BACK. This is the second half of the 1.0.0 criterion, made executable ------------
# "passes its own first gate run AND merges cleanly with this one." The first half is above. This is the
# second, and until the vocabulary reconciliation existed there was no definition of "cleanly" to check:
# dmmerge converged BEANS while the two gardens' type systems stayed divergent, so a merged corpus could
# hold a bean of a kind the merged law never declared. Now the law is reconciled first and the merged
# corpus is checked against it, so a germinated garden either merges or says exactly why not.
run('git', 'checkout', '-q', '--', '.', cwd=G)
run('git', 'reset', '-q', cwd=G)
r = run(sys.executable, os.path.join(ROOT, 'bin', 'dmmerge.py'), ROOT, G, cwd=ROOT)
out = r.stdout + r.stderr
check("a germinated garden MERGES BACK with the one it grew from — the 1.0.0 criterion's second half",
      r.returncode == 0 and 'MERGE REFUSED' not in out, out.strip()[-400:])
check("...their laws reconcile: the seed interpolated the pin, so both gardens share one Tier-0 version",
      f'reconciled at std-vocab@{_ver}' in out, [l for l in out.splitlines() if 'VOCABULARY' in l])
check("...and the merged corpus has no uncovered kind, key or unmet obligation",
      'UNCOVERED' not in out and 'UNMET' not in out,
      '; '.join(l.strip() for l in out.splitlines() if 'UNCOVERED' in l or 'UNMET' in l))
check("the child's bean is IN the merged result, not silently dropped",
      'person:ada' in out or 'ada' in out)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\ngerminate: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
