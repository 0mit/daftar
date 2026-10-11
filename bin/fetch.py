#!/usr/bin/env python3
"""fetch — bring a standard's table from its provider to this machine: a scheme the law holds `fetched`
(core/law/registries.yaml, `knowledge_schemes`), downloaded from where its row's `fetch.from` says, into a cache outside
git, and read into the rows its `registry_files` file holds.

    python3 bin/fetch.py <scheme>                 # download it from its provider, and read it
    python3 bin/fetch.py <scheme> --from <file>   # a copy at hand: one this machine's person downloaded from the
                                                  # provider, or a peer's unchanged copy where the scheme's licence
                                                  # allows unchanged copies to be handed on
    python3 bin/fetch.py --list                   # what this machine has fetched, each copy by its SHA-256

DAFTAR SHIPS NO ONE ELSE'S TABLE where the provider's terms do not let it: each machine reaches the provider itself,
under the provider's terms, and keeps the provider's file unchanged beside the rows read from it. The cache is this
machine's, never the garden's: `DAFTAR_STANDARDS_CACHE`, else `%LOCALAPPDATA%\\daftar\\standards` on Windows, else
`$XDG_CACHE_HOME/daftar/standards` (`~/.cache/daftar/standards`). Each copy is kept under the SHA-256 of the provider's
file: `<scheme>/<sha-256>/source.<ext>`, `rows.tsv` and `fetched.json` (from where, when, how many rows). A garden reads
a fetched scheme's codes from the newest copy here (bin/knowledge.py), and from the release's copy while it carries one.

Nothing is sent but the request for the provider's file. Print the line it prints into the save's entry: what was
read, from where, and its SHA-256, so the garden says which copy its codes were read against.
"""
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr


class Refused(Exception):
    """Why a table was not fetched or not read: said to the person, and nothing is kept."""


def cache_dir():
    """Where this machine keeps what it fetched — outside every garden."""
    if os.environ.get('DAFTAR_STANDARDS_CACHE'):
        return os.environ['DAFTAR_STANDARDS_CACHE']
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        return os.path.join(os.environ['LOCALAPPDATA'], 'daftar', 'standards')
    return os.path.join(os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache'),
                        'daftar', 'standards')


# ------------------------------------------------------------------------------------------------ the readers
def _openpyxl():
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        raise Refused("the provider's file is a spreadsheet (xlsx), and openpyxl, which reads one, is not installed "
                      "here (`pip install openpyxl`)") from None


def ilo_isco_08_xlsx(data):
    """The ILO's ISCO-08 structure (`ISCO-08 EN Structure and definitions.xlsx`): its first sheet, one row a group —
    `Level` (1 to 4), `ISCO 08 Code`, `Title EN` — read into code, level, parent and name_en. The definitions, tasks and
    occupations it also holds are the ILO's text, and are not read."""
    wb = _openpyxl().load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    sheet = wb.worksheets[0]
    rows = sheet.iter_rows(values_only=True)
    head = [str(c).strip() if c is not None else '' for c in next(rows, ())]
    want = ('Level', 'ISCO 08 Code', 'Title EN')
    if any(w not in head for w in want):
        raise Refused(f"the ILO's file has not the columns read here ({', '.join(want)}): its first row is "
                      f"{', '.join(h for h in head if h)[:200]}")
    at = {w: head.index(w) for w in want}
    levels = {'1': 'major', '2': 'sub-major', '3': 'minor', '4': 'unit'}
    out = []
    for r in rows:
        if not r or all(c is None for c in r):
            continue
        level, code, title = (str(r[at[w]]).strip() if r[at[w]] is not None else '' for w in want)
        level = level[:-2] if level.endswith('.0') else level
        if level not in levels or not code.isdigit() or len(code) != int(level) or not title:
            raise Refused(f"a row of the ILO's file is no group read here: level {level!r}, code {code!r}")
        out.append({'code': code, 'level': levels[level], 'parent': code[:-1], 'name_en': title})
    if not out:
        raise Refused("the ILO's file holds no group")
    return out


def _head(cells):
    """A header row's cells as words: a cell's line breaks and the spreadsheet's escaped carriage returns are spaces."""
    return [' '.join(str(c).replace('_x000D_', ' ').split()) if c is not None else '' for c in cells]


# UN/CEFACT's marks in a code's `Status`, as Recommendation 20 has used them: `X` a code marked deleted, `D` deprecated.
# The others (an entry added, renamed, changed) say what moved in the revision, not whether the code stands.
REC20_STATUS = {'X': 'deleted', 'D': 'deprecated'}


def unece_rec20_xlsx(data):
    """UN/CEFACT's Recommendation No. 20 (`rec20_Rev<N>e-<year>.xlsx`): its sheet of every code, one row a code
    (Annexes II and III) — `Status`, `Common Code`, `Name`, `Symbol` — read into code, status, name_en and symbol, the
    status `deleted` (`X`) or `deprecated` (`D`), another mark as written, and none where the code stands. Annex I, which
    lists a code once for each quantity it measures (its `Quantity`), is not that sheet. The descriptions, levels and
    conversion factors the file also holds are UNECE's text, and are not read."""
    wb = _openpyxl().load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    want = ('Status', 'Common Code', 'Name', 'Symbol')
    sheets = []
    for sheet in wb.worksheets:
        rows = sheet.iter_rows(values_only=True)
        head = _head(next(rows, ()))
        if all(w in head for w in want) and 'Quantity' not in head:
            sheets.append((sheet, rows, head))
    if len(sheets) != 1:
        raise Refused(f"{len(sheets)} sheets of UNECE's file list every code once with the columns read here "
                      f"({', '.join(want)}), and one is read: its sheets are {', '.join(s.title for s in wb.worksheets)}")
    sheet, rows, head = sheets[0]
    at = {w: head.index(w) for w in want}
    out, seen = [], set()
    for r in rows:
        if not r or all(c is None for c in r):
            continue
        status, code, name, symbol = (' '.join(str(r[at[w]]).split()) if at[w] < len(r) and r[at[w]] is not None
                                      else '' for w in want)
        if not re.fullmatch(r'[0-9A-Z]{2,3}', code) or not name or code in seen:
            raise Refused(f"a row of UNECE's file is no code read here: code {code!r}, name {name[:60]!r}"
                          + (" (a second row of it)" if code in seen else ''))
        seen.add(code)
        out.append({'code': code, 'status': REC20_STATUS.get(status, status), 'name_en': name, 'symbol': symbol})
    if not out:
        raise Refused("UNECE's file holds no code")
    return out


def loinc_table_csv(data):
    """LOINC's table (`LoincTable/Loinc.csv`, alone or inside the release's zip): one row a term — `LOINC_NUM`, `PROPERTY`,
    `SCALE_TYP`, `STATUS`, `LONG_COMMON_NAME` — read into code, status, property, scale and name_en, the status as LOINC
    writes it in lower case (`active`, `trial`, `discouraged`, `deprecated`). The table's other columns — the component,
    the system, the method, the definitions, the example units — are LOINC's text, and are not read."""
    if data[:2] == b'PK':
        import zipfile
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as e:
            raise Refused(f"LOINC's file is no zip it can be read in: {e}") from None
        inside = [n for n in z.namelist() if n.replace('\\', '/').endswith('LoincTable/Loinc.csv')]
        if len(inside) != 1:
            raise Refused(f"LOINC's zip holds {len(inside)} LoincTable/Loinc.csv, and one is read")
        data = z.read(inside[0])
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise Refused("LOINC's table is not UTF-8 text: no LoincTable/Loinc.csv") from None
    rows = csv.reader(io.StringIO(text))
    head = [h.strip() for h in next(rows, [])]
    want = ('LOINC_NUM', 'PROPERTY', 'SCALE_TYP', 'STATUS', 'LONG_COMMON_NAME')
    if any(w not in head for w in want):
        raise Refused(f"LOINC's file has not the columns read here ({', '.join(want)}): its first row is "
                      f"{', '.join(h for h in head if h)[:200]} — the table is LoincTable/Loinc.csv of LOINC's release")
    at = {w: head.index(w) for w in want}
    out, seen = [], set()
    for r in rows:
        if not r or all(not c.strip() for c in r):
            continue
        code, prop, scale, status, name = (r[at[w]].strip() if at[w] < len(r) else '' for w in want)
        if not re.fullmatch(r'[1-9][0-9]{0,6}-[0-9]', code) or code in seen or not prop or not scale:
            raise Refused(f"a row of LOINC's table is no term read here: code {code!r}, property {prop!r}, scale {scale!r}"
                          + (" (a second row of it)" if code in seen else ''))
        seen.add(code)
        out.append({'code': code, 'status': status.lower(), 'property': prop, 'scale': scale, 'name_en': name})
    if not out:
        raise Refused("LOINC's table holds no term")
    return out


def ifc_express(data):
    """IFC's schema in EXPRESS (`IFC4X3_ADD2.exp`): its measure types (`TYPE Ifc…Measure = …;`) and its SI units — each
    name of `IfcSIUnitName`, alone and after each prefix of `IfcSIPrefix`, written as a model writes the two
    (`MILLI.METRE`) — read into code, kind (`measure` or `unit`) and base (the type a measure is defined by; a unit's
    name). The schema's entities, rules and functions are buildingSMART's text, and are not read."""
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise Refused("IFC's schema is not UTF-8 text: no EXPRESS schema") from None
    if not re.search(r'^SCHEMA IFC\w*;', text, re.M):
        raise Refused("the file is no IFC schema in EXPRESS: it declares no `SCHEMA IFC…;`")

    def enum(name):
        m = re.search(r'^TYPE ' + name + r' = ENUMERATION OF\s*\(([^)]*)\);', text, re.M)
        return [v.strip() for v in m.group(1).split(',') if v.strip()] if m else []
    measures = re.findall(r'^TYPE (Ifc\w+Measure) = ([^;]+);', text, re.M)
    names, prefixes = enum('IfcSIUnitName'), enum('IfcSIPrefix')
    if not measures or not names or not prefixes:
        raise Refused(f"IFC's schema holds {len(measures)} measure types, {len(names)} SI unit names and {len(prefixes)} "
                      f"prefixes, and each is read")
    out = [{'code': m, 'kind': 'measure', 'base': ' '.join(b.split())} for m, b in measures]
    for n in names:
        out.append({'code': n, 'kind': 'unit', 'base': n})
        out += [{'code': f"{p}.{n}", 'kind': 'unit', 'base': n} for p in prefixes]
    return out


def _sql_inserts(text, table):
    """Each `INSERT INTO <table> (columns) VALUES (...);` of an SQL script, as {column: value}: a string with its doubled
    quotes undone, a number as written, NULL as ''. A statement may span lines, as a remark's line break makes it."""
    head = re.compile(r'INSERT INTO ' + re.escape(table) + r' \(([^)]*)\) VALUES \(')
    for m in head.finditer(text):
        cols, vals, i = [c.strip() for c in m.group(1).split(',')], [], m.end()
        while i < len(text) and text[i] != ')':
            if text[i] == "'":
                j, buf = i + 1, []
                while j < len(text) and not (text[j] == "'" and text[j + 1:j + 2] != "'"):
                    buf.append(text[j])
                    j += 2 if text[j] == "'" else 1
                vals.append(''.join(buf))
                i = j + 1
            elif text[i] in ' ,\t\r\n':
                i += 1
            else:
                j = i
                while j < len(text) and text[j] not in ',)':
                    j += 1
                v = text[i:j].strip()
                vals.append('' if v.upper() == 'NULL' else v)
                i = j
        if len(vals) != len(cols):
            raise Refused(f"an insert into {table} holds {len(vals)} values for {len(cols)} columns")
        yield dict(zip(cols, vals))


def epsg_sql(data):
    """EPSG's dataset as its SQL scripts (`EPSG-v<N>-PostgreSQL.zip`, or its `…Data_Script.sql`): each row of
    `epsg_unitofmeasure` — `uom_code`, `unit_of_meas_name`, `unit_of_meas_type`, `target_uom_code`, `factor_b`,
    `factor_c`, `deprecated` — read into code, name_en, type, target, factor_b, factor_c and status (`deprecated`, or
    none): a unit is factor_b / factor_c of its target, written as EPSG writes them. The dataset's other tables (the
    reference systems, the transformations) and its remarks are EPSG's, and are not read here."""
    if data[:2] == b'PK':
        import zipfile
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as e:
            raise Refused(f"EPSG's file is no zip it can be read in: {e}") from None
        inside = [n for n in z.namelist() if n.endswith('Data_Script.sql')]
        if len(inside) != 1:
            raise Refused(f"EPSG's zip holds {len(inside)} data scripts (…Data_Script.sql), and one is read")
        data = z.read(inside[0])
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise Refused("EPSG's data script is not UTF-8 text") from None
    want = ('uom_code', 'unit_of_meas_name', 'unit_of_meas_type', 'target_uom_code', 'factor_b', 'factor_c', 'deprecated')
    out, seen = [], set()
    for r in _sql_inserts(text, 'epsg_unitofmeasure'):
        if any(w not in r for w in want):
            raise Refused(f"EPSG's units of measure have not the columns read here ({', '.join(want)})")
        code = r['uom_code']
        if not code.isdigit() or code in seen or not r['unit_of_meas_name']:
            raise Refused(f"a unit of EPSG's dataset is none read here: code {code!r}"
                          + (" (a second row of it)" if code in seen else ''))
        seen.add(code)
        out.append({'code': code, 'name_en': r['unit_of_meas_name'], 'type': r['unit_of_meas_type'],
                    'target': r['target_uom_code'], 'factor_b': r['factor_b'], 'factor_c': r['factor_c'],
                    'status': 'deprecated' if r['deprecated'] == '1' else ''})
    if not out:
        raise Refused("EPSG's file holds no unit of measure (`INSERT INTO epsg_unitofmeasure`): its data script is read")
    return out


def gs1_syntax_dictionary(data):
    """GS1's Barcode Syntax Dictionary (`gs1-syntax-dictionary.txt`): one line an application identifier or a range of
    them — `AIs [flags] specification [attributes] # title` — read into code (each AI of a range: `3100-3105` is six),
    format (its specification: `N6`, `N3,iso4217 N..15`) and name_en (its title, `NET WEIGHT (kg)`). Its flags, its
    attributes and its comments are GS1's, and are not read."""
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise Refused("GS1's dictionary is not UTF-8 text") from None
    out, seen = [], set()
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        body, _, title = line.partition('#')
        words = body.split()
        m = re.fullmatch(r'([0-9]{2,4})(?:-([0-9]{2,4}))?', words[0])
        if not m or (m.group(2) and (len(m.group(2)) != len(m.group(1)) or m.group(2) < m.group(1))):
            raise Refused(f"line {n} of GS1's dictionary names no application identifier read here: {words[0]!r}")
        spec = [w for w in words[1:] if re.match(r'^\[?[NXYZ][0-9.]', w)]
        if not spec:
            raise Refused(f"line {n} of GS1's dictionary gives {words[0]} no specification")
        first, last = m.group(1), m.group(2) or m.group(1)
        for ai in range(int(first), int(last) + 1):
            code = str(ai).zfill(len(first))
            if code in seen:
                raise Refused(f"GS1's dictionary names the application identifier {code} twice")
            seen.add(code)
            out.append({'code': code, 'format': ' '.join(spec), 'name_en': ' '.join(title.split())})
    if not out:
        raise Refused("GS1's dictionary names no application identifier")
    return out


CLDR_LANGUAGES = ('en', 'fa', 'tr')     # the names read: the law's English, and the languages of its widgets


def cldr_units_json(data):
    """Unicode CLDR's unit names (`cldr-units-full`, the package Unicode publishes, a gzipped tar; or a zip of
    cldr-json): for each unit of `main/en/units.json` — each entry of its `long` names that has a `displayName`, its
    prefixes and patterns passed over — the code, and its long display name in English, Persian and Turkish, read into
    code, name_en, name_fa and name_tr. Its patterns (`{0} metres`), short and narrow forms and other languages are
    CLDR's, and are not read."""
    import tarfile
    import zipfile
    files = {}
    try:
        if data[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(data))
            names = z.namelist()
            get = z.read
        else:
            tf = tarfile.open(fileobj=io.BytesIO(data), mode='r:*')
            names = [m.name for m in tf.getmembers() if m.isfile()]
            get = lambda n: tf.extractfile(n).read()  # noqa: E731
    except (zipfile.BadZipFile, tarfile.TarError) as e:
        raise Refused(f"CLDR's file is neither a tar nor a zip it can be read in: {e}") from None
    for lang in CLDR_LANGUAGES:
        hit = [n for n in names if n.replace('\\', '/').endswith(f'main/{lang}/units.json')]
        if len(hit) != 1:
            raise Refused(f"CLDR's file holds {len(hit)} main/{lang}/units.json, and one of each of "
                          f"{', '.join(CLDR_LANGUAGES)} is read")
        try:
            files[lang] = json.loads(get(hit[0]).decode('utf-8'))['main'][lang]['units']['long']
        except (ValueError, KeyError) as e:
            raise Refused(f"CLDR's main/{lang}/units.json holds no units' long names: {e}") from None
    out = []
    for code, entry in files['en'].items():
        if not (isinstance(entry, dict) and entry.get('displayName')):
            continue
        out.append({'code': code, **{f'name_{lang}': str((files[lang].get(code) or {}).get('displayName') or '')
                                     for lang in CLDR_LANGUAGES}})
    if not out:
        raise Refused("CLDR's English units name no unit")
    return out


READERS = {'ilo-isco-08-xlsx': ilo_isco_08_xlsx, 'unece-rec20-xlsx': unece_rec20_xlsx,
           'loinc-table-csv': loinc_table_csv, 'ifc-express': ifc_express, 'epsg-sql': epsg_sql,
           'gs1-syntax-dictionary': gs1_syntax_dictionary, 'cldr-units-json': cldr_units_json}


# ------------------------------------------------------------------------------------------------ the law's rows
def _law(root=ROOT):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core import read
    d = os.path.join(root, 'core', 'law')
    d = d if os.path.isfile(os.path.join(d, 'registries.yaml')) else os.path.join(ROOT, 'core', 'law')
    return read.data(os.path.join(d, 'registries.yaml'))


def scheme_row(scheme, root=ROOT):
    law = _law(root)
    row = next((r for r in law.get('knowledge_schemes') or [] if isinstance(r, dict) and r.get('scheme') == scheme), None)
    if row is None:
        raise Refused(f"{scheme!r} is no scheme of the knowledge tree")
    if row.get('holding') != 'fetched' or not isinstance(row.get('fetch'), dict):
        raise Refused(f"{scheme} is held `{row.get('holding') or 'shipped'}`, not fetched: its codes are read where "
                      f"the law holds them")
    columns = None
    f = next((r.get('file') for r in law.get('registry_files') or [] if isinstance(r, dict) and r.get('registry') == scheme),
             None)
    if f and os.path.isfile(os.path.join(ROOT, f)):
        with open(os.path.join(ROOT, f), encoding='utf-8') as fh:
            columns = next(csv.reader(fh, delimiter='\t'), None)
    return row, columns


# ------------------------------------------------------------------------------------------------ the act
def keep(scheme, data, source, *, root=ROOT, now=None):
    """Read the provider's file `data` (from `source`) by the scheme's reader, and keep it in this machine's cache.
    Returns (sha-256, rows, the directory kept in)."""
    row, columns = scheme_row(scheme, root)
    reader = READERS.get(str(row['fetch'].get('reader')))
    if reader is None:
        raise Refused(f"{scheme}'s reader `{row['fetch'].get('reader')}` is no reader of this release")
    rows = reader(data)
    if columns and set(columns) != set(rows[0]):
        raise Refused(f"the rows read have the columns {', '.join(rows[0])}, and {scheme}'s file has {', '.join(columns)}")
    sha = hashlib.sha256(data).hexdigest()
    d = os.path.join(cache_dir(), scheme, sha)
    tmp = d + '.part'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    ext = os.path.splitext(str(row['fetch'].get('from')).split('?')[0])[1] or '.bin'
    with open(os.path.join(tmp, 'source' + ext), 'wb') as fh:
        fh.write(data)
    cols = columns or list(rows[0])
    with open(os.path.join(tmp, 'rows.tsv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    when = (now or datetime.datetime.now().astimezone()).isoformat(timespec='seconds')
    with open(os.path.join(tmp, 'fetched.json'), 'w', encoding='utf-8') as fh:
        json.dump({'scheme': scheme, 'from': source, 'at': when, 'sha256': sha, 'rows': len(rows)}, fh, indent=1)
    shutil.rmtree(d, ignore_errors=True)
    os.replace(tmp, d)
    return sha, rows, d


def download(url):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'daftar-fetch (a standard\'s table, for its reader)'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except OSError as e:
        raise Refused(f"the provider did not answer ({url}): {e}") from None


def fetched(scheme):
    """The copies of `scheme` this machine keeps, newest first: [(when, sha-256, rows.tsv)]."""
    d = os.path.join(cache_dir(), scheme)
    out = []
    for sha in os.listdir(d) if os.path.isdir(d) else []:
        meta = os.path.join(d, sha, 'fetched.json')
        rows = os.path.join(d, sha, 'rows.tsv')
        if not sha.endswith('.part') and os.path.isfile(meta) and os.path.isfile(rows):
            try:
                with open(meta, encoding='utf-8') as fh:
                    m = json.load(fh)
            except (OSError, ValueError):
                continue
            out.append((str(m.get('at') or ''), sha, rows))
    return sorted(out, reverse=True)


def crossed(scheme, rows):
    """[line]: what the provider's rows, read, say of the scheme's crossing into the law's units and kinds (`units` on its
    row): how many of its codes cross (through every axis, where it names axes), each value on an axis no row names,
    and each crossed code it has not, or marks deprecated or deleted — a revision that moved what the law's crossing
    names. Nothing for a scheme with no crossing."""
    import units as dmunits
    try:
        n, missing, marked, unknown = dmunits.against(scheme, rows)
    except ValueError:
        return []
    out = [f"fetch: {n} of its {len(rows)} codes cross into the law's units and kinds (python3 bin/units.py --codes "
           f"{scheme})"]
    for axis, values in unknown.items():
        out.append(f"fetch: on its axis {axis}, values no row of the law's crossing names: {', '.join(values)}")
    if missing:
        out.append(f"fetch: crossed by the law, and not in this copy: {', '.join(missing)}")
    if marked:
        out.append(f"fetch: crossed by the law, and marked by the provider: "
                   f"{', '.join(f'{c} ({s})' for c, s in marked)}")
    return out


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    if argv == ['--list']:
        base = cache_dir()
        for scheme in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            for when, sha, _rows in fetched(scheme):
                print(f"{scheme}\t{when}\tsha-256:{sha}")
        print(f"fetch: this machine's cache is {base}")
        return 0
    scheme, rest = argv[0], argv[1:]
    try:
        row, _cols = scheme_row(scheme)
        if rest[:1] == ['--from'] and len(rest) == 2:
            with open(rest[1], 'rb') as fh:
                data, source = fh.read(), os.path.abspath(rest[1])
        elif not rest:
            source = str(row['fetch'].get('from'))
            try:
                data = download(source)
            except Refused as e:
                raise Refused(f"{e} — download it from there by hand, as its provider serves a person, and read that "
                              f"copy: python3 bin/fetch.py {scheme} --from <file>") from None
        else:
            print(__doc__)
            return 2
        try:
            sha, rows, d = keep(scheme, data, source)
        except Refused as e:
            if rest:
                raise
            raise Refused(f"{e} — what {source} answered is not the table its reader reads: a provider that serves its "
                          f"table to a person signed in is downloaded there by hand, and read with: python3 bin/fetch.py "
                          f"{scheme} --from <file>") from None
    except (Refused, OSError) as e:
        print(f"fetch: NOT FETCHED: {e}", file=sys.stderr)
        return 1
    print(f"fetch: {scheme}, {len(rows)} rows, kept in {d}")
    for line in crossed(scheme, rows):
        print(line)
    print(f"for the save's entry:\n  - read: {scheme} from {source}, sha-256 {sha}, {len(rows)} rows")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
