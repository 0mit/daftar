"""view_prefs — a reader's own way of reading: their language as ONE BCP 47 tag whose Unicode extension (UTS #35) says
the calendar (`ca`), the digits (`nu`), the hour cycle (`hc`), the first day of the week (`fw`) and the zone moments are
shown in (`tz`) — `fa-u-ca-persian-nu-arabext-hc-h23-fw-sat` — and, beside it, named, what the tag has no key for: how a
day is written (`date`) and how a currency is named (`currency`). Kept with the reader's account on the host (view_serve's
users, daftard's record of the person), never in the garden: a reader's way of reading is no fact of the garden.

    check(prefs)          -> (the preferences as kept, [what is refused, in a sentence])
    settings_of(prefs)    -> what the widgets read (`settings.reader`: locale, zone, date, currency)
    zones()               -> [(the tag's `tz` type, the IANA zone it stands for)], CLDR's
    parse(tag)            -> the tag's parts, read by the grammar of RFC 5646 — never a pattern of ours

THE STANDARD'S OWN DATA. Which types each key takes is CLDR's (`common/bcp47/*.xml`), carried in
seed/knowledge/cldr-bcp47.tsv; `python3 view_prefs.py --from-ldml <cldr>/common/bcp47` writes it from any copy of CLDR.
A page reads the tag with Intl.Locale; the host reads it here. Unset is the language's own, as CLDR says it.
"""
import os
import re
import sys

KEYS = ('ca', 'fw', 'hc', 'nu', 'tz')                 # the Unicode keys a reader sets, in the order a canonical tag has them
DATE = ('short', 'medium', 'long', 'full')            # Intl's date styles: the numeric day, …, the day with its weekday
CURRENCY = ('symbol', 'narrowSymbol', 'code', 'name')  # Intl's currency displays
HERE = os.path.dirname(os.path.abspath(__file__))


class Refused(ValueError):
    pass


def _table_path():
    for root in (os.environ.get('DAFTAR_ROOT') or '', os.path.join(HERE, '..', '..', '..')):
        p = os.path.join(root, 'seed', 'knowledge', 'cldr-bcp47.tsv') if root else ''
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    return None


_TABLE = None


def table():
    """{key: {type: [aliases]}} — CLDR's types of each key a reader sets (seed/knowledge/cldr-bcp47.tsv)."""
    global _TABLE
    if _TABLE is None:
        _TABLE = {k: {} for k in KEYS}
        path = _table_path()
        if path:
            with open(path, encoding='utf-8') as fh:
                rows = fh.read().splitlines()
            for ln in rows[1:]:
                c = ln.split('\t')
                if len(c) >= 2 and c[0] in _TABLE:
                    _TABLE[c[0]][c[1]] = [a for a in (c[2].split(' ') if len(c) > 2 and c[2] != '-' else []) if a]
    return _TABLE


def zones():
    """[(tz type, IANA zone)] — each zone CLDR names a `tz` type for, by the first of its aliases (the IANA name)."""
    return sorted(((t, a[0]) for t, a in table()['tz'].items() if a), key=lambda x: x[1])


# ------------------------------------------------------------------------------------------------ the grammar (RFC 5646)
_ALPHA, _DIGIT = re.compile(r'[A-Za-z]+'), re.compile(r'[0-9]+')
_ALNUM = re.compile(r'[A-Za-z0-9]+')


def _is(rx, s, lo, hi):
    return lo <= len(s) <= hi and rx.fullmatch(s) is not None


def parse(tag):
    """The parts of a language tag, by RFC 5646's grammar (`langtag`): language (2–3 letters, or 4–8), up to three extended
    language subtags, script (4 letters), region (2 letters or 3 digits), variants, extensions (a singleton and its
    subtags of 2–8), private use (`x-`). Refused, with a sentence, where it is no such tag."""
    if not isinstance(tag, str) or not tag or len(tag) > 200:
        raise Refused('a language is written as a BCP 47 tag, such as fa or fa-u-ca-persian')
    sub = tag.split('-')
    if any(not s for s in sub):
        raise Refused(f'{tag!r}: a tag has no empty part')
    if not all(_ALNUM.fullmatch(s) for s in sub):
        raise Refused(f'{tag!r}: a tag is letters and digits between hyphens')
    out = {'language': '', 'extlang': [], 'script': '', 'region': '', 'variants': [], 'extensions': {}, 'private': []}
    i = 0
    if not (_is(_ALPHA, sub[0], 2, 3) or _is(_ALPHA, sub[0], 4, 8)):
        raise Refused(f'{tag!r}: a tag begins with its language, two or three letters')
    out['language'] = sub[0].lower()
    i = 1
    while i < len(sub) and len(out['extlang']) < 3 and len(sub[0]) <= 3 and _is(_ALPHA, sub[i], 3, 3):
        out['extlang'].append(sub[i].lower())
        i += 1
    if i < len(sub) and _is(_ALPHA, sub[i], 4, 4):
        out['script'] = sub[i].title()
        i += 1
    if i < len(sub) and (_is(_ALPHA, sub[i], 2, 2) or _is(_DIGIT, sub[i], 3, 3)):
        out['region'] = sub[i].upper()
        i += 1
    while i < len(sub) and (_is(_ALNUM, sub[i], 5, 8) or (len(sub[i]) == 4 and sub[i][0].isdigit())):
        out['variants'].append(sub[i].lower())
        i += 1
    while i < len(sub) and len(sub[i]) == 1 and sub[i].lower() != 'x':
        single = sub[i].lower()
        if single in out['extensions']:
            raise Refused(f'{tag!r}: the extension -{single}- is written once')
        i += 1
        parts = []
        while i < len(sub) and _is(_ALNUM, sub[i], 2, 8):
            parts.append(sub[i].lower())
            i += 1
        if not parts:
            raise Refused(f'{tag!r}: the extension -{single}- holds nothing')
        out['extensions'][single] = parts
    if i < len(sub) and sub[i].lower() == 'x':
        i += 1
        while i < len(sub) and _is(_ALNUM, sub[i], 1, 8):
            out['private'].append(sub[i].lower())
            i += 1
        if not out['private']:
            raise Refused(f'{tag!r}: private use (-x-) holds nothing')
    if i != len(sub):
        raise Refused(f'{tag!r}: {sub[i]!r} stands where no part of a language tag can')
    return out


def unicode_keys(parts):
    """{key: type} of the `-u-` extension (UTS #35): each key two characters, a letter second, its type the subtags of
    three to eight characters after it; a key given twice is refused."""
    u, out, key = parts['extensions'].get('u') or [], {}, None
    for s in u:
        if len(s) == 2 and s[1].isalpha():
            if s in out:
                raise Refused(f'the key {s} is written once')
            key, out[s] = s, ''
        elif key is None:
            raise Refused(f'{s!r}: the -u- extension names its attributes no reader sets here')
        else:
            out[key] = (out[key] + '-' + s) if out[key] else s
    return out


def check(prefs):
    """(the preferences as the host keeps them, [refusals]) — the tag read by the grammar, its Unicode keys only those a
    reader sets here, each type one CLDR has for its key; the date's style and the currency's naming one of Intl's. A
    preference not given is not kept: the language's own stands for it."""
    prefs = prefs if isinstance(prefs, dict) else {}
    out, bad = {}, []
    tag = str(prefs.get('locale') or '').strip()
    if tag:
        try:
            p = parse(tag)
            keys = unicode_keys(p)
            if set(p['extensions']) - {'u'}:
                bad.append('only the Unicode extension (-u-) is a reader\'s here: ' + ', '.join(f'-{x}-' for x in sorted(set(p['extensions']) - {'u'})))
            T = table()
            for k, v in keys.items():
                if k not in KEYS:
                    bad.append(f'-u-{k}- is no choice a reader makes here (they are {", ".join(KEYS)})')
                elif T[k] and v not in T[k]:
                    bad.append(f'{v!r} is no {k} of CLDR\'s')
            if not bad:
                base = '-'.join([p['language']] + p['extlang'] + ([p['script']] if p['script'] else [])
                                + ([p['region']] if p['region'] else []) + p['variants'])
                u = '-'.join(f'{k}-{keys[k]}' for k in sorted(keys))
                out['locale'] = base + (f'-u-{u}' if u else '')
        except Refused as e:
            bad.append(str(e))
    if prefs.get('date'):
        if prefs['date'] in DATE:
            out['date'] = prefs['date']
        else:
            bad.append(f'a day is written {", ".join(DATE)}: not {prefs["date"]!r}')
    if prefs.get('currency'):
        if prefs['currency'] in CURRENCY:
            out['currency'] = prefs['currency']
        else:
            bad.append(f'a currency is named by its {", ".join(CURRENCY)}: not {prefs["currency"]!r}')
    return out, bad


def settings_of(prefs):
    """What the widgets read of a reader's preferences (`settings.reader`): the tag, the IANA zone its `tz` stands for,
    the date's style, the currency's naming — each absent where unset."""
    prefs = prefs if isinstance(prefs, dict) else {}
    out = {k: prefs[k] for k in ('locale', 'date', 'currency') if isinstance(prefs.get(k), str) and prefs[k]}
    if out.get('locale'):
        try:
            tz = unicode_keys(parse(out['locale'])).get('tz')
        except Refused:
            tz = None
        aliases = table()['tz'].get(tz) if tz else None
        if aliases:
            out['zone'] = aliases[0]
    return out


# --------------------------------------------------------------------------------------- CLDR's own data, as a table
def from_ldml(folder):
    """The rows of seed/knowledge/cldr-bcp47.tsv from CLDR's own `common/bcp47` (calendar.xml, number.xml,
    timezone.xml): each type of each key a reader sets, its aliases, and CLDR's description of it."""
    import xml.etree.ElementTree as ET
    rows = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.xml'):
            continue
        root = ET.parse(os.path.join(folder, name)).getroot()
        for key in root.iter('key'):
            k = key.get('name')
            if k not in KEYS:
                continue
            for t in key.iter('type'):
                if t.get('deprecated') == 'true':
                    continue
                rows.append((k, t.get('name'), t.get('alias') or '-', re.sub(r'\s+', ' ', t.get('description') or '-')))
    return sorted(rows)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--from-ldml':
        print('key\ttype\taliases\tdescription')
        for r in from_ldml(sys.argv[2]):
            print('\t'.join(r))
    else:
        print(__doc__)
