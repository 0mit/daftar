#!/usr/bin/env python3
"""garden_worker: daftard's hands inside one garden (the MVP's read and write path).

    python garden_worker.py            run in the garden's root; one JSON request per line on stdin, one answer per line
                                       on stdout; what the garden's own code prints goes to stderr (daftard's log)

It answers the handplace's data calls and runs the garden's sync and exchange rounds with THE GARDEN'S OWN CODE
(dashboard/model.py, dashboard/sync.py, exchange/exchange.py, bin/pass.py), so what is read and written is exactly what
that garden's model and gate say: daftard decides nothing about a garden's facts. Until daftard's own index reads
gardens natively (design/DESIGN.md §5), this is how it reads them.

A request: {"id": 7, "method": "payload", "params": {...}}
An answer: {"id": 7, "ok": true, "result": ...}   or   {"id": 7, "ok": false, "error": {"status": 409, "message": "...",
           "diagnostic": "...", "kind": "refused"|"failed"}}

The message is what the person may be shown; the diagnostic is the whole of it (the gate's word, a traceback), which
daftard keeps with the error's reference and shows only to whoever's privileges cover it (design §3, guided errors).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path

ROOT = Path.cwd()
OUT = sys.stdout                       # the protocol's own stream: nothing else may write to it
sys.stdout = sys.stderr                # whatever the garden's code prints goes to daftard's log
# TWO KINDS OF GARDEN. A garden that carries its own handplace code (dashboard/model.py, sync.py, exchange/) is
# read and written through that code. A garden that carries none is served by the BOARD of another tree
# (`DAFTAR_TOOLS`: board/model.py and exchange/), which writes through the served garden's own bin/safe.py, gate and
# bin/save.py, as the board server did. Either way daftard decides nothing about the garden's facts.
#
# AND A GARDEN OF THE CORE ALONE (`core`): one grown from a release of the core, which carries no handplace of its own
# and is served no board — the kind most gardens are. daftard serves it what stands on the core alone: Odoo's client,
# the served pages, forms and passkeys, through the garden's own core/ and bin/. The handplace's own pages (its payload,
# books, calendar, exchange) are not here, and say so.
KIND = os.environ.get('DAFTAR_KIND') or 'dashboard'
TOOLS = Path(os.environ.get('DAFTAR_TOOLS') or ROOT)
if KIND == 'board':
    sys.path[:0] = [str(TOOLS / 'board'), str(TOOLS / 'exchange')]
    import model as board_model        # noqa: E402  the board (board/model.py of the tools' tree)
    BOARD = board_model.Garden(ROOT, os.environ.get('DAFTAR_EXCHANGE_DIR') or None)   # it adds the garden's bin/
    xc, safe, LOCK, Refused = board_model.xc, BOARD.safe, board_model.LOCK, board_model.Refused
elif KIND == 'core':
    import threading
    sys.path[:0] = [str(ROOT / 'bin'), str(ROOT)]
    import safe                        # noqa: E402  the garden's own bin/safe.py: its atomic writes
    LOCK = threading.RLock()

    class xc:                          # noqa: N801  of the exchange's helpers, the one a core garden needs: the save lock
        class Busy(Exception):
            pass

        class SaveLock:
            """The clone's save lock, as bin/save.py takes it (`.git/daftar-save.lock`), taken without waiting."""

            def __init__(self, garden):
                self.path = os.path.join(subprocess.run(['git', '-C', garden, 'rev-parse', '--absolute-git-dir'],
                                                        capture_output=True, text=True).stdout.strip(), 'daftar-save.lock')

            def __enter__(self):
                self.f = open(self.path, 'a+')
                try:
                    if os.name == 'nt':
                        import msvcrt
                        self.f.seek(0)
                        msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    self.f.close()
                    raise xc.Busy()
                return self

            def __exit__(self, *exc):
                try:
                    if os.name == 'nt':
                        import msvcrt
                        self.f.seek(0)
                        msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
                finally:
                    self.f.close()

    class Refused(ValueError):
        """What the garden's own tools, or this worker, would not do: said to the person, with its status."""

        def __init__(self, message, status=400):
            super().__init__(message)
            self.status = status
else:
    sys.path[:0] = [str(ROOT / 'dashboard'), str(ROOT / 'exchange'), str(ROOT / 'bin'), str(ROOT)]
    import model                       # noqa: E402  the garden's own model (dashboard/model.py)

    def _own(name, path):
        """A module of the garden's own, by its path: a garden upgraded to a release of the core holds the release's
        bin/sync.py beside its dashboard/sync.py, and its own model puts bin/ first — by name, `import sync` took the
        release's tool, and every hub step failed ("module 'sync' has no attribute 'Busy'", 2026-10-14)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    sync = _own('dashboard_sync', ROOT / 'dashboard' / 'sync.py')    # the garden's own hub step (dashboard/sync.py)
    xc, safe, LOCK, Refused = model.xc, model.dmsafe, model.LOCK, model.Refused


def git(*args):
    """git in the garden, its output stripped ('' on a failure: what asks says what that means)."""
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                          errors='replace').stdout.strip()


_IDENTITY = {}


def identity():
    """{garden_id, garden, gardener}: the garden's own word of itself (bin/propose.py id)."""
    if KIND == 'board':
        return BOARD.me
    if KIND != 'core':
        return model.garden_identity()
    if not _IDENTITY:
        r = subprocess.run([sys.executable, str(ROOT / 'bin' / 'propose.py'), 'id'], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=60)
        for line in r.stdout.splitlines():
            k, sep, v = line.partition(':')
            if sep and k.strip() in ('garden_id', 'garden', 'gardener'):
                v = v.strip().strip('"')
                _IDENTITY[k.strip()] = None if v.startswith('(') else v      # "(none named in GARDEN.md)"
    return _IDENTITY


def exchange_folder():
    if KIND == 'core':
        return None
    return (os.environ.get('DAFTAR_EXCHANGE_DIR') or None) if KIND == 'board' else model.exchange_dir()


def front(path):
    """A document's front matter, read by the garden's own reader ({} where it cannot be read)."""
    if KIND != 'core':
        return xc.front(path)
    from core import read as core_read
    try:
        return core_read.document(str(path))[0]
    except core_read.Unread:
        return {}


def title_of(bean):
    """A bean as the garden names it: its title, or its id."""
    try:
        return str(front(bean_file(bean) or ROOT / 'beans' / f'{bean}.md').get('title') or bean)
    except Exception:
        return bean


def gardener():
    return identity().get('gardener')


def nowhere(params):
    raise Refused('این بخش در این دفتر نیست.', 404)


def session_info(params):
    """The exchange folder and its last round."""
    if KIND == 'board':
        return {'exchange': BOARD.exchange_status()}
    if KIND == 'core':
        return {'exchange': {'folder': None, 'last': None}}
    folder, last = model.exchange_dir(), None
    if folder:
        try:
            f = Path(folder) / identity()['garden_id'] / 'last.json'
            last = json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
        except Exception:
            last = None
    return {'exchange': {'folder': folder, 'last': last}}


def hello(params):
    ident = identity()
    who = ident.get('gardener')
    return {'garden_id': ident.get('garden_id'), 'garden': ident.get('garden'), 'gardener': who, 'me': title_of(who),
            'head': git('rev-parse', 'HEAD'), 'root': str(ROOT), 'kind': KIND}


def payload(params):
    if KIND == 'core':
        return core_front()
    if KIND == 'board':
        data = BOARD.payload()
        data['kind'] = 'board'
        places = board_model.currency_places(ROOT)
        data['currencies'] = [{'code': u, 'digits': places.get(u, 2)} for u in data.get('units') or []]
        return data
    data = model.payload(bool(params.get('private', True)))       # the model's own flag, passed by position
    # a currency's places, from the garden's own table of currencies, for the money widget (it keeps no copy)
    places = {code: row.get('digits') for code, row in model.currencies().items()}
    for c in data.get('currencies') or []:
        if isinstance(c, dict) and c.get('digits') is None:
            c['digits'] = places.get(c.get('code'))
    return data


BEAN = re.compile(r'[a-z0-9][a-z0-9-]{0,120}')


def core_front():
    """What a garden of the core alone offers on its front page, which it has none of its own (its pages are to be its
    page beans, drawn by the view: V6): the Odoo series whose views it captured, each opened by Odoo's own client, and
    the register it names, read live — never a record."""
    import register
    conf = register.settings() or {}
    series = sorted(odoo_captures())
    reg = None
    if conf.get('series'):
        bean = str(conf.get('bean') or '')
        reg = {'series': str(conf['series']), 'bean': bean, 'title': title_of(bean) if BEAN.fullmatch(bean) else bean,
               'captured': str(conf['series']) in series}
    return {'kind': 'core', 'odoo': series, 'register': reg, 'head': git('rev-parse', 'HEAD'),
            'asOf': time.strftime('%Y-%m-%d'), 'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S')}


def books(params):
    if KIND in ('board', 'core'):
        return nowhere(params)
    return model.books(params.get('from') or None, params.get('to') or None, params.get('unit') or 'TRY')


def history(params):
    if KIND in ('board', 'core'):
        return nowhere(params)
    return model.history(params['ref'])


def calendar(params):
    if KIND in ('board', 'core'):
        return nowhere(params)
    return model.calendar(params['from'], params['to'])


def view_html(params):
    """The view's page, and the scripts its asset wrote into it: daftard lets only those run, by their hashes, never a
    script it finds in the page — a bean's text the page carried unescaped would be one (security audit 2.4). With a
    `page` — a page bean of a garden whose handplace is its page beans (daftard asks with one for no other) — or for a
    garden of the core whose handplace they are, the view's own page of that bean, drawn by the release the garden runs,
    as `view report` draws it, in the garden's language; else what it always was: a dashboard's own, nowhere else."""
    page = str((params or {}).get('page') or '')
    if page or KIND == 'core' and (params or {}).get('handplace') == 'view':
        return view_page_html(page, str((params or {}).get('lang') or ''))
    if KIND in ('board', 'core'):
        return nowhere(params)
    return {'page': model.view_html(), 'scripts': view_scripts()}


def view_page_html(page, lang):
    """The view's whole page of one page bean (its own `build_html`, the scripts its asset declares): what `view report`
    writes, for the gardener, with no held value in it."""
    vm, vr, _vs, ve = _view()
    if page and not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', page):
        raise Refused('این صفحه در این دفتر نیست.', 404)
    with LOCK:
        problems = vm.init(str(ROOT), page or None)
        if problems:
            raise Refused('این صفحه کشیده نمی‌شود: ' + '؛ '.join(map(str, problems))[:300], 404)
        p = vr.payload()
        if lang and isinstance(p.get('engraved'), dict):
            if hasattr(ve, 'localize'):                  # a release that names the law's words in the reader's language
                ve.localize(p['engraved'], lang)
            else:
                p['engraved']['settings']['garden']['lang'] = lang
        return {'page': vr.build_html(p), 'scripts': view_scripts()}


def view_scripts():
    """The scripts the garden's view asset writes into its page, as the asset declares them (`view_report.SCRIPTS`),
    or, in a release before it declared them, its script constants: the asset's code, never a bean's text. A page
    drawn without the view asset runs none."""
    vr = sys.modules.get('view_report')
    if vr is None:
        return []
    declared = getattr(vr, 'SCRIPTS', None)
    if declared is not None:
        return [x for x in declared if isinstance(x, str)]
    kit = sys.modules.get('view_kit') or getattr(vr, 'kit', None)
    found = (getattr(vr, 'DIRECTION_JS', None), getattr(kit, 'RUNTIME_JS', None), getattr(vr, 'SCRIPT', None))
    return [x for x in found if isinstance(x, str)]


# ---------------------------------------------------------------------------------------------------- the view's pages
# A GARDEN WHOSE HANDPLACE IS ITS PAGE BEANS (daftard.json `handplace: "view"`): each page is read,
# scoped to its reader, drawn and written by THE VIEW'S OWN CODE, from the release the garden runs (its own
# assets/view/lib) — the readings (view_engraved), the scoping the view's served page asks (view_serve.Host's own
# `scoped_payload`), and the one write path (view_write). daftard holds the reader's being and its sitting; the garden's
# bin/pass.py says what that being may read and write. Nothing here draws, reads or writes a fact of its own.
def _view():
    """The view's library from the garden's own release, on the path: (view_model, view_report, view_serve,
    view_engraved) — Refused where the garden runs no release that draws pages of readings."""
    lib = ROOT / 'assets' / 'view' / 'lib'
    if not (lib / 'view_engraved.py').is_file():
        raise Refused('صفحه‌های این دفتر هنوز روی نمای نسخه‌ای که دفتر اجرا می‌کند نیستند.', 409)
    for p in (str(lib), str(ROOT / 'bin'), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import view_model, view_report, view_serve, view_engraved
    return view_model, view_report, view_serve, view_engraved


def _view_host(reader, lang, head, prefs=None):
    """The view's own served host (view_serve.Host), for one reader — the being daftard says sits here, the gardener
    where nobody sits — built without its server's configuration: every answer it gives, and every scoping its
    `scoped_payload` and view_engraved's `scoped` ask of it, are its own, read from the garden's bin/pass.py grants.
    No ceiling of a configuration narrows it (`orgs: ['*']`), and none widens it: daftard's reader is a person of the
    garden at its own machine. It may write where a grant opens a being to them, and start a page's action only as a
    walk this machine names for its tool (`view_act`, daftard.json `walks`); a tool's own command it never runs."""
    _vm, vr, vs, _ve = _view()
    import importlib
    dmpass = importlib.import_module('pass')
    h = vs.Host.__new__(vs.Host)
    h.cfg = {'users': {reader: dict({'bean': reader, 'actions': True, 'orgs': ['*'], 'lang': lang or ''},
                                    **{k: str(v) for k, v in (prefs or {}).items() if k in ('locale', 'date', 'currency') and v})}}
    h.head, h.payload = head, vr.payload()
    h.views = {v['key']: v for v in h.payload['views'].values()}
    h.beans, h.gardener = dmpass.beans_here(str(ROOT)), dmpass.gardener_of(str(ROOT))
    h.answers, h.closed_memo = {}, {}
    return h


def _prefs():
    """The garden's own view_prefs (its release's), which reads a reader's tag — Refused where its release has none."""
    _view()
    try:
        import view_prefs
    except ImportError:
        raise Refused('نسخه‌ای که این دفتر اجرا می‌کند هنوز ترجیح خواننده را نمی‌شناسد.', 409)
    return view_prefs


def prefs_check(params):
    """A reader's way of reading, read by the garden's own view (RFC 5646's grammar, CLDR's types): {prefs, reader} as
    kept and as the widgets read them, or Refused with each sentence. Nothing of the garden is written."""
    vp = _prefs()
    kept, bad = vp.check(params.get('prefs') if isinstance(params.get('prefs'), dict) else {})
    if bad:
        raise Refused('؛ '.join(bad), 400)
    return {'prefs': kept, 'reader': vp.settings_of(kept)}


def prefs_zones(params):
    """The zones a reader may read moments in: CLDR's `tz` types, each with the IANA zone it stands for."""
    return [list(z) for z in _prefs().zones()]


def _garden_id():
    """This garden's id (bin/parse.py `garden_id`): the first twelve hex digits of the root of its history."""
    import parse as dmparse
    return dmparse.garden_id(str(ROOT))


def _bean_ready(vp):
    if not (hasattr(vp, 'to_bean') and hasattr(vp, 'from_bean')):
        raise Refused('نسخه‌ای که این دفتر اجرا می‌کند ترجیح خواننده را هنوز به شکل پرونده نمی‌نویسد.', 409)
    return vp


def prefs_bean(params):
    """A reader's way of reading as the garden's own view writes it as a bean (view_prefs.to_bean: a `document` whose
    `draw` of the reader holds the form `reader_preferences`), with this garden's id — to keep, or to carry to another
    machine. {bean}: its text. Nothing of the garden is written."""
    vp = _bean_ready(_prefs())
    try:
        text = vp.to_bean(params.get('prefs') if isinstance(params.get('prefs'), dict) else {},
                          str(params.get('reader') or ''), garden=_garden_id())
    except vp.Refused as e:
        raise Refused(str(e), 400)
    return {'bean': text}


def prefs_from_bean(params):
    """The preferences a bean holds, read back by the garden's own view (view_prefs.from_bean) and checked as a
    reader's choice is: {bean, reader, garden, prefs, here}, `here` this garden's id, for daftard to say whether the
    bean was set in it. Nothing of the garden is written."""
    vp = _bean_ready(_prefs())
    try:
        got = vp.from_bean(str(params.get('text') or ''))
    except vp.Refused as e:
        raise Refused(str(e), 400)
    return dict(got, here=_garden_id())


def view_assets():
    """What the browser loads of the garden's release to draw its pages, as the release itself lists it: the widgets'
    modules in the order they lean on one another (view_widgets.ORDER), the classic scripts — direction.js, the
    renderers in their order (view_report.ENGRAVED_JS), the runtime — and their styles. A release that adds a renderer
    or a widget is served it with no change here."""
    _vm, vr, _vs, _ve = _view()
    import view_widgets
    return {'widgets': [str(x) for x in getattr(view_widgets, 'ORDER', ())],
            'scripts': ['widgets/direction.js'] + [os.path.basename(f) for f in getattr(vr, 'ENGRAVED_JS', [])] + ['view_runtime.js'],
            'styles': ['widgets/widgets.css', 'view_engraved.css']}


def view_pages(params):
    """The garden's page beans, in the order of its handplace (the view's own `handplace()`, where its release has it,
    else by id): {pages: [{bean, title, place}], assets} — what the navigation lists, and what the browser loads."""
    vm = _view()[0]
    with LOCK:
        vm.init(str(ROOT), None)                # binds the garden; with several pages it draws none, and needs none here
        if vm.CORE is None:
            pages = []
        elif hasattr(vm, 'handplace'):
            pages = vm.handplace()
        else:
            pages = [{'bean': p, 'title': str(vm.fm(p).get('title') or p), 'place': None} for p in vm.CORE.pages()]
        return {'pages': pages, 'assets': view_assets()}


def view_page(params):
    """One page bean's payload for its reader, scoped by the view's own code: its drawings (each at every lens), the
    readings engraved for this reader, their sheets, and the widgets' settings in the reader's language."""
    vm, _vr, vs, _ve = _view()
    page, reader, lang = str(params.get('page') or ''), str(params.get('reader') or ''), str(params.get('lang') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', page) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', reader):
        raise Refused('این صفحه در این دفتر نیست.', 404)
    with LOCK:
        problems = vm.init(str(ROOT), page)
        if problems:
            raise Refused('این صفحه کشیده نمی‌شود: ' + '؛ '.join(map(str, problems))[:300], 404)
        h = _view_host(reader, lang, git('rev-parse', 'HEAD'), params.get('prefs') if isinstance(params.get('prefs'), dict) else None)
        if not h.may(reader)[0]:
            raise Refused('این صفحه برای شما باز نیست.', 403)
        p = vs.Host.scoped_payload(h, reader)
    keep = ('page', 'garden', 'release', 'levels', 'units', 'views', 'order', 'engraved', 'palette_css')
    return {k: p[k] for k in keep if k in p}


def view_style(params):
    """The style a page's drawings need beside the release's files: the kit's own (inline in the asset's Python), with
    the garden's palette."""
    vm, _vr, _vs, _ve = _view()
    import view_kit
    page = str(params.get('page') or '')
    with LOCK:
        pal = ''
        if re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', page) and not vm.init(str(ROOT), page):
            pal = vm.palette_css()
        return {'css': view_kit.SCHEMA_CSS + pal}


# ---------------------------------------------------------------------------------------------------- the board
# THE BOARD (daftard's page `/board`): one being or several, the cursor, kept still while the aspect around it turns —
# the view profile's archetype `cursor`, read by THE VIEW'S OWN CODE from the release the garden runs (its own
# assets/view/lib/view_board.py), over the garden's beans and law and every store this host keeps. daftard draws it;
# what is read, and through which aspects, is the release's. Only reading: nothing here writes. Its answers are not
# held (held.go): a store changes without the garden's version moving, so each question is asked here, of the law and
# the beans read once a version and the stores read in a snapshot each time.
_BOARD = {'key': None, 'board': None}


def _board():
    lib = ROOT / 'assets' / 'view' / 'lib'
    if not (lib / 'view_board.py').is_file():
        raise Refused('این دفتر تخته‌ای ندارد: نمای نسخه‌ای که اجرا می‌کند آن را ندارد.', 409)
    for p in (str(lib), str(ROOT / 'bin'), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import view_board
    key = '|'.join([git('rev-parse', 'HEAD')] + [str(os.stat(ROOT / f).st_mtime_ns) if (ROOT / f).exists() else '-'
                                                 for f in ('beans', 'VOCAB.md', 'GARDEN.md')])
    if _BOARD['key'] != key:
        try:
            _BOARD['board'], _BOARD['key'] = view_board.Board(str(ROOT)), key
        except view_board.Refused as e:
            raise Refused(str(e), 409)
    return view_board, _BOARD['board']


def _board_ids(params):
    ids = [str(x) for x in (params.get('cursor') or []) if isinstance(x, str)][:8]
    if not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:._#-]{0,200}', x) for x in ids):
        raise Refused('این نشانی در این دفتر نیست.', 400)
    return ids


def board_aspects(params):
    """The aspects this garden's board turns through (the law's `aspects` of the profiles it takes), the law's
    orientations, and where a blank board may begin."""
    with LOCK:
        return _board()[1].aspects()


def board_lens(params):
    """One aspect through a cursor: groups of neighbours, each before or after the cursor and on one being's side."""
    vb, B = _board()
    aspect = str(params.get('aspect') or '')
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', aspect):
        raise Refused('این نگاه در این دفتر نیست.', 400)
    with LOCK:
        try:
            return B.lens(aspect, _board_ids(params))
        except vb.Refused as e:
            raise Refused(str(e), 404)


def board_being(params):
    """One being's sheet: what the store keeps of it and, where a bean is it, its statements — those only for a reader
    the garden's own grants open the bean to (bin/pass.py may), or its gardener."""
    vb, B = _board()
    ids = _board_ids({'cursor': [params.get('id')]})
    if not ids:
        raise Refused('این نشانی در این دفتر نیست.', 400)
    with LOCK:
        sheet = B.being(ids[0])
    reader = str(params.get('reader') or '')
    if sheet.get('garden') and reader != (B.gardener or '') and not (
            PERSON.fullmatch(reader) and _may(reader, 'read', sheet['garden']['bean']).granted):
        sheet['garden'] = None
    return sheet


def board_find(params):
    """What each being of the cursor holds beneath it whose name has the text."""
    vb, B = _board()
    with LOCK:
        try:
            return B.find(str(params.get('q') or ''), _board_ids(params))
        except vb.Refused as e:
            raise Refused(str(e), 400)


def view_write(params):
    """A sheet's Save, or a drawing's form of a verb: the statements it adds, changes and takes out, written by the
    view's one write path (view_write.write) as the reader's being — each through bin/safe.py, judged by the gate, one
    commit with one journal entry, signed where the reader sits with their own key. A refusal keeps nothing."""
    _view()
    import importlib
    import view_write as vw
    body = params.get('body') if isinstance(params.get('body'), dict) else {}
    reader = str(params.get('reader') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', reader):
        raise Refused('چه کسی می‌نویسد؟', 403)
    dmpass = importlib.import_module('pass')

    def may(act, b, positions=None):
        return dmpass.may(reader, act, b, positions=positions, root=str(ROOT)).granted
    ops, bean, kind = body.get('ops'), body.get('bean') or None, body.get('kind') or None
    if bean is not None and not (isinstance(bean, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', bean)):
        raise Refused('این مورد در این دفتر نیست.', 404)
    if kind is not None and not (isinstance(kind, str) and re.fullmatch(r'[a-z][a-z0-9-]{0,40}', kind)):
        raise Refused('چنین گونه‌ای در قانون نیست.', 400)
    with LOCK, signed(params.get('sign')):
        name, email = author()                  # the sitting's person, once its environment is the request's
        ident = {'GIT_AUTHOR_NAME': name, 'GIT_AUTHOR_EMAIL': email, 'GIT_COMMITTER_NAME': name, 'GIT_COMMITTER_EMAIL': email}
        before = {k: os.environ.get(k) for k in ident}
        os.environ.update(ident)
        try:
            r = vw.write(str(ROOT), reader, None if kind else bean, ops, kind=kind, may=may)
        finally:
            for k, v in before.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    return {k: x for k, x in r.items() if k != 'output' or not r.get('ok')}


def view_act(params):
    """A page's action, or a person's decision on the plan of a run it started — by the view's own host (its release's
    `Host.start`, `Host.decide`), for the person reading: the walk a page's action starts is one this machine names for
    the action's tool (daftard.json `walks`), run by the garden's own bin/act.py as the reader's being — the law asked
    whether they may — and signed where they sit; each attempt audited in daftard's own record of the garden, never in
    git. {status, answer}: the plan to ratify, or why nothing ran."""
    vm, _vr, _vs, _ve = _view()
    import threading
    body = params.get('body') if isinstance(params.get('body'), dict) else {}
    reader, page = str(params.get('reader') or ''), str(body.get('page') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', reader):
        raise Refused('چه کسی؟', 403)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,120}', page):
        raise Refused('این صفحه در این دفتر نیست.', 404)
    walks = params.get('walks') if isinstance(params.get('walks'), dict) else {}
    with LOCK, signed(params.get('sign')):
        if vm.init(str(ROOT), page):
            raise Refused('این صفحه کشیده نمی‌شود.', 404)
        h = _view_host(reader, str(params.get('lang') or ''), git('rev-parse', 'HEAD'))
        if not hasattr(h, 'start'):
            raise Refused('نسخه‌ای که این دفتر اجرا می‌کند هنوز کاری را از صفحه آغاز نمی‌کند.', 409)
        h.cfg['tools'] = {str(k): {'walk': str(v)} for k, v in walks.items() if isinstance(v, str)}
        h.cfg['audit_log'] = str(params.get('audit') or os.devnull)
        h.wlock, h.refresh = threading.Lock(), (lambda *a, **k: None)   # one run at a time: the worker's own LOCK holds
        name, email = author()                  # the sitting's person, once its environment is the request's
        ident = {'GIT_AUTHOR_NAME': name, 'GIT_AUTHOR_EMAIL': email, 'GIT_COMMITTER_NAME': name, 'GIT_COMMITTER_EMAIL': email}
        before = {k: os.environ.get(k) for k in ident}
        os.environ.update(ident)
        try:
            if body.get('do') in ('ratify', 'decline'):
                code, ans = h.decide(reader, str(body.get('bean') or ''), str(body.get('course') or ''), body['do'])
            else:
                ins = body.get('inputs') if isinstance(body.get('inputs'), dict) else {}
                code, ans = h.start(reader, str(body.get('m') or ''), str(body.get('el') or ''), str(body.get('tool') or ''),
                                    str(body.get('bean') or ''), inputs=ins,
                                    reason=str(body['reason']) if body.get('reason') else None)
        finally:
            for k, v in before.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    return {'status': code, 'answer': ans}


def save(params):
    if KIND == 'core':
        return nowhere(params)
    return (BOARD if KIND == 'board' else model).save(params['body'])


def sync_step(params):
    """One step with the hub, under the model's lock, as the dashboard's syncer took it. A board's garden — a garden of
    the core — keeps in step with its peers by its own bin/sync.py (core_sync)."""
    if KIND in ('board', 'core'):        # `by`: the host bean the machine merges as, signed with its key (`sign`)
        by = str((params or {}).get('by') or '')
        with LOCK:
            return core_sync(by=by if re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', by) else None)
    try:
        with model.LOCK:
            return sync.step()
    except sync.Busy:
        return {'state': 'busy'}


SYNC_LINE = re.compile(r'sync: ([^:]+): (.*)')


def core_sync(by=None):
    """EVERY MACHINE OF A GARDEN IS A PEER (design §7.1): the garden's own bin/sync.py fetches each peer into quarantine,
    judges every commit it brings by the hub's rules and merges what passes. A merge commit is someone's, signed: `by`
    is whose — the host bean the machine is, for a merge with no conflict (class I, design §6.5: signed with the
    machine's own key), or the person at a sitting (sync_merge). With nobody to make it (`by` None) the step takes
    fast-forwards only (`--ff-only`), and where both sides moved says `diverged` and waits. A merge that stops on a
    conflict is a person's to settle (class J). A garden whose release carries no sync tool, or that has no peer, is
    off."""
    tool = ROOT / 'bin' / 'sync.py'
    if not tool.exists() or not git('remote'):
        return {'state': 'off'}
    before = git('rev-parse', 'HEAD')
    try:
        r = subprocess.run([sys.executable, str(tool)] + (['--by', by] if by else ['--ff-only']), cwd=ROOT,
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    except subprocess.TimeoutExpired:
        return {'state': 'error', 'why': 'the sync did not finish within ten minutes'}
    said = (r.stdout + r.stderr).strip()
    peers = {m.group(1): m.group(2) for m in (SYNC_LINE.match(ln) for ln in said.splitlines()) if m}
    after = git('rev-parse', 'HEAD')
    pulled = int(git('rev-list', '--count', f'{before}..{after}') or 0) if after != before else 0
    out = {'pulled': pulled, 'pushed': 0, 'peers': peers,
           'restart': bool(pulled and git('diff', '--name-only', before, after, '--', 'bin', 'core'))}
    if 'a save holds this clone' in said:
        out.update(state='busy', why='a save is running; the next step tries again')
    elif 'changes not yet saved' in said:
        out.update(state='dirty', why='a change no commit has yet; the next step tries again')
    elif any(v.startswith('REFUSED') for v in peers.values()):
        out.update(state='refused', why=said[-600:])
    elif any(v.startswith('diverged') or 'stops on a conflict' in v for v in peers.values()):
        out.update(state='diverged', why=said[-600:])
    elif r.returncode != 0:
        out.update(state='error', why=said[-600:])
    else:
        out['state'] = ('merged' if by else 'pulled') if pulled else 'current'
    out['pushed'] = sum(1 for ln in said.splitlines() if ln.endswith(': pushed'))
    return out


def sync_merge(params):
    """A person at a sitting merges what the peers brought where both sides moved: the merge commit is theirs, saved
    through the gate with its entry and signed in their sitting (`sign`, applied by the dispatcher)."""
    who = str(params.get('who') or '')
    if KIND not in ('board', 'core'):
        raise Refused('این دفتر با ابزار خودش همگام می‌شود.', 404)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', who):
        raise Refused('ادغام کار یک نفر است که پشت این دفتر نشسته باشد.', 403)
    with LOCK:
        return core_sync(by=who)


def exchange_round(params):
    """One round of the exchange with the other gardens, where the gardener has consented; what it commits goes to the
    hub at once, where there is one."""
    folder = exchange_folder()
    if not folder:
        return {'state': 'off'}
    with LOCK:
        done = xc.run(str(ROOT), folder)
    if KIND != 'board' and (done.get('taken') or done.get('sent')):
        with model.LOCK:
            done['hub'] = sync.step()
    return done


def follow_up(params):
    """Whom a person follows a refusal up with: the gardener, and whoever holds a grant that would open the act
    (bin/pass.py may: closed by default, every grant read with its holder). Read, never written."""
    import importlib
    dmpass = importlib.import_module('pass')    # bin/pass.py: `pass` is a keyword, so it is imported by name
    who = dmpass.gardener_of(str(ROOT))
    out = [{'who': who, 'why': 'gardener'}]
    actor, act, bean = params.get('actor'), params.get('act') or 'write', params.get('bean')
    if actor and bean:
        try:
            answer = dmpass.may(actor, act, bean, root=str(ROOT))
            for holder, key in answer[2]:
                if holder and holder not in [o['who'] for o in out]:
                    out.append({'who': holder, 'why': 'grant ' + str(key)})
        except Exception:
            pass
    for o in out:                      # each named as the garden names them (the person bean's title)
        o['title'] = title_of(o['who'])
    return out


# ------------------------------------------------------------------------------------ what waits for the person
# THE LANDING PAGE (/go/<garden>/<kind>/<id>) is where a notification, a link or any platform's own lead brings a person
# to decide something only a person may (MODEL.md, Contract of Parts). The address only NAMES the case; everything
# shown is read here, from the garden, so an address cannot put words in the garden's mouth. A decision is the
# gardener's own save, made through the garden's own tools: its lock, bin/save.py, its gate, its journal.
PENDING = ROOT / 'log' / 'pending.md'
SLUG = re.compile(r'[a-z0-9][a-z0-9-]{0,120}')
NEED = re.compile(r'[A-Za-z0-9][A-Za-z0-9-]{0,120}')
NEED_LEAD = re.compile(r'([a-z0-9][a-z0-9-]{0,120})\.([A-Za-z0-9][A-Za-z0-9-]{0,120})')
PROPOSAL =re.compile(r'PROPOSAL-[A-Za-z0-9][A-Za-z0-9-]{0,120}')
FIELD = re.compile(r'- ([A-Za-z_]+):[ \t]?(.*)')
HEAD = re.compile(r'proposed (\S+) by (.+)')
BUSY = 'تغییر دیگری در دفتر در حال ذخیره شدن است؛ چند لحظهٔ دیگر دوباره تلاش کنید.'
STALE = 'این مورد از وقتی صفحه باز شد تغییر کرده است. صفحه را تازه کنید و دوباره بخوانید.'
# what the person writes is one line of plain text: no control characters, no bidi controls (TEXT.md)
UNSAFE = re.compile('[\x00-\x1f\x7f-\x9f\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]')


def pending_entries():
    """Each entry of log/pending.md, in order: {slug, what, since, by, fields, status, digest, start, end}, its lines
    [start, end). The queue's own example of an entry, inside a fence, is not one."""
    if not PENDING.exists():
        return []
    lines = PENDING.read_text(encoding='utf-8').splitlines(keepends=True)
    out, fence = [], False
    for i, line in enumerate(lines):
        if line.startswith('```'):
            fence = not fence
            continue
        if not fence and line.startswith('## '):
            if out:
                out[-1]['end'] = i
            parts = [x.strip() for x in line[3:].split(' · ')]
            m = HEAD.fullmatch(parts[-1]) if len(parts) > 2 else None
            out.append({'slug': parts[0], 'what': parts[1] if len(parts) > 1 else '', 'since': m.group(1) if m else '',
                        'by': m.group(2) if m else '', 'start': i, 'end': len(lines)})
    for e in out:
        body, fields, last, fence = lines[e['start']:e['end']], {}, None, False
        for line in body[1:]:
            if line.startswith('```'):
                fence = not fence
            m = None if fence else FIELD.match(line)
            if m:
                last = m.group(1)
                fields[last] = m.group(2).rstrip()
            elif last and line.strip() and not line.startswith('---'):
                fields[last] += '\n' + line.rstrip()
        e['fields'] = fields
        e['status'] = (fields.get('status') or '').split('#')[0].strip().split(' ')[0]
        e['digest'] = hashlib.sha256(''.join(body).encode('utf-8')).hexdigest()
    return out






def exchange_state():
    """(folder of this garden's proposals, the last round) or (None, None) where it exchanges with no garden."""
    root = exchange_folder()
    if not root:
        return None, None
    d = Path(root) / identity()['garden_id']
    try:
        last = json.loads((d / 'last.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        last = {}
    return d, last


def waiting_needs():
    """WHAT WAITS IS A NEED (core 3.7): each need not met on the bean it concerns, as the garden's own release reads it
    (bin/waiting.py --json, the one reader of what waits): [{about, need, what, whose, for, class, strength, blocked_by,
    title}]. A garden of a core before 3.7 carries no bin/waiting.py: what waits there is log/pending.md's entries
    alone (None). A reading that fails is said in daftard's log, and shows nothing rather than something wrong."""
    tool = ROOT / 'bin' / 'waiting.py'
    if not tool.is_file():
        return None
    r = subprocess.run([sys.executable, str(tool), '--json'], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120)
    try:
        got = json.loads(r.stdout) if r.returncode == 0 else None
    except ValueError:
        got = None
    if not isinstance(got, list):
        print('waiting: bin/waiting.py --json read nothing: ' + (r.stdout + r.stderr).strip()[-300:], file=sys.stderr)
        return []
    return [x for x in got if isinstance(x, dict) and SLUG.fullmatch(str(x.get('about', '')))
            and NEED.fullmatch(str(x.get('need', '')))]


def leads(params):
    """What waits for the person, each with what its landing page is called: the needs not met (core 3.7), and the
    decisions still parked in log/pending.md (all of them, before 3.7; after it, those no move has made needs yet),
    proposals from another garden that no standing consent covers, and those the exchange set aside."""
    out = []
    for e in pending_entries():
        if e['status'] == 'proposed' and SLUG.fullmatch(e['slug']):
            out.append({'kind': 'pending', 'id': e['slug'], 'title': e['what'], 'class': e['fields'].get('class', ''),
                        'since': e['since'], 'by': e['by']})
    for x in waiting_needs() or []:     # a need's landing is `<bean>.<need>`: the address names it, the page reads it
        out.append({'kind': 'pending', 'id': f"{x['about']}.{x['need']}", 'title': str(x.get('what') or ''),
                    'class': str(x.get('class') or ''), 'since': '', 'by': '', 'about': x['about'],
                    'for': ', '.join(str(p) for p in x.get('for') or []), 'strength': str(x.get('strength') or ''),
                    'blocked_by': [str(b) for b in x.get('blocked_by') or []]})
    d, last = exchange_state()
    if d:
        waiting = {w.split(':', 1)[0] for w in (last or {}).get('waiting') or []}
        for where in ('inbox', 'held'):
            for f in sorted((d / where).glob('PROPOSAL-*.md')):
                if where == 'inbox' and f.name not in waiting:
                    continue                    # a standing consent covers it: the next round takes it
                e = xc.envelope(f)
                out.append({'kind': 'proposal', 'id': f.stem, 'where': where, 'from': e['name'] or e['from'],
                            'under': e['under'], 'beans': e['beans'],
                            'since': time.strftime('%Y-%m-%d', time.localtime(f.stat().st_mtime))})
    out += release_leads()
    out += form_leads()
    out += passkey_leads()
    return out


def release_leads():
    """What the garden's own release reads as waiting, and for whom (bin/leads.py, where its release has it): a case at
    a step, an open session. Its decisions are the needs (waiting_needs) and the queue's entries this worker reads
    already, so they are not taken twice. Each keeps whose it is (`for`), read from the garden, never configured."""
    tool = ROOT / 'bin' / 'leads.py'
    if not tool.is_file():
        return []
    r = subprocess.run([sys.executable, str(tool), '--json'], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120)
    try:
        got = json.loads(r.stdout) if r.returncode == 0 else []
    except ValueError:
        return []
    out = []
    for x in got:
        if not isinstance(x, dict) or x.get('kind') not in ('case', 'session', 'health', 'obligation') \
                or not SLUG.fullmatch(str(x.get('about', ''))):
            continue
        kind, lid = x['kind'], x.get('about', '')
        if kind in ('health', 'obligation'):        # a failure a reading shows; a clause falling due: the bean is the case
            out.append({'kind': kind, 'id': lid, 'title': x.get('why', ''), 'for': x.get('for', ''),
                        'since': str(x.get('since') or x.get('due') or '')})
            continue
        if kind == 'case' and x.get('step') == 'ratify' and SLUG.fullmatch(str(x.get('course', ''))):
            kind, lid = 'action', f"{x['about']}.{x['course']}"     # an action's plan waits to be ratified (bin/act.py)
        out.append({'kind': kind, 'id': lid, 'title': x.get('why', ''), 'for': x.get('for', ''), 'since': x.get('since') or ''})
    return out


# ------------------------------------------------------------------------------------ served: beyond this machine
# A SERVED PAGE IS ASKED OF `may` BEFORE EACH ONE (design §10.1, flow row `served`): the person signed in reads a bean
# only where the garden's own grants open it to them (bin/pass.py may: closed by default), and their own leads only.
# Nothing here is configured: who may read what is the garden's word.
PERSON = re.compile(r'[a-z0-9][a-z0-9-]{0,63}')


def _may(person, act, bean):
    import importlib
    if str(ROOT / 'bin') not in sys.path:
        sys.path.insert(0, str(ROOT / 'bin'))
    dmpass = importlib.import_module('pass')    # bin/pass.py: `pass` is a keyword, so it is imported by name
    return dmpass.may(person, act, bean, root=str(ROOT))


def served_person(params):
    """{mail, granted}: where a sign-in link to the person goes — the mail their own bean names — and whether any grant
    of the garden names them at all; a person no grant names is sent nothing (and the page says the same either way)."""
    person = str(params.get('id') or '')
    if not PERSON.fullmatch(person):
        return {'mail': '', 'granted': False}
    try:
        who = globals()['person']({'id': person})
    except Refused:
        return {'mail': '', 'granted': False}
    import importlib
    if str(ROOT / 'bin') not in sys.path:
        sys.path.insert(0, str(ROOT / 'bin'))
    dmpass = importlib.import_module('pass')
    granted = any(v == 'grant' and person in (r.get('to') if isinstance(r.get('to'), list) else [r.get('to')])
                  for fm in dmpass.beans_here(str(ROOT)).values() for _i, v, r in dmpass.statements(fm))
    return {'mail': who.get('mail') or '', 'granted': granted}


def served_read(params):
    """A bean as the garden's parser reads it, for the person signed in, where a grant opens it to them: {id, title,
    kind, statements}; refused (403) where none does — and the same refusal for a bean that is not there, so a page
    tells nobody what is kept."""
    person, bean = str(params.get('person') or ''), str(params.get('id') or '')
    nope = Refused('این را کسی برای شما باز نکرده است.', 403)
    if not PERSON.fullmatch(person) or not SLUG.fullmatch(bean):
        raise nope
    path = bean_file(bean)                 # a mapping, as a bean of beans/
    if path is None or not _may(person, 'read', bean).granted:
        raise nope
    parse = _garden_parse()
    fm = parse.loads(parse.split_front_matter(path.read_text(encoding='utf-8'))[0]) or {}
    return {'id': bean, 'title': str(fm.get('title') or bean), 'kind': str(fm.get('kind') or ''),
            'statements': fm.get('statements') or []}


def served_leads(params):
    """The leads that are the signed-in person's own, as the garden's release reads them (bin/leads.py --for): a decision
    a grant gives them, a case at their step, an obligation that binds them — and nothing of anyone else's."""
    person = str(params.get('person') or '')
    if not PERSON.fullmatch(person):
        raise Refused('این را کسی برای شما باز نکرده است.', 403)
    tool = ROOT / 'bin' / 'leads.py'
    if not tool.is_file():
        return []
    r = subprocess.run([sys.executable, str(tool), '--for', person, '--json'], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120)
    try:
        got = json.loads(r.stdout) if r.returncode == 0 else []
    except ValueError:
        return []
    return [{'kind': str(x.get('kind') or ''), 'about': str(x.get('about') or ''), 'title': str(x.get('why') or ''),
             'since': str(x.get('since') or ''), 'overdue': bool(x.get('overdue'))}
            for x in got if isinstance(x, dict) and x.get('for') == person]


# A FORM FOR SOMEONE WITHOUT A GARDEN (design §10.5): a bean of the garden whose text asks numbered questions, opened
# to a person by a `grant … as: write` of it (for an extent, its `at`). What they answer on the served page is their
# own words, never written into the garden by the page: it is laid outside the garden, in the garden's mailbox, and
# waits as a lead for the gardener, whose save takes it (class D: a person's word is theirs; the save is the
# ratification). The page shows them the questions and what they gave before; never the garden.
QUESTION = re.compile(r'^\s*(\d{1,3})[.)]\s+(\S.*)$')
TEXT_UNSAFE = re.compile('[\x00-\x09\x0b-\x1f\x7f-\x9f\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]')
FORM_FILE = re.compile(r'([a-z0-9][a-z0-9-]{0,120})\.([a-z0-9][a-z0-9-]{0,63})\.(\d{8}T\d{6})')


def mailboxes():
    """Where this machine keeps its gardens' mailboxes, outside every garden — as bin/mailbox.py's boxes()."""
    if os.environ.get('DAFTAR_MAILBOX'):
        return Path(os.environ['DAFTAR_MAILBOX'])
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'daftar' / 'mailbox'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share') / 'daftar' / 'mailbox'


def forms_box():
    return mailboxes() / str(identity().get('garden_id') or 'unknown') / 'forms'


def questions_of(bean):
    """The numbered questions a form's text asks, in order: its body as the garden's own parser splits it, so a rule
    (`---`) in the text is text, not a fence."""
    body = _garden_parse().split_front_matter((ROOT / 'beans' / f'{bean}.md').read_text(encoding='utf-8'))[1]
    return [m.group(2).strip() for m in (QUESTION.match(ln) for ln in body.splitlines()) if m]


def forms_for(person):
    """The forms open to the person now: beans a `grant … as: write` names them for, which `may` grants at this moment."""
    import importlib
    if str(ROOT / 'bin') not in sys.path:
        sys.path.insert(0, str(ROOT / 'bin'))
    dmpass = importlib.import_module('pass')
    beans = dmpass.beans_here(str(ROOT))
    out = []
    for fm in beans.values():
        for _i, v, r in dmpass.statements(fm):
            to = r.get('to') if isinstance(r.get('to'), list) else [r.get('to')]
            of = r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]
            if v == 'grant' and r.get('as') == 'write' and person in to:
                out += [str(b) for b in of if str(b) in beans and str(b) not in out]
    today = time.strftime('%Y-%m-%d', time.localtime())          # a grant's extent is read by the day
    return [b for b in out if dmpass.may(person, 'write', b, at=today, root=str(ROOT)).granted and questions_of(b)]


def laid(person=None, form=None):
    """The answers laid in the forms box and not yet taken: [(path, form, person, stamp)], newest first."""
    box = forms_box()
    out = []
    for f in sorted(box.glob('*.md'), reverse=True) if box.is_dir() else []:
        m = FORM_FILE.fullmatch(f.stem)
        if m and (person is None or m.group(2) == person) and (form is None or m.group(1) == form):
            out.append((f, m.group(1), m.group(2), m.group(3)))
    return out


def served_forms(params):
    """The forms open to the signed-in person, each with its questions and what they gave last, if it still waits."""
    person = str(params.get('person') or '')
    if not PERSON.fullmatch(person):
        raise Refused('این را کسی برای شما باز نکرده است.', 403)
    out = []
    for b in forms_for(person):
        last = laid(person, b)
        given = head_of(last[0][0]) if last else None
        out.append({'id': b, 'title': title_of(b), 'questions': questions_of(b),
                    'given': (given or {}).get('answers'), 'at': (given or {}).get('at')})
    return out


def served_submit(params):
    """What the person answers to a form open to them, laid outside the garden for the gardener to take: their words as
    they wrote them, the moment (by this machine's disciplined clock) and the page they came through."""
    person, form = str(params.get('person') or ''), str(params.get('id') or '')
    nope = Refused('این را کسی برای شما باز نکرده است.', 403)
    if not PERSON.fullmatch(person) or not SLUG.fullmatch(form) or form not in forms_for(person):
        raise nope
    qs, answers = questions_of(form), params.get('answers')
    if not isinstance(answers, list) or len(answers) != len(qs) or not all(isinstance(a, str) for a in answers):
        raise Refused('به هر پرسش یک پاسخ — خالی هم می‌شود — بدهید.', 400)
    answers = [a.replace('\r\n', '\n').strip() for a in answers]
    if any(TEXT_UNSAFE.search(a) or len(a) > 4000 for a in answers):
        raise Refused('پاسخی نویسه‌ای دارد که در دفتر نوشته نمی‌شود، یا بیش از چهار هزار نویسه است.', 400)
    c = clock({})
    if c.get('may') is False:
        raise Refused('ساعت این رایانه با منبع‌های زمانش نمی‌خواند؛ پاسخ شما با زمان نادرست ثبت نمی‌شود. کمی بعد دوباره بفرستید.', 503)
    stamp = time.strftime('%Y%m%dT%H%M%S', time.localtime())
    at = time.strftime('%Y-%m-%d %H:%M:%S%z', time.localtime())
    head = {'form': form, 'person': person, 'at': at, 'through': 'served', 'answers': answers}
    box = forms_box()
    box.mkdir(mode=0o700, parents=True, exist_ok=True)
    f = box / f'{form}.{person}.{stamp}.md'
    lines = ['<!-- ' + json.dumps(head, ensure_ascii=False) + ' -->', '', f'# {title_of(person)} — {title_of(form)}', '']
    for i, (q, a) in enumerate(zip(qs, answers), 1):
        lines += [f'{i}. {q}', '', '   ' + (a.replace('\n', '\n   ') if a else '(—)'), '']
    tmp = f.with_suffix('.arriving')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)   # a person's words: this account's alone (audit 2.5)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))
    os.replace(tmp, f)
    return {'laid': f.stem, 'at': at}


def form_leads():
    """Answers laid by people without a garden, each a lead for the gardener to take."""
    return [{'kind': 'form', 'id': f.stem, 'title': f"{title_of(p)}: {title_of(form)}", 'since': s[:4] + '-' + s[4:6] + '-' + s[6:8]}
            for f, form, p, s in laid()]


def form_answers(params):
    """One laid answer, for the gardener's page: who, which form, when, and each question with its answer."""
    f = form_file(params)
    head = head_of(f)
    return {'id': f.stem, 'form': head['form'], 'form_title': title_of(head['form']), 'person': head['person'],
            'person_title': title_of(head['person']), 'at': head['at'],
            'questions': [{'q': q, 'a': a} for q, a in zip(questions_of(head['form']), head['answers'])]}


def head_of(f):
    """What a laid answer says of itself: its first line, `<!-- {json} -->`."""
    first = f.read_text(encoding='utf-8').split('\n', 1)[0]
    return json.loads(first[len('<!-- '):-len(' -->')])


def form_file(params):
    fid = str(params.get('id') or '')
    if not FORM_FILE.fullmatch(fid):
        raise Refused('پیدا نشد.', 404)
    f = forms_box() / f'{fid}.md'
    if not f.is_file():
        raise Refused('پیدا نشد.', 404)
    return f


def take_form(params):
    """The gardener takes one person's answers into the garden: a document of their words as they gave them, saved in
    the gardener's name (the ratification), and the laid file moved aside as taken."""
    rid = request_id(params)
    prior = already(rid)
    if prior:
        return {'saved': True, 'commit': prior, 'duplicate': True}
    f = form_file(params)
    head = head_of(f)
    form, person, stamp = FORM_FILE.fullmatch(f.stem).groups()
    bean = f'{form}-{person}-{stamp[:8]}-{stamp[9:13]}'[:120]
    who = gardener()
    path = ROOT / 'beans' / f'{bean}.md'
    words = [ln for ln in f.read_text(encoding='utf-8').split('\n')[2:]]
    lock = save_lock()
    try:
        if git('status', '--porcelain'):
            raise Refused(BUSY, 409)
        if path.exists():
            raise Refused('این پاسخ پیش‌تر گرفته شده است.', 409)
        title = f"{title_of(person)}'s answers to {title_of(form)}, {head['at'][:10]}".replace('"', "'")
        path.write_text('---\n' f'bean: {bean}\nkind: document\ntitle: "{title}"\nstatements:\n'
                        f'  - say: {{ by: {who}, at: now, note: "taken from the served page: {person}\'s own words, as given" }}\n'
                        f'  - concern: {{ by: self, of: [{person}] }}\n'
                        f'  - part: {{ by: self, of: {form} }}\n'
                        'details:\n  words:\n'
                        f'    by: {person}\n    at: \'{head["at"]}\'\n    through: served\n---\n' + '\n'.join(words) + '\n',
                        encoding='utf-8')
    finally:
        lock.__exit__(None, None, None)
    ok, said = run_save(who, f"Took {person}'s answers to {form}; handplace-request:{rid}",
                        [f'- action: wrote [[{bean}]]: [[{person}]]\'s own words to [[{form}]], given on the served page '
                         f'at {head["at"]}, taken as given', f'- ratified_by: {who}, on the handplace (daftard)'])
    if not ok:
        if path.exists() and not already(rid):
            path.unlink()
        raise refused_save(said)
    (f.parent / 'taken').mkdir(exist_ok=True)
    shutil.move(str(f), str(f.parent / 'taken' / f.name))
    return {'saved': True, 'commit': git('rev-parse', 'HEAD'), 'bean': bean}


# A PASSKEY a person makes on the served page is theirs to hold, and the garden's to name (class F): daftard verifies
# it, lays it outside the garden, and it waits as a lead until the gardener's save names it in the person's bean
# (`name: { by: passkey, of: self, as: <credential id>.<key> }`, the namespace `passkey`). A sign-in is verified
# against what the person's bean names, and nothing else.
ANCHOR = re.compile(r'[A-Za-z0-9_-]{22,1364}\.[A-Za-z0-9_-]{58,700}')
PASSKEY_FILE = re.compile(r'([a-z0-9][a-z0-9-]{0,63})\.(\d{8}T\d{6})')


def passkeys_box():
    return mailboxes() / str(identity().get('garden_id') or 'unknown') / 'passkeys'


def served_passkeys(params):
    """The passkeys the person's own bean names: its `name … by: passkey` anchors."""
    person = str(params.get('person') or '')
    path = ROOT / 'beans' / f'{person}.md'
    if not PERSON.fullmatch(person) or not path.is_file():
        return []
    parse = _garden_parse()
    fm = parse.loads(parse.split_front_matter(path.read_text(encoding='utf-8'))[0]) or {}
    return [str(r['as']) for st in fm.get('statements') or [] if isinstance(st, dict) and len(st) == 1
            for v, r in st.items() if v == 'name' and isinstance(r, dict) and r.get('by') == 'passkey'
            and 'held' not in r and ANCHOR.fullmatch(str(r.get('as') or ''))]


def passkey_lay(params):
    """A passkey the person made, verified by daftard, laid for the gardener to name as theirs."""
    person, anchor = str(params.get('person') or ''), str(params.get('anchor') or '')
    if not PERSON.fullmatch(person) or not ANCHOR.fullmatch(anchor):
        raise Refused('این کلید پذیرفته نشد.', 400)
    if anchor in served_passkeys({'person': person}):
        return {'laid': '', 'said': 'این کلید پیش‌تر به نام شما ثبت شده است.'}
    box = passkeys_box()
    box.mkdir(mode=0o700, parents=True, exist_ok=True)
    f = box / f"{person}.{time.strftime('%Y%m%dT%H%M%S', time.localtime())}.txt"
    fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)        # this account's alone (audit 2.5)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(anchor + '\n')
    return {'laid': f.stem, 'said': 'کلید شما ساخته شد؛ وقتی نگه‌دارندهٔ دفتر آن را به نام شما ثبت کند، با آن وارد می‌شوید.'}


def passkey_leads():
    box = passkeys_box()
    return [{'kind': 'passkey', 'id': f.stem, 'title': f"{title_of(m.group(1))}: a passkey to name as theirs",
             'since': m.group(2)[:4] + '-' + m.group(2)[4:6] + '-' + m.group(2)[6:8]}
            for f in (sorted(box.glob('*.txt')) if box.is_dir() else []) for m in [PASSKEY_FILE.fullmatch(f.stem)] if m]


def passkey_file(params):
    pid = str(params.get('id') or '')
    m = PASSKEY_FILE.fullmatch(pid)
    f = passkeys_box() / f'{pid}.txt'
    if not m or not f.is_file():
        raise Refused('پیدا نشد.', 404)
    return f, m.group(1), f.read_text(encoding='utf-8').strip()


def passkey_laid(params):
    f, person, anchor = passkey_file(params)
    return {'id': f.stem, 'person': person, 'person_title': title_of(person), 'credential': anchor.split('.', 1)[0][:16]}


def take_passkey(params):
    """The gardener names a person's passkey as theirs (class F): a `name` in the person's own bean, said by the
    gardener, saved in their sitting."""
    rid = request_id(params)
    prior = already(rid)
    if prior:
        return {'saved': True, 'commit': prior, 'duplicate': True}
    f, person, anchor = passkey_file(params)
    if not ANCHOR.fullmatch(anchor):
        raise Refused('این کلید پذیرفته نشد.', 400)
    path = ROOT / 'beans' / f'{person}.md'
    if not path.is_file():
        raise Refused('چنین کسی در این دفتر نیست.', 404)
    who = gardener()
    n = 1 + sum(1 for _ in served_passkeys({'person': person}))
    sid = f'passkey-{n}'
    lock = save_lock()
    try:
        if git('status', '--porcelain'):
            raise Refused(BUSY, 409)
        text = path.read_text(encoding='utf-8')
        while f'id: {sid},' in text:
            n += 1
            sid = f'passkey-{n}'
        import importlib.util                          # the garden's own safe edit: statements added, nothing lost
        spec = importlib.util.spec_from_file_location('garden_safe', ROOT / 'bin' / 'safe.py')
        gsafe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gsafe)
        gsafe.add_statements(str(path), f'- name: {{ id: {sid}, by: passkey, of: self, as: "{anchor}" }}\n'
                                        f'- say: {{ by: {who}, of: [{sid}], at: now }}\n')
    finally:
        lock.__exit__(None, None, None)
    ok, said = run_save(who, f"{person}'s passkey named as theirs; handplace-request:{rid}",
                        [f'- action: [[{person}]] holds a passkey, made on the served page and verified there; named '
                         f'as theirs by the gardener (class F)', f'- ratified_by: {who}, on the handplace (daftard)'])
    if not ok:
        relock = save_lock(60)
        try:
            if not already(rid):
                subprocess.run(['git', 'checkout', '--', str(path)], cwd=ROOT, capture_output=True)
        finally:
            relock.__exit__(None, None, None)
        raise refused_save(said)
    (f.parent / 'taken').mkdir(exist_ok=True)
    shutil.move(str(f), str(f.parent / 'taken' / f.name))
    return {'saved': True, 'commit': git('rev-parse', 'HEAD')}


# ODOO'S OWN WEB CLIENT, ANSWERED FROM THE GARDEN (design §10.2): the series' views the garden captured
# (captures/views/odoo-<series>/, importers/odoo/views.py), and the calls the client makes answered by odoo_rpc over
# the records the reader may read. The records come from the garden through the law's crosswalk of each model (P5.3);
# until a model has one, it has no records here, and its views show none.
# an Odoo model's name, as a folder of the captures is named by it: words of lowercase letters, digits and `_`, joined by
# dots — most have one (res.partner), some none (Odoo's own `base`) — and so never a path
MODEL = re.compile(r'[a-z][a-z0-9_]*(\.[a-z0-9_]+)*')


def odoo_captures():
    """{series: its captures folder} of the views this garden holds."""
    base = ROOT / 'captures' / 'views'
    return {d.name[len('odoo-'):]: d for d in sorted(base.glob('odoo-*')) if (d / 'CAPTURE.json').is_file()} if base.is_dir() else {}


def odoo_models(series):
    d = odoo_captures().get(series)
    return sorted(x.name for x in d.iterdir() if x.is_dir() and MODEL.fullmatch(x.name)) if d else []


LANG = re.compile(r'[a-z]{2,3}(_[A-Z]{2})?')
# the view types Odoo's client asks for: a name a file is read by, so a word of lowercase letters and `_` and never a
# path (security audit 2.3) — Odoo's own (list, form, kanban, search, pivot…) and those an addon or a test registers
VIEW_TYPE = re.compile(r'[a-z][a-z_]{0,31}')


def odoo_fields(series, model, lang=''):
    """The fields as the capture describes them, in the reader's language where it was taken in it."""
    d = odoo_captures().get(series)
    if not d or not MODEL.fullmatch(model or ''):
        return {}
    for name in ([f'fields.{lang}.json'] if lang and LANG.fullmatch(lang) and lang != 'en_US' else []) + ['fields.json']:
        f = d / model / name
        if f.is_file():
            return json.loads(f.read_text(encoding='utf-8'))
    return {}


def odoo_related(series, model, lang=''):
    """{model: fields} of each other model the captured views of `model` show, as the capture describes them."""
    d = odoo_captures().get(series)
    if not d or not MODEL.fullmatch(model or ''):
        return {}
    for name in ([f'related.{lang}.json'] if lang and LANG.fullmatch(lang) and lang != 'en_US' else []) + ['related.json']:
        f = d / model / name
        if f.is_file():
            got = json.loads(f.read_text(encoding='utf-8'))
            return {m: v for m, v in got.items() if MODEL.fullmatch(str(m)) and isinstance(v, dict)} if isinstance(got, dict) else {}
    return {}


def odoo_title(series, model, lang=''):
    """What a model is called on its own views — the `string` of its list (or search) view, in the reader's language
    where it was taken in it — else the model's name."""
    import xml.etree.ElementTree as ET
    d = odoo_captures().get(series)
    if not d or not MODEL.fullmatch(str(model or '')):
        return model
    for vt in ('list', 'search', 'kanban'):
        for f in ([d / model / f'{vt}.{lang}.xml'] if lang and LANG.fullmatch(lang) else []) + [d / model / f'{vt}.xml']:
            if f.is_file():
                try:
                    s = ET.fromstring(f.read_text(encoding='utf-8')).get('string')
                except ET.ParseError:
                    s = None
                if s:
                    return s
    return model


def read_only(arch, view_type):
    """The captured view as served while daftard takes no write through Odoo's client: told so on its root (`create`,
    `edit`, `delete`, `duplicate` off), so the client offers none. The capture itself is left as it came."""
    if view_type == 'search':
        return arch
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(arch)
    except ET.ParseError:
        return arch
    for attr in ('create', 'edit', 'delete', 'duplicate'):
        root.set(attr, '0')
    return ET.tostring(root, encoding='unicode')


# EVERY ANSWER IS MADE OF WHAT THE READER MAY READ (design §10.2: "every domain ANDed with the reader's grants"; P5.4).
# A call of Odoo's client is answered over one OdooReading: of the garden's beans, those the reader's grants open —
# the garden's own `may` (bin/pass.py), closed by default, asked once of each bean — and nothing else. The crosswalks
# read only those beans (a garden handed to the garden's own core/crosswalk.py with the others left out), so a record
# whose bean is closed is not there: no count, sum, group, search panel counter or result is made of it. A path that
# reaches a closed bean reaches nothing: no many2one names it, no department's complete name carries its title, no
# `inverse` lists it, no company is reached through it, and a record selected only through it is not selected. A value
# that is the id of a closed bean is no value. The answerer (odoo_rpc) is handed this reading and has no other way
# into the garden. A grant that opens only parts of a bean does not open it as a record: a record is the whole bean.
#
# AS OF A COMMIT (design §10.3): the beans are the garden's at that commit, read by today's crosswalks — the way
# Odoo's model is read is today's law; what was said is that commit's. THE GRANTS ARE TODAY'S. Answered by the
# philosophy (`safety`, `parts`) — vetoable: who may read a bean is the gardener's decision now, about a person, not a
# fact of the past. A grant withdrawn closes the bean's past with its present; judged as of then, its whole past would
# stay open to the reader the gardener has closed it to. A grant given opens the bean's history with it, as reading a
# bean opens what it says. What must not be read even so is sealed before it is committed (MODEL: what harm can come
# of, git does not keep), since no seal takes back what history holds.
ASOF_TREES = {}                       # commit -> a folder holding that commit's beans/ and mappings/, made once each


def _forget_asof():
    for d in ASOF_TREES.values():
        shutil.rmtree(d, ignore_errors=True)
    ASOF_TREES.clear()


def asof_tree(commit):
    """A folder holding the beans (and mappings) of `commit` as git holds them, for the garden's own reader to read: made
    once each, and the four last made kept."""
    if commit in ASOF_TREES:
        return ASOF_TREES[commit]
    import atexit
    import io
    import tarfile
    import tempfile
    if not ASOF_TREES:
        atexit.register(_forget_asof)
    d = Path(tempfile.mkdtemp(prefix='daftar-asof-'))
    dirs = [x for x in ('beans', 'mappings') if git('rev-parse', '--verify', '-q', f'{commit}:{x}')]
    if dirs:
        tar = subprocess.run(['git', 'archive', '--format=tar', commit, '--', *dirs], cwd=ROOT, capture_output=True)
        if tar.returncode != 0:
            shutil.rmtree(d, ignore_errors=True)
            raise Refused('آن نسخه از دفتر خوانده نشد.', 404)
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as t:
            t.extractall(d, filter='data')
    ASOF_TREES[commit] = d
    while len(ASOF_TREES) > 4:
        shutil.rmtree(ASOF_TREES.pop(next(iter(ASOF_TREES))), ignore_errors=True)
    return d


COMMITISH = re.compile(r'[0-9a-f]{4,40}')
MOMENT = re.compile(r'(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2})?)(Z|[+-]\d{2}:?\d{2})?)?')


def odoo_asof(params):
    """The commit of the garden's history the reader is to see it as of: `at` a commit (one HEAD reaches) or a moment —
    a day is its end, in the garden's zone, and a moment without its offset is in that zone — giving the last commit of
    the first-parent line at or before it. {commit, at, subject}; {} for now (`at` empty)."""
    at = str(params.get('at') or '').strip()
    if not at:
        return {}
    commit = ''
    if COMMITISH.fullmatch(at):
        commit = git('rev-parse', '--verify', '-q', at + '^{commit}')
    else:
        m = MOMENT.fullmatch(at)
        if not m:
            raise Refused('یک نسخه (شناسهٔ کامیت) یا یک لحظه بدهید: 2026-10-11 یا 2026-10-11 14:30.', 400)
        import datetime as dt
        from zoneinfo import ZoneInfo
        try:
            zone = ZoneInfo(str(front(ROOT / 'GARDEN.md').get('zone') or 'UTC'))
        except Exception:
            zone = ZoneInfo('UTC')
        day, clock, off = m.groups()
        try:
            t = dt.datetime.strptime(day + ' ' + (clock or '23:59:59'), '%Y-%m-%d %H:%M:%S' if (clock or '23:59:59').count(':') == 2
                                     else '%Y-%m-%d %H:%M')
        except ValueError:
            raise Refused('این لحظه خوانده نشد.', 400)
        if off:
            off = '+00:00' if off == 'Z' else off if ':' in off else off[:3] + ':' + off[3:]
            sign = 1 if off[0] == '+' else -1
            t = t.replace(tzinfo=dt.timezone(sign * dt.timedelta(hours=int(off[1:3]), minutes=int(off[4:6]))))
        else:
            t = t.replace(tzinfo=zone)
        commit = git('rev-list', '-1', '--first-parent', f'--before={int(t.timestamp())}', 'HEAD')
    if not commit or subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT,
                                    capture_output=True).returncode != 0:
        raise Refused('این دفتر در آن لحظه نسخه‌ای نداشت.', 404)
    full, when, subject = (git('show', '-s', '--format=%H%x00%cI%x00%s', commit).split('\x00') + ['', '', ''])[:3]
    return {'commit': full, 'at': when, 'subject': subject}


class OdooReading:
    """What one call of Odoo's client is answered from: of the garden's beans (as of `asof`, a commit; none: the working
    tree), only those the reader's grants open now, read through the law's crosswalks of the series."""

    def __init__(self, series, reader, asof=None):
        self.series, self.reader, self.asof = series, str(reader or ''), asof or None
        self._R, self._records, self.readable, self.closed = None, {}, set(), set()

    def reader_of_law(self):
        """The garden's own crosswalk reader over the beans this reader may read, or None where there is none."""
        if self._R is not None:
            return self._R or None
        self._R = False
        if not PERSON.fullmatch(self.reader):
            return None
        try:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from core import crosswalk, engine
            from core.check import garden_law
        except ImportError:
            return None
        import importlib
        if str(ROOT / 'bin') not in sys.path:
            sys.path.insert(0, str(ROOT / 'bin'))
        dmpass = importlib.import_module('pass')
        tree = asof_tree(self.asof) if self.asof else ROOT
        G = engine.Garden.read(str(tree))
        now = dmpass.beans_here(str(ROOT))                     # the grants are read from the garden as it is now
        keeper = gardener()
        self.readable = {b for b in G.beans
                         if dmpass.may(self.reader, 'read', b, root=str(ROOT), beans=now, gardener=keeper).granted}
        self.closed = (set(G.beans) | set(now)) - self.readable
        G.beans = {b: x for b, x in G.beans.items() if b in self.readable}
        import inspect
        extra = {'unseal': self.unseal} if 'unseal' in inspect.signature(crosswalk.Reader).parameters else {}
        try:
            self._R = crosswalk.Reader(str(ROOT), 'odoo', self.series, law=garden_law(str(ROOT)), garden=G, **extra)
        except crosswalk.Refused:
            self._R = False
        return self._R or None

    # WHAT IS HELD IS RESOLVED FOR THE GARDENER ALONE. A field the law carries held (a government number, a private
    # mail) is read from a sealed statement through this host's own store (the garden's bin/held.py), never from git.
    # Answered by the philosophy (`safety`: the default is caution) — vetoable: the store is its keeper's, the
    # gardener's; whether a grant can open a sealed statement to anyone else is the law's to say (a RULE-CHANGE), so
    # until it does, no other reader is resolved one.
    def unseal(self, bean, verb, roles):
        if self.reader != gardener() or not isinstance(roles.get('held'), str):
            return None
        import importlib
        try:
            held = importlib.import_module('held')
            rec = held.resolve(roles['held'], root=str(ROOT))
        except Exception:                       # held elsewhere, erased, or no store here: not known, never an error
            return None
        if not isinstance(rec, dict) or rec.get('verb') != verb or (roles.get('id') and rec.get('key') != roles['id']):
            return None
        return dict(rec.get('entry') or {})

    def records(self, model):
        """The records of a model this reading holds: every one a bean the reader may read, every value read from such
        beans alone. A model the law does not cross has none."""
        if model in self._records:
            return self._records[model]
        R, out = self.reader_of_law(), []
        if R is not None and model in R.rows:
            from core import crosswalk
            try:
                got = R.records(model)
            except crosswalk.Refused:
                got = []
            def closed(x):                                  # a closed bean's id, or a statement of one (`bean#id`)
                return isinstance(x, str) and x.split('#', 1)[0] in self.closed
            for rec in got:
                for k, v in list(rec.items()):
                    if closed(v):
                        rec[k] = False                         # the id of a bean closed to the reader is no value
                    elif isinstance(v, list) and any(closed(x) for x in v):
                        rec[k] = [x for x in v if not closed(x)]
                out.append(rec)
        self._records[model] = out
        return out

    def bean_of(self, model, record_id):
        """The bean a record of the model is, where the reader may read it; else None."""
        R = self.reader_of_law()
        if R is None or model not in R.rows:
            return None
        from core import crosswalk
        try:
            return next((b for b in R.selected(model) if crosswalk.number(model, b) == record_id), None)
        except crosswalk.Refused:
            return None


def odoo_records(series, model, reader, asof=None):
    """The records of a model the reader may read (OdooReading), for one question."""
    return OdooReading(series, reader, asof).records(model)


# A READER'S FAVOURITES (design §10.2: "kept in the garden as the person's own"). Answered by the philosophy (`once`,
# `sibling`; DESIGN §3, a reader's settings are the reader's own) — vetoable: a favourite is one person's saved
# search, a customisation of how they read, like their labels: kept on their own ref, refs/daftar/custom/<person>,
# beside their labels in its labels.json (`favourites`), never a bean and never anyone else's. Odoo's shared filters
# (a favourite with no user) have no place here: a search others should share is a reading of the garden (`reckon`),
# said in it. So a reader is answered their own favourites and nobody else's.
def odoo_favourites(reader, model, action_id=None):
    """The reader's own favourites of a model, as Odoo's ir.filters.get_filters gives them."""
    if not PERSON.fullmatch(str(reader or '')):
        return []
    ref = f'refs/daftar/custom/{reader}'
    if not git('rev-parse', '--verify', '-q', ref + '^{commit}'):
        return []
    try:
        doc = json.loads(git('cat-file', 'blob', f'{ref}:labels.json') or '{}')
    except ValueError:
        return []
    out = []
    favs = doc.get('favourites') if isinstance(doc, dict) else None
    for key, f in sorted((favs or {}).items(), key=lambda kv: str((kv[1] or {}).get('at') or '')):
        if not isinstance(f, dict) or f.get('gone') or f.get('model') != model:
            continue
        if f.get('action_id') not in (None, False, action_id):
            continue
        out.append({'id': int(hashlib.sha256(f'{reader}:{key}'.encode()).hexdigest()[:7], 16),
                    'name': str(f.get('name') or ''), 'is_default': bool(f.get('is_default')),
                    'domain': str(f.get('domain') or '[]'), 'context': str(f.get('context') or '{}'),
                    'sort': str(f.get('sort') or '[]'), 'user_id': [1, title_of(reader)],
                    'action_id': False})
    return out


# A RECORD'S HISTORY, IN ITS CHATTER (design §10.3: "each bean has a timeline: each change with its journal entry and who
# knew what, statement by statement"). Odoo's chatter asks /mail/thread/messages of the record a form shows; it is
# answered with the history of the bean that record is: one message for each commit that changed the bean, newest
# first — who made the change and when, the journal entry the commit added, and each statement the change added or took
# out, with the act it is known by (said, read, derived or made, by whom, when). Only for a bean the reader may read
# now; as of a commit, only the history up to it. A statement that names a bean closed to the reader names it as
# closed, and an entry is shown only where every bean it names, and every bean its commit changed, is open to them —
# else the message says the entry is closed to them.
CLOSED = '(closed)'
WIKI = re.compile(r'\[\[([a-z0-9][a-z0-9._-]*)\]\]')


_PARSE = []


def _garden_parse():
    """The garden's own bin/parse.py, loaded once."""
    if not _PARSE:
        import importlib.util
        spec = importlib.util.spec_from_file_location('garden_parse', ROOT / 'bin' / 'parse.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _PARSE.append(mod)
    return _PARSE[0]


def _statements_of(text):
    """(header, [(verb, roles)]) of a bean's text, read by the garden's own reader; ({}, []) where none."""
    if not text:
        return {}, []
    from core import read as core_read
    try:
        head = _garden_parse().split_front_matter(text)[0]
        fm = core_read.loads(head, 'bean') if head is not None else {}
    except Exception:
        return {}, []
    fm = fm if isinstance(fm, dict) else {}
    out = []
    for st in fm.get('statements') or []:
        if isinstance(st, dict) and len(st) == 1:
            (v, r), = st.items()
            if isinstance(r, dict):
                out.append((str(v), r))
    return fm, out


def _said(value, closed):
    """A filler as the reader may see it: a bean closed to them named as closed."""
    if isinstance(value, dict):
        return '{ ' + ', '.join(f'{k}: {_said(v, closed)}' for k, v in value.items()) + ' }'
    if isinstance(value, list):
        return '[' + ', '.join(_said(v, closed) for v in value) + ']'
    v = str(value)
    if v in closed or v.split('#', 1)[0] in closed:
        return CLOSED
    return v


KNOWING = ('say', 'read', 'derive', 'make')


def _statement_text(verb, roles, closed):
    """A statement as the reader may see it. Answered by the philosophy (`provenance`: a fact says who said it) —
    vetoable: the knower of a knowing act is shown as the bean says it, closed or not, since who knows a statement is
    what the timeline is for; any other bean closed to the reader is named as closed."""
    if 'held' in roles:
        return f"{verb}: (held off git{', ' + str(roles['id']) if roles.get('id') else ''})"
    if verb in KNOWING:
        knower = roles.get('by')
        return f'{verb}: ' + _said(roles, closed - ({knower} if isinstance(knower, str) else set()))
    return f'{verb}: ' + _said(roles, closed)


def _knower(stmt, statements, knowing, closed):
    """The act a statement is known by in its bean: the knowing act naming its id, else the one naming none."""
    sid = stmt[1].get('id')
    acts = [(v, r) for v, r in statements if v in knowing]
    hit = next(((v, r) for v, r in acts if sid and sid in (r.get('of') if isinstance(r.get('of'), list) else [r.get('of')])), None)
    hit = hit or next(((v, r) for v, r in acts if 'of' not in r), None)
    if hit is None:
        return ''
    v, r = hit
    return {'say': 'said', 'read': 'read', 'derive': 'derived', 'make': 'made'}.get(v, v) + \
        f" by {r.get('by')}" + (f", {r.get('at')}" if r.get('at') else '')


def _empty_tree():
    """The empty tree's id in this repository's hash, what a first commit's change is read against."""
    return subprocess.run(['git', 'hash-object', '-t', 'tree', '--stdin'], cwd=ROOT, input='', capture_output=True,
                          text=True).stdout.strip()


def _blob(commit, paths):
    """The text of the first of `paths` the commit holds, or ''."""
    for p in paths:
        r = subprocess.run(['git', 'show', f'{commit}:{p}'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                           errors='replace')
        if r.returncode == 0:
            return r.stdout
    return ''


def odoo_timeline(reading, model, record_id, asof=None, limit=30, before=None, after=None):
    """The messages of a record's chatter: its bean's history, as the reader may read it."""
    import html
    bean = reading.bean_of(model, record_id)
    if bean is None:
        return []
    paths = [f'beans/{bean}.md', f'mappings/{bean}.md']
    head = asof or 'HEAD'
    log = git('log', '--no-merges', '--format=%H%x00%P%x00%an%x00%aI%x00%s', head, '--', *paths)
    knowing = KNOWING
    tag = int(hashlib.sha256(bean.encode()).hexdigest()[:4], 16)
    out = []
    for line in log.splitlines():
        commit, parents, who, when, _subject = (line.split('\x00') + [''] * 5)[:5]
        parent = parents.split()[0] if parents.split() else None
        pos = int(git('rev-list', '--count', commit) or 0)
        mid = pos * 65536 + tag
        if (before is not None and mid >= before) or (after is not None and mid <= after):
            continue
        new_fm, new = _statements_of(_blob(commit, paths))
        old_fm, old = _statements_of(_blob(parent, paths) if parent else '')
        key = lambda vr: json.dumps(vr, sort_keys=True, ensure_ascii=False, default=str)  # noqa: E731
        was, now = {key(x): x for x in old}, {key(x): x for x in new}
        closed = reading.closed
        tracking = []
        for k in ('title', 'summary'):
            if (old_fm.get(k) or '') != (new_fm.get(k) or ''):
                tracking.append((k, str(old_fm.get(k) or ''), str(new_fm.get(k) or '')))
        for k, st in now.items():
            if k not in was:
                known = _knower(st, new, knowing, closed) if st[0] not in knowing else ''
                tracking.append((st[0], '', _statement_text(*st, closed) + (f' — {known}' if known else '')))
        for k, st in was.items():
            if k not in now:
                tracking.append((st[0], _statement_text(*st, closed), ''))
        # the journal entry this commit added, shown where it names nothing closed to the reader
        added = [ln[1:] for ln in git('diff', '--unified=0', parent or _empty_tree(),
                                      commit, '--', 'log/journal.md').splitlines()
                 if ln.startswith('+') and not ln.startswith('+++')]
        changed = {Path(p).stem for p in git('diff', '--name-only', parent or _empty_tree(),
                                             commit, '--', 'beans', 'mappings').splitlines()}
        named = set(WIKI.findall('\n'.join(added))) | changed
        if named & closed:
            body = '<p>' + html.escape('This change also touched what is closed to you; its journal entry is not shown.') + '</p>'
        else:
            body = ''.join(f'<p>{html.escape(ln.lstrip("# ").strip())}</p>' if ln.startswith('## ') else
                           f'<p>{html.escape(ln.strip())}</p>' for ln in added if ln.strip())
        stamp = when[:19].replace('T', ' ')
        try:
            import datetime as dt
            stamp = dt.datetime.fromisoformat(when).astimezone(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        out.append({
            'id': mid, 'body': body, 'date': stamp, 'create_date': stamp, 'write_date': stamp, 'email_from': False,
            'message_type': 'notification', 'subtype_id': False, 'subject': False, 'model': model, 'res_id': record_id,
            'record_name': title_of(bean), 'default_subject': title_of(bean), 'starred_partner_ids': [],
            'author': {'id': int(hashlib.sha256(who.encode()).hexdigest()[:7], 16), 'name': who, 'type': 'partner'},
            'notifications': [], 'attachments': [], 'linkPreviews': [], 'reactions': [], 'pinned_at': False,
            'needaction_partner_ids': [], 'history_partner_ids': [], 'is_note': True, 'is_discussion': False,
            'subtype_description': f'commit {commit[:12]}', 'recipients': [], 'scheduledDatetime': False,
            'trackingValues': [{'id': mid * 64 + n, 'changedField': field, 'fieldName': field, 'fieldType': 'char',
                                'oldValue': {'currencyId': False, 'value': o}, 'newValue': {'currencyId': False, 'value': v}}
                               for n, (field, o, v) in enumerate(tracking[:60])],
        })
        if len(out) >= (limit or 30):
            break
    return out



def odoo_session(params):
    """What the page tells the client of its session: who reads, and this garden as its one company."""
    who, series = str(params.get('reader') or gardener() or ''), str(params.get('series') or '')
    asof = str(params.get('asof') or '')
    asof = asof if re.fullmatch(r'[0-9a-f]{40}', asof) else ''
    lang = str(params.get('lang') or 'en_US') if re.fullmatch(r'[a-z]{2,3}(_[A-Z]{2})?', str(params.get('lang') or '')) else 'en_US'
    major = [int(x) for x in series.split('.')[:2]] if re.fullmatch(r'\d+\.\d+', series) else [17, 0]
    name = title_of(who) if who else 'daftar'
    garden = identity().get('garden') or 'garden'
    # the reader's days are the garden's: the zone its days are reckoned in (GARDEN.md `zone`), so a day it says begins
    # at its own midnight on the page too
    zone = str(front(ROOT / 'GARDEN.md').get('zone') or 'UTC')
    zone = zone if re.fullmatch(r'[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z0-9_+-]+)*', zone) else 'UTC'
    return {'uid': 1, 'user_id': [1], 'partner_id': 1, 'name': name, 'username': who, 'partner_display_name': name,
            'is_admin': False, 'is_system': False, 'is_internal_user': True, 'db': garden,
            'user_context': {'lang': lang, 'tz': zone, 'uid': 1},
            'user_settings': {'id': 1, 'user_id': {'id': 1}},
            'server_version': series, 'server_version_info': major + [0, 'final', 0, ''],
            'cache_hashes': {'translations': 'daftar', 'load_menus': 'daftar'},
            'user_companies': {'current_company': 1, 'allowed_companies': {'1': {'id': 1, 'name': garden, 'sequence': 0,
                                                                                   'child_ids': [], 'parent_id': False}},
                               'disallowed_ancestor_companies': {}},
            'currencies': {}, 'display_switch_company_menu': False, 'home_action_id': False, 'active_ids_limit': 20000,
            'max_file_upload_size': 0, 'notification_type': 'inbox', 'odoobot_initialized': True, 'show_effect': False,
            'tour_disable': True, 'web_tours': [], 'support_url': '', 'web.base.url': '', 'iap_company_enrich': False,
            'profile_session': None, 'profile_collectors': None, 'profile_params': None,
            'bundle_params': {'lang': lang},
            'daftar': {'asof': odoo_asof({'at': asof}) if asof else {}, 'lang': lang},
            **(odoo_session_19(params, name, garden) if major[0] >= 19 else {})}


def odoo_session_19(params, name, garden):
    """What 19's client reads of its session beside 17's: what each kind of view is called in the page's language (as
    the series' client was taken with it), the start of its mail store (the reader as its one partner and user), its
    menus' version, and no tour. NEVER `browser_cache_secret`: given one, 19's client keeps its answers — records, the
    search panel's values — in the browser's own disk cache (IndexedDB); without it, in memory only, so nothing a reader
    was shown is left on their machine."""
    vi = params.get('view_info')
    vi = {k: v for k, v in vi.items() if VIEW_TYPE.fullmatch(str(k)) and isinstance(v, dict)} if isinstance(vi, dict) else {}
    seed = json.dumps([garden, params.get('series'), sorted(odoo_models(str(params.get('series') or '')))])
    return {'view_info': vi, 'is_public': False, 'groups': {'base.group_allow_export': False},
            'tour_enabled': False, 'current_tour': None, 'quick_login': False, 'test_mode': False,
            'registry_hash': hashlib.sha256(seed.encode()).hexdigest(), 'partner_write_date': '1970-01-01 00:00:00',
            'websocket_worker_version': '', 'show_effect': False,
            'storeData': {'Store': {'self_partner': 1, 'odoobot': 2, 'internalUserGroupId': 1, 'mt_comment': 1, 'mt_note': 2,
                                    'action_discuss_id': False, 'hasCannedResponses': False, 'hasGifPickerFeature': False,
                                    'hasLinkPreviewFeature': False, 'hasMessageTranslationFeature': False,
                                    'channel_types_with_seen_infos': [],
                                    'settings': {'id': 1, 'user_id': {'id': 1}, 'embedded_actions_config_ids': {},
                                                 'is_discuss_sidebar_category_channel_open': False,
                                                 'is_discuss_sidebar_category_chat_open': False, 'volumes': [['ADD', []]],
                                                 'channel_notifications': False, 'push_to_talk_key': False,
                                                 'use_push_to_talk': False, 'voice_active_duration': 0}},
                          'res.partner': [{'id': 1, 'name': name, 'active': True, 'main_user_id': 1,
                                           'write_date': '1970-01-01 00:00:00'},
                                          {'id': 2, 'name': 'daftar', 'active': False, 'im_status': 'bot',
                                           'write_date': '1970-01-01 00:00:00'}],
                          'res.users': [{'id': 1, 'partner_id': 1, 'share': False, 'notification_type': 'inbox'}]}}


def odoo_rpc(params):
    """One call of the client: {path, payload, reader, series} → its result."""
    import odoo_rpc as orpc
    series, path = str(params.get('series') or ''), str(params.get('path') or '')
    payload, reader = params.get('payload') or {}, str(params.get('reader') or '')
    asof = str(params.get('asof') or '')
    asof = asof if re.fullmatch(r'[0-9a-f]{40}', asof) else None
    models = odoo_models(series)
    if not models:
        raise Refused('این دفتر هیچ نمای اودویی از این سری نگرفته است.', 404)
    major = int(series.split('.')[0]) if re.fullmatch(r'\d+\.\d+', series) else 17
    actions = {i + 1: m for i, m in enumerate(models)}
    lang = str(params.get('lang') or ((payload.get('kwargs') or {}).get('context') or {}).get('lang')
               or (payload.get('context') or {}).get('lang') or '')
    lang = lang if LANG.fullmatch(lang) and lang != 'en_US' else ''
    if path.startswith('/web/webclient/load_menus'):
        root = {'id': 'root', 'name': 'root', 'children': list(actions), 'appID': False, 'xmlid': '', 'actionID': False,
                'actionModel': False, 'actionPath': False, 'webIcon': None, 'webIconData': None, 'webIconDataMimetype': None,
                'backgroundImage': None}
        menus = {'root': root}
        for i, m in actions.items():
            menus[i] = {'id': i, 'name': odoo_title(series, m, lang), 'children': [], 'appID': i, 'xmlid': '', 'actionID': i,
                        'actionModel': 'ir.actions.act_window', 'actionPath': False, 'webIcon': None, 'webIconData': None,
                        'webIconDataMimetype': None, 'backgroundImage': None}
        return menus
    if path.startswith('/web/webclient/translations'):
        return {'lang': 'en_US', 'lang_parameters': {'direction': 'ltr', 'date_format': '%Y-%m-%d', 'time_format': '%H:%M:%S',
                'grouping': '[3,0]', 'decimal_point': '.', 'thousands_sep': ',', 'week_start': 1}, 'modules': {}, 'multi_lang': False}
    if path == '/web/action/load':
        m = actions.get(payload.get('action_id'))
        if not m:
            raise Refused('پیدا نشد.', 404)
        d = odoo_captures()[series] / m
        types = [t for t in ('list', 'kanban', 'form') if (d / f'{t}.xml').is_file()]
        out = {'type': 'ir.actions.act_window', 'id': payload['action_id'], 'name': odoo_title(series, m, lang), 'res_model': m,
               'views': [[False, t] for t in types], 'view_mode': ','.join(types), 'context': {}, 'domain': [],
               'target': 'current', 'search_view_id': False, 'help': '', 'xml_id': '', 'limit': 80}
        if major >= 19:                 # what 19's action service reads beside: no path of its own, no embedded actions
            out.update(display_name=out['name'], path=False, embedded_action_ids=[], res_id=0, mobile_view_mode='kanban')
        return out
    if path == '/mail/data' and major >= 19:          # 19's mail starts as a store: nothing waits, a record's thread
        out = {'Store': {'activityCounter': 0, 'activityGroups': [], 'initChannelsUnreadCounter': 0,
                         'inbox': {'counter': 0, 'id': 'inbox', 'model': 'mail.box'},
                         'starred': {'counter': 0, 'id': 'starred', 'model': 'mail.box'}}}
        for fp in payload.get('fetch_params') or []:
            if isinstance(fp, list) and len(fp) == 2 and fp[0] == 'mail.thread' and isinstance(fp[1], dict):
                model, rid = str(fp[1].get('thread_model') or ''), fp[1].get('thread_id')
                reading = OdooReading(series, reader, asof)
                open_ = model in models and isinstance(rid, int) and reading.bean_of(model, rid) is not None
                out.setdefault('mail.thread', []).append({
                    'id': rid if isinstance(rid, int) else 0, 'model': model if MODEL.fullmatch(model) else '',
                    'hasReadAccess': open_, 'hasWriteAccess': False, 'canPostOnReadonly': False, 'attachments': [],
                    'areAttachmentsLoaded': True, 'isLoadingAttachments': False, 'followers': [], 'followersCount': 0,
                    'recipients': [], 'recipientsCount': 0, 'scheduledMessages': [], 'selfFollower': False,
                    'suggestedRecipients': [], 'partner_fields': [], 'primary_email_field': None})
        return out
    if path == '/mail/thread/messages' and major >= 19:
        # a record's history in 19's chatter (its Store's shape) is not built yet: the 17 chatter's is (P5.4b)
        return {'data': {}, 'messages': []}
    if path == '/mail/init_messaging':
        return {'channels': [], 'current_partner': {'id': 1, 'name': title_of(reader) if reader else 'daftar', 'type': 'partner'},
                'currentGuest': False, 'current_user_id': 1, 'current_user_settings': {'id': 1, 'user_id': {'id': 1}},
                'hasLinkPreviewFeature': False, 'hasGifPickerFeature': False, 'hasMessageTranslationFeature': False,
                'initBusId': 0, 'internalUserGroupId': 1, 'menu_id': False, 'needaction_inbox_counter': 0,
                'starred_counter': 0, 'shortcodes': [], 'odoobot': {'id': 2, 'name': 'daftar', 'type': 'partner'},
                'odoobotOnboarding': False, 'companyName': identity().get('garden') or '', 'action_discuss_id': False,
                'mt_comment_id': False}
    if path in ('/mail/load_message_failures',):
        return []
    if path in ('/mail/thread/data', '/mail/thread/messages'):        # a record's chatter: its bean's history (P5.4b)
        model, rid = str(payload.get('thread_model') or ''), payload.get('thread_id')
        reading = OdooReading(series, reader, asof)
        if path == '/mail/thread/data':
            open_ = model in models and isinstance(rid, int) and reading.bean_of(model, rid) is not None
            out = {'hasWriteAccess': False, 'hasReadAccess': open_, 'canPostOnReadonly': False}
            asked = payload.get('request_list') or []
            if open_:
                for k, v in (('activities', []), ('attachments', []), ('followers', []), ('suggestedRecipients', [])):
                    if k in asked:
                        out[k] = v
                if 'followers' in asked:
                    out.update(followersCount=0, selfFollower=None, recipientsCount=0, recipients=[])
            return out
        if model not in models or not isinstance(rid, int):
            return {'messages': []}
        lim = payload.get('limit') if isinstance(payload.get('limit'), int) else 30
        return {'messages': odoo_timeline(reading, model, rid, asof, max(1, min(lim, 100)),
                                          payload.get('before') if isinstance(payload.get('before'), int) else None,
                                          payload.get('after') if isinstance(payload.get('after'), int) else None)}
    if path.startswith('/web/dataset/call_kw'):
        model, method = str(payload.get('model') or ''), str(payload.get('method') or '')
        kw, args = payload.get('kwargs') or {}, payload.get('args') or []
        if method == 'systray_get_activities':
            return []
        if method in ('iap_enrich_auto',):
            return {}
        if not MODEL.fullmatch(model):
            raise Refused(f'{model!r} is no model name', 404)
        # a model the garden captured no view of has no records here (what the garden does not say, no record has); its
        # fields are those a captured view describes it with, where one does

        def views(m, wanted):
            if m not in models or not MODEL.fullmatch(str(m)):
                return {'views': {}, 'models': {}}
            d = odoo_captures()[series] / m
            out = {}
            for _vid, vt in wanted:
                if not VIEW_TYPE.fullmatch(str(vt)):    # a type that is no word names no file here
                    continue
                f = next((x for x in ([d / f'{vt}.{lang}.xml'] if lang and LANG.fullmatch(lang) else []) + [d / f'{vt}.xml']
                          if x.is_file()), None)
                if f:
                    out[vt] = {'arch': read_only(f.read_text(encoding='utf-8'), vt), 'id': False, 'model': m}
                    if vt == 'search':
                        out[vt]['filters'] = []
                    if major >= 19:
                        out[vt]['toolbar'] = {}
            got = {**odoo_related(series, m, lang), m: odoo_fields(series, m, lang)}
            if major >= 19:                             # 19 wraps each model's fields
                got = {k: {'fields': v} for k, v in got.items()}
            return {'views': out, 'models': got}
        if model == 'ir.filters' and method != 'get_filters':
            raise Refused('a favourite is saved on its reader\'s own handplace; daftard takes no write here yet', 501)

        if method not in LOCAL_CALLS and register_serves(series):   # a register's records: asked of it, live (§15.6)
            return register_call(series, reader, params.get('lang'), asof, model, method, args, kw, params.get('routes'))
        reading = OdooReading(series, reader, asof)        # one reading for the whole call: the reader's part of the garden
        def fields(m):
            got = odoo_fields(series, m, lang)
            if got or m in models:
                return got
            return next((r[m] for r in (odoo_related(series, c, lang) for c in models) if m in r), {})
        answer = orpc.Answerer(reading.records, fields, views,
                               lambda m, action_id=None: odoo_favourites(reader, m, action_id))
        week = params.get('week_start')
        answer.speak(series, int(week) if str(week or '').isdigit() else 7)
        try:
            return answer.call(model, method, args, kw)
        except orpc.Unsupported as e:
            raise Refused(f'daftar does not answer this yet: {e}', 501)
        except orpc.Denied as e:                      # Odoo's own refusal, said as Odoo says it
            raise Refused(str(e), 403)
    # a form's button runs a method of its record: of a register's record, refused as every call that is no read is
    if path.startswith('/web/dataset/call_button') and register_serves(series):
        return register_call(series, reader, params.get('lang'), asof, str(payload.get('model') or ''),
                             str(payload.get('method') or ''), payload.get('args') or [], payload.get('kwargs') or {},
                             params.get('routes'))
    raise Refused('پیدا نشد.', 404)


# A REGISTER READ LIVE (design §10.2, §15.6; python/register.py): where daftard.json names a register for a garden and a
# series, the records of that series' client are the register's, asked of it on each call and kept nowhere; the views,
# the fields, the menus, the session and the reader's favourites stay the garden's (what it captured), and a properties
# field has no definitions here (a capture carries none: odoo_rpc's base_definitions_19). Who may read the register is
# who may read its bean, by the garden's own `may`. It is read by the routes daftard hands the call (the healthy ones,
# in order: internal/register), and what each route did goes back with the answer (REGISTER_NOTES).
LOCAL_CALLS = {'get_views', 'fields_get', 'get_filters', 'has_group', 'check_access_rights', 'has_access', 'check_access',
               'get_properties_base_definition'}
REGISTER_NOTES = []


def register_serves(series):
    import register
    conf = register.settings()
    return bool(conf) and str(conf.get('series') or '') == series


def register_call(series, reader, lang, asof, model, method, args, kw, routes=None):
    """One data call of the client, asked of the register as the reader may ask it, by the routes daftard handed it."""
    import register
    if asof:
        raise Refused('the register is read as it is now: its past is not in the garden', 409)
    try:
        r = register.Register(register.settings(), routes, REGISTER_NOTES)
        open_ = bool(PERSON.fullmatch(reader or '')) and _may(reader, 'read', r.bean).granted

        def fields(m):                                  # what the garden captured of a model: its own, or as a view shows it
            got = odoo_fields(series, m, lang if lang != 'en_US' else '')
            if got or m in odoo_models(series):
                return got
            return next((x[m] for x in (odoo_related(series, c) for c in odoo_models(series)) if m in x), {})
        zone = str(front(ROOT / 'GARDEN.md').get('zone') or '')
        return register.Reading(r, fields, open_, lang or 'en_US', zone).call(model, method, args, kw)
    except register.Refused as e:
        raise Refused(str(e), e.status) from None


ACTION_ID = re.compile(r'([a-z0-9][a-z0-9-]{0,120})\.([a-z0-9][a-z0-9-]{0,120})')


COURSES = r"""
import json, sys
root, bean = sys.argv[1], sys.argv[2]
sys.path[:0] = [root + '/bin', root]
import seq
got = seq.courses(root, bean) if hasattr(seq, 'courses') else None
print(json.dumps(got, default=str))
"""


def courses(params):
    """A being's courses as the garden's release reads them, in the one shape its archetype `course` draws (bin/seq.py
    `courses`, daftar 2.22): a course written, a clause's occurrences, a standing need — each with its steps, the step
    it stands at, since when, who acts, whether it is overdue, and its needs. A lead of a garden of the core opens here
    (a case of an agency opens its client's case). {id, title, summary, courses}; `courses` None where the release
    reads none (older than 2.22)."""
    bean = str(params.get('id') or '')
    if not SLUG.fullmatch(bean):
        raise Refused('no such being')
    r = subprocess.run([sys.executable, '-I', '-c', COURSES, str(ROOT), bean], cwd=ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=120)
    try:
        got = json.loads(r.stdout) if r.returncode == 0 else None
    except ValueError:
        got = None
    if r.returncode != 0:
        raise Refused('the garden could not read its courses: ' + (r.stderr.strip().splitlines() or [''])[-1][:300])
    path = bean_file(bean)
    summary = str(front(path).get('summary') or '') if path else ''
    return {'id': bean, 'title': title_of(bean), 'summary': summary, 'courses': got}


def action(params):
    """An action's run as its page shows it: where its course stands (bin/seq.py) and the plan it was shown, as captured
    (captures/actions/), for a person to ratify or decline. {bean, course, step, plan, captured}."""
    m = ACTION_ID.fullmatch(str(params.get('id') or ''))
    if not m:
        raise Refused('no such action')
    bean, course = m.groups()
    r = subprocess.run([sys.executable, str(ROOT / 'bin' / 'seq.py'), 'course', bean], cwd=ROOT, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=120)
    caps = sorted((ROOT / 'captures' / 'actions').glob(f"{bean}.{course}.plan.*.txt"),
                  key=lambda p: int(p.name.rsplit('.', 2)[-2]) if p.name.rsplit('.', 2)[-2].isdigit() else 0)
    plan = caps[-1].read_text(encoding='utf-8', errors='replace') if caps else ''
    stands = next((l for l in r.stdout.splitlines() if f'course {course} ' in l), r.stdout.strip()[-300:])
    return {'bean': bean, 'course': course, 'stands': stands, 'plan': plan,
            'captured': caps[-1].relative_to(ROOT).as_posix() if caps else ''}


def act(params):
    """Act on an action's run through the garden's own bin/act.py: `run` its engine's steps, or a person's `ratify` or
    `decline` of the plan they were shown — in the request's sitting, so the commit is theirs, signed."""
    m = ACTION_ID.fullmatch(str(params.get('id') or ''))
    do, who = str(params.get('do') or ''), str(params.get('who') or '')
    if not m or do not in ('run', 'ratify', 'decline') or (do != 'run' and not SLUG.fullmatch(who)):
        raise Refused('no such act')
    tool = ROOT / 'bin' / 'act.py'
    if not tool.is_file():
        raise Refused("this garden's release carries no bin/act.py")
    args = [sys.executable, str(tool), m.group(1), m.group(2)] + ([] if do == 'run' else [f'--{do}', who])
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=3600)
    said = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        exc = Refused(said.splitlines()[-1][:300] if said else 'the action did not run')
        exc.diagnostic = said
        raise exc
    return {'done': True, 'said': said[-600:]}


# ------------------------------------------------------------------------------------ routines: this machine's own
# THE GARDEN DECIDES, DAFTARD KEEPS THE CLOCK (internal/routines). What runs, when, on which machine, what it waits on
# and what proves it are the garden's statements, read by its own bin/routines.py and run by its own bin/act.py; this
# only calls them, with the machine's signing (`sign`, applied by the dispatcher) where daftard holds the machine's key.
# A release that carries no bin/routines.py is off, and says so once.
def _routines_tool():
    tool = ROOT / 'bin' / 'routines.py'
    return tool if tool.is_file() else None


def routines_tick(params):
    """The routines of this machine, once (bin/routines.py tick): what was started, read again or skipped."""
    tool = _routines_tool()
    if tool is None:
        return {'state': 'off', 'why': "this garden's release carries no bin/routines.py"}
    r = subprocess.run([sys.executable, str(tool), 'tick', '--json'], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=2900)
    if r.returncode != 0:
        return {'state': 'error', 'why': (r.stdout + r.stderr).strip()[-600:], 'done': []}
    try:
        return {'state': 'ran', 'done': json.loads(r.stdout or '[]')}
    except ValueError:
        return {'state': 'error', 'why': 'bin/routines.py tick printed no document', 'done': []}


def _cadence(listed):
    """The fastest numeric cadence of a tool's catalogue, in seconds (`on-change` keys are read when their work runs)."""
    got = [int(e['cadence']) for e in (listed or {}).get('catalogue') or []
           if isinstance(e, dict) and str(e.get('cadence', '')).isdigit()]
    return min(got) if got else 300


def probe_round(params):
    """Each tool this machine holds, probed where its catalogue's cadence says it is due: {tools: {tool: its document},
    read: [the tools read this round], why: {tool: why it was not}}. The documents are the tools' own `probe --json`
    (CONTRACT §2); daftard keeps them (internal/routines), and nothing here writes but the catalogue's copy."""
    tool = _routines_tool()
    d = Path(str(params.get('dir') or '')) if params.get('dir') else None     # Path('') is the garden: never written
    if tool is None or d is None or not d.is_dir():
        return {'tools': {}, 'read': [], 'why': {}}
    floor = max(5, int(params.get('every') or 30))
    r = subprocess.run([sys.executable, str(tool), 'tools', '--json'], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120)
    try:
        tools = json.loads(r.stdout) if r.returncode == 0 else []
    except ValueError:
        tools = []
    out, read, why = {}, [], {}
    now = time.time()
    for t in tools:
        name, path = str(t.get('tool') or ''), str(t.get('path') or '')
        if not SLUG.fullmatch(name) or not path:
            continue
        cmd = [sys.executable, path] if path.endswith('.py') else [path]
        listing = d / f".{name}.list.json"
        try:
            listed = json.loads(listing.read_text(encoding='utf-8')) if listing.is_file() and now - listing.stat().st_mtime < 86400 else None
        except (OSError, ValueError):
            listed = None
        if listed is None:
            try:
                lr = subprocess.run(cmd + ['probe', '--list', '--json'], capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', timeout=60)
                listed = json.loads(lr.stdout) if lr.stdout.strip().startswith('{') else {}
                listing.write_text(json.dumps(listed), encoding='utf-8')
            except (OSError, ValueError, subprocess.TimeoutExpired):
                listed = {}
        last = d / f"{name}.json"
        try:
            prev = json.loads(last.read_text(encoding='utf-8')) if last.is_file() else None
        except (OSError, ValueError):
            prev = None
        if prev is not None and now - last.stat().st_mtime < max(floor, _cadence(listed)):
            out[name] = prev
            continue
        try:
            pr = subprocess.run(cmd + ['probe', '--json'], capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=120)
            doc = json.loads(pr.stdout) if pr.stdout.strip().startswith('{') else None
        except (OSError, subprocess.TimeoutExpired) as e:
            doc, pr = None, None
            why[name] = f"its probe did not answer ({type(e).__name__})"
        if not isinstance(doc, dict) or not isinstance(doc.get('readings'), list):
            why.setdefault(name, f"its probe gave no readings (exit {getattr(pr, 'returncode', '?')})")
            if prev is not None:
                out[name] = prev
            continue
        out[name] = doc
        read.append(name)
    return {'tools': out, 'read': read, 'why': why}


def routines_cross(params):
    """The beings' needs read against the readings daftard keeps (bin/routines.py cross): what crossed, written once."""
    tool = _routines_tool()
    if tool is None:
        return {'done': []}
    files = [str(Path(f)) for f in params.get('readings') or []
             if isinstance(f, str) and f.endswith('.json') and Path(f).is_file() and not Path(f).name.startswith('.')]
    if not files:
        return {'done': []}
    r = subprocess.run([sys.executable, str(tool), 'cross', '--json'] + [a for f in files for a in ('--readings', f)],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1700)
    try:
        return {'done': json.loads(r.stdout or '[]')} if r.returncode == 0 else {'done': [], 'why': (r.stdout + r.stderr)[-600:]}
    except ValueError:
        return {'done': [], 'why': 'bin/routines.py cross printed no document'}


GONE = 'این مورد در صف تصمیم‌ها پیدا نشد؛ شاید پیش‌تر تصمیمش گرفته شده باشد.'


def _shown(v, depth=0):
    """A need's neighbourhood (its bean's `details.waiting.<id>`) as lines a person reads: its words where it carries
    them (a queue entry moved whole), else each key and what it holds."""
    if isinstance(v, dict):
        if isinstance(v.get('words'), str):
            return v['words']
        return '\n'.join(('  ' * depth) + f'{k}: ' + (_shown(x, depth + 1) if not isinstance(x, (dict, list))
                                                      else '\n' + _shown(x, depth + 1)) for k, x in v.items())
    if isinstance(v, list):
        return '\n'.join(('  ' * depth) + '- ' + _shown(x, depth + 1) for x in v)
    return str(v)


_SPACES = []


def bean_file(bean):
    """Where a bean is: the first of the garden's spaces that holds it (bin/garden.py SPACES — beans/ and mappings/ —
    as the garden's own release names them), or None."""
    if not _SPACES:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('garden_spaces', ROOT / 'bin' / 'garden.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _SPACES.extend(mod.SPACES)
        except Exception:
            _SPACES.extend(('beans', 'mappings'))
    return next((ROOT / space / f'{bean}.md' for space in _SPACES if (ROOT / space / f'{bean}.md').is_file()), None)


def need_landing(bean, need):
    """One need not met, as its landing page shows it: what it asks, whose it is, its class and strength, what blocks
    it, and its neighbourhood — read from the bean each time, so the address puts no words in the garden's mouth. Its
    digest is of its statement's line and its neighbourhood: a decision on what changed since it was shown is
    refused."""
    found = [x for x in waiting_needs() or [] if x['about'] == bean and x['need'] == need]
    path = bean_file(bean)
    if not found or path is None:
        raise Refused(GONE, 404)
    x, fm = found[0], front(path)
    waiting = (fm.get('details') or {}).get('waiting') if isinstance(fm.get('details'), dict) else None
    near = waiting.get(need) if isinstance(waiting, dict) else None
    line = next((ln for ln in path.read_text(encoding='utf-8').splitlines()
                 if re.match(r'\s*- need:', ln) and re.search(r'\bid: *["\']?' + re.escape(need) + r'["\']?\s*[,}]', ln)), '')
    near_text = _shown(near) if near is not None else ''
    fields = {'class': str(x.get('class') or ''), 'neighbourhood': near_text,
              'whose': ', '.join(str(p) for p in x.get('whose') or []),
              'for': ', '.join(str(p) for p in x.get('for') or []), 'strength': str(x.get('strength') or '')}
    if x.get('blocked_by'):
        fields['blocked_by'] = ', '.join(str(b) for b in x['blocked_by'])
    who = gardener()
    return {'slug': f'{bean}.{need}', 'need': need, 'about': bean, 'aboutTitle': str(x.get('title') or bean),
            'what': str(x.get('what') or ''), 'since': '', 'by': '', 'fields': fields, 'status': 'proposed',
            'digest': hashlib.sha256((line + '\n' + json.dumps(near, ensure_ascii=False, sort_keys=True, default=str))
                                     .encode('utf-8')).hexdigest(),
            'twice': False, 'text': line.strip() + ('\n\n' + near_text if near_text else ''), 'gardener': who,
            'gardenerTitle': title_of(who), 'mayMeet': who in (x.get('for') or []) and not x.get('blocked_by')}


def pending(params):
    slug = params.get('id') or ''
    m = NEED_LEAD.fullmatch(slug)
    if m:
        return need_landing(*m.groups())
    found = [e for e in pending_entries() if e['slug'] == slug]
    if SLUG.fullmatch(slug) and not found and bean_file(slug):
        needs = [x for x in waiting_needs() or [] if x['about'] == slug]   # the release's view names a decision by
        if needs:                                                           # its bean: the needs that wait on it
            return {'slug': slug, 'about': slug, 'aboutTitle': title_of(slug), 'status': 'list',
                    'needs': [{'id': f"{slug}.{x['need']}", 'title': str(x.get('what') or ''),
                               'class': str(x.get('class') or ''), 'strength': str(x.get('strength') or '')}
                              for x in needs]}
    if not SLUG.fullmatch(slug) or not found:
        raise Refused(GONE, 404)
    e = found[-1]
    lines = PENDING.read_text(encoding='utf-8').splitlines(keepends=True)[e['start']:e['end']]
    return {**{k: e[k] for k in ('slug', 'what', 'since', 'by', 'fields', 'status', 'digest')},
            'twice': len(found) > 1, 'text': ''.join(lines).strip(), 'gardener': gardener(),
            'gardenerTitle': title_of(gardener())}


def words_of(params, required):
    words = ' '.join(str(params.get('words') or '').split())
    if UNSAFE.search(words) or len(words) > 1000:
        raise Refused('متن شما نویسه‌ای دارد که در دفتر نوشته نمی‌شود، یا بیش از هزار نویسه است.')
    if required and not words:
        raise Refused('پاسخ خود را بنویسید.')
    return words                       # their words as they wrote them: quoted, never changed


def save_lock(wait=10):
    """The clone's save lock (bin/save.py `lock`, as the exchange takes it), waited for `wait` seconds."""
    end = time.monotonic() + wait
    while True:
        lock = xc.SaveLock(str(ROOT))
        try:
            lock.__enter__()
            return lock
        except xc.Busy:
            if time.monotonic() >= end:
                raise Refused(BUSY, 409)
            time.sleep(0.1)


# A REQUEST MADE IN A SITTING carries `sign`: the environment its commits are made with — authored as the person at
# the keyboard and signed with their key, whose passphrase ssh-keygen asks of daftard (internal/sitting). It holds for
# that one request: the worker answers one request at a time, and puts the environment back before the next. Only
# these names are taken; anything else a request carries is not the worker's to set.
SIGNING = ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL', 'GIT_CONFIG_COUNT',
           'GIT_CONFIG_KEY_0', 'GIT_CONFIG_VALUE_0', 'GIT_CONFIG_KEY_1', 'GIT_CONFIG_VALUE_1', 'GIT_CONFIG_KEY_2',
           'GIT_CONFIG_VALUE_2', 'SSH_ASKPASS', 'SSH_ASKPASS_REQUIRE', 'DAFTARD_ASKPASS', 'DISPLAY')


class signed:
    """The request's commits are the sitting person's while it runs: `sign` applied to the environment, and taken
    back after, whatever happened."""

    def __init__(self, sign):
        self.sign = {k: str(v) for k, v in (sign or {}).items() if k in SIGNING}
        self.before = {}

    def __enter__(self):
        self.before = {k: os.environ.get(k) for k in self.sign}
        os.environ.update(self.sign)
        return self

    def __exit__(self, *exc):
        for k, v in self.before.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def author():
    """Who a commit the handplace makes is by: the sitting's person where the request carries one, else the handplace."""
    name = os.environ.get('GIT_AUTHOR_NAME') if os.environ.get('DAFTARD_ASKPASS') else None
    email = os.environ.get('GIT_AUTHOR_EMAIL') if name else None
    return (name, email) if name and email else ('Daftar handplace', 'daftard@localhost')


def run_save(who, what, body):
    """bin/save.py in the gardener's name, committed by the handplace, or by the person sitting at it; (ok, what it
    said)."""
    name, email = author()
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
               GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
    r = subprocess.run([sys.executable, str(ROOT / 'bin' / 'save.py'), who, what, '--body', *body], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    return r.returncode == 0, r.stdout + r.stderr


def already(rid):
    """The commit a request already made (a retry after a lost answer saves nothing twice), or ''."""
    return git('log', '-1', '--format=%H', '--fixed-strings', '--grep=handplace-request:' + rid)


def request_id(params):
    try:
        return uuid.UUID(str(params.get('request'))).hex
    except ValueError:
        raise Refused('شناسهٔ درخواست معتبر نیست.')


def refused_save(said):
    lines = [' '.join(l.split()) for l in said.splitlines() if l.strip()]
    first = next((l for l in lines if not l.startswith('save:')), None) or next(iter(lines), '')
    r = Refused('دفتر این تصمیم را نپذیرفت؛ چیزی تغییر نکرد. دلیل: ' + first[:300], 422)
    r.diagnostic = said
    return r


def decide_pending(params):
    """The gardener's decision on one parked entry: `acked` (the proposal ratified as it stands, with their words if
    they gave any) or `answered` (their words written under it; it stays proposed, for whoever proposed it). Written
    into the entry, as the queue's own entries are acked, and saved with its journal entry in their name."""
    rid, decision = request_id(params), params.get('decision')
    if decision not in ('acked', 'answered'):
        raise Refused('تصمیم معتبر نیست.')
    m = NEED_LEAD.fullmatch(str(params.get('id') or ''))
    if m:
        return meet_need(params, rid, decision, *m.groups())
    words = words_of(params, required=decision == 'answered')
    prior = already(rid)
    if prior:
        return {'saved': True, 'commit': prior, 'duplicate': True}
    who = gardener()
    lock = save_lock()
    before = None
    try:
        if git('status', '--porcelain'):
            raise Refused(BUSY, 409)
        found = [e for e in pending_entries() if e['slug'] == params.get('id')]
        if len(found) != 1 or found[0]['digest'] != params.get('digest'):
            raise Refused(STALE, 409)
        e = found[0]
        if e['status'] != 'proposed':
            raise Refused('تصمیم این مورد پیش‌تر گرفته شده است.', 409)
        before = PENDING.read_bytes()
        lines = before.decode('utf-8').splitlines(keepends=True)
        body = lines[e['start']:e['end']]
        tail = len(body)
        while tail > 1 and not body[tail - 1].strip():
            tail -= 1
        said = f'"{words}"' if words else ''
        if decision == 'acked':
            mark = f'{who} (gardener), on the handplace' + (f': {said}' if said else '')
            out, marked = [], False
            for line in body[:tail]:
                m = FIELD.match(line)
                if m and m.group(1) == 'status':
                    out.append('- status: acked\n')
                elif m and m.group(1) == 'acked_by':
                    out.append(f'- acked_by: {mark}\n')
                    marked = True
                else:
                    out.append(line)
            if not marked:
                i = next(i for i, l in enumerate(out) if l.startswith('- status:'))
                out.insert(i + 1, f'- acked_by: {mark}\n')
        else:
            out = body[:tail] + [f'- answer: {who} (gardener), on the handplace, {time.strftime("%Y-%m-%d")}: {said}\n']
        if not out[-1].endswith('\n'):
            out[-1] += '\n'
        lines[e['start']:e['end']] = out + body[tail:]
        safe.write_atomic(str(PENDING), ''.join(lines).encode('utf-8'))
    except Exception:
        if before is not None:
            safe.write_atomic(str(PENDING), before)
        raise
    finally:
        lock.__exit__(None, None, None)         # bin/save.py takes it itself
    what = (f'Ratified {e["slug"]}' if decision == 'acked' else f'Answered {e["slug"]}') + f'; handplace-request:{rid}'
    note = [f'- decision: {who} ' + ('ratified the proposal parked as' if decision == 'acked' else
                                     'answered, without ratifying, the proposal parked as') +
            f' {e["slug"]} in log/pending.md (class {e["fields"].get("class", "unstated")}).',
            '- via: the handplace (daftard), the gardener\'s own decision on the landing page.']
    if words:
        note.append(f'- words: {said}')
    ok, said_save = run_save(who, what, note)
    if not ok:
        with_lock = save_lock(60)
        try:
            if not already(rid):            # its commit was not made after all
                git('reset', '-q', 'HEAD', '--', 'log/pending.md', 'log/journal.md')
                safe.write_atomic(str(PENDING), before)
                unjournal(rid)
        finally:
            with_lock.__exit__(None, None, None)
        raise refused_save(said_save)
    return {'saved': True, 'commit': git('rev-parse', 'HEAD')}


def judged_alone(bean, mid):
    """The read-back of a meet: the bean read again, and the `meet` written (`mid`) and the `say` knowing it each judged
    alone as the gate judges a statement in its bean, by the one judge (core/judge.py `statement`, from core 4.11, the
    door of a write's read-back): ['<rule>: <what>']. Where the garden's judge has no such door, nothing is judged here,
    and its gate judges the commit whole all the same."""
    try:
        from core import engine, judge as dmjudge
        from core.check import garden_law
    except ImportError:
        return []
    if not hasattr(dmjudge, 'statement'):
        return []
    G = engine.Garden.read(str(ROOT))
    b = G.beans.get(bean)
    if b is None:
        return [f'read: {bean} does not read back']
    L = garden_law(str(ROOT))
    J = engine.Judge(L, G)
    ours = [(i, v, r) for i, v, r in b.items if isinstance(r, dict)
            and ((v == 'meet' and r.get('id') == mid) or (v == 'say' and r.get('of') == [mid]))]
    if len(ours) != 2:
        return [f'read: `meet#{mid}` and the `say` knowing it do not read back from {bean}']
    return [f'{rule}: {msg}' for i, v, r in ours for rule, _where, msg in dmjudge.statement(L, G, b, i, v, r, by=J)]


def meet_need(params, rid, decision, bean, need):
    """The gardener meets one need on its bean, as the law writes it (bin/waiting.py: `- meet: { by: <person>, of:
    <id> }`, known by that person's `say`, their words its note), saved with its journal entry in their name, and
    refused where it changed since the page showed it, waits for someone else, or waits on another need first. A
    need is met or not: words without meeting it are written where it was parked, not here."""
    if decision != 'acked':
        raise Refused('نیاز یا برآورده می‌شود یا منتظر می‌ماند؛ پاسخی بی‌آنکه برآورده شود، در پروندهٔ خودش نوشته می‌شود.')
    words = words_of(params, required=False)
    prior = already(rid)
    if prior:
        return {'saved': True, 'commit': prior, 'duplicate': True}
    who = gardener()
    lock = save_lock()
    path = before = view = None
    try:
        if git('status', '--porcelain'):
            raise Refused(BUSY, 409)
        land, path = need_landing(bean, need), bean_file(bean)
        if land['digest'] != params.get('digest'):
            raise Refused(STALE, 409)
        f = land['fields']
        if f.get('blocked_by'):
            raise Refused('این نیاز نخست منتظر ' + f['blocked_by'] + ' است.', 409)
        if not land['mayMeet']:
            raise Refused('این نیاز منتظر ' + (f['for'] or '؟') + ' است، نه شما.', 403)
        ids = {str(r.get('id')) for st in front(path).get('statements') or [] if isinstance(st, dict)
               for r in st.values() if isinstance(r, dict) and r.get('id')}
        mid = next(m for m in [f'{need}-met'] + [f'{need}-met-{n}' for n in range(2, 100)] if m not in ids)
        before, view = path.read_bytes(), PENDING.read_bytes() if PENDING.exists() else None
        note = f', note: {json.dumps(words, ensure_ascii=False)}' if words else ''
        safe.add_statements(str(path), f'- meet: {{ id: {mid}, by: {who}, of: {need} }}\n'
                                       f'- say: {{ by: {who}, of: [{mid}], at: now{note} }}\n')
        found = judged_alone(bean, mid)
        if found:
            r = Refused('دفتر این تصمیم را نپذیرفت؛ چیزی تغییر نکرد. دلیل: ' + found[0][:300], 422)
            r.diagnostic = '\n'.join(found)
            raise r
    except Exception:
        if before is not None:
            safe.write_atomic(str(path), before)
        raise
    finally:
        lock.__exit__(None, None, None)         # bin/save.py takes it itself
    what = f'Met {bean}#{need}; handplace-request:{rid}'
    note = [f'- decision: {who} met the need {bean}#{need} (class {land["fields"]["class"] or "unsaid"}): {land["what"]}',
            '- via: the handplace (daftard), the gardener\'s own decision on the landing page.']
    if words:
        note.append(f'- words: "{words}"')
    ok, said_save = run_save(who, what, note)
    if not ok:
        with_lock = save_lock(60)
        try:
            if not already(rid):            # its commit was not made after all
                git('reset', '-q', 'HEAD', '--', str(path.relative_to(ROOT)), 'log/pending.md', 'log/journal.md')
                safe.write_atomic(str(path), before)
                if view is not None:
                    safe.write_atomic(str(PENDING), view)
                elif PENDING.exists():
                    PENDING.unlink()
                unjournal(rid)
        finally:
            with_lock.__exit__(None, None, None)
        raise refused_save(said_save)
    return {'saved': True, 'commit': git('rev-parse', 'HEAD')}


def unjournal(rid):
    """The journal without this request's entry, every other entry as it stands."""
    journal = ROOT / 'log' / 'journal.md'
    out, ours = [], False
    for line in journal.read_text(encoding='utf-8').splitlines(keepends=True):
        if line.startswith('## '):
            ours = ('handplace-request:' + rid) in line
        if not ours:
            out.append(line)
    safe.write_atomic(str(journal), ''.join(out).encode('utf-8'))


def proposal_file(params):
    d, _last = exchange_state()
    name = params.get('id') or ''
    if not d or not PROPOSAL.fullmatch(name):
        raise Refused('این پیشنهاد پیدا نشد.', 404)
    for where in ('inbox', 'held'):
        f = d / where / (name + '.md')
        if f.exists():
            return d, where, f
    if (d / 'done' / (name + '.md')).exists():
        raise Refused('این پیشنهاد پیش‌تر در دفتر گرفته شده است.', 409)
    raise Refused('این پیشنهاد پیدا نشد.', 404)


def peer_of(B, garden_id):
    return next((b for b, fm in B.items() if xc.garden_id_of(fm) == garden_id), None)


def proposal(params):
    """One proposal from another garden: who sent it, under which agreement, each bean it carries (with the bean
    here it would fuse with), why it waits, and, asked with `check`, what bin/propose.py `read` says of taking it."""
    d, where, f = proposal_file(params)
    e = xc.envelope(f)
    B = xc.beans(str(ROOT))
    peer = peer_of(B, e['from'])
    carried = xc.offered(f)
    out = {'id': f.stem, 'where': where, 'from': e['from'], 'fromName': e['name'], 'peer': peer,
           'peerTitle': title_of(peer) if peer else '', 'under': e['under'], 'fingerprint': e['fingerprint'],
           'beans': [{'id': b, 'title': str((carried.get(b) or {}).get('title') or b),
                      'here': b in B, 'hereTitle': title_of(b) if b in B else ''} for b in e['beans']],
           'why': '', 'gardener': gardener(), 'gardenerTitle': title_of(gardener())}
    why = d / 'held' / (f.stem + '.why.txt')
    if where == 'held' and why.exists():
        out['why'] = why.read_text(encoding='utf-8').strip()[-3000:]
    if params.get('check'):
        r = xc.tool(str(ROOT), 'bin/propose.py', 'read', str(f), timeout=600)
        out['read'] = {'ok': r.returncode == 0, 'said': (r.stdout + r.stderr).strip()[-6000:]}
    return out


def take_proposal(params):
    """The gardener's yes to ONE proposal no standing consent covers (or one set aside, read again): read, taken
    and saved in their name, exactly as an exchange round takes one under a consent (exchange/exchange.py)."""
    rid = request_id(params)
    prior = already(rid)
    if prior:
        return {'saved': True, 'commit': prior, 'duplicate': True}
    d, where, f = proposal_file(params)
    e = xc.envelope(f)
    if e['fingerprint'] != params.get('fingerprint'):
        raise Refused(STALE, 409)
    B = xc.beans(str(ROOT))
    peer = peer_of(B, e['from'])
    if not peer:
        raise Refused('این پیشنهاد از دفتری است که این دفتر هنوز نمی‌شناسد؛ نخستین آشنایی دو دفتر (رده F) '
                            'باید جدا ثبت شود. با نگه‌دارندهٔ دفتر پیگیری کنید.', 409)
    ours = [b for b in e['beans'] if b in B and not xc.taken_from(B[b], peer)]
    if ours:
        raise Refused('این پیشنهاد پرونده‌هایی را می‌آورد که در همین دفتر ساخته شده‌اند ('
                            + '، '.join(ours) + ')؛ هر پرونده فقط از دفتری که در آن ساخته شده می‌آید.', 409)
    who = gardener()
    lock = save_lock()
    try:
        if git('status', '--porcelain'):
            raise Refused(BUSY, 409)
        r = xc.tool(str(ROOT), 'bin/propose.py', 'read', str(f), timeout=600)
        if r.returncode:
            x = Refused('دفتر این پیشنهاد را نمی‌پذیرد؛ چیزی تغییر نکرد. جزئیات «بررسی» را ببینید.', 422)
            x.diagnostic = r.stdout + r.stderr
            raise x
        t = xc.tool(str(ROOT), 'bin/propose.py', 'take', str(f), timeout=600)
        if t.returncode:
            xc.restore(str(ROOT))
            x = Refused('گرفتن این پیشنهاد ممکن نشد؛ چیزی تغییر نکرد.', 422)
            x.diagnostic = t.stdout + t.stderr
            raise x
    finally:
        lock.__exit__(None, None, None)
    body = [f'- ratified_by: {who}, on the handplace (daftard), for this proposal of {peer} alone'] + \
        xc.journal_lines(t.stdout)
    ok, said = run_save(who, f"Took {', '.join(e['beans'])} from {peer}; handplace-request:{rid}", body)
    if not ok:
        relock = save_lock(60)
        try:
            if not already(rid):
                xc.restore(str(ROOT))     # it began on a clean tree: nothing else is lost
        finally:
            relock.__exit__(None, None, None)
        raise refused_save(said)
    shutil.move(str(f), str(d / 'done' / f.name))
    return {'saved': True, 'commit': git('rev-parse', 'HEAD')}


def may_send(params):
    """Whether the garden's flow law grants a lead's notice to leave the machine for `party`: a `send` from the estate
    to a remote party, which the core's row `sent-out` refuses until a garden's own row grants that party
    (core/law/flows.yaml; a RULE-CHANGE). {granted, grant, rows}."""
    party = str(params.get('party') or '')
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from core.check import garden_law
        ok, grant, rows = garden_law(str(ROOT)).decide('estate', 'remote', 'send', party=party or None)
        return {'granted': bool(ok), 'grant': grant, 'rows': list(rows)}
    except Exception as exc:       # a garden this cannot judge grants nothing
        return {'granted': False, 'grant': 'unread', 'rows': [], 'why': str(exc)[:200]}


def clock(params):
    """What this machine's time sources show of its clock, as the garden's own `bin/clock.py` reads it (core 1.1): {may,
    lines}; {may: None} where the garden's release has no clock check yet."""
    tool = ROOT / 'bin' / 'clock.py'
    if not tool.is_file():
        return {'may': None, 'lines': []}
    r = subprocess.run([sys.executable, str(tool)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=30)
    return {'may': r.returncode == 0, 'lines': [l for l in r.stdout.splitlines() if l.strip()]}


# A SAVE THE CLOCK REFUSED (core 1.1: no stamp from a clock not shown within half a minute of its sources) is no
# refusal of what the person wrote: it is the machine's, and its keeper's to set right. It is answered as such, the
# clock's own sentence its message, so the page says what to do and whom to ask.
STAMP_REFUSED = re.compile(r'NOT STAMPED: (.*?)(?: — nothing written)?$', re.M)


def clock_refusal(text):
    """The clock's sentence where `text` is a save the clock refused, else None."""
    m = STAMP_REFUSED.search(text or '')
    return m.group(1).strip() if m else None


def person(params):
    """{id, title, mail}: how a person of this garden is called and their mail, read from their bean through the
    garden's own parser — what a commit made in their sitting is authored as. `mail` is empty where the bean names none."""
    pid = str(params.get('id') or '')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', pid):
        raise Refused('no such person')
    path = ROOT / 'beans' / (pid + '.md')
    if not path.is_file():
        raise Refused('no such person')
    parse = _garden_parse()
    fm = parse.loads(parse.split_front_matter(path.read_text(encoding='utf-8'))[0]) or {}
    mail = ''
    for st in fm.get('statements') or []:
        if isinstance(st, dict) and len(st) == 1:
            verb, roles = next(iter(st.items()))
            if verb == 'name' and isinstance(roles, dict) and roles.get('by') == 'mail' and 'held' not in roles \
                    and isinstance(roles.get('as'), str):
                mail = roles['as']
                break
    return {'id': pid, 'title': str(fm.get('title') or pid), 'mail': mail}


METHODS = {f.__name__: f for f in (hello, session_info, payload, books, history, calendar, view_html, view_pages, view_page,
                                   view_style, view_write, view_act, prefs_check, prefs_zones, prefs_bean, prefs_from_bean,
                                   save, sync_step,
                                   exchange_round, follow_up, leads, pending, decide_pending, proposal, take_proposal,
                                   person, clock, may_send, action, courses, act, sync_merge, served_person, served_read,
                                   served_leads, served_forms, served_submit, form_answers, take_form,
                                   served_passkeys, passkey_lay, passkey_laid, take_passkey, odoo_session, odoo_rpc,
                                   odoo_asof, routines_tick, probe_round, routines_cross, board_aspects,
                                   board_lens, board_being, board_find)}


def answer(rid, ok, value):
    out = {'id': rid, 'ok': ok, ('result' if ok else 'error'): value}
    if REGISTER_NOTES:                   # what the register's routes did in this call, for daftard: never a record
        out['register'] = list(REGISTER_NOTES)
    OUT.write(json.dumps(out, ensure_ascii=False, default=str) + '\n')
    OUT.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rid = None
        REGISTER_NOTES.clear()
        try:
            req = json.loads(line)
            rid = req.get('id')
            fn = METHODS.get(req.get('method'))
            if fn is None:
                answer(rid, False, {'status': 404, 'message': 'unknown method', 'kind': 'failed'})
                continue
            params = req.get('params') or {}
            with signed(params.pop('sign', None) if isinstance(params, dict) else None):
                answer(rid, True, fn(params))
        except Refused as exc:
            said = clock_refusal(getattr(exc, 'diagnostic', None) or '') or clock_refusal(str(exc))
            if said:
                answer(rid, False, {'status': 503, 'message': said, 'kind': 'clock',
                                    'diagnostic': getattr(exc, 'diagnostic', None) or str(exc)})
                continue
            answer(rid, False, {'status': getattr(exc, 'status', 400), 'message': str(exc), 'kind': 'refused',
                                'diagnostic': getattr(exc, 'diagnostic', None) or ''})
        except Exception as exc:     # the person is told it did not go ahead; the whole of it goes with the reference
            answer(rid, False, {'status': 500, 'message': str(exc)[-300:], 'kind': 'failed',
                                'diagnostic': traceback.format_exc()})


if __name__ == '__main__':
    os.environ.setdefault('PYTHONUTF8', '1')
    main()
