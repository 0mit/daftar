#!/usr/bin/env python3
"""intake — a source's feeds read into a store, and only what the source permits (core 4.9; `python3 bin/daftar.py
intake`).

    python3 bin/intake.py setup [--by <who>] [--owner <who>]        the walks walk-intake, walk-source and walk-design
                                                                    written into this garden's mappings
    python3 bin/intake.py permits <source> [<url>]                  what the intake may read of a source, and why: it
                                                                    fetches nothing but the robots rules of its hosts
    python3 bin/intake.py read <source>... --into store:<name>      each source's feeds read into the store
    python3 bin/intake.py read --all --into store:<name>            every source admitted on walk-source

    options: --agent "<who reads, and how to reach them>" (else $DAFTAR_INTAKE_AGENT), --as <the reader's bean>
             (default `intake`), --every <seconds> (the least time between two requests to one host, 1 by default),
             --path <file> in place of --into, --json

(`python` on Windows.) A SOURCE is a bean found at its feeds: each `be: { at: "<url>", as: location }`, a position in
the `uri` system, is a feed the intake reads. It reads a source only where all of these hold, and says which did not:

  ADMITTED   the source's course on walk-source — its `be … at: walk-source, as: order` — stands at `admitted`, by its
             last move: listed, its terms read, and admitted by a person; paused or dropped, it is not read.
  ITS TERMS  an agreement about the source (a bean that is `about` it) permits it: a capability of the reader there,
             `can: { by: <the reader>, of: "<in words>", at: "<url>" }`, holding a `permitted` and no `forbidden`, as
             core/inforce.py reads a statement's standing. A capability covers the URLs that begin with its `at`, and
             with no `at`, the source's own feeds; of those that cover a URL, the longest `at` decides, and of two as
             long a forbidden one. A URL no capability covers is not read: the intake reads only what a source permits.
             Its clause may set a rate — `clause: { amount: { count: "1", unit: "{request}" }, within: { of: time,
             measure: { count: "10", unit: s } } }` — the least time between two requests the intake then keeps.
  ITS ROBOTS the robots rules of the URL's host (RFC 9309), read by Python's own urllib.robotparser for the reader's
             product token, `daftar-intake`: a path they disallow is not read, and their crawl delay or request rate
             is kept. Robots rules the host does not give (a 4xx) allow all; refused (401, 403) or failing (a 5xx, no
             answer) they allow nothing.

POLITE. One request at a time; to one host, never sooner after the last than the slowest of `--every`, the robots
rules' delay or rate, and the terms' rate. A user agent that names the reader honestly — `daftar-intake/<release>
(+<agent>)`, the agent given — and none at all without one: nothing is fetched. Conditional requests: each feed is
asked with the ETag and the Last-Modified its last answer gave, and an answer `304 Not Modified` writes nothing. A
redirect is followed at most five times, each hop judged again by the terms, the robots rules and the rate of its own
URL. `429` or `503` stops the host for this run, and the feed is not asked again before its `Retry-After` (ten
minutes where it says none). An answer is read to at most 32 MiB.

INTO THE STORE, NEVER GIT. A feed's answer is read in its format (RSS, Atom or JSON Feed: its type, else its first
element or brace) through the crosswalk `feed-item` into the store named, known by one `read` of the source — `by`
this host, `from` the source, `through` its URL — as bin/import.py keeps any reading (the flow `store-recorded`). An
item new to the store is placed on walk-intake, `fetched` then `extracted`, by this host. What only the intake needs
— each feed's validators, its last status, when it may be asked again, each host's robots rules — is the source's
detail `intake` in the store. Nothing is written to a bean.

THE WALKS are the standard's: an item taken in (walk-intake), a source (walk-source) and a design (walk-design), their
steps and reasons in WALKS below, which `setup` writes into a garden as mappings, as bin/run.py writes walk-run, and
checks where it has them. A course on one is a `be … as: order`, each step it reaches a `move`.
"""
import datetime
import email.utils
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr

TOKEN = 'daftar-intake'           # the product token robots rules name the reader by
EVERY = 1.0                       # seconds between two requests to one host, where nothing asks for longer
MAX_BYTES = 32 * 1024 * 1024
TIMEOUT = 30
HOPS = 5
RETRY = 600                       # seconds a host that said 429 or 503 is left, where its Retry-After says nothing
CROSSWALK = 'feed-item'

# ------------------------------------------------------------------------------------------------ the walks
WALKS = {
    'walk-intake': {
        'title': 'walk-intake — how an item taken in goes: from fetched to classified, or set aside',
        'summary': 'The walk an item a source gave goes along (bin/intake.py): fetched, extracted, suggested, reviewed, '
                   'classified — or set aside. The intake moves an item to fetched and extracted; a classifier '
                   'suggests, a person reviews, and its classes stand.',
        'body': "The steps of an item taken in, as bin/intake.py holds them (`WALKS`). A course on this walk is a `be` "
                "of the item, `as: order`; the intake writes it, and the item's first two moves, in the store it reads "
                "into. A suggestion is a `classify` a classifier derived; a review, a person's `respond` to it.",
        'steps': {
            'fetched': {'to': ['extracted'], 'machine': True,
                        'says': 'read from its source as the source gave it, under its terms and its robots rules, '
                                'and kept off git'},
            'extracted': {'to': ['suggested', 'reviewed', 'set-aside'], 'machine': True,
                          'says': 'its statements read out of what was fetched, through a crosswalk of the law'},
            'suggested': {'to': ['reviewed', 'set-aside'],
                          'says': 'a classifier suggested its classes: each a `classify`, derived and never anyone\'s '
                                  'word'},
            'reviewed': {'to': ['classified', 'suggested'],
                         'says': 'a person responded to each suggestion — confirms, disputes or abstains — and gave '
                                 'their own classes where they differ'},
            'classified': {'final': True,
                           'says': 'its classes stand: confirmed or given by a person, or a graduated classifier\'s, '
                                   'still derived'},
            'set-aside': {'exit': True, 'final': True, 'reasons': ['duplicate', 'out-of-scope', 'withdrawn', 'unreadable'],
                          'says': 'not taken further: the same item again, outside what the garden follows, withdrawn '
                                  'at its source, or not readable'},
        },
    },
    'walk-source': {
        'title': 'walk-source — how a source goes: from listed to admitted, paused or dropped',
        'summary': 'The walk a source of the intake goes along (bin/intake.py): listed, its terms read, admitted — '
                   'perhaps paused — or dropped. The intake reads a source only while its course stands at admitted.',
        'body': "The steps of a source, as bin/intake.py holds them (`WALKS`). A course on this walk is a `be` of the "
                "source, `as: order`; each move is a person's. Its terms are an agreement about it, whose permitted "
                "and forbidden clauses the intake reads before every request, with the robots rules of its hosts.",
        'steps': {
            'listed': {'to': ['terms-read', 'dropped'],
                       'says': 'named as a source to read: its feeds, each `be … as: location` in the `uri` system'},
            'terms-read': {'to': ['admitted', 'dropped'],
                           'says': 'its terms read by a person and written as an agreement about it: what the reader '
                                   'is permitted and forbidden there'},
            'admitted': {'to': ['paused', 'dropped', 'terms-read'],
                         'says': 'admitted by a person: the intake reads what its terms and its robots rules permit'},
            'paused': {'resumes': True, 'reasons': ['asked', 'retry-after'],
                       'says': 'not read for now, at someone\'s word or until its host asks again; it returns to where '
                               'it was'},
            'dropped': {'exit': True, 'final': True, 'reasons': ['terms-forbid', 'asked', 'gone', 'unwanted'],
                        'says': 'no longer read: its terms forbid it, its publisher asked, it is gone, or the garden '
                                'no longer wants it'},
        },
    },
    'walk-design': {
        'title': 'walk-design — how a design goes: from drafted to verified, withdrawn or declined',
        'summary': 'The walk a design and each of its bodies go along: drafted, shown, ratified, built, verified — or '
                   'withdrawn by its author, or declined by the person who ratifies.',
        'body': "The steps of a design, as bin/intake.py ships them (`WALKS`) beside the intake's own two. A course on "
                "this walk is a `be` of the design, or of one of its bodies, `as: order`; each move is its author's or "
                "the ratifying person's. What is ratified is built as it was shown.",
        'steps': {
            'drafted': {'to': ['shown', 'withdrawn'], 'says': 'written by its author, not yet shown'},
            'shown': {'to': ['ratified', 'drafted', 'declined', 'withdrawn'],
                      'says': 'shown to the person who ratifies it, with what it changes and its neighbourhood'},
            'ratified': {'to': ['built', 'withdrawn'], 'says': 'ratified by that person, as shown'},
            'built': {'to': ['verified', 'drafted'], 'says': 'built as it was ratified'},
            'verified': {'final': True, 'says': 'what was built read back against what was ratified, and found to hold'},
            'withdrawn': {'exit': True, 'final': True, 'reasons': ['superseded', 'asked'],
                          'says': 'taken back by its author: another design holds it, or it was asked to be'},
            'declined': {'exit': True, 'final': True, 'reasons': ['asked'],
                         'says': 'declined by the person who ratifies it'},
        },
    },
}


def walk_mapping(walk, by, owner):
    """mappings/<walk>.md as this tool writes it: the steps and reasons of WALKS, made by `by`, owned by `owner`."""
    w = WALKS[walk]
    q = json.dumps
    lines = [f'  - make: {{ by: {by}, at: now, note: "written by bin/intake.py setup: the standard walk" }}',
             f'  - own: {{ id: own, by: {owner}, of: self }}']
    for st, d in w['steps'].items():
        roles = [f'id: {st}', f"as: {q(d['says'])}"]
        if d.get('to'):
            roles.append(f"to: [{', '.join(d['to'])}]")
        marks = {k: ('"true"' if v is True else '[' + ', '.join(v) + ']') for k, v in d.items()
                 if k in ('final', 'exit', 'resumes', 'machine', 'reasons')}
        if marks:
            roles.append('walk: { ' + ', '.join(f'{k}: {v}' for k, v in marks.items()) + ' }')
        lines.append(f"  - step: {{ {', '.join(roles)} }}")
    return (f"---\nbean: {walk}\nkind: procedure\ntitle: {q(w['title'])}\nsummary: {q(w['summary'])}\nstatements:\n"
            + '\n'.join(lines) + f"\n---\n\n{w['body']}\n")


class Refused(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def setup(root, by, owner):
    """Each walk in this garden: written where it has none; where it has one, its steps and reasons checked against
    WALKS. [(path, what was done)]."""
    from core import engine
    out, differ = [], []
    for walk, w in WALKS.items():
        p = os.path.join(root, 'mappings', f'{walk}.md')
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(walk_mapping(walk, by, owner))
            out.append((p, 'written: save it with its journal entry (bin/save.py)'))
            continue
        b = engine._bean(p, walk)
        have = {r.get('id'): r for _i, v, r in b.items if v == 'step'}
        mine = []
        for st, d in w['steps'].items():
            r = have.get(st)
            if r is None:
                mine.append(f'{st}: missing')
                continue
            marks = r.get('walk') or {}
            if list(r.get('to') or []) != d.get('to', []):
                mine.append(f"{st}: leads to {r.get('to')}, the standard to {d.get('to', [])}")
            for k in ('final', 'exit', 'resumes', 'machine'):
                if (str(marks.get(k)) == 'true') != bool(d.get(k)):
                    mine.append(f'{st}: {k}')
            if list(marks.get('reasons') or []) != d.get('reasons', []):
                mine.append(f"{st}: reasons {marks.get('reasons')}, the standard's {d.get('reasons', [])}")
        mine += [f'{st}: a step the standard does not have' for st in have if st not in w['steps']]
        if mine:
            differ.append(f"{p} differs from the standard walk: " + '; '.join(mine))
        else:
            out.append((p, "the garden's walk is the standard's"))
    if differ:
        raise Refused(' | '.join(differ))
    return out


# ------------------------------------------------------------------------------------------------ the moment
def moment(t=None):
    """A moment to the millisecond, local, with its offset."""
    t = time.time() if t is None else t
    s = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t)) + f'.{int(round(t * 1000)) % 1000:03d}'
    z = time.strftime('%z', time.localtime(t))
    return s + z[:-2] + ':' + z[-2:]


def epoch(m):
    try:
        return datetime.datetime.fromisoformat(str(m)).timestamp()
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------------------------------------ the garden's word
def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def origin(url):
    """`<scheme>://<host>[:port]` of a URL, its host in lower case: where its robots rules are."""
    u = urllib.parse.urlsplit(url)
    return f"{u.scheme.lower()}://{(u.netloc or '').lower()}"


def _norm(url):
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((u.scheme.lower(), (u.netloc or '').lower(), u.path or '/', u.query, ''))


class Source:
    """A source as the garden says it: its feeds, where its course on walk-source stands, and what its terms permit the
    reader."""

    def __init__(self, G, F, bid, reader):
        from core import lines
        b = G.beans.get(bid)
        if b is None or b.unread:
            raise Refused(f"no bean {bid} here: a source is a bean, found at its feeds (`be … as: location`)")
        self.id, self.b, self.reader, self.F = bid, b, reader, F
        self.feeds = [str(r['at']) for _i, v, r in b.items if v == 'be' and r.get('as') == 'location'
                      and isinstance(r.get('at'), str) and re.match(r'^https?://', str(r['at']))]
        # where its course on walk-source stands: the step of its last move (bin/act.py reads a course alike)
        course = next((r.get('id') for _i, v, r in b.items if v == 'be' and r.get('at') == 'walk-source'
                       and r.get('as') == 'order' and isinstance(r.get('id'), str)), None)
        self.course, self.step = course, None
        if course:
            names = {course, f'{bid}#{course}', f'self#{course}'}
            moves = [(epoch(m['at']) or 0, i, m['step']) for i, m in lines.moves_of(b) if m.get('course') in names]
            if moves:
                self.step = max(moves)[2]
        self.terms = []                     # [(terms bean, capability roles, its standing, its clause)]
        for tid in sorted(G.beans):
            t = G.beans[tid]
            if t.unread or not any(v == 'about' and bid in [str(x) for x in _listed(r.get('of'))] for _i, v, r in t.items):
                continue
            for _i, v, r in t.items:
                if v == 'can' and str(r.get('by')) == reader:
                    self.terms.append((tid, r, F.in_force(tid, r, standing=True), r.get('clause') or {}))

    def admitted(self):
        if not self.course:
            return False, f"{self.id} has no course on walk-source: nobody listed it as a source"
        if self.step != 'admitted':
            return False, f"{self.id} stands at `{self.step or 'no step'}` on walk-source, not `admitted`"
        return True, f"{self.id} is admitted on walk-source"

    def permits(self, url):
        """(True or False, why, the least seconds between two requests its terms ask, or None)."""
        u = _norm(url)
        cover = []
        for tid, r, standing, clause in self.terms:
            at = r.get('at')
            if at is None:
                if u in {_norm(f) for f in self.feeds}:
                    cover.append((0, tid, r, standing, clause))
            elif isinstance(at, str) and u.startswith(_norm(at)):
                cover.append((len(_norm(at)), tid, r, standing, clause))
        if not cover:
            return False, (f"no terms of {self.id} let {self.reader} read {url}: the intake reads only what a source "
                           f"permits"), None
        top = max(c[0] for c in cover)
        best = [c for c in cover if c[0] == top]
        for _n, tid, r, standing, _clause in best:
            if standing is not True:
                return False, f"{tid}#{r.get('id', '?')} ({r.get('of')!r}) is not permitted, or is forbidden, there", None
        _n, tid, r, _s, clause = best[0]
        return True, f"permitted by {tid}#{r.get('id', '?')} ({r.get('of')!r})", rate(clause)


def rate(clause):
    """The least seconds between two requests a clause asks — its `amount` of `{request}` `within` a length — or None."""
    a, w = clause.get('amount'), clause.get('within')
    if not isinstance(a, dict) or not isinstance(w, dict) or not isinstance(w.get('measure'), dict):
        return None
    if a.get('unit') != '{request}':
        return None
    try:
        import units as dmunits
        secs = dmunits.convert(str(w['measure'].get('count')), str(w['measure'].get('unit')), 's')
        n = float(a.get('count'))
        return float(secs) / n if n > 0 else None
    except Exception:                     # noqa: BLE001 — a window that is no length of time asks for no rate
        return None


# ------------------------------------------------------------------------------------------------ asking politely
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                       # each hop is judged again, by the intake


class Answer:
    def __init__(self, url, status, headers=None, body=b'', error=None):
        self.url, self.status, self.headers, self.body, self.error = url, status, headers or {}, body, error


class Asker:
    """One request at a time, each host asked no sooner than its interval after the last."""

    def __init__(self, agent, every=EVERY, opener=None, clock=time.monotonic, sleep=time.sleep):
        version = '0'
        try:
            from core import read
            version = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml')).get('version') or '0')
        except Exception:                 # noqa: BLE001 — a tree without the core's face names version 0
            pass
        self.ua = f"{TOKEN}/{version} (+{agent})"
        self.every, self.last, self.wait = every, {}, {}
        self.opener = opener or urllib.request.build_opener(_NoRedirect)
        self.clock, self.sleep = clock, sleep
        self.asked = []                   # (origin, the clock when asked, url), for the account

    def interval(self, host, more=None):
        return max([self.every] + [x for x in (self.wait.get(host), more) if x])

    def ask(self, url, headers=None, more=None):
        host = origin(url)
        gap = self.interval(host, more)
        if host in self.last:
            due = self.last[host] + gap
            now = self.clock()
            if now < due:
                self.sleep(due - now)
        req = urllib.request.Request(url, headers=dict(headers or {}, **{'User-Agent': self.ua}))
        self.last[host] = self.clock()
        self.asked.append((host, self.last[host], url))
        try:
            with self.opener.open(req, timeout=TIMEOUT) as r:
                body = r.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    return Answer(url, r.status, dict(r.headers), b'', error=f"longer than {MAX_BYTES} bytes: not read")
                return Answer(url, r.status, dict(r.headers), body)
        except urllib.error.HTTPError as e:
            try:
                body = e.read(MAX_BYTES)
            except Exception:             # noqa: BLE001
                body = b''
            return Answer(url, e.code, dict(e.headers or {}), body)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return Answer(url, None, error=str(getattr(e, 'reason', e)))


def _header(h, name):
    for k, v in h.items():
        if k.lower() == name.lower():
            return v
    return None


def retry_after(h, now=None):
    """Seconds an answer's Retry-After asks (its seconds, or its HTTP date), RETRY where it says none."""
    v = _header(h, 'Retry-After')
    if v is None:
        return RETRY
    v = v.strip()
    if v.isdigit():
        return int(v)
    try:
        when = email.utils.parsedate_to_datetime(v).timestamp()
        return max(0, when - (now or time.time()))
    except (TypeError, ValueError):
        return RETRY


class Robots:
    """Each host's robots rules, read once a run by Python's urllib.robotparser (RFC 9309), asked conditionally."""

    def __init__(self, asker, kept):
        self.asker, self.kept, self.parsed = asker, kept, {}

    def rules(self, url):
        host = origin(url)
        if host in self.parsed:
            return self.parsed[host]
        rp = urllib.robotparser.RobotFileParser()
        k = dict(self.kept.get(host) or {})
        target, hops, a = host + '/robots.txt', 0, None
        while True:
            hdr = {}
            if k.get('etag'):
                hdr['If-None-Match'] = k['etag']
            if k.get('last_modified'):
                hdr['If-Modified-Since'] = k['last_modified']
            a = self.asker.ask(target, hdr)
            if a.status in (301, 302, 303, 307, 308) and _header(a.headers, 'Location') and hops < HOPS:
                target, hops = urllib.parse.urljoin(target, _header(a.headers, 'Location')), hops + 1
                continue
            break
        said = None
        if a.status == 304 and 'body' in k:
            rp.parse(k['body'].splitlines())
            said = 'unchanged'
        elif a.status == 200:
            text = a.body.decode('utf-8', 'replace')
            rp.parse(text.splitlines())
            k = {'etag': _header(a.headers, 'ETag'), 'last_modified': _header(a.headers, 'Last-Modified'), 'body': text}
            said = 'read'
        elif a.status in (401, 403):
            rp.disallow_all, said = True, f'refused ({a.status}): nothing is read'
        elif a.status is not None and 400 <= a.status < 500:
            rp.allow_all, said = True, f'none given ({a.status}): all is allowed'
        else:
            rp.disallow_all, said = True, f"not read ({a.status or a.error}): nothing is read"
        k['status'], k['at'] = a.status, moment()
        self.kept[host] = k
        delay = rp.crawl_delay(TOKEN)
        rr = rp.request_rate(TOKEN)
        if rr and rr.requests:
            delay = max(delay or 0, rr.seconds / rr.requests)
        if delay:
            self.asker.wait[host] = max(self.asker.wait.get(host) or 0, float(delay))
        self.parsed[host] = (rp, said)
        return self.parsed[host]

    def allows(self, url):
        rp, said = self.rules(url)
        if rp.disallow_all:
            return False, f"the robots rules of {origin(url)}: {said}"
        if rp.allow_all:
            return True, f"the robots rules of {origin(url)}: {said}"
        ok = rp.can_fetch(TOKEN, url)
        return ok, f"the robots rules of {origin(url)} {'allow' if ok else 'disallow'} {TOKEN} there"


# ------------------------------------------------------------------------------------------------ the format
TYPES = {'application/rss+xml': 'rss', 'application/atom+xml': 'atom', 'application/feed+json': 'json-feed'}


def format_of(answer):
    """The feed format of an answer: its media type, else its first element or brace; None where it is no feed."""
    t = (_header(answer.headers, 'Content-Type') or '').split(';')[0].strip().lower()
    if t in TYPES:
        return TYPES[t]
    head = answer.body[:4096].decode('utf-8', 'replace').lstrip('﻿ \t\r\n')
    if head.startswith('{'):
        return 'json-feed'
    m = re.search(r'<(?![?!])(?:[A-Za-z_][\w.-]*:)?([A-Za-z_][\w.-]*)', head)
    return {'rss': 'rss', 'feed': 'atom'}.get(m.group(1)) if m else None


def _import_module():
    """bin/import.py, whose name is a word of Python's: loaded by its path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('dmimport', os.path.join(HERE, 'import.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------------------------------------ the intake
class Intake:
    """One run of the intake over a garden, into one store."""

    def __init__(self, root, store, agent, reader='intake', every=EVERY, asker=None):
        from core import engine
        from core.inforce import InForce
        if not agent or not str(agent).strip():
            raise Refused("the intake names its reader honestly: give who reads and how to reach them (`--agent`, or "
                          "DAFTAR_INTAKE_AGENT) — nothing is fetched without it", 2)
        self.root, self.S, self.reader = root, store, reader
        self.G = engine.Garden.read(root)
        if reader not in self.G.beans:
            raise Refused(f"the reader {reader} has no bean here: the terms' capabilities name the being that reads "
                          f"(`--as`), a program of this garden", 2)
        missing = [w for w in WALKS if w not in self.G.beans]
        if missing:
            raise Refused(f"this garden has no {', '.join(missing)}: write the standard walks first "
                          f"(`bin/intake.py setup`), and save them", 2)
        self.F = InForce(root, G=self.G)
        self.asker = asker or Asker(agent, every)
        self.robots = None
        self.log = []

    def source(self, bid):
        return Source(self.G, self.F, bid, self.reader)

    def admitted(self):
        """The beans whose course on walk-source stands at `admitted`."""
        out = []
        for bid in sorted(self.G.beans):
            b = self.G.beans[bid]
            if not b.unread and any(v == 'be' and r.get('at') == 'walk-source' and r.get('as') == 'order'
                                    for _i, v, r in b.items):
                if Source(self.G, self.F, bid, self.reader).step == 'admitted':
                    out.append(bid)
        return out

    def judge(self, src, url, robots=True):
        """(True or False, [why], the terms' interval): may the reader ask for `url` now."""
        whys = []
        ok, why = src.admitted()
        whys.append(why)
        if not ok:
            return False, whys, None
        ok, why, gap = src.permits(url)
        whys.append(why)
        if not ok:
            return False, whys, None
        if robots:
            ok, why = self.robots.allows(url)
            whys.append(why)
            if not ok:
                return False, whys, None
        return True, whys, gap

    def read(self, bid, dry=False):
        """Read each feed of a source into the store. [{feed, status, said, items, new}]."""
        src = self.source(bid)
        detail = (self.S.detail(bid, 'intake') or {}) if self.S is not None else {}
        urls = detail.setdefault('urls', {})
        self.robots = Robots(self.asker, detail.setdefault('robots', {}))
        out = []
        if not src.feeds:
            out.append({'source': bid, 'feed': None, 'said': f"{bid} is found at no feed: `be: {{ at: \"<url>\", as: "
                                                            f"location }}` in the `uri` system"})
        stopped = set()
        for feed in src.feeds:
            row = {'source': bid, 'feed': feed}
            kept = dict(urls.get(feed) or {})
            nb = epoch(kept.get('not_before'))
            if nb and nb > time.time():
                row['said'] = f"not asked before {kept['not_before']}: its host asked to wait"
                out.append(row)
                continue
            if origin(feed) in stopped:
                row['said'] = 'its host asked to wait, this run'
                out.append(row)
                continue
            url, hops, answer = feed, 0, None
            while True:
                ok, whys, gap = self.judge(src, url)
                if not ok:
                    row['said'] = (f"redirected to {url}, not followed: " if hops else '') + '; '.join(whys)
                    if hops:
                        urls[feed] = dict(kept, status=answer.status, at=moment(), url=url)
                    answer = None
                    break
                if dry:
                    row['said'] = 'would be asked: ' + '; '.join(whys[1:])
                    break
                hdr = {}
                if url == feed and kept.get('etag'):
                    hdr['If-None-Match'] = kept['etag']
                if url == feed and kept.get('last_modified'):
                    hdr['If-Modified-Since'] = kept['last_modified']
                answer = self.asker.ask(url, hdr, gap)
                loc = _header(answer.headers, 'Location')
                if answer.status in (301, 302, 303, 307, 308) and loc and hops < HOPS:
                    url, hops = urllib.parse.urljoin(url, loc), hops + 1
                    continue
                break
            if answer is None:
                out.append(row)
                continue
            row['status'] = answer.status
            kept.update({'status': answer.status, 'at': moment(), 'url': answer.url})
            if answer.status == 200:
                kept['etag'] = _header(answer.headers, 'ETag')
                kept['last_modified'] = _header(answer.headers, 'Last-Modified')
                kept['sha256'] = hashlib.sha256(answer.body).hexdigest()
                kept.pop('not_before', None)
                try:
                    row.update(self.keep(src, answer))
                except Exception as e:    # noqa: BLE001 — an answer that is no feed is said, and nothing is written
                    row['said'] = f"not read: {e}"
            elif answer.status == 304:
                row['said'] = 'not modified since it was last read: nothing written'
            elif answer.status in (429, 503):
                wait = retry_after(answer.headers)
                kept['not_before'] = moment(time.time() + wait)
                stopped.add(origin(url))
                row['said'] = f"its host asked to wait ({answer.status}): not asked before {kept['not_before']}"
            elif answer.status in (301, 302, 303, 307, 308):
                row['said'] = f"redirected more than {HOPS} times: not followed"
            else:
                row['said'] = f"answered {answer.status or answer.error}: nothing written"
            urls[feed] = kept
            out.append(row)
        if self.S is not None and not dry:
            with self.S.batch():
                self.S.detail(bid, 'intake', detail)
        return out

    def keep(self, src, answer):
        """An answer read through the crosswalk into the store, known by one `read` of the source; each item new to the
        store placed on walk-intake."""
        from core import formats, readers
        fmt = format_of(answer)
        if fmt is None:
            raise Refused("its answer is no feed this release reads (RSS, Atom, JSON Feed)")
        ext = {'rss': '.rss', 'atom': '.atom', 'json-feed': '.json'}[fmt]
        d = tempfile.mkdtemp(prefix='daftar-intake-')
        path = os.path.join(d, 'answer' + ext)
        try:
            with open(path, 'wb') as fh:
                fh.write(answer.body)
            ids = [r.get('id') for r in readers.feed(formats.read(fmt, path, None)) if r.get('id')]
            new = [i for i in dict.fromkeys(ids) if not self.S.has_being(i)]
            at = moment()
            dmimport = _import_module()
            imp = dmimport.Import(self.root, CROSSWALK, keep='store', store=self.S, fmt=fmt, source_layer='world')
            with self.S.batch():
                imp.source(path, fmt=fmt, act={'from': src.id, 'through': answer.url, 'at': at})
                imp.done()
                host = imp._host()
                if new:
                    made = self.S.put(host, 'make', {'by': host, 'at': moment()})
                    ref = f'{host}#{made}'
                    for i in new:
                        if not self.S.has_being(i):
                            continue          # an item the crosswalk wrote nothing of
                        self.S.put(i, 'be', {'id': 'intake', 'by': i, 'at': 'walk-intake', 'as': 'order',
                                             'note': f'taken in from {src.id}'}, act=ref)
                        for step, when in (('fetched', at), ('extracted', moment())):
                            self.S.put(i, 'move', {'of': i, 'through': f'{i}#intake', 'by': host,
                                                   'at': [when, f'walk-intake#{step}'],
                                                   'why': f'read from {src.id} by the intake'}, act=ref)
            return {'items': len(set(ids)), 'new': len(new), 'format': fmt,
                    'said': f"{len(set(ids))} item(s) read ({fmt}), {len(new)} new to the store"}
        finally:
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)


# ------------------------------------------------------------------------------------------------ the command line
def _arg(argv, flag, default=None):
    vals = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == flag]
    return vals[-1] if vals else default


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    flags = {'--into', '--path', '--agent', '--as', '--every', '--by', '--owner'}
    pos = [a for i, a in enumerate(rest) if not a.startswith('--') and (i == 0 or rest[i - 1] not in flags)]
    try:
        if cmd == 'setup':
            from core import read
            gardener = None
            try:
                gardener = read.document(os.path.join(ROOT, 'GARDEN.md'))[0].get('gardener')
            except Exception:             # noqa: BLE001
                pass
            login = os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'
            for p, said in setup(ROOT, _arg(rest, '--by', login), _arg(rest, '--owner', gardener or login)):
                print(f'intake setup: {os.path.relpath(p, ROOT)}: {said}')
            return 0
        agent = _arg(rest, '--agent', os.environ.get('DAFTAR_INTAKE_AGENT'))
        reader = _arg(rest, '--as', 'intake')
        every = float(_arg(rest, '--every', EVERY))
        if cmd == 'permits':
            if not pos:
                print('intake: permits <source> [<url>]', file=sys.stderr)
                return 2
            it = Intake(ROOT, None, agent or 'permits: nothing is fetched but robots rules', reader, every)
            src = it.source(pos[0])
            it.robots = Robots(it.asker, {})
            urls = pos[1:] or src.feeds
            if not urls:
                print(f"{pos[0]}: found at no feed")
            for u in urls:
                ok, whys, gap = it.judge(src, u, robots=bool(agent))
                print(f"{'READ    ' if ok else 'NOT READ'} {u}")
                for w in whys:
                    print(f"           {w}")
                if ok:
                    host = origin(u)
                    print(f"           at most one request to {host} each {it.asker.interval(host, gap):g} s")
                if not agent:
                    print("           (its robots rules not asked: give --agent to ask them)")
            return 0
        if cmd == 'read':
            import store as dmstore
            into = _arg(rest, '--into', '')
            if not (into.startswith('store:') or _arg(rest, '--path')):
                print('intake: read <source>... --into store:<name>: an intake writes into a store, never git',
                      file=sys.stderr)
                return 2
            S = dmstore.open_store(into.split(':', 1)[1] if into.startswith('store:') else None,
                                   path=_arg(rest, '--path'), root=ROOT)
            try:
                it = Intake(ROOT, S, agent, reader, every)
                sources = it.admitted() if '--all' in rest else pos
                if not sources:
                    print('intake: no source to read' + (' — none stands at `admitted` on walk-source'
                                                         if '--all' in rest else ': name one, or --all'))
                    return 1
                rows = [row for bid in sources for row in it.read(bid, dry='--dry' in rest)]
            finally:
                S.close()
            if '--json' in rest:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            else:
                for row in rows:
                    print(f"{row['source']} {row.get('feed') or ''}: {row.get('said', '')}")
            return 0
    except Refused as e:
        print(f'intake: {e}', file=sys.stderr)
        return e.code
    print(__doc__.strip())
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
