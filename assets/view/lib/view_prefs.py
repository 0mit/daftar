"""view_prefs — a reader's own way of reading: their language as ONE BCP 47 tag whose Unicode extension (UTS #35) says
the calendar (`ca`), the digits (`nu`), the hour cycle (`hc`), the first day of the week (`fw`) and the zone moments are
shown in (`tz`) — `fa-u-ca-persian-nu-arabext-hc-h23-fw-sat` — and, beside it, named, what the tag has no key for: how a
day is written (`date`) and how a currency is named (`currency`). Kept with the reader's account on the host (view_serve's
users, daftard's record of the person), never in the garden: a reader's way of reading is no fact of the garden.

    check(prefs)          -> (the preferences as kept, [what is refused, in a sentence])
    settings_of(prefs)    -> what the widgets read (`settings.reader`: locale, zone, date, currency)
    zones()               -> [(the tag's `tz` type, the IANA zone it stands for)], CLDR's
    parse(tag)            -> the tag's parts, read by the grammar of RFC 5646 — never a pattern of ours
    to_bean(prefs, reader, garden=None, bean=None)  -> a bean that holds them (the view profile's `reader_preferences`)
    from_bean(text)       -> {bean, reader, garden, prefs} read back from one, checked as `check` checks; or Refused

    python3 view_prefs.py export --config <host file> --user <account> [--garden <garden root>] [--out <bean.md>]
    python3 view_prefs.py import <bean.md> --config <host file> [--user <account>] [--garden <garden root>]

A BEAN OF THEM, TO KEEP OR TO CARRY (ratified 2026-10-13). A reader's way of reading is the host's to keep, in its own
file; written as a bean — a `document` whose `draw` of the reader holds the form `reader_preferences` — it is backed up
or carried to another machine, and read back there, losing nothing: preferences → bean → preferences and bean →
preferences → bean are each the same. Export and import touch only the three keys of the account they name, and print
nothing of the host's file. The bean is a file a person carries; a garden holds it only where a person puts it there,
and then its gate judges the form.

THE STANDARD'S OWN DATA. Which types each key takes is CLDR's (`common/bcp47/*.xml`), carried in
seed/knowledge/cldr-bcp47.tsv; `python3 view_prefs.py --from-ldml <cldr>/common/bcp47` writes it from any copy of CLDR.
A page reads the tag with Intl.Locale; the host reads it here. Unset is the language's own, as CLDR says it.
"""
import json
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


# --------------------------------------------------------------------------------------- a bean of them, and back
_ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,120}$')
_GARDEN = re.compile(r'^[0-9a-f]{12}$')
FIELDS = ('locale', 'date', 'currency')


def to_bean(prefs, reader, garden=None, bean=None):
    """The text of a bean holding a reader's preferences, as `check` keeps them: a `document` whose `draw` of the reader
    holds the form `reader_preferences` (core/law/profiles.yaml), the reader's own `say` and `own`. One written of the
    same preferences is the same text. Refused where `check` refuses them, or the reader or the garden is no id."""
    kept, bad = check(prefs)
    if bad:
        raise Refused('; '.join(bad))
    if not isinstance(reader, str) or not _ID.match(reader):
        raise Refused(f'{reader!r}: the reader is named by their bean\'s id')
    if garden is not None and not (isinstance(garden, str) and _GARDEN.match(garden)):
        raise Refused(f'{garden!r}: a garden is named by its id, twelve hexadecimal digits (python3 bin/propose.py id)')
    bid = bean or f'preferences-{reader}'
    if not _ID.match(bid):
        raise Refused(f'{bid!r}: a bean\'s id is lowercase letters, digits and hyphens')
    form = ([('garden', garden)] if garden else []) + [(k, kept[k]) for k in FIELDS if k in kept]
    held = ', '.join(f'{k}: {json.dumps(v)}' for k, v in form)
    return ('---\n'
            f'bean: {bid}\n'
            'kind: document\n'
            f'title: "a way of reading: {reader}"\n'
            'summary: "a reader\'s own way of reading, kept on the host they read on, written here to keep or to carry"\n'
            'statements:\n'
            f'  - say: {{ by: {reader}, at: now }}\n'
            f'  - own: {{ by: {reader}, of: self }}\n'
            f'  - draw: {{ id: preferences, by: self, of: [{reader}], preferences: {{ {held} }} }}\n'
            '---\n'
            'A reader\'s way of reading: their language, calendar, digits, hour cycle, first day of the week and zone, how a '
            'day is written and a currency named. The host they read on keeps it; this is its copy.\n')


def from_bean(text):
    """{bean, reader, garden, prefs} of a bean `to_bean` wrote, its preferences checked as `check` checks them — what a
    host keeps, read back. Refused, by name, where it holds no preferences, names no one reader, or holds what `check`
    refuses."""
    import yaml
    m = re.match(r'^---\r?\n(.*?)\r?\n---', text if isinstance(text, str) else '', re.S)
    if not m:
        raise Refused('this is no bean: no front matter')
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise Refused(f'this bean does not read: {e}')
    bid = fm.get('bean') if isinstance(fm, dict) else None
    held = [r for s in (fm.get('statements') or []) if isinstance(s, dict) for v, r in s.items()
            if v == 'draw' and isinstance(r, dict) and isinstance(r.get('preferences'), dict)]
    if len(held) != 1:
        raise Refused(f'{bid}: it holds no preferences — one `draw` holds the form `reader_preferences`, and here '
                      f'{len(held)} do')
    r = held[0]
    of = r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]
    if len(of) != 1 or not isinstance(of[0], str) or not _ID.match(of[0]):
        raise Refused(f'{bid}: its preferences name no one reader (their `draw` is `of` the reader)')
    form = r['preferences']
    extra = sorted(set(form) - set(FIELDS) - {'garden'})
    if extra:
        raise Refused(f'{bid}: {", ".join(extra)}: no preference of a reader')
    garden = form.get('garden')
    if garden is not None and not (isinstance(garden, str) and _GARDEN.match(garden)):
        raise Refused(f'{bid}: {garden!r} is no garden\'s id')
    kept, bad = check({k: form[k] for k in FIELDS if k in form})
    if bad:
        raise Refused(f'{bid}: ' + '; '.join(bad))
    return {'bean': bid, 'reader': of[0], 'garden': garden, 'prefs': kept}


def _garden_id(root):
    """A garden's id (bin/parse.py `garden_id`): the first twelve hexadecimal digits of the root of its history."""
    import subprocess
    r = subprocess.run(['git', '-C', root, 'rev-list', '--first-parent', '--max-parents=0', 'HEAD'], capture_output=True,
                       text=True, encoding='utf-8')
    roots = r.stdout.split()
    if r.returncode or not roots:
        raise Refused(f'{root}: no garden\'s history here, so no garden\'s id')
    return roots[-1][:12]


def _write_private(path, text):
    """Whole, flushed and swapped in, readable by its owner alone — as the host writes its own file."""
    import tempfile
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.prefs-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def export(config, user, garden_root=None):
    """The bean of an account's preferences in view_serve's host file (its `users`): the account's own bean the reader."""
    cfg = json.load(open(config, encoding='utf-8'))
    rec = (cfg.get('users') or {}).get(user)
    if not isinstance(rec, dict):
        raise Refused(f'{user!r}: no such account in {config}')
    if not rec.get('bean'):
        raise Refused(f'{user!r}: the account names no bean of the garden, so no reader the preferences are of')
    return to_bean({k: rec[k] for k in FIELDS if rec.get(k)}, rec['bean'],
                   garden=_garden_id(garden_root) if garden_root else None)


def import_(text, config, user=None, garden_root=None):
    """The preferences a bean holds, written into the host file's account of their reader — that account's three keys
    made what the bean says (one it does not hold taken out), nothing else of the file changed. (account, prefs)."""
    got = from_bean(text)
    if garden_root and got['garden'] and got['garden'] != _garden_id(garden_root):
        raise Refused(f'{got["bean"]}: its preferences were set in the garden {got["garden"]}, not in this one')
    cfg = json.load(open(config, encoding='utf-8'))
    users = cfg.get('users') or {}
    if user is None:
        named = [u for u, r in users.items() if isinstance(r, dict) and r.get('bean') == got['reader']]
        if len(named) != 1:
            raise Refused(f'{got["bean"]}: {len(named)} accounts here are {got["reader"]}\'s: name the one (--user)')
        user = named[0]
    rec = users.get(user)
    if not isinstance(rec, dict):
        raise Refused(f'{user!r}: no such account in {config}')
    if rec.get('bean') != got['reader']:
        raise Refused(f'{got["bean"]} is {got["reader"]}\'s way of reading, and the account {user!r} is not theirs')
    for k in FIELDS:
        if k in got['prefs']:
            rec[k] = got['prefs'][k]
        else:
            rec.pop(k, None)
    _write_private(config, json.dumps(cfg, indent=1))
    return user, got['prefs']


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


def main(argv):
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    if len(argv) == 2 and argv[0] == '--from-ldml':
        print('key\ttype\taliases\tdescription')
        for r in from_ldml(argv[1]):
            print('\t'.join(r))
        return 0
    try:
        if argv[:1] == ['export'] and opt('--config') and opt('--user'):
            text = export(opt('--config'), opt('--user'), opt('--garden'))
            if opt('--out'):
                _write_private(opt('--out'), text)
                print(f'view_prefs: {opt("--user")}\'s way of reading written to {opt("--out")}')
            else:
                sys.stdout.write(text)
            return 0
        if argv[:1] == ['import'] and len(argv) > 1 and opt('--config'):
            user, prefs = import_(open(argv[1], encoding='utf-8').read(), opt('--config'), opt('--user'), opt('--garden'))
            print(f'view_prefs: {user}\'s way of reading read back from {argv[1]}: '
                  + (', '.join(f'{k} {v}' for k, v in prefs.items()) or 'their language\'s own'))
            return 0
    except (Refused, OSError, ValueError) as e:
        print(f'view_prefs: {e}', file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
