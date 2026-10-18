"""statements — a bank's statement file, read into one shape, whatever standard it is written in. None is privileged:
each format is an adapter beside the others, and a bank's own CSV is read by a mapping the garden declares.

    read(path, fmt, mapping=None) -> {
        'format', 'account': <the bank's id of the account, as the file states it>, 'currency',
        'opening': {count, unit, day} | None, 'closing': {count, unit, day} | None,
        'lines': [{ 'ref', 'day', 'value_day', 'count' (signed: + money in), 'unit', 'text', 'party', 'code' }],
        'refused': [(where, why)] }             # a line not read is refused by name, never dropped in silence

FORMATS: `camt.053` and `camt.054` (ISO 20022, any version of the namespace), `ofx` (1.x SGML and 2.x XML), `mt940`
(SWIFT), `csv` (with a mapping: { delimiter, decimal, skip, columns: { day, amount | debit+credit, text, ref, party,
currency, value_day, code }, day_format: yyyy-mm-dd (absent) | dd.mm.yyyy | dd/mm/yyyy | dd-mm-yyyy, sign: as-is |
negate } — a `day_format` or a `sign` the adapter does not read is refused by name, never passed over). Every amount
is read as written — a decimal string,
never a float; a statement's own arithmetic (opening + lines = closing, per currency) is the caller's check. `code` is
the bank's own code of a line's transaction (camt's BkTxCd, OFX's TRNTYPE, MT940's transaction type), kept as written.

A FILE IS DATA, NEVER INSTRUCTIONS. An XML file that declares a document type (`<!DOCTYPE`, an entity) is refused before
it is parsed, so no entity of it is expanded; nothing a file says is run or fetched.
"""
import csv
import re
import xml.etree.ElementTree as ET

FORMATS = ('camt.053', 'camt.054', 'ofx', 'mt940', 'csv')     # the readers of core/law/formats.yaml this asset is home to


def _undeclared(raw):
    """The `xml` format's own guard (core/formats.py `undeclared`), in this adapter's words."""
    try:
        from core.formats import undeclared, Refused
    except ImportError:                      # the adapter read alone, outside a garden of the release
        if re.search(rb'<!(DOCTYPE|ENTITY)', raw, re.I):
            raise Unreadable("it declares a document type or an entity: a statement is data, refused before it is parsed")
        return
    try:
        undeclared(raw, what='a statement')
    except Refused as e:
        raise Unreadable(str(e)) from None


class Unreadable(Exception):
    pass


def _dec(text, decimal='.'):
    """A decimal as written, sign kept, the thousands separator dropped: '1.234,56' with decimal ',' is '1234.56'."""
    t = str(text or '').strip().replace(' ', '').replace(' ', '')
    if decimal == ',':
        t = t.replace('.', '').replace(',', '.')
    else:
        t = t.replace(',', '')
    if not re.fullmatch(r'[+-]?\d+(\.\d+)?', t):
        raise ValueError(f"{text!r} is no amount")
    return t.lstrip('+')


def _neg(t):
    return t[1:] if t.startswith('-') else '-' + t if t not in ('0', '0.0', '0.00') else t


def read(path, fmt, mapping=None):
    if fmt not in FORMATS:
        raise Unreadable(f"{fmt!r} is none of {', '.join(FORMATS)}")
    if fmt in ('camt.053', 'camt.054'):
        return _camt(path, fmt)
    if fmt == 'ofx':
        return _ofx(path)
    if fmt == 'mt940':
        return _mt940(path)
    return _csv(path, mapping or {})


# ------------------------------------------------------------------------------------------------ ISO 20022 camt
def _camt(path, fmt):
    with open(path, 'rb') as fh:
        raw = fh.read()
    _undeclared(raw)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise Unreadable(f"not XML: {e}")
    ns = re.match(r'\{([^}]+)\}', root.tag)
    if not ns or not re.search(r'camt\.05[34]\.\d+\.\d+', ns.group(1)):
        raise Unreadable(f"no camt.053/054 namespace ({root.tag})")
    q = lambda p: '/'.join(f"{{{ns.group(1)}}}{x}" for x in p.split('/'))
    stmt = root.find('.//' + q('Stmt')) if fmt == 'camt.053' else root.find('.//' + q('Ntfctn'))
    if stmt is None:
        raise Unreadable("no statement (Stmt) or notification (Ntfctn) in it")
    out = {'format': fmt, 'account': None, 'currency': None, 'opening': None, 'closing': None, 'lines': [], 'refused': []}
    acct = stmt.find(q('Acct'))
    if acct is not None:
        out['account'] = (acct.findtext(q('Id/IBAN')) or acct.findtext(q('Id/Othr/Id')))
        out['currency'] = acct.findtext(q('Ccy'))
    for bal in stmt.findall(q('Bal')):
        code = bal.findtext(q('Tp/CdOrPrtry/Cd'))
        amt = bal.find(q('Amt'))
        if amt is None:
            continue
        sign = '' if bal.findtext(q('CdtDbtInd')) == 'CRDT' else '-'
        val = {'count': (sign + amt.text.strip()) if sign and amt.text.strip() != '0' else amt.text.strip(),
               'unit': amt.get('Ccy'), 'day': bal.findtext(q('Dt/Dt')) or (bal.findtext(q('Dt/DtTm')) or '')[:10]}
        if code in ('OPBD', 'PRCD') and out['opening'] is None:
            out['opening'] = val
        elif code in ('CLBD',):
            out['closing'] = val
    for n, e in enumerate(stmt.findall(q('Ntry')), 1):
        try:
            amt = e.find(q('Amt'))
            if (e.findtext(q('Sts/Cd')) or e.findtext(q('Sts')) or 'BOOK') not in ('BOOK',):
                out['refused'].append((f"entry {n}", "not booked (its status is not BOOK): a pending line is no payment"))
                continue
            count = amt.text.strip()
            if e.findtext(q('CdtDbtInd')) == 'DBIT':
                count = _neg(count)
            party = (e.findtext('.//' + q('RltdPties/Dbtr/Nm')) if not count.startswith('-')
                     else e.findtext('.//' + q('RltdPties/Cdtr/Nm'))) or e.findtext('.//' + q('RltdPties/Dbtr/Pty/Nm')) \
                or e.findtext('.//' + q('RltdPties/Cdtr/Pty/Nm'))
            text = ' '.join(x.text.strip() for x in e.iter(f"{{{ns.group(1)}}}Ustrd") if x.text) or \
                e.findtext(q('AddtlNtryInf'))
            out['lines'].append({
                'ref': e.findtext(q('AcctSvcrRef')) or e.findtext(q('NtryRef')) or f"{n}",
                'day': e.findtext(q('BookgDt/Dt')) or (e.findtext(q('BookgDt/DtTm')) or '')[:10],
                'value_day': e.findtext(q('ValDt/Dt')) or None, 'count': count, 'unit': amt.get('Ccy'),
                'text': text, 'party': party,
                'code': e.findtext(q('BkTxCd/Domn/Cd')) and '/'.join(x for x in (
                    e.findtext(q('BkTxCd/Domn/Cd')), e.findtext(q('BkTxCd/Domn/Fmly/Cd')),
                    e.findtext(q('BkTxCd/Domn/Fmly/SubFmlyCd'))) if x) or e.findtext(q('BkTxCd/Prtry/Cd'))})
        except AttributeError as ex:
            out['refused'].append((f"entry {n}", f"cannot be read: {ex}"))
    return out


# ------------------------------------------------------------------------------------------------ OFX
def _ofx(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        raw = fh.read()
    body = raw[raw.find('<OFX>'):] if '<OFX>' in raw else raw
    tag = lambda name, text: (re.search(rf'<{name}>\s*([^<\r\n]*)', text) or [None, None])[1]
    out = {'format': 'ofx', 'account': (tag('ACCTID', body) or '').strip() or None,
           'currency': (tag('CURDEF', body) or '').strip() or None, 'opening': None, 'closing': None, 'lines': [],
           'refused': []}
    led = re.search(r'<LEDGERBAL>(.*?)(</LEDGERBAL>|<AVAILBAL>|</STMTRS>)', body, re.S)
    if led:
        out['closing'] = {'count': _dec(tag('BALAMT', led.group(1))), 'unit': out['currency'],
                          'day': _ofx_day(tag('DTASOF', led.group(1)))}
    for n, m in enumerate(re.finditer(r'<STMTTRN>(.*?)(</STMTTRN>|(?=<STMTTRN>)|(?=</BANKTRANLIST>))', body, re.S), 1):
        t = m.group(1)
        try:
            out['lines'].append({'ref': (tag('FITID', t) or str(n)).strip(), 'day': _ofx_day(tag('DTPOSTED', t)),
                                 'value_day': _ofx_day(tag('DTUSER', t)) if tag('DTUSER', t) else None,
                                 'count': _dec(tag('TRNAMT', t)), 'unit': (tag('CURRENCY', t) or out['currency'] or '').strip()
                                 or out['currency'], 'text': ((tag('MEMO', t) or '') or (tag('NAME', t) or '')).strip() or None,
                                 'party': (tag('NAME', t) or '').strip() or None, 'code': (tag('TRNTYPE', t) or '').strip() or None})
        except (ValueError, TypeError) as e:
            out['refused'].append((f"STMTTRN {n}", str(e)))
    return out


def _ofx_day(t):
    t = (t or '').strip()
    if not re.match(r'\d{8}', t):
        raise ValueError(f"{t!r} is no OFX date")
    return f"{t[:4]}-{t[4:6]}-{t[6:8]}"


# ------------------------------------------------------------------------------------------------ SWIFT MT940
def _mt940(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        raw = fh.read().replace('\r\n', '\n')
    fields = re.findall(r'^:(\d{2}[A-Z]?):(.*?)(?=^:\d{2}[A-Z]?:|^-}|\Z)', raw, re.M | re.S)
    out = {'format': 'mt940', 'account': None, 'currency': None, 'opening': None, 'closing': None, 'lines': [],
           'refused': []}

    def bal(v):
        m = re.match(r'([CD])(\d{6})([A-Z]{3})([\d,]+)', v.strip())
        if not m:
            raise ValueError(f"{v.strip()!r} is no balance")
        cnt = _dec(m.group(4), ',')
        return {'count': cnt if m.group(1) == 'C' else _neg(cnt), 'unit': m.group(3), 'day': _yymmdd(m.group(2))}
    last = None
    for tag_, v in fields:
        try:
            if tag_ == '25':
                out['account'] = v.strip()
            elif tag_ in ('60F', '60M'):
                out['opening'] = bal(v)
                out['currency'] = out['opening']['unit']
            elif tag_ in ('62F', '62M'):
                out['closing'] = bal(v)
            elif tag_ == '61':
                m = re.match(r'(\d{6})(\d{4})?(R?[CD])([A-Z])?([\d,]+)([NSF][A-Z0-9]{3})([^/\n]*)(//([^\n]*))?', v.strip())
                if not m:
                    raise ValueError(f"{v.strip()[:40]!r} is no statement line")
                cnt = _dec(m.group(5), ',')
                debit = m.group(3) in ('D', 'RC')
                vd = _yymmdd(m.group(1))
                last = {'ref': (m.group(9) or m.group(7) or '').strip() or f"{len(out['lines']) + 1}",
                        'day': (vd[:4] + '-' + m.group(2)[:2] + '-' + m.group(2)[2:]) if m.group(2) else vd,
                        'value_day': vd, 'count': _neg(cnt) if debit else cnt, 'unit': out['currency'],
                        'text': None, 'party': None, 'code': m.group(6)}
                out['lines'].append(last)
            elif tag_ == '86' and last is not None:
                last['text'] = ' '.join(v.split())
        except ValueError as e:
            out['refused'].append((f":{tag_}:", str(e)))
    return out


def _yymmdd(t):
    return f"20{t[:2]}-{t[2:4]}-{t[4:6]}"


# ------------------------------------------------------------------------------------------------ a bank's CSV, by a mapping
DAY_FORMATS = {'yyyy-mm-dd': None, 'dd.mm.yyyy': '.', 'dd/mm/yyyy': '/', 'dd-mm-yyyy': '-'}   # each, its separator
SIGNS = ('as-is', 'negate')


def _csv(path, m):
    cols = m.get('columns') or {}
    if not cols.get('day') or not (cols.get('amount') or (cols.get('debit') and cols.get('credit'))):
        raise Unreadable("a CSV mapping names the columns of `day` and of `amount` (or `debit` and `credit`)")
    fmt = m.get('day_format') or 'yyyy-mm-dd'
    if fmt not in DAY_FORMATS:
        raise Unreadable(f"day_format: {fmt!r} is none the adapter reads ({', '.join(DAY_FORMATS)})")
    if m.get('sign', 'as-is') not in SIGNS:
        raise Unreadable(f"sign: {m.get('sign')!r} is none the adapter reads ({', '.join(SIGNS)})")
    dec = m.get('decimal', '.')
    with open(path, encoding=m.get('encoding', 'utf-8-sig'), newline='') as fh:
        rows = list(csv.DictReader(fh, delimiter=m.get('delimiter', ',')))
    rows = rows[int(m.get('skip', 0)):]
    out = {'format': 'csv', 'account': m.get('account'), 'currency': m.get('currency'), 'opening': None, 'closing': None,
           'lines': [], 'refused': []}
    for n, r in enumerate(rows, 1):
        try:
            if cols.get('amount'):
                cnt = _dec(r[cols['amount']], dec)
            else:
                d, c = (r.get(cols['debit']) or '').strip(), (r.get(cols['credit']) or '').strip()
                if bool(d) == bool(c):
                    raise ValueError("a line states a debit or a credit, one of them")
                cnt = _neg(_dec(d, dec)) if d else _dec(c, dec)
            if m.get('sign') == 'negate':
                cnt = _neg(cnt)
            day = (r.get(cols['day']) or '').strip()
            if DAY_FORMATS[fmt] and re.fullmatch(r'\d{2}' + re.escape(DAY_FORMATS[fmt]) + r'\d{2}'
                                                 + re.escape(DAY_FORMATS[fmt]) + r'\d{4}', day):
                day = '-'.join(reversed(day.split(DAY_FORMATS[fmt])))
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
                raise ValueError(f"{day!r} is no day in the form the mapping says ({fmt})")
            out['lines'].append({'ref': (r.get(cols.get('ref', '')) or str(n)).strip(), 'day': day,
                                 'value_day': (r.get(cols.get('value_day', '')) or None),
                                 'count': cnt, 'unit': (r.get(cols.get('currency', '')) or m.get('currency')),
                                 'text': (r.get(cols.get('text', '')) or None), 'party': (r.get(cols.get('party', '')) or None),
                                 'code': (r.get(cols.get('code', '')) or None)})
        except (ValueError, KeyError) as e:
            out['refused'].append((f"row {n}", str(e)))
    return out
