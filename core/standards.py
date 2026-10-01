"""standards — what the outside standards say, read from the release that carries them, by the tools that read them.

The core hardcodes no system of positions, no unit and no code (spec §13). They come from the standards the release
already carries, read here once and by today's readers, so the new engine and today's gate cannot disagree about them:

  positions   the systems of `anchor_systems` (ISO 8601 and the CLDR calendars, EPSG, IANA ports, RFC 3986, the
              filesystems…), each with its one form — judged by dmparse.in_form, the one judge of a form
  quantities  the law's `quantities` and `units` (whose UCUM codes are core/law/units.yaml's), and the currencies of
              ISO 4217 (`seed/knowledge/currencies.tsv`) with their names; a count is read exactly by dmunits.exact
  protocols   the IANA-named rows of `net_protocols`
  codes       the schemes of our knowledge tree, through dmknowledge (ISCO-08, ISCED-F 2013, the technologies…)
  zones       the IANA time zones (`seed/knowledge/time-zones.tsv`)

A garden adds rows of its own to these tables in its VOCAB.md (`tables:`), which `law.Law` joins to them."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse      # noqa: E402 — today's reader of today's law, and the one judge of a system's form
import dmunits      # noqa: E402 — a count, read exactly
import dmknowledge  # noqa: E402 — the one finder of a code of a scheme


class Standards:
    def __init__(self, root=ROOT):
        self.root = root
        path = os.path.join(root, 'seed', 'std-vocab.md')
        with open(path, encoding='utf-8') as fh:
            law = dmparse.loads(dmparse.split_front_matter(fh.read())[0]) or {}
        self.old = law                      # today's law as its own reader reads it: the profiles it offers, its rows
        self.systems = {str(r['system']): r for r in law.get('anchor_systems') or [] if isinstance(r, dict) and r.get('system')}
        self.protocols = {str(r['protocol']) for r in law.get('net_protocols') or [] if isinstance(r, dict) and r.get('protocol')}
        self.quantities = {str(q['quantity']) for q in law.get('quantities') or [] if isinstance(q, dict) and q.get('quantity')}
        # the law's units by their English names (the core writes them in UCUM: core/law/units.yaml), and the
        # currencies of ISO 4217 by their codes, each with its name
        self.units = {str(u['unit']): str(u['quantity']) for u in law.get('units') or [] if isinstance(u, dict) and u.get('unit')}
        self.currencies = {}
        files = {r.get('registry'): r.get('file') for r in law.get('registry_files') or [] if isinstance(r, dict)}
        for q in law.get('quantities') or []:
            uf = q.get('units_from') if isinstance(q, dict) and isinstance(q.get('units_from'), dict) else None
            if uf and files.get(uf.get('registry')):
                for row in self._tsv(files[uf['registry']]):
                    if row.get(uf.get('take')):
                        self.currencies.setdefault(row[uf['take']], row.get('name', ''))
        self.zones = {r['zone'] for r in self._tsv(files.get('time-zones') or 'seed/knowledge/time-zones.tsv') if r.get('zone')}
        self.knowledge = dmknowledge.Knowledge(root)

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
    """The standards of the release at `root`, read once per process."""
    if root not in _ONE:
        _ONE[root] = Standards(root)
    return _ONE[root]
