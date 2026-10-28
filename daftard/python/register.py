"""register — an Odoo instance whose records a garden's Odoo pages read live, never mirrored (design §10.2, §15.6).

A garden may keep no copy of some records at all: people who keep no garden, kept in an organisation's own register (its
Odoo), are records about people that git would never forget. For such a garden daftard serves the series' own client as
for any other (its views captured, its session and menus daftard's), but the data calls are asked of the register
itself, on each call, and nothing of what it answers is kept: not in the garden, not on this machine's disk, not in its
log.

WHO MAY READ IT is the garden's own decision, as for any of its beans: the register is a bean of the garden (`bean` in
daftard.json: an instance), and a reader may read the register exactly where the garden's own `may` lets them read that
bean — closed by default; the gardener may; anyone else as a grant `of` it opens it, over the extent it holds. A grant
opens the register whole: which of its records a reader may read is not yet something the law can say (its records are
not beans), so that is the one place `grant_domain` would narrow, and it narrows nothing yet. Every domain is ANDed with
it all the same, so a law that says more needs no second path.

WHAT IS ASKED is an allow-list of read calls, each with its signature, so the domain is found wherever the call carries it
and ANDed with the reader's grants; every field a specification, a domain, an order or a group names is held to the
fields the garden captured of that model (the views the reader is shown, and nothing else of the register); the context
is cut to the reader's language and zone and the few switches a read takes; a write, or any other call, is refused here
and never reaches the register.

HOW: Odoo 19's JSON-2 (`POST /json/2/<model>/<method>`, named arguments), as a read-only account of the register's, its
API key in this machine's state folder (registers/<garden>.key, private to the user), never in git, a page, a log or a
command line. Plain HTTP only to this machine's own loopback; never through a proxy the environment names, and never
after a redirect (the key would go where the redirect says).

BY WHICH ROUTE: a register may be reached by more than one route (daftard.json `register.routes`; internal/register
keeps them and their health): daftard hands each call the routes to try, in order — the healthy ones, then an https
route not known to be healthy as the last resort — and none where no route is healthy. A read goes by the first; one
that fails at the connection — refused, reset, timed out, its TLS failed, never an HTTP answer such as 401, 403 or
404 — is asked once more, of the next route, and the route that failed is not asked again in the same call. Only
reads ever reach a register (READS), so asking one again repeats nothing. A page's reads wait ATTEMPT seconds on a
route at most and BUDGET seconds in all, and where no route is healthy the page is told so at once. What each route
did is noted for daftard (`notes`: which answered, which missed and how), never a record.

WHAT THE REGISTER SAYS WHEN IT REFUSES is never repeated: its words can carry a record's values. The reader is told that
it refused and how (the kind of Odoo's exception), and nothing else is kept.
"""
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import stat
import time
import urllib.error
import urllib.parse
import urllib.request

MODEL = re.compile(r'[a-z][a-z0-9_]*(\.[a-z0-9_]+)*')
FIELD = re.compile(r'[a-z_][a-z0-9_]*')
SERIES = re.compile(r'(\d+)\.\d+')
OPERATORS = {'=', '!=', '<', '<=', '>', '>=', '=?', 'like', 'not like', 'ilike', 'not ilike', '=like', '=ilike', 'in',
             'not in', 'child_of', 'parent_of', 'any', 'not any', 'any!', 'not any!'}
AGGREGATES = {'sum', 'avg', 'max', 'min', 'count', 'count_distinct', 'bool_and', 'bool_or', 'array_agg',
              'array_agg_distinct', 'recordset'}
GRANULARITIES = {'hour', 'day', 'week', 'month', 'quarter', 'year', 'year_number', 'quarter_number', 'month_number',
                 'iso_week_number', 'day_of_year', 'day_of_month', 'day_of_week', 'hour_number', 'minute_number',
                 'second_number'}
TRUE_LEAF, FALSE_LEAF = (1, '=', 1), (0, '=', 1)

# THE READ CALLS a series' client makes, by their names in 19's own signatures: the positional parameters after a
# record method's ids, whether it takes ids, and the keyword parameters it takes beside. Nothing else is asked.
METHODS = {
    'web_search_read': (('domain', 'specification', 'offset', 'limit', 'order', 'count_limit'), False, ()),
    'search_read': (('domain', 'fields', 'offset', 'limit', 'order'), False, ()),
    'search': (('domain', 'offset', 'limit', 'order'), False, ()),
    'search_count': (('domain', 'limit'), False, ()),
    'name_search': (('name', 'domain', 'operator', 'limit'), False, ()),
    'web_name_search': (('name', 'specification', 'domain', 'operator', 'limit'), False, ()),
    'web_read_group': (('domain', 'groupby', 'aggregates', 'limit', 'offset', 'order'), False,
                       ('auto_unfold', 'opening_info', 'unfold_read_specification', 'unfold_read_default_limit',
                        'groupby_read_specification')),
    'formatted_read_group': (('domain', 'groupby', 'aggregates', 'having', 'offset', 'limit', 'order'), False, ()),
    'read_group': (('domain', 'fields', 'groupby', 'offset', 'limit', 'orderby', 'lazy'), False, ()),
    'search_panel_select_range': (('field_name',), False,
                                  ('category_domain', 'comodel_domain', 'enable_counters', 'expand', 'filter_domain',
                                   'hierarchize', 'limit', 'search_domain')),
    'search_panel_select_multi_range': (('field_name',), False,
                                        ('category_domain', 'comodel_domain', 'enable_counters', 'expand',
                                         'filter_domain', 'group_by', 'group_domain', 'limit', 'search_domain')),
    'web_read': (('specification',), True, ()),
    'read': (('fields', 'load'), True, ()),
}
# the switches of a read a context may carry to the register; everything else of it stays here
CONTEXT = {'active_test': bool, 'bin_size': bool, 'read_group_expand': bool, 'formatted_display_name': bool}
# EVERY METHOD THAT EVER REACHES A REGISTER: the client's reads (METHODS, with `search` and `web_read` among them, asked
# for the reader's grants and a ranking's records), and the register's own ranking (`suggest`), a read too.
READS = frozenset(METHODS) | {'suggest'}
ATTEMPT = 14                  # seconds a read waits on one route at most
BUDGET = 30                   # seconds one call's reads wait in all, at most: two attempts, and what is left


class Refused(Exception):
    """A call daftard will not ask of the register, or one the register refused: `message` is safe to show, `status` its
    HTTP status. It never carries the register's own words."""

    def __init__(self, message, status=403):
        super().__init__(message)
        self.status = status


class Unreached(Exception):
    """A route by which the register did not answer at all: `kind` says how (refused, reset, timeout, tls, dns or
    unreachable). An HTTP answer, a refusal included, is never one."""

    def __init__(self, kind):
        super().__init__(kind)
        self.kind = kind


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):        # a redirect is the register's answer, refused as such: never followed
        return None


# no proxy the environment names, no redirect followed, TLS verified against this machine's own authorities
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect(),
                                     urllib.request.HTTPSHandler(context=ssl.create_default_context()))


def settings():
    """The register daftard.json names for this garden, as daftard hands it to the worker (DAFTAR_REGISTER), or None."""
    raw = os.environ.get('DAFTAR_REGISTER') or ''
    try:
        conf = json.loads(raw) if raw else None
    except ValueError:
        return None
    return conf if isinstance(conf, dict) else None


def loopback(host):
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def checked_url(url):
    """A route's address as daftard reads one: https://host[:port], or http:// on this machine's own loopback."""
    url = str(url or '').rstrip('/')
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ('http', 'https') or not u.hostname or u.path not in ('', '/') or u.query or u.fragment \
            or u.username is not None or u.password is not None:
        raise Refused('the register is named by an address daftard cannot read', 500)
    if u.scheme == 'http' and not loopback(u.hostname):
        raise Refused('the register is reached over plain HTTP only on this machine: name it by https', 500)
    return url


class Register:
    """One register, as one call reads it: the routes to it (those daftard handed the call, in the order to try them;
    none handed: its one `url`), its database, the series whose client reads it, the bean that records it in the
    garden, and the file its account's key is in. `notes` gathers what each route did, for daftard."""

    def __init__(self, conf, routes=None, notes=None):
        conf = conf or {}
        self.db = str(conf.get('db') or '')
        self.series = str(conf.get('series') or '')
        self.bean = str(conf.get('bean') or '')
        self.key_file = str(conf.get('key_file') or '')
        given = [{'route': 1, 'url': conf.get('url')}] if routes is None else routes
        if not isinstance(given, list):
            raise Refused('the register is named by an address daftard cannot read', 500)
        self.routes = []
        for r in given:
            n = r.get('route') if isinstance(r, dict) else None
            if not isinstance(n, int) or isinstance(n, bool):
                raise Refused('the register is named by an address daftard cannot read', 500)
            self.routes.append({'route': n, 'url': checked_url(r.get('url'))})
        self.down = set()                 # the routes that did not answer in this call: not asked again in it
        self.notes = notes if notes is not None else []
        self.deadline = time.monotonic() + BUDGET
        m = SERIES.fullmatch(self.series)
        if not m or int(m.group(1)) < 19:
            raise Refused('a register is read through JSON-2, which Odoo has from series 19', 500)
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', self.bean):
            raise Refused('the register names no bean of the garden', 500)

    def key(self):
        """The account's API key, from a file only this user may read; never kept in a page, a log or an error."""
        try:
            st = os.stat(self.key_file)
            if os.name == 'posix' and st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                raise Refused("the register's key file can be read by others than this user: make it 0600", 500)
            with open(self.key_file, encoding='utf-8') as fh:
                key = fh.read().strip()
        except OSError:
            raise Refused("the register's key is not on this machine", 500) from None
        if not key or any(c.isspace() for c in key):
            raise Refused("the register's key file holds no key", 500)
        return key

    def call(self, model, method, ids=None, **kwargs):
        """One read of the register, by JSON-2, by the first route that answers of the two first it was handed: its
        answer, or a Refused that repeats none of the register's words."""
        if not MODEL.fullmatch(model) or not FIELD.fullmatch(method):
            raise Refused('no such call', 404)
        if method not in READS:                          # never so: Reading asks nothing else, and nothing else is sent
            raise Refused(f'daftard asks the register no {method!r}: it reads, and writes nothing', 501)
        body = dict(kwargs)
        if ids is not None:
            body['ids'] = ids
        data, key = json.dumps(body).encode('utf-8'), self.key()
        if not self.routes:
            self.notes.append({'none': True})
            raise Refused('the register cannot be reached now: none of its routes answers (daftard keeps asking them)',
                          503)
        for r in [r for r in self.routes if r['route'] not in self.down][:2]:
            left = self.deadline - time.monotonic()
            if left < 1:
                break
            try:
                got = self.ask(r['url'], model, method, data, key, min(ATTEMPT, left))
            except Refused:                              # it answered, refusing: said so, and never asked again
                self.notes.append({'route': r['route'], 'answered': True})
                raise
            except Unreached as e:
                self.down.add(r['route'])
                self.notes.append({'route': r['route'], 'missed': e.kind})
                # A READ THAT FAILED AT THE CONNECTION IS ASKED ONCE MORE, OF THE NEXT ROUTE. That repeats nothing on
                # the register: every method that reaches one is a read (READS; anything else was refused above).
                assert method in READS, method
                continue
            self.notes.append({'route': r['route'], 'answered': True})
            return got
        raise Refused('the register did not answer by any of its routes', 504)

    def ask(self, url, model, method, data, key, wait):
        """The register's answer by one route, read within `wait` seconds; Unreached where it did not answer at all."""
        req = urllib.request.Request(f'{url}/json/2/{model}/{method}', data, {
            'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'bearer ' + key,
            'X-Odoo-Database': self.db, 'User-Agent': 'daftard'})
        until = time.monotonic() + wait
        try:
            with OPENER.open(req, timeout=wait) as r:
                raw = []
                while True:                               # the whole answer within the wait, however it trickles
                    if time.monotonic() > until:
                        raise TimeoutError('the answer took longer than its wait')
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    raw.append(chunk)
        except urllib.error.HTTPError as e:              # it answered: its refusal said, never asked again
            status = 401 if e.code == 401 else 403 if e.code == 403 else 404 if e.code == 404 else 502
            raise Refused(f'the register refused the call ({refusal_kind(e)})', status) from None
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            raise Unreached(unreached_kind(e)) from None
        try:
            return json.loads(b''.join(raw).decode('utf-8'))
        except ValueError:                               # an answer, but not the register's: not asked again
            raise Refused('the register did not answer', 502) from None


def unreached_kind(e):
    """How a route did not answer, in one word: never the error's own text."""
    e = getattr(e, 'reason', e) if isinstance(e, urllib.error.URLError) else e
    if isinstance(e, (socket.timeout, TimeoutError)) or 'timed out' in str(e).lower():
        return 'timeout'
    if isinstance(e, ConnectionRefusedError):
        return 'refused'
    if isinstance(e, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, http.client.HTTPException)):
        return 'reset'
    if isinstance(e, ssl.SSLError):
        return 'tls'
    if isinstance(e, socket.gaierror):
        return 'dns'
    return 'unreachable'


def refusal_kind(e):
    """What of the register's refusal is said: the kind of Odoo's exception, or the HTTP status. Never its message,
    which can carry a record's values."""
    try:
        got = json.loads(e.read().decode('utf-8', 'replace')) or {}
    except Exception:  # noqa: BLE001 — a refusal with no JSON: its status says it
        got = {}
    return kind_of(got) or str(e.code)


def kind_of(got):
    name = got.get('name') if isinstance(got, dict) else None
    return name if isinstance(name, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{0,80}', name) else ''


class Reading:
    """The register as one reader reads it, for one call: the fields the garden captured (`fields(model)`), and whether
    the reader may read the register at all (`open_`, the garden's own `may` on the register's bean)."""

    def __init__(self, register, fields, open_, lang='en_US', tz=None):
        self.register, self.fields, self.open_ = register, fields, open_
        self.lang = lang if re.fullmatch(r'[a-z]{2,3}(_[A-Z]{2})?(@[a-z]+)?', lang or '') else 'en_US'
        self.tz = tz if isinstance(tz, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z0-9_+-]+)*', tz) else None

    # ---- who may read what
    def grant_domain(self, model):
        """The reader's grants as a domain of `model`: every record where the register is open to them (a grant opens it
        whole); None where it is not, and then nothing is asked."""
        return [] if self.open_ else None

    def anded(self, model, domain):
        """The client's domain ANDed with the reader's grants. Odoo reads a list of domain trees as their conjunction,
        so the grants' trees set before the client's are ANDed with them."""
        g = self.grant_domain(model)
        if g is None:
            raise Refused('the register is not open to you: whoever keeps the garden can open it', 403)
        self.check_domain(model, domain)
        return list(g) + list(domain or [])

    # ---- what may be named
    def allowed(self, model):
        """The fields of `model` a call may name: those the garden captured of it, and its id and display name."""
        return set(self.fields(model) or {}) | {'id', 'display_name'}

    def field(self, model, name):
        if not FIELD.fullmatch(str(name)) or name not in self.allowed(model):
            raise Refused(f'{model}.{name} is not a field the garden\'s views show', 403)
        return (self.fields(model) or {}).get(name) or {}

    def relation(self, model, name):
        desc = self.field(model, name)
        rel = desc.get('relation')
        if desc.get('type') not in ('many2one', 'one2many', 'many2many') or not rel or not MODEL.fullmatch(rel):
            raise Refused(f'{model}.{name} is no relation to follow', 403)
        return rel

    def check_path(self, model, path):
        """A dotted path of fields, each allowed in the model it is read in; the model its last field is a field of."""
        parts = str(path).split('.')
        for p in parts[:-1]:
            model = self.relation(model, p)
        self.field(model, parts[-1])
        return model

    def check_domain(self, model, domain):
        if domain in (None, False):
            return
        if not isinstance(domain, list):
            raise Refused('a domain is a list', 400)
        for t in domain:
            if t in ('&', '|', '!'):
                continue
            if not isinstance(t, (list, tuple)) or len(t) != 3:
                raise Refused('a domain names a leaf daftard does not read', 400)
            if tuple(t) in (TRUE_LEAF, FALSE_LEAF):
                continue
            path, op, value = t
            if op not in OPERATORS:
                raise Refused(f'the operator {op!r}', 400)
            owner = self.check_path(model, path)            # the model the path's last field is a field of
            if op in ('any', 'not any', 'any!', 'not any!'):  # its sub-domain is of the model that field relates to
                self.check_domain(self.relation(owner, str(path).split('.')[-1]), value)

    def check_spec(self, model, spec):
        """A read specification: each field allowed, a relation's own specification held to its model's fields."""
        if not isinstance(spec, dict):
            raise Refused('a specification is a mapping', 400)
        out = {}
        for name, sub in spec.items():
            desc = self.field(model, name)
            sub = sub if isinstance(sub, dict) else {}
            clean = {}
            if 'fields' in sub:
                rel = desc.get('relation') if desc.get('type') in ('many2one', 'one2many', 'many2many') else None
                if not rel:
                    raise Refused(f'{model}.{name} has no fields of its own to read', 400)
                clean['fields'] = self.check_spec(rel, sub['fields'] or {})
            for k in ('limit', 'offset'):
                if isinstance(sub.get(k), int) and not isinstance(sub.get(k), bool):
                    clean[k] = sub[k]
            if isinstance(sub.get('order'), str) and desc.get('relation'):
                self.check_order(desc['relation'], sub['order'])
                clean['order'] = sub['order']
            out[name] = clean
        return out

    def check_fields(self, model, names):
        if names in (None, False):
            return sorted(set(self.fields(model) or {}))       # all, as Odoo reads them: all the garden captured
        if not isinstance(names, list):
            raise Refused('fields are a list', 400)
        for n in names:
            self.field(model, n)
        return names

    def check_order(self, model, order):
        if order in (None, False, ''):
            return
        for term in str(order).split(','):
            words = term.split()
            if not words:
                continue
            head = words[0].split(':')[0]
            if head != '__count':
                self.check_path(model, head)
            rest = [w.lower() for w in words[1:]]
            if not all(w in ('asc', 'desc', 'nulls', 'first', 'last') for w in rest):
                raise Refused('an order daftard does not read', 400)

    def check_groupby(self, model, groupby):
        for spec in ([groupby] if isinstance(groupby, str) else list(groupby or [])):
            path, _, gran = str(spec).partition(':')
            if gran and gran not in GRANULARITIES:
                raise Refused(f'the granularity {gran!r}', 400)
            self.check_path(model, path)

    def check_aggregates(self, model, aggregates):
        for spec in aggregates or []:
            if spec == '__count':
                continue
            name, _, func = str(spec).partition(':')
            if func and func not in AGGREGATES:
                raise Refused(f'the aggregate {func!r}', 400)
            self.field(model, name.split('(')[0])

    def context(self, ctx):
        """The reader's language and zone, and the switches a read takes; nothing else of the client's context."""
        out = {'lang': self.lang}
        if self.tz:
            out['tz'] = self.tz
        for k, kind in CONTEXT.items():
            if isinstance((ctx or {}).get(k), kind):
                out[k] = ctx[k]
        if isinstance((ctx or {}).get('fill_temporal'), (bool, dict)):
            out['fill_temporal'] = bool(ctx['fill_temporal']) if isinstance(ctx['fill_temporal'], bool) else {
                k: v for k, v in ctx['fill_temporal'].items() if k in ('fill_from', 'fill_to', 'min_groups')
                and isinstance(v, (str, int))}
        return out

    # ---- the call
    def call(self, model, method, args, kwargs):
        """One call of the client, asked of the register as the reader may ask it."""
        if method not in METHODS:
            raise Refused(f'daftard asks the register no {method!r}: it reads, and writes nothing', 501)
        if not MODEL.fullmatch(model) or not (self.fields(model) or {}):
            raise Refused(f'{model} is no model the garden captured a view of', 404)
        positional, takes_ids, keywords = METHODS[method]
        args, kw = list(args or []), dict(kwargs or {})
        ctx = self.context(kw.pop('context', None))
        ids = None
        if takes_ids:
            ids = args.pop(0) if args else kw.pop('ids', [])
            ids = [ids] if isinstance(ids, int) and not isinstance(ids, bool) else ids
            if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
                raise Refused('ids are numbers', 400)
        if len(args) > len(positional):
            raise Refused(f'{method} takes {len(positional)} arguments', 400)
        named = dict(zip(positional, args))
        for k, v in kw.items():
            if k not in positional and k not in keywords:
                raise Refused(f'{method} takes no {k!r}', 400)
            if k in named:
                raise Refused(f'{method} was given {k!r} twice', 400)
            named[k] = v
        self.check(model, method, named)
        if takes_ids:                                       # only the records the reader's grants open
            g = self.grant_domain(model)
            if g is None:
                raise Refused('the register is not open to you: whoever keeps the garden can open it', 403)
            if g and ids:
                ids = [i for i in self.register.call(model, 'search', domain=g + [('id', 'in', ids)], context=ctx)
                       if i in ids]
        if method in ('name_search', 'web_name_search') and self.ranks(model, named):
            return self.suggested(model, method, named, ctx)
        if method.startswith('search_panel_'):              # the panel's base domain, ANDed with the reader's grants
            named['search_domain'] = self.anded(model, named.get('search_domain') or [])
        elif not takes_ids:                                  # every other read's domain, so ANDed
            named['domain'] = self.anded(model, named.get('domain') or [])
        if method.startswith('search_panel_'):               # the comodel's values are records the reader may read too
            rel = (self.fields(model) or {}).get(named.get('field_name'), {}).get('relation')
            if rel and MODEL.fullmatch(rel):
                g = self.grant_domain(rel)
                if g:
                    named['comodel_domain'] = g + list(named.get('comodel_domain') or [])
        return self.register.call(model, method, ids, context=ctx, **named)

    # ---- the register's own ranking of what people type (P7.3)
    # A model the register searches the way people type keeps a stored, folded index of what it is searched by
    # (`suggest_index`) and ranks with its own readable scores (its `suggest`: every result says which field and which
    # kind of match found it, no learned ranking). Where the garden captured that index, a many2one's suggestions and the
    # search box's sub-items are the register's own ranking, not a plain `ilike` on the name: a word typed with Arabic
    # letters, without its madda, with a typo or as an older word finds what the register's own pages find. Nothing is
    # ranked here: the register ranks, in its own code, over the records the reader's grants open.
    def ranks(self, model, named):
        return ('suggest_index' in (self.fields(model) or {}) and (named.get('operator') or 'ilike') == 'ilike'
                and isinstance(named.get('name'), str) and named['name'].strip() != '')

    def suggested(self, model, method, named, ctx):
        limit = named.get('limit') if isinstance(named.get('limit'), int) and not isinstance(named.get('limit'), bool) else 100
        got = self.register.call(model, 'suggest', query=named['name'], domain=self.anded(model, named.get('domain') or []),
                                 limit=max(1, min(limit, 100)), context=ctx)
        ids = []
        for r in got if isinstance(got, list) else [None]:
            # each result names its record as Odoo writes a recordset (`model(7,)`): read strictly, of this model only
            m = re.fullmatch(re.escape(model) + r'\((\d+),\)', str(r.get('record') or '')) if isinstance(r, dict) else None
            if not m:
                raise Refused('the register ranked in a shape daftard does not read', 502)
            ids.append(int(m.group(1)))
        if not ids:
            return []
        spec = named.get('specification') if method == 'web_name_search' else {'display_name': {}}
        read = self.register.call(model, 'web_read', ids, specification=spec or {'display_name': {}}, context=ctx)
        by = {x.get('id'): x for x in read if isinstance(x, dict)}
        if method == 'name_search':
            return [[i, by[i].get('display_name')] for i in ids if i in by]
        if set(spec or {}) <= {'display_name'}:          # as 19's web_name_search answers a display name alone
            return [{'id': i, 'display_name': by[i].get('display_name'),
                     '__formatted_display_name': by[i].get('display_name')} for i in ids if i in by]
        return [by[i] for i in ids if i in by]

    def check(self, model, method, named):
        """Every field the call names held to the garden's captures, before anything is asked."""
        for key in ('domain', 'search_domain', 'category_domain', 'filter_domain'):
            if key in named:
                self.check_domain(model, named[key])
        if 'having' in named and named['having']:
            raise Refused('a group read with `having`', 501)
        if 'specification' in named:
            named['specification'] = self.check_spec(model, named['specification'] or {})
        for key in ('unfold_read_specification',):
            if named.get(key):
                named[key] = self.check_spec(model, named[key])
        if named.get('groupby_read_specification'):
            grs = named['groupby_read_specification']
            if not isinstance(grs, dict):
                raise Refused('a groupby read specification is a mapping', 400)
            named['groupby_read_specification'] = {g: self.check_spec(self.relation(model, g), s) for g, s in grs.items()}
        if method in ('read', 'search_read'):              # named or not: Odoo reads every field where none are named
            named['fields'] = self.check_fields(model, named.get('fields'))
        if method == 'read_group':
            self.check_aggregates(model, [f for f in (named.get('fields') or []) if f != '__count'])
        for key in ('order', 'orderby'):
            if key in named:
                self.check_order(model, named[key])
        if 'groupby' in named:
            self.check_groupby(model, named['groupby'])
        if 'aggregates' in named:
            self.check_aggregates(model, named['aggregates'])
        if 'field_name' in named:
            self.field(model, named['field_name'])
        if 'opening_info' in named and named['opening_info'] is not None and not isinstance(named['opening_info'], list):
            raise Refused('opening_info is a list', 400)
        for oi in named.get('opening_info') or []:
            if isinstance(oi, dict) and oi.get('progressbar_domain'):
                self.check_domain(model, oi['progressbar_domain'])
        rel = None
        if 'field_name' in named:
            rel = (self.fields(model) or {}).get(named['field_name'], {}).get('relation')
        if named.get('comodel_domain'):
            if not rel:
                raise Refused('a comodel domain where the field has no comodel', 400)
            self.check_domain(rel, named['comodel_domain'])
        if named.get('group_by'):
            if not rel:
                raise Refused('a group_by where the field has no comodel', 400)
            self.field(rel, named['group_by'])
        if named.get('group_domain'):
            gd = named['group_domain']
            if not isinstance(gd, dict):
                raise Refused('a group_domain is a mapping', 400)
            for d in gd.values():
                self.check_domain(model, d)
        if 'operator' in named and named['operator'] not in OPERATORS:
            raise Refused(f"the operator {named['operator']!r}", 400)
