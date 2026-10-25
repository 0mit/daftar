#!/usr/bin/env python3
"""core_monitoring — monitoring as needs (core 4.3): a probe is a reading of a being's need, its health apart from its
value; a need's silence is its interval; a failure found benign leaves the leads until its review falls due; a cause
is a `come` between two happenings; a board member says one line; and a probed name is resolved where it is served on
the LAN.

- the law: `fail`'s `by` takes a statement, the reading that is the probe; `need` takes an `interval`, an extent; the
  verdicts hold `benign`; `come`'s roles take statements; a drawing's members take `says`;
- the gate: a probe's failure, a need's interval, a failure found benign with its review, a cause between failures —
  in one bean and across two — stand; an interval with ends or on another line is refused by rule measured; benign said
  of what is no failure, or with no day it is looked at again, by rule squares; a failure that came of a being, a need
  that came of a failure, a being that came of a failure, and a circle of causes, by rule life; a member's `says` that
  is no prose, by rule profile;
- a garden: `bin/routines.py cross` writes a probe's failure once — by the reading, never the being's — and its repair
  when it reads again; a reading older than the need's interval, or a probe failing for longer, is the need's silence,
  a crossing of the being; `bin/leads.py` tells a probe's failure as the probe's, and a failure found benign is no lead
  until the day its review falls due, when it is one again beside the review's own obligation;
- the view: a board member's `says` is in the shape the runtime draws; the adapter's LAN is the standards' private
  ranges, and a prefix either side states narrows it to one network.

Run: python3 test/core_monitoring.py   (0 = green)
"""
import datetime, ipaddress, json, os, shutil, socket, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, 'bin')):
    sys.path.insert(0, _p)
sys.path.append(os.path.join(ROOT, 'test'))           # after the root: test/core.py is a suite, not the core
from core import engine, read  # noqa: E402
from core.law import Law  # noqa: E402
import grow  # noqa: E402

FAILS = []
PY = sys.executable
HOST = socket.gethostname()
CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
T = tempfile.mkdtemp(prefix='core-monitoring-')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


SAY = {'say': {'by': 'sam', 'at': 'now'}}


def bean(bid, kind, *statements):
    return engine.Bean(bid, header={'bean': bid, 'kind': kind, 'title': bid, 'statements': [SAY, *statements]})


def found(*beans, rules=None):
    base = {bid: engine.Bean(bid, header={'bean': bid, 'kind': b['kind'], 'title': bid, 'statements': b['statements']})
            for bid, b in CASES['garden'].items()}
    g = engine.Garden(dict(base, **{b.id: b for b in beans}), CASES['zone'],
                      files=['VOCAB.md', 'GARDEN.md', 'log/journal.md'], manifest={'gardener': 'sam'})
    return [f for f in engine.Judge(LAW, g).run() if rules is None or f[0] in rules]


READING = {'id': 'none-down', 'reading': {'what': 'no service is down', 'inputs': [
    {'name': 'down', 'origin': {'act': 'read', 'nature': 'soma', 'by': 'nas'}, 'quantity': 'number'}],
    'steps': [{'id': 'zero', 'op': 'constant', 'value': {'count': '0', 'unit': '{item}'}},
              {'id': 'ok', 'op': 'compare', 'of': 'down', 'with': 'zero', 'is': 'at-most'}]}}
TEN = {'of': 'time', 'measure': {'count': '10', 'unit': 'min'}}
F1 = {'fail': {'id': 'f1', 'by': 'self', 'as': 'errors in the log', 'at': '2026-10-01 10:00'}}
F2 = {'fail': {'id': 'f2', 'by': 'self', 'as': 'DNS timeouts', 'at': '2026-10-01 10:05'}}
REVIEW = {'obligatory': {'id': 'f1-review', 'of': 'f1-benign', 'through': 'sam', 'clause': {'due': '2026-11-15'}}}

try:
    # ---- THE LAW
    fail, need, come = LAW.verbs['fail'], LAW.verbs['need'], LAW.verbs['come']
    check("the law: a failure is a being's or a reading's — `fail`'s `by` takes a statement, the probe",
          'statement' in fail['roles']['by']['shape'] and 'probe' in fail['meaning'], fail['roles']['by'])
    check("the law: a need takes its `interval`, an extent, how long its reading may be silent",
          need.get('qualifiers', {}).get('interval') == {'shape': 'form', 'form': 'extent'} and 'silent' in need['meaning'],
          need.get('qualifiers'))
    check("the law: a response may find a failure benign", 'benign' in (LAW.tables.get('verdicts') or []),
          LAW.tables.get('verdicts'))
    check("the law: a `come` may be between two happenings, a cause",
          'statement' in come['roles']['by']['shape'] and 'statement' in come['roles']['through']['shape'], come['roles'])
    members = LAW.profile_forms['drawing']['attrs']['members']['in']['entries'] if hasattr(LAW, 'profile_forms') else None
    if members is None:
        import yaml
        members = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'profiles.yaml'), encoding='utf-8'))['forms'][
            'drawing']['attrs']['members']['in']['entries']
    check("the law: a board's member says one line of prose (`says`, beside `fact`)",
          members.get('says') == {'in': 'prose'} and 'fact' in members, members)

    # ---- THE GATE
    probe = bean('mx', 'host', {'need': {'id': 'up', 'by': 'self', 'of': 'every service runs', 'interval': TEN}},
                 {'meet': {'by': 'none-down', 'of': 'up'}}, {'reckon': READING},
                 {'fail': {'id': 'p1', 'by': 'none-down', 'as': 'the probe none-down does not read', 'at': '2026-10-01 10:00'}})
    got = found(probe, rules={'valency', 'measured', 'form', 'knowing'})
    check("the gate: a probe's failure — a `fail` by the reading that meets the need — and the need's interval stand",
          not got, got)
    for name, interval, says in (
            ("an interval with an end", {'of': 'time', 'from': '2026-10-01', 'measure': {'count': '10', 'unit': 'min'}},
             "has no ends"),
            ("an interval on another line", {'of': 'place', 'measure': {'count': '10', 'unit': 'm'}}, "a length of time"),
            ("an interval counted in cells, with no system", {'of': 'time', 'level': 'day', 'count': '1'}, "a level belongs")):
        got = found(bean('mx', 'host', {'need': {'id': 'up', 'by': 'self', 'of': 'x', 'interval': interval}}), rules={'measured'})
        check(f"rule measured: {name} is refused", any(says in m for _r, _w, m in got), got)
    got = found(bean('mx', 'host', {'need': {'id': 'up', 'by': 'self', 'of': 'x',
                                             'interval': {'of': 'time', 'in': 'gregorian-civil', 'level': 'day', 'count': '1'}}}),
                rules={'measured'})
    check("rule measured: an interval of one calendar day stands", not got, got)

    benign = {'respond': {'id': 'f1-benign', 'by': 'sam', 'of': ['f1'], 'as': 'benign',
                          'through': 'the filter never sends QUIT; nothing is lost'}}
    got = found(bean('mx', 'host', F1, benign, REVIEW), rules={'squares', 'valency', 'measured'})
    check("the gate: a failure found benign, its review an obligation of the response falling due, stands", not got, got)
    for name, st, says in (
            ("benign said of a need", [{'need': {'id': 'f1', 'by': 'self', 'of': 'x'}}, benign, REVIEW],
             "benign is said of a failure"),
            ("benign with no review", [F1, benign], "names no day it is looked at again"),
            ("benign whose review has no day", [F1, benign, {'obligatory': {'of': 'f1-benign', 'through': 'sam'}}],
             "names no day it is looked at again"),
            ("benign with no id to be looked at by", [F1, {'respond': {'by': 'sam', 'of': ['f1'], 'as': 'benign'}}, REVIEW],
             "give the response an `id`"),
            ("a second verdict beside benign", [F1, benign, REVIEW, {'respond': {'by': 'sam', 'of': ['f1'], 'as': 'confirms'}}],
             "second verdict")):
        got = found(bean('mx', 'host', *st), rules={'squares'})
        check(f"rule squares: {name} is refused", any(says in m for _r, _w, m in got), got)
    other = bean('dns', 'host', F2, {'come': {'by': 'f2', 'through': ['mx#f1']}})
    got = found(bean('mx', 'host', F1, benign, REVIEW), other, rules={'life', 'valency'})
    check("the gate: a cause across two beans — a failure came of another's — stands", not got, got)
    for name, beans, says in (
            ("a failure that came of a person", [bean('mx', 'host', F1, {'come': {'by': 'f1', 'through': ['sam']}})],
             "is no `fail`"),
            ("a need that came of a failure", [bean('mx', 'host', F1, {'need': {'id': 'up', 'by': 'self', 'of': 'x'}},
                                                    {'come': {'by': 'up', 'through': ['f1']}})], "is not one"),
            ("a machine that came of a failure", [bean('mx', 'host', F1, {'come': {'by': 'self', 'through': ['f1']}})],
             "only a happening comes through a happening"),
            ("a circle of causes across two beans", [bean('mx', 'host', F1, {'come': {'by': 'f1', 'through': ['dns#f2']}}),
                                                     other], "comes through itself")):
        got = found(*beans, rules={'life'})
        check(f"rule life: {name} is refused", any(says in m for _r, _w, m in got), got)
    got = found(bean('mx', 'host', F1, F2, {'come': {'by': 'f2', 'through': ['f1']}}), bean('nest-1', 'host'),
                rules={'life'})
    check("rule life: a being's coming is judged as before beside a cause (nothing new refused)", not got, got)

    def board(member):
        return bean('shop', 'service', {'draw': {'id': 'page', 'by': 'self', 'of': ['parts'],
                                                 'page': {'drawings': 'file:drawings/shop.py'}}},
                    {'draw': {'id': 'parts', 'by': 'self', 'of': ['nas'], 'drawing': {
                        'purpose': 'p', 'outcome': 'o', 'stages': [{'label': 's', 'doer': 'd'}],
                        'questions': [{'lens': 'orient', 'ask': 'a?'}], 'archetype': 'board', 'blind': [{'what': 'w'}],
                        'members': [member]}}})
    got = found(board({'label': 'the store', 'says': 'answers on the network', 'being': 'nas'}), rules={'profile'})
    check("the gate: a board member's one line of prose stands", not got, got)
    got = found(board({'label': 'the store', 'says': {'line': 'answers'}, 'being': 'nas'}), rules={'profile'})
    check("rule profile: a member's `says` that is no prose is refused", any('says' in w or 'says' in m for _r, w, m in got), got)

    # ---- A GARDEN: the probe's health, the need's silence, benign and its review, read by the tools
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])

    def write(rel, text):
        p = os.path.join(G, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)

    def text(rel):
        with open(os.path.join(G, rel), encoding='utf-8') as fh:
            return fh.read()

    def save(what, *body):
        return grow.run(PY, 'bin/save.py', 'sam', what, '--body', *body, cwd=G)

    def moment(minutes_ago=0):
        return (datetime.datetime.now().astimezone() - datetime.timedelta(minutes=minutes_ago)).isoformat(timespec='seconds')

    def readings(down=None, minutes_ago=0):
        p = os.path.join(T, 'readings.json')
        rows = [] if down is None else [{'key': 'mail.down', 'being': 'mailer', 'property': 'number',
                                         'value': {'count': str(down), 'unit': '{item}'}, 'at': moment(minutes_ago),
                                         'instrument': 'mail-probe:fake', 'quality': 'ok'}]
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump({'tool': 'mail-probe', 'version': '1', 'at': moment(), 'readings': rows}, fh)
        return p

    def cross(down=None, minutes_ago=0):
        r = grow.run(PY, 'bin/routines.py', 'cross', '--readings', readings(down, minutes_ago), '--json', cwd=G)
        try:
            return r, json.loads(r.stdout)
        except ValueError:
            return r, None

    def leads():
        r = grow.run(PY, 'bin/leads.py', '--json', cwd=G)
        try:
            return [x for x in json.loads(r.stdout) if x.get('about') == 'mailer']
        except ValueError:
            return r.out

    write('VOCAB.md', '---\nnamespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name '
                      'for itself" }\n---\n# the garden\'s own rows\n')
    write('beans/box.md', f'''---
bean: box
kind: host
title: "box — the machine that reads the probes"
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
---
The machine.
''')
    write('beans/mail-probe.md', '''---
bean: mail-probe
kind: program
title: "mail-probe — what reads whether the mail services run"
statements:
  - make: { by: sam, at: now }
---
The tool, which runs nowhere here: what it read is given.
''')
    write('beans/mailer.md', '''---
bean: mailer
kind: host
title: "mailer — a mail server"
statements:
  - read:   { by: sam, at: now }
  - own:    { by: sam, of: self }
  - need:   { id: up, by: self, of: "every mail service runs", interval: { of: time, measure: { count: "10", unit: min } } }
  - meet:   { by: none-down, of: up }
  - reckon: { id: none-down, reading: { what: "no mail service is down (counted)", inputs: [ { name: mail-down, origin: { act: read, nature: soma, by: mail-probe }, quantity: number } ], steps: [ { id: zero, op: constant, value: { count: "0", unit: "{item}" } }, { id: ok, op: compare, of: mail-down, with: zero, is: at-most } ] } }
---
A mail server.
''')
    r = save('RULE-CHANGE: a machine, a probe and a mail server', '- action: RULE-CHANGE — VOCAB.md adds the namespace '
             'anchor-hostname; wrote [[box]], [[mail-probe]], [[mailer]]', '- ratified_by: sam')
    check("the garden holds a mail server's need, met by its probe, with an interval of ten minutes — through its gate",
          r.returncode == 0, r.out[-1200:])

    r, d = cross(down=0)
    check("cross: a probe that reads, and a need that holds, write nothing", r.returncode == 0 and d == [], r.out[-800:])
    r, d = cross(down=None)
    mt = text('beans/mailer.md')
    check("cross: a reading that does not read is the probe's failure — a `fail` BY the reading, written once — and not "
          "the being's", r.returncode == 0 and '- fail: { id: none-down-unread-' in mt and 'by: none-down' in mt
          and 'by: self, as: "every mail service runs' not in mt and any(x.get('probe') for x in d or []), r.out[-800:] + mt[-900:])
    L = leads()
    check("leads: a probe's failure is a health lead, told as the probe's and not the being's",
          isinstance(L, list) and any(x['kind'] == 'health' and x.get('probe') == 'none-down' and "probe's failure" in x['why']
                                      for x in L), L)
    r, d = cross(down=None)
    check("cross: a probe still failing writes nothing again: once, never each sample",
          r.returncode == 0 and d == [] and text('beans/mailer.md').count('- fail:') == 1, r.out[-600:])
    r, d = cross(down=0)
    mt = text('beans/mailer.md')
    check("cross: the probe reading again writes the repair of its failure, and the lead goes",
          r.returncode == 0 and '- repair: { id: none-down-unread-' in mt and 'the probe none-down reads again' in mt
          and not [x for x in leads() if x['kind'] == 'health'], r.out[-600:] + mt[-600:])
    r, d = cross(down=0, minutes_ago=30)
    mt = text('beans/mailer.md')
    check("cross: a reading older than the need's interval is its silence — the being's crossing, said silent",
          r.returncode == 0 and 'every mail service runs: silent past its interval' in mt
          and any(x['kind'] == 'health' and 'silent' in x['why'] for x in leads()), r.out[-600:] + mt[-700:])
    r, d = cross(down=0)
    check("cross: a fresh reading that holds repairs the silence", r.returncode == 0 and 'up holds again' in
          text('log/journal.md')[-3000:] and not [x for x in leads() if x['kind'] == 'health'], r.out[-600:])
    # a probe failing since an hour ago: past the interval, the need is silent though no reading says how much
    write('beans/mailer.md', text('beans/mailer.md').replace(
        '---\nA mail server.', f'  - fail: {{ id: none-down-unread-old, by: none-down, as: "the probe none-down does not read", '
                               f'at: "{(datetime.datetime.now().astimezone() - datetime.timedelta(minutes=60)).isoformat(timespec="minutes").replace("T", " ")}" }}\n  - read: {{ by: sam, of: [none-down-unread-old], at: now }}\n'
                               f'---\nA mail server.', 1))
    r = save('the probe of mailer failing since an hour ago', '- action: [[mailer]] its probe failing since an hour ago')
    check("a probe's failure an hour old is written through the gate", r.returncode == 0, r.out[-800:])
    r, d = cross(down=None)
    mt = text('beans/mailer.md')
    check("cross: a probe failing for longer than the need's interval is its silence: the being's crossing, through the "
          "need, with no reading to show", r.returncode == 0 and 'silent past its interval' in mt.split('none-down-unread-old', 1)[1]
          and 'through: up,' in mt and any(x['kind'] == 'health' and x.get('fail', '').startswith('up-') for x in leads()),
          r.out[-600:] + mt[-900:])

    # benign: a failure found benign is no lead until its review falls due
    today = datetime.date.today()
    later, sooner = (today + datetime.timedelta(days=30)).isoformat(), (today - datetime.timedelta(days=2)).isoformat()
    base = text('beans/mailer.md')

    def benign(day):
        fid = next(x['fail'] for x in leads() if x['kind'] == 'health' and x.get('fail', '').startswith('up-'))
        write('beans/mailer.md', base.replace('---\nA mail server.', f'''  - respond: {{ id: up-benign, by: sam, of: [{fid}], as: benign, through: "the probe's host is down for its move; the mail runs" }}
  - obligatory: {{ id: up-benign-review, of: up-benign, through: sam, clause: {{ due: "{day}" }} }}
  - say: {{ by: sam, of: [up-benign, up-benign-review], at: now }}
---
A mail server.''', 1))
        return fid, save(f'the silence of mailer found benign until {day}', f'- action: [[mailer]] its silence found benign, '
                                                                             f'looked at again on {day}')
    fid, r = benign(later)
    L = leads()
    check("leads: a failure found benign is no health lead while the day its review falls due is ahead",
          r.returncode == 0 and isinstance(L, list) and not [x for x in L if x.get('fail') == fid], (r.out[-600:], L))
    grow.run('git', 'reset', '-q', '--hard', 'HEAD~1', cwd=G)
    fid, r = benign(sooner)
    L = leads()
    check("leads: once its review has fallen due, the failure is a health lead again, and the review an obligation",
          r.returncode == 0 and any(x.get('fail') == fid for x in L) and any(x['kind'] == 'obligation' and
                                                                              x.get('clause') == 'up-benign-review' for x in L),
          (r.out[-600:], L))

    # ---- THE VIEW
    sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
    import view_model as vm  # noqa: E402
    prom = vm.adapter('prometheus')                    # as the asset loads it: by its file, beside its siblings
    op = vm.operate('parts', {'archetype': 'board', 'members': [{'label': 'the store', 'says': 'records to the share',
                                                                 'being': 'nas'}]})
    check("view: a board member's `says` is in the operate shape the runtime draws",
          op.get('items') and op['items'][0].get('says') == 'records to the share', op)
    net = ipaddress.ip_network
    check("view: the LAN is the standards' private ranges — RFC 1918's three and RFC 4193's — never a documentation range",
          all(any(ipaddress.ip_address(a) in n for n in prom.LANS) for a in ('10.1.2.3', '172.20.0.1', '192.168.7.7', 'fd12::1'))
          and not any(ipaddress.ip_address(a) in n for n in prom.LANS
                      for a in ('192.0.2.1', '198.51.100.1', '203.0.113.1', '172.32.0.1', '2001:db8::1')), prom.LANS)
    check("view: where neither position states a prefix, nothing says a being is on the monitor's LAN (only the "
          "monitor's own machine is resolved so)", not prom._one_lan('10.1.0.40', None, [('10.1.0.9', None)]))
    check("view: a prefix the monitor's machine states narrows its LAN to one network",
          not prom._one_lan('10.2.0.40', None, [('10.1.0.9', net('10.1.0.0/24'))])
          and prom._one_lan('10.1.0.40', None, [('10.1.0.9', net('10.1.0.0/24'))]))
    check("view: a prefix the serving being states narrows it the same; and an IPv6 LAN is no IPv4 one",
          not prom._one_lan('10.1.0.40', net('10.1.0.0/24'), [('10.2.0.9', None)])
          and not prom._one_lan('fd00::5', None, [('10.1.0.9', None)]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_monitoring: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
