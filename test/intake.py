#!/usr/bin/env python3
"""intake — a source's feeds read into a store, and only what the source permits (core 4.9; bin/intake.py).

Grows a garden of the core from a release made of this tree (test/grow.py) and serves an invented newsroom on the
loopback (http.server, started here: never the internet). Each check is of what the intake asked and what it kept:

  walks     `setup` writes walk-intake, walk-source and walk-design into the garden's mappings, the gate passes them,
            setup again says they are the standard's, and a walk changed by hand is named where it differs
  honest    nothing is asked without an agent; with one, every request names `daftar-intake/<release> (+<agent>)`
  admitted  a source whose course on walk-source stands anywhere but `admitted` is not asked for anything
  terms     a feed under a capability its terms forbid, or under none, is never asked; `permits` says why
  robots    a path the host's robots rules disallow for `daftar-intake` is never asked, and robots rules that fail (a
            5xx) allow nothing
  rate      two requests to one host are never nearer than the slowest of the floor, the robots rules' delay and the
            terms' rate
  keeps     a feed read into the store, never git: each item a document produced by its site and found at its link,
            known by one `read` of the source; each new item on walk-intake at `fetched`, then `extracted`
  again     a feed asked again carries its ETag and Last-Modified; `304` writes nothing
  redirect  each hop judged again: a hop into what the terms forbid is not followed
  wait      `429` with Retry-After: the feed is not asked again before it

Run: python3 test/intake.py   (0 = green)
"""
import http.server
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()
import grow  # noqa: E402

FAILS = []
PY = sys.executable
T = tempfile.mkdtemp(prefix='intake-')
G = os.path.join(T, 'garden')
AGENT = 'a test of the intake; https://example.org/reader'


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


RSS = '''<?xml version="1.0"?>
<rss version="2.0"><channel><title>The Valley Courier</title><link>https://news.example.org/</link>
<item><title>The mill reopens</title><link>https://news.example.org/2026/10/mill</link>
<guid>urn:courier:mill</guid><pubDate>Tue, 27 Oct 2026 08:30:00 +0100</pubDate><description>Work starts again.</description></item>
<item><title>A bridge is closed</title><link>https://news.example.org/2026/10/bridge</link>
<pubDate>Tue, 27 Oct 2026 09:00:00 +0100</pubDate></item>
</channel></rss>
'''
JSON_FEED = json.dumps({'version': 'https://jsonfeed.org/version/1.1', 'title': 'The Valley Courier',
                        'items': [{'id': 'urn:courier:fair', 'url': 'https://news.example.org/2026/10/fair',
                                   'title': 'The autumn fair', 'date_published': '2026-10-26T10:00:00+01:00'}]})


class Site:
    """An invented newsroom: what it serves, and every request it was sent."""

    def __init__(self, robots, robots_status=200):
        self.robots, self.robots_status, self.seen = robots, robots_status, []
        site = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                site.seen.append((self.path, dict(self.headers), time.monotonic()))
                p = self.path
                if p == '/robots.txt':
                    return self.send(site.robots_status, site.robots, 'text/plain')
                if p == '/feed.rss':
                    if self.headers.get('If-None-Match') == '"v1"':
                        return self.send(304, '', None, {'ETag': '"v1"'})
                    return self.send(200, RSS, 'application/rss+xml',
                                     {'ETag': '"v1"', 'Last-Modified': 'Tue, 27 Oct 2026 08:00:00 GMT'})
                if p == '/feed.json':
                    return self.send(200, JSON_FEED, 'application/json')
                if p == '/moved':
                    return self.send(301, '', None, {'Location': '/members/feed.rss'})
                if p == '/busy':
                    return self.send(429, 'later', 'text/plain', {'Retry-After': '3600'})
                return self.send(200, RSS, 'application/rss+xml')

            def send(self, status, body, ctype, headers=None):
                data = body.encode('utf-8')
                self.send_response(status)
                if ctype:
                    self.send_header('Content-Type', ctype)
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def paths(self):
        return [p for p, _h, _t in self.seen]


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def save(what, body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=G)


def intake(*a, agent=True):
    return grow.run(PY, 'bin/intake.py', *a, *(('--agent', AGENT) if agent else ()), cwd=G)


def source(bid, site, feeds, step, rate_ms=1500):
    """A source bean found at its feeds, its course on walk-source at `step`, and an agreement about it: the reader may
    read the site, one request in `rate_ms`, and never what only members read."""
    moves = []
    for n, s in enumerate(['listed', 'terms-read', 'admitted'][:['listed', 'terms-read', 'admitted'].index(step) + 1]):
        moves.append(f'  - move: {{ id: m{n}, by: sam, of: self, through: source, '
                     f'at: ["2026-10-2{n}T09:00:00+03:00", "walk-source#{s}"] }}')
    write(f'beans/{bid}.md', f'---\nbean: {bid}\nkind: service\ntitle: "{bid} — an invented newsroom\'s feeds"\n'
          'statements:\n  - say: { by: sam, at: now }\n'
          + ''.join(f'  - be: {{ id: feed-{i}, by: self, at: "{site.url}{f}", as: location }}\n'
                    for i, f in enumerate(feeds))
          + '  - be: { id: source, by: self, at: walk-source, as: order }\n' + '\n'.join(moves) + '\n---\nA source.\n')
    write(f'beans/{bid}-terms.md', f'---\nbean: {bid}-terms\nkind: contract\ntitle: "{bid}-terms — what the newsroom '
          'lets a reader do"\nstatements:\n  - say: { by: sam, at: now }\n'
          f'  - about: {{ of: [{bid}] }}\n'
          f'  - can: {{ id: read-site, by: intake, of: "read the site by machine", at: "{site.url}/", clause: '
          f'{{ amount: {{ count: "1", unit: "{{request}}" }}, within: {{ of: time, measure: {{ count: "{rate_ms}", '
          'unit: ms } } } }\n'
          '  - permitted: { of: read-site, through: self }\n'
          f'  - can: {{ id: members, by: intake, of: "read what only members read", at: "{site.url}/members/" }}\n'
          '  - forbidden: { of: members, through: self }\n---\nThe terms, as a person read them.\n')


try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden of the core grows, and carries the intake", r.returncode == 0
          and os.path.isfile(os.path.join(G, 'bin', 'intake.py')), r.out[-600:])

    # ---- the walks
    r = intake('setup', '--by', 'sam', agent=False)
    walks = {w: os.path.isfile(os.path.join(G, 'mappings', f'{w}.md')) for w in ('walk-intake', 'walk-source', 'walk-design')}
    check("walks: setup writes walk-intake, walk-source and walk-design into the garden's mappings",
          r.returncode == 0 and all(walks.values()), (walks, r.out[-800:]))
    r = save('the standard walks of an intake, a source and a design',
             '- action: wrote [[walk-intake]], [[walk-source]], [[walk-design]] by bin/intake.py setup')
    check("walks: the gate passes them, each a procedure of steps", r.returncode == 0, r.out[-1200:])
    src_steps = text('mappings/walk-source.md')
    check("walks: walk-source leads listed → terms-read → admitted, paused resumes, dropped is a way out",
          'id: listed' in src_steps and 'to: [admitted, dropped]' in src_steps and 'resumes: "true"' in src_steps
          and 'id: dropped' in src_steps and 'exit: "true"' in src_steps, src_steps)
    r = intake('setup', agent=False)
    check("walks: setup again says each is the standard's", r.returncode == 0
          and r.out.count("the standard's") == 3, r.out[-600:])
    write('mappings/walk-design.md', text('mappings/walk-design.md').replace('to: [verified, drafted]', 'to: [verified]'))
    r = intake('setup', agent=False)
    check("walks: a walk changed by hand is named where it differs, and nothing is written",
          r.returncode != 0 and 'walk-design' in r.out and 'built: leads to' in r.out, r.out[-600:])
    grow.run('git', 'checkout', '--', 'mappings/walk-design.md', cwd=G)

    # ---- the garden: a host that keeps a store, the reader, three sources on two sites
    site = Site('User-agent: daftar-intake\nDisallow: /private/\nCrawl-delay: 1\n\nUser-agent: *\nDisallow: /\n')
    down = Site('', robots_status=500)
    S = os.path.join(T, 'stores')
    os.makedirs(S)
    me = socket.gethostname().lower().split('.')[0]
    write('beans/nas.md', '---\nbean: nas\nkind: host\ntitle: "nas"\nstatements:\n  - say: { by: sam, at: now }\n'
          f'  - name: {{ by: dns, of: self, as: "{me}.example.org" }}\ndetails:\n  roots:\n    test:\n'
          f'      system: unix-filesystem\n      at: "{me}:{S}"\n  stores:\n    t:\n      at: "root:test/t.sqlite"\n'
          '      form: sqlite\n---\nA host.\n')
    write('beans/intake.md', '---\nbean: intake\nkind: program\ntitle: "intake — the reader of this garden\'s sources"\n'
          'statements:\n  - make: { by: sam, at: now }\n---\nThe reader the terms name.\n')
    write('beans/courier-co.md', '---\nbean: courier-co\nkind: org\ntitle: "courier-co — an invented newsroom"\n'
          'statements:\n  - say: { by: sam, at: now }\n  - name: { by: dns, of: self, as: news.example.org }\n---\nIt.\n')
    source('courier', site, ['/feed.rss', '/members/feed.atom', '/private/feed.rss', '/feed.json'], 'admitted')
    source('gazette', site, ['/gazette.rss'], 'terms-read')
    source('dimmed', down, ['/feed.rss'], 'admitted')
    r = save('a host, the reader, and three sources with their terms',
             '- action: wrote [[nas]], [[intake]], [[courier-co]], [[courier]], [[courier-terms]], [[gazette]], '
             '[[gazette-terms]], [[dimmed]], [[dimmed-terms]]')
    check("the sources, their terms and their courses pass the gate", r.returncode == 0, r.out[-1500:])

    # ---- permits: the terms and the course, said without fetching a feed
    r = intake('permits', 'courier', agent=False)
    lines = r.out
    check("permits: the site's feed is read, permitted by its terms; what only members read is not — forbidden there",
          r.returncode == 0 and f'READ     {site.url}/feed.rss' in lines and f'NOT READ {site.url}/members/feed.atom' in lines
          and 'courier-terms#members' in lines, lines[-1500:])
    check("permits: without an agent, no robots rules are asked, and nothing at all is fetched",
          'robots rules not asked' in lines and site.seen == [], (site.paths(), lines[-400:]))
    r = intake('permits', 'courier', f'http://elsewhere.example/feed.rss', agent=False)
    check("permits: a URL no capability covers is not read — the intake reads only what a source permits",
          'NOT READ' in r.out and 'reads only what a source permits' in r.out, r.out[-600:])
    r = intake('permits', 'gazette', agent=False)
    check("admitted: a source standing at terms-read on walk-source is not read",
          'NOT READ' in r.out and 'not `admitted`' in r.out, r.out[-600:])

    # ---- honest: nothing without an agent
    r = intake('read', 'courier', '--into', 'store:t', agent=False)
    check("honest: no agent, nothing asked — the intake names its reader or fetches nothing",
          r.returncode == 2 and 'agent' in r.out and site.seen == [], (r.out[-400:], site.paths()))

    # ---- the read
    t0 = time.monotonic()
    r = intake('read', 'courier', 'gazette', 'dimmed', '--into', 'store:t', '--json')
    try:
        rows = json.loads(r.stdout)
    except ValueError:
        rows = []
    by = {(x['source'], (x.get('feed') or '').split('/', 3)[-1]): x for x in rows}
    asked = site.paths()
    check("honest: every request names the reader, `daftar-intake/<release> (+<agent>)`",
          site.seen and all(h.get('User-Agent', '').startswith('daftar-intake/') and h['User-Agent'].endswith(f'(+{AGENT})')
                            for _p, h, _t in site.seen), [h.get('User-Agent') for _p, h, _t in site.seen])
    check("robots: the host's robots rules are asked once, first", asked[:1] == ['/robots.txt'] and asked.count('/robots.txt') == 1,
          asked)
    check("terms: what its terms forbid (the members' feed) is never asked; robots: what they disallow for "
          "daftar-intake (/private/) is never asked",
          '/members/feed.atom' not in asked and '/private/feed.rss' not in asked
          and 'forbidden' in by.get(('courier', 'members/feed.atom'), {}).get('said', '')
          and 'disallow' in by.get(('courier', 'private/feed.rss'), {}).get('said', ''), (asked, rows))
    check("admitted: the source at terms-read asked for nothing", '/gazette.rss' not in asked, asked)
    check("robots: robots rules that fail (500) allow nothing — the feed behind them is never asked",
          [p for p, _h, _t in down.seen] == ['/robots.txt'] and 'nothing is read' in by.get(('dimmed', 'feed.rss'), {}).get('said', ''),
          ([p for p, _h, _t in down.seen], rows))
    times = [t for _p, _h, t in site.seen]
    gaps = [b - a for a, b in zip(times, times[1:])]
    check("rate: two requests to one host are never nearer than the slowest asked — here the terms' 1.5 s, beside the "
          "robots rules' 1 s and the floor's 1 s", gaps and min(gaps) >= 1.45, gaps)
    check("keeps: both feeds read, three items, all new to the store",
          by.get(('courier', 'feed.rss'), {}).get('new') == 2 and by.get(('courier', 'feed.json'), {}).get('new') == 1, rows)
    sys.path.insert(0, G)
    os.chdir(G)
    import store as dmstore  # noqa: E402
    st = dmstore.open_store('t', root=G, create=False)
    items = sorted(b for (b,) in st.db.execute("SELECT id FROM being WHERE id LIKE 'i-%'"))
    one = {v: rr for v, rr, _a in st.get(items[0])} if items else {}
    allv = [(v, rr, a) for i in items for v, rr, a in st.get(i)]
    reads = [rr for v, rr, _a in st.get('courier') if v == 'read']
    check("keeps: each item a document produced by the site its link names, found at its link — in the store, never git",
          len(items) == 3 and all(st.kind_of(i) == 'document' for i in items)
          and sum(1 for v, rr, _a in allv if v == 'produce' and rr.get('by') == 'courier-co') == 3
          and sum(1 for v, rr, _a in allv if v == 'be' and rr.get('as') == 'location') == 3, allv)
    check("keeps: known by one `read` of the source a feed, from it, through its URL",
          len(reads) == 2 and all(x.get('from') == 'courier' and str(x.get('through', '')).startswith(site.url) for x in reads),
          reads)
    moves = [(rr.get('at') or [None, None])[1] for v, rr, _a in allv if v == 'move']
    check("keeps: each new item placed on walk-intake, fetched then extracted",
          sum(1 for v, rr, _a in allv if v == 'be' and rr.get('at') == 'walk-intake') == 3
          and moves.count('walk-intake#fetched') == 3 and moves.count('walk-intake#extracted') == 3, moves)
    det = st.detail('courier', 'intake') or {}
    check("keeps: what only the intake needs — each feed's validators, the host's robots rules — is the source's detail",
          det.get('urls', {}).get(f'{site.url}/feed.rss', {}).get('etag') == '"v1"' and site.url in det.get('robots', {}),
          det)
    st.close()
    r = grow.run('git', 'status', '--porcelain', cwd=G)
    check("keeps: nothing written into git", r.stdout.strip() == '', r.out)

    # ---- again: conditional
    n0 = len(site.seen)
    r = intake('read', 'courier', '--into', 'store:t', '--json', '--every', '0.1')
    again = [(p, h) for p, h, _t in site.seen[n0:]]
    rss = [h for p, h in again if p == '/feed.rss']
    check("again: the feed asked again carries its ETag and Last-Modified, and its 304 writes nothing",
          rss and rss[0].get('If-None-Match') == '"v1"' and rss[0].get('If-Modified-Since') == 'Tue, 27 Oct 2026 08:00:00 GMT'
          and 'not modified' in r.out, (again, r.out[-800:]))
    st = dmstore.open_store('t', root=G, create=False)
    check("again: the store holds the same three items", st.db.execute("SELECT COUNT(*) FROM being WHERE id LIKE 'i-%'"
                                                                       ).fetchone()[0] == 3)
    st.close()

    # ---- redirect and wait
    source('wire', site, ['/moved', '/busy'], 'admitted', rate_ms=100)
    r = save('a source that moved and one that is busy', '- action: wrote [[wire]], [[wire-terms]]')
    n0 = len(site.seen)
    r = intake('read', 'wire', '--into', 'store:t', '--json', '--every', '0.1')
    asked = [p for p, _h, _t in site.seen[n0:]]
    check("redirect: each hop judged again — a hop into what the terms forbid is not followed",
          '/moved' in asked and '/members/feed.rss' not in asked and 'forbidden' in r.out, (asked, r.out[-800:]))
    st = dmstore.open_store('t', root=G, create=False)
    busy = (st.detail('wire', 'intake') or {}).get('urls', {}).get(f'{site.url}/busy', {})
    st.close()
    check("wait: 429 with Retry-After — when it may be asked again is kept", busy.get('status') == 429
          and busy.get('not_before'), busy)
    n0 = len(site.seen)
    r = intake('read', 'wire', '--into', 'store:t', '--json', '--every', '0.1')
    check("wait: it is not asked again before then", '/busy' not in [p for p, _h, _t in site.seen[n0:]]
          and 'not asked before' in r.out, r.out[-600:])
    site.httpd.shutdown()
    down.httpd.shutdown()
finally:
    os.chdir(ROOT)
    shutil.rmtree(T, ignore_errors=True)

print(f"\nintake: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
