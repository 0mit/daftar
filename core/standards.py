"""standards — what the outside standards say, read from the core's law that carries them, by the tools that read them.

The core hardcodes no system of positions, no unit and no code (spec §13). They come from the standards the release
carries in core/law/ (generated from std-vocab until v1 retires it: core/translate.py), read here once, every value a
string as written, so the new engine and today's gate cannot disagree about them:

  positions   the systems of `systems.yaml` (ISO 8601 and the CLDR calendars, EPSG, IANA ports, RFC 3986, the
              filesystems…), each with its one form — judged by dmparse.in_form, the one judge of a form
  quantities  the quantities of `quantities.yaml`, whose units are units.yaml's in UCUM, and the currencies of ISO 4217
              (`seed/knowledge/currencies.tsv`, by `registries.yaml`) with their names; a count is read exactly by
              dmunits.exact
  protocols   the IANA-named rows of `protocols.yaml`
  codes       the schemes of our knowledge tree (`registries.yaml`), through dmknowledge (ISCO-08, ISCED-F 2013, the
              technologies…), with the schemes a garden holds as its own
  zones       the IANA time zones (`seed/knowledge/time-zones.tsv`)

A garden carries the release's core/law/ from v0.49.0 on; one that does not yet reads this release's. A garden adds rows
of its own to these tables in its VOCAB.md (`tables:`), which `law.Law` joins to them."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import dmparse      # noqa: E402 — the one judge of a system's form, and the one splitter of a coding
import dmunits      # noqa: E402 — a count, read exactly
import dmknowledge  # noqa: E402 — the one finder of a code of a scheme

FILES = ('systems', 'places', 'protocols', 'quantities', 'registries')   # core/law/<name>.yaml: a standard's tables


class Standards:
    def __init__(self, root=ROOT):
        self.root = root
        law = os.path.join(root, 'core', 'law')
        self.law_dir = law if os.path.isfile(os.path.join(law, 'systems.yaml')) else os.path.join(ROOT, 'core', 'law')
        self.tables = {}                    # every standard's table by the core's name of it, its rows as written
        for name in FILES:
            for table, rows in read.data(os.path.join(self.law_dir, name + '.yaml')).items():
                if table != 'forms':
                    self.tables[table] = rows
        self.systems = self._keyed('systems', 'system')
        self.protocols = self._keyed('protocols', 'protocol')
        self.quantities = self._keyed('quantities', 'quantity')
        # the currencies of ISO 4217 by their codes, each with its name: the units of the quantity whose units are a
        # registry's rows (`units_from`)
        self.currencies = {}
        files = {r.get('registry'): r.get('file') for r in self.tables.get('registry_files') or [] if isinstance(r, dict)}
        for q in self.quantities.values():
            uf = q.get('units_from') if isinstance(q.get('units_from'), dict) else None
            if uf and files.get(uf.get('registry')):
                for row in self._tsv(files[uf['registry']]):
                    if row.get(uf.get('take')):
                        self.currencies.setdefault(row[uf['take']], row.get('name', ''))
        self.zones = {r['zone'] for r in self._tsv(files.get('time-zones') or 'seed/knowledge/time-zones.tsv') if r.get('zone')}
        self.knowledge = dmknowledge.Knowledge(root, law={k: self.tables.get(k) or [] for k in ('registry_files',
                                                                                              'knowledge_schemes')})
        self._old = None

    def _keyed(self, table, key):
        return {str(r[key]): r for r in self.tables.get(table) or [] if isinstance(r, dict) and r.get(key)}

    @property
    def old(self):
        """Today's law as its own reader reads it, for what has not moved into core/law/ yet: the profiles a release
        offers (core/commit.py reads seed/LANGUAGE's profile lines by them). The garden's, else this release's."""
        if self._old is None:
            path = os.path.join(self.root, 'seed', 'std-vocab.md')
            path = path if os.path.isfile(path) else os.path.join(ROOT, 'seed', 'std-vocab.md')
            with open(path, encoding='utf-8') as fh:
                self._old = dmparse.loads(dmparse.split_front_matter(fh.read())[0]) or {}
        return self._old

    def _tsv(self, rel):
        try:
            with open(os.path.join(self.root, rel), encoding='utf-8') as fh:
                return list(csv.DictReader(fh, delimiter='\t'))
        except OSError:
            return []

    def code(self, value):
        """'' when `value` is a code of a scheme the knowledge tree holds (`<scheme>:<code>`), else why it is not."""
        scheme, code = dmparse.split_coding(value)
        if scheme is None:
            return f"{value!r} is not a code written with its scheme, `<scheme>:<code>`"
        if scheme not in self.knowledge.schemes:
            return f"{scheme!r} is no scheme of the knowledge tree: one of {', '.join(sorted(self.knowledge.schemes))}"
        try:
            row = self.knowledge.row(scheme, code)
        except (KeyError, OSError) as e:
            return f"the scheme {scheme} cannot be read here: {e}"
        return '' if row else f"{code!r} is no code of {scheme}"

    def count(self, text):
        """The count `text` as an exact Fraction, or None when it is not written as one (plain decimal digits)."""
        try:
            return dmunits.exact(text)
        except ValueError:
            return None


_ONE = {}


def here(root=ROOT):
    """The standards of the release at `root` (a garden: its own core/law/, else this release's), read once per
    process."""
    if root not in _ONE:
        _ONE[root] = Standards(root)
    return _ONE[root]


def carried(root):
    """True when the garden at `root` carries a law of its own: the core's (core/law/), or today's (seed/std-vocab.md),
    beside which its seed/knowledge/ and its own schemes are read."""
    return os.path.isfile(os.path.join(root, 'core', 'law', 'systems.yaml')) \
        or os.path.isfile(os.path.join(root, 'seed', 'std-vocab.md'))
