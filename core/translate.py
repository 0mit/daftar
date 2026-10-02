#!/usr/bin/env python3
"""translate — today's law and beans (v0.48.0, std-vocab 32.0) written in the core's statements, by the `replaces` map.

    python3 core/translate.py levels > core/law/levels.yaml    # the bodies' levels, from the law's `complexity`
    python3 core/translate.py layers > core/law/layers.yaml    # the flow law's sources and the files' standing
    python3 core/translate.py flows > core/law/flows.yaml      # the flow law: methods, rows, a logged pass's metadata
    python3 core/translate.py tools > core/law/tools.yaml      # the tools by their verbs, in their families (part 9)
    python3 core/translate.py vacancies > core/law/vacancies.yaml   # what nothing takes up yet, at its place (part 9)
    python3 core/translate.py kinds  > core/law/kinds.yaml     # the kinds, from the law's `gene`
    python3 core/translate.py systems > core/law/systems.yaml  # a standard's rows (systems, places, protocols,
                                                               # quantities, registries), from the law's tables of it
    python3 core/translate.py law                              # every generated file of core/law/ written again
    python3 core/translate.py garden <garden> <copy>           # a copy of the garden, its beans in statements, counted

THE LAW'S ROWS are generated from the law that has them, never typed, until std-vocab is retired (v1) and they become
the source; test/core_standards.py holds each file equal to what the law generates. The detailed levels are rows of our
knowledge tree (Q3): `complexity` names `logos` where the core says `reason`, and `stands_on` where it says `stands`; the
frame and λόγος are the face's own. The kinds are `gene`: soma is a body, lekton the sayable, and `rung: logos` is `rung: reason`.

A GARDEN IS TRANSLATED INTO A COPY, never in place: every file is copied, the beans and mappings are rewritten in
statements, and VOCAB.md gains the rows the beans need (the garden's own kinds, the namespaces its names are given in, the
rows it added to the standards' tables). Each term goes the way verbs.yaml's `replaces` map sends it:

  provenance → a knowing act: observed → read, asserted-by-human → say, inferred and generated-by-tool → derive,
               stated-in-document → say; its `by` the bean the text names; an agent's, the session bean whose start
               and stop hold the act's moment, its reading then `derive` (ratified 2026-10-01); else `unknown` with the
               text as its note; its
               `at` the moment the clock wrote that day: the heading of the journal entry that names the bean, else the
               commit that first wrote the day. A party's own provenance is an act of its own.
  identity   → name: by the standard's namespace where the anchor establishes (fqdn → dns, mac → ieee-eui48, email →
               mail, phone → e164, garden_id → garden-id, content_hash → sha-256 and its bare digest, the key
               fingerprints → openpgp, ssh, wireguard); a qualified minted name → garden; an issuer's → a namespace
               named for the issuer; any other → the anchor's key as the garden's namespace (`anchor-<key>`); a name the
               garden minted for the bean itself → the bean, no statement (core/law/namespaces.yaml, 2026-10-01)
  owned_by   → own; an owner outside the ledger → `{ someone: org }`, its words the note   responsibility → answer
  via        → come                  located_at, lives_in → be                           part_of → part
  instance_of, os → run              depends_on, consumes, reaches → need                knowledge → use, classify
  risks      → fail                  capabilities → can, on the two squares              roles → do
  produces   → produce (an artifact: a being, a position, or the words that say it)
  a unit     → its UCUM code (core/law/units.yaml), the law's English name attached there; a garden's own unit a row of
               VOCAB.md's `units`, its code composed from the law's (`gigabyte-per-day` is `GBy/d`)
  parties, over, words → agree, a party's yes only: one with no acceptance on record is a party kept in `details`
  clauses → can, on the permission square            transactions → pay, bear
  vacancies  → the `vacant` of the garden's row the position names (the rule `vacancy`)
  endpoints  → serve                 timing start/stop → be, as presence                 workspace.opened_at → open

PROSE OF SEVERAL LINES IS A BLOCK SCALAR (`|`), and a statement holding it a block mapping: a line feed is text only
there (the rule `form`).

WHAT FITS NO VERB GOES TO `details`, WHOLE: a term no verb takes keeps its whole subtree there, under its name; what is
left of an entry a verb took stays there under the term and the statement's id. The front matter's comments go to
`details.comments`, each with the item it sat on.

THE COPY IS A GARDEN OF THE CORE: its GARDEN.md pins `core@<version>`, the law's own, and its VOCAB.md holds no pin (the
law a garden runs is GARDEN.md's alone); both are read back and must hold what they held but the pin. The translator
reads the words of std-vocab 32 (`READS`), and refuses a garden that runs older ones. bin/dmupgrade.py adopts the core
in place from this copy (v1 part 4).

THE COUNT IS THE PROOF. Every leaf of the old front matter — every value, as written — is given exactly one place: a
statement's role, the header, `details`, or a derivation the law makes (a bean's `nature` is its kind's; before the law,
the owner answers). The written file is read back and each place is checked to hold its value; the comments are counted
too. The command prints the count for the garden, and exits 1 if anything is unplaced or not found where it was put."""
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse  # noqa: E402 — today's reader of today's law, and the one splitter of a front matter
from core import frame  # noqa: E402

LAW = os.path.join(ROOT, 'seed', 'std-vocab.md')
READS = 32                                  # the major version of today's law whose words a garden is translated from
FACE_LEVELS = {'space-time', 'logos'}       # the face's own: the frame of bodies, and reason
RENAMED = {'logos': 'reason'}               # the law's Greek word, where the core uses the role's
NATURES = {'soma': 'body', 'lekton': 'sayable'}
ACTS = {'observed': 'read', 'asserted-by-human': 'say', 'stated-in-document': 'say', 'inferred': 'derive',
        'generated-by-tool': 'derive'}
MODES = {'legal': 'law', 'technical': 'keeping', 'experience': 'meeting', 'financial': 'paying'}
PERMISSION = {'required': 'obligatory', 'omissible': 'omissible', 'permitted': 'permitted', 'forbidden': 'forbidden'}
FEASIBILITY = {'possible': 'possible', 'impossible': 'impossible', 'contingent': 'contingent'}
DOCUMENTS = ('beans', 'mappings')
AGENT = re.compile(r'\bagent\b', re.I)     # a provenance's `by` that names an agent, in the prose it is written in


def old_law(path=LAW):
    with open(path, encoding='utf-8') as fh:
        return dmparse.loads(dmparse.split_front_matter(fh.read())[0]) or {}


def _q(s):
    """A scalar as YAML writes it plainly where it can, quoted where it must be: in JSON's escapes, which YAML's double
    quotes read, so a backslash, a quote or a line break comes back as written."""
    s = str(s)
    plain = s and s[0].isalnum() and all(c.isalnum() or c in '-_' for c in s) \
        and s.lower() not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off')
    return s if plain else json.dumps(s, ensure_ascii=False)


# ================================================================================================ the law's rows
def levels(law):
    """The text of core/law/levels.yaml: every level of `complexity` that is not the face's own, in its order."""
    out = ["# The bodies' levels: rows of our knowledge tree, the steps of the lines of bodies beside the face's own.",
           "# GENERATED by `python3 core/translate.py levels` from std-vocab " + str(law.get('version')) + "'s `complexity`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "levels:"]
    for r in law.get('complexity') or []:
        lv = str(r['level'])
        if lv in FACE_LEVELS:
            continue
        stands = []
        for s in r.get('stands_on') or []:
            at = RENAMED.get(str(s['level']), str(s['level']))
            stands.append("{ at: %s, as: %s%s }" % (_q(at), _q(s['as']), f", while: {_q(s['while'])}" if s.get('while') else ''))
        out.append(f"  - {{ level: {_q(lv)}, line: {_q(RENAMED.get(str(r['line']), str(r['line'])))}, "
                   f"stands: [{', '.join(stands)}], meaning: {_q(r.get('meaning', ''))} }}")
    return '\n'.join(out) + '\n'


def layers(law, face_layers):
    """The text of core/law/layers.yaml: the flow law's sources (every layer of `layers` the face does not name) and the
    standing of files (each layer's `holds`), from the law's `layers`."""
    rows = [r for r in law.get('layers') or [] if isinstance(r, dict) and r.get('layer')]
    out = ["# The layers beside the face's own, and which files stand in which: rows of the flow law and of the layer map.",
           "# GENERATED by `python3 core/translate.py layers` from std-vocab " + str(law.get('version')) + "'s `layers`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "flow_sources: [" + ', '.join(_q(r['layer']) for r in rows if r['layer'] not in face_layers) + "]",
           "standing:"]
    for r in rows:
        holds = [str(h) for h in r.get('holds') or []]
        if holds:
            out.append(f"  - {{ layer: {_q(r['layer'])}, holds: [{', '.join(_q(h) for h in holds)}] }}")
    return '\n'.join(out) + '\n'


def kind_row(g):
    """A row of `gene` (or a garden's `local_gene`) as a row of the core's kinds."""
    row = {'kind': str(g['genos']), 'nature': NATURES.get(str(g.get('of_nature')), str(g.get('of_nature')))}
    if g.get('level'):
        row['level'] = RENAMED.get(str(g['level']), str(g['level']))
    if g.get('rung'):
        row['rung'] = RENAMED.get(str(g['rung']), str(g['rung']))
    return row


def kinds(law):
    out = ["# The kinds of being a bean records, each with its nature, and its level and rung where it has them.",
           "# GENERATED by `python3 core/translate.py kinds` from std-vocab " + str(law.get('version')) + "'s `gene`;",
           "# a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.",
           "kinds:"]
    for g in law.get('gene') or []:
        row = kind_row(g)
        out.append("  - { " + ', '.join(f"{k}: {_q(v)}" for k, v in row.items()) + " }")
    return '\n'.join(out) + '\n'


# THE STANDARDS' ROWS (v1, part 1): every table the core reads from an outside standard, generated from the law that has
# them, so there is one source until std-vocab is retired and these files become it. Each file holds its tables in the
# standard's own columns, and each table's form from `registry_forms`: which columns every row holds, which it may, and
# where a column's values come from. Two tables take the core's names; a value in a word the core renamed is written in
# the core's (the natures, the knowing acts, λόγος); prose is kept as written. Each entry: (what the file holds, its
# tables as (the core's name, the law's)).
STANDARDS = {
    'systems': (
        "The systems of position: calendars, scales, coordinates, filesystems and addresses, each with the one form "
        "its positions are written in (ISO 8601, CLDR, EPSG, POSIX and Windows path grammars, RFC 3986, the IANA ports…), "
        "the shape their columns take, and the operating systems and storage formats that name a filesystem's grammar.",
        (('systems', 'anchor_systems'), ('system_shape', 'system_shape'), ('operating_systems', 'operating_systems'),
         ('storage_formats', 'storage_formats'))),
    'places': (
        "The frame of places: the bodies (IAU, IUGG) and the reference systems fixed to them (EPSG, ISO 19111), with "
        "their kinds and frames.",
        (('bodies', 'bodies'), ('reference_system_kinds', 'reference_system_kinds'),
         ('reference_frames', 'reference_frames'), ('reference_systems', 'reference_systems'))),
    'protocols': (
        "The protocols, by the IANA protocol and service registries' names: the layer each is at, what it rides on, "
        "its transport and its default ports.",
        (('protocols', 'net_protocols'),)),
    'quantities': (
        "The quantities (ISO 80000, SI): the dimensions, what each quantity is of and on which scale, and the kinds of "
        "accuracy a maker states (GUM). Their units are core/law/units.yaml's, in UCUM; currencies are ISO 4217's.",
        (('dimensions', 'dimensions'), ('quantities', 'quantities'), ('accuracy_kinds', 'accuracy_kinds'))),
    'registries': (
        "Where a standard's own table is kept (seed/knowledge/), and the schemes of our knowledge tree: ISCED-F 2013, "
        "ISCO-08, the technologies, the geologic chart and the rest, with what each column of a scheme says.",
        (('registry_files', 'registry_files'), ('knowledge_schemes', 'knowledge_schemes'),
         ('knowledge_scheme_form', 'knowledge_scheme_form'))),
}
TABLE_NAMES = {old: new for _what, tables in STANDARDS.values() for new, old in tables if new != old}
VALUE_WORDS = {'nature': NATURES, 'act': {'derived': 'derive', 'said': 'say', 'read': 'read', 'made': 'make'},
               'level': RENAMED, 'rung': RENAMED}
WIDTH = 120


def in_core_words(x, key=None):
    """`x` (read as strings) with each value in a word the core renamed written in the core's, and a form's `registry`
    named by the core's name of its table."""
    if isinstance(x, dict):
        return {k: in_core_words(v, k) for k, v in x.items()}
    if isinstance(x, list):
        return [in_core_words(v, key) for v in x]
    words = TABLE_NAMES if key == 'registry' else VALUE_WORDS.get(key, {})
    return words.get(x, x)


def _flow(x):
    if isinstance(x, dict):
        return '{ ' + ', '.join(f"{_q(k)}: {_flow(v)}" for k, v in x.items()) + ' }' if x else '{}'
    if isinstance(x, list):
        return '[' + ', '.join(_flow(v) for v in x) + ']'
    return _q(x)


def _block(key, x, ind):
    """The lines of `key: x` at the indent `ind`: one line where it fits, else each part on its own."""
    one = f"{ind}{_q(key)}: {_flow(x)}"
    if not isinstance(x, (dict, list)) or not x or len(one) <= WIDTH:
        return [one]
    out = [f"{ind}{_q(key)}:"]
    for k, v in x.items() if isinstance(x, dict) else ():
        out += _block(k, v, ind + '  ')
    for v in x if isinstance(x, list) else ():
        out += _item(v, ind + '  ')
    return out


def _item(v, ind):
    one = f"{ind}- {_flow(v)}"
    if not isinstance(v, dict) or not v or len(one) <= WIDTH:
        return [one]
    out = []
    for k, w in v.items():
        out += _block(k, w, ind + '  ')
    out[0] = f"{ind}- {out[0][len(ind) + 2:]}"
    return out


def standard(law, name):
    """The text of core/law/<name>.yaml: the tables of STANDARDS[name] and their forms, from the law read as strings."""
    what, tables = STANDARDS[name]
    said = (f"GENERATED by `python3 core/translate.py {name}` from std-vocab {law.get('version')}'s "
            + ', '.join(f"`{old}`" for _new, old in tables) + "; a change is made there, or by a RULE-CHANGE that "
            "moves these rows, never by hand here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    forms = law.get('registry_forms') or {}
    for new, old in tables:
        out += _block(new, in_core_words(law.get(old)), '')
    held = {new: in_core_words(forms[old]) for new, old in tables if old in forms}
    out += _block('forms', held, '') if held else []
    return '\n'.join(out) + '\n'


SIGNS = {'is': '=', 'in': '∈', 'at_least': '≥', 'at_most': '≤', 'exists': '∃', 'absent': '∄'}   # today's comparator
# words the core names by their Unicode signs (core.yaml `comparators`); `reached`, `at_step` and `refers_to` have none
LINE_FORMS = (('series', 'series'), ('step', 'steps'), ('reading', 'selections'))   # a form of a line, and the term it was
LINE_TAKEN = {'series': ('note',), 'step': ('id', 'do', 'by', 'next', 'note'), 'reading': ('note',)}   # what the
# statement says in its roles and its `note`, not in its form: a step's id, what is done (`as`), who acts (`by`), and the
# steps it leads on to (`to`) — the words of a way on, where it has any, kept by the step it leads to in `ways`
WAYS = {'in': {'keyed_by': 'to', 'entries': {
    'to': {'required': 'true', 'in': {'type': 'kebab'}, 'meaning': "the step it leads to: one of the step's `to`"},
    'when': {'in': 'prose', 'meaning': "when this way on is taken: said by each of two or more"},
    'note': {'in': 'prose', 'meaning': "optional prose"}}},
    'meaning': "the words of a way on, one entry for each step it leads to that has any: when it is taken, a note"}


def _kind_words(x):
    """A reading's grammar in the core's words: a kind is `kind`, of the core's `kinds`, where today's was `genos`."""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out['kind' if k == 'genos' else k] = _kind_words(v)
        if out.get('registry') == 'gene':
            out['registry'], out['take'] = 'kinds', 'kind'
        return out
    if isinstance(x, list):
        return [_kind_words(v) for v in x]
    return re.sub(r'\bgenos\b', 'kind', x) if isinstance(x, str) else x


def lines(law):
    """The text of core/law/lines.yaml: the grammar of a reading (its operations, comparisons, aggregates, ordering keys,
    selection_form and pin_form) and the forms of a line — a series, a step of a walk, a reading — each the attributes
    today's term holds, from the law read as strings."""
    what = ("The forms of a line (v1 part 6): what a series holds along its line, how a walk goes at a step, and the steps "
            "of a reading, each held by a statement of its verb (`record`, `step`, `reckon`) in one qualifier of the "
            "shape `form`; and the grammar a reading is read in — its closed list of operations, the comparisons a "
            "condition names (by the core's Unicode sign where it has one), the aggregates, the ordering keys and a "
            "pin's form.")
    said = (f"GENERATED by `python3 core/translate.py lines` from std-vocab {law.get('version')}'s `operations`, "
            "`comparators`, `aggregates`, `ordering_keys`, `selection_form`, `pin_form` and the terms `series`, "
            "`steps` and `selections`; a change is made there, or by a RULE-CHANGE that moves these rows, never by hand "
            "here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    comps = []
    for c in law.get('comparators') or []:
        row = dict(c)
        if row.get('comparator') in SIGNS:
            row = {'comparator': row['comparator'], 'sign': SIGNS[row['comparator']], **{k: v for k, v in row.items()
                                                                                         if k != 'comparator'}}
        comps.append(row)
    comps += [{'comparator': s, 'sign': s, 'monotone': 'false', 'meaning': m} for s, m in (
        ('≠', "the value at the path is not the operand: the core's sign, which today's words lacked"),
        ('<', "less than the operand, read as `at_least` is: the core's sign, which today's words lacked"),
        ('>', "more than the operand, read as `at_least` is: the core's sign, which today's words lacked"))]
    for key, x in (('operations', law.get('operations')), ('comparisons', comps),
                   ('aggregates', law.get('aggregates')), ('ordering_keys', law.get('ordering_keys')),
                   ('selection_form', law.get('selection_form')), ('pin_form', law.get('pin_form'))):
        out += _block(key, _kind_words(in_core_words(x)), '')
    terms = {t.get('term'): t for t in law.get('terms') or [] if isinstance(t, dict)}
    forms = {}
    for form, term in LINE_FORMS:
        schema = dict((terms[term].get('schema') or {}))
        attrs = {k: v for k, v in (schema.get('attrs') or {}).items() if k not in LINE_TAKEN.get(form, ())}
        row = {'meaning': terms[term].get('meaning'), 'replaces': term}
        for k in ('entry_one_of',):
            if k in schema:
                row['one_of'] = schema[k]
        if form == 'step':
            attrs['ways'] = WAYS
        row['attrs'] = attrs
        forms[form] = row
    out += _block('forms', _kind_words(in_core_words(forms)), '')
    return '\n'.join(out) + '\n'


# THE FORMS OF A MEASURE (v1 part 7): what an extent, a repetition, an uncertainty, a mechanism and a coefficient are, as
# today's law writes them, and the forms a statement holds them in — a region and a repetition on a line, what a clause
# holds beside its words, and what a placement holds beside its position. A form's attribute is today's term's, less what
# the statement says in its roles: a clause's words (`of`), who it binds (`by`), whom it is owed to (`to`) and its figure;
# a placement's position and its host (`at`). A clause's form is held by its `can`, or by the position on the
# permission square an agreement takes of the statement it asks (`obligatory: { of: <a pay>, through, clause }`).
MEASURE_FORMS = (('clause', 'clauses', ('what', 'by', 'to', 'note', 'permission')),
                 ('placement', 'located_at', ('system', 'at', 'host', 'note')))
MEASURE_TABLES = ('extent_form', 'recurrence_form', 'uncertainty_form', 'compatibility', 'mechanism_form',
                  'coefficient_form')
FORM_RULES = {'extent': ('extent_form', ('requires', 'open_ends', 'not_a_recurrence', 'not_a_calendar_bucket', 'lines')),
              'recurrence': ('recurrence_form', ('requires',))}


def measures(law):
    """The text of core/law/measures.yaml: the lines a region or a repetition lies on (today's aspects, by the dimension
    their systems are in), the forms of an extent, a repetition and an uncertainty, compatibility, a mechanism's and a
    coefficient's rows, and the forms `extent`, `recurrence`, `clause` and `placement`, from the law read as strings."""
    what = ("The forms of a measure (v1 part 7): the lines a region or a repetition lies on, how a region is bounded, how "
            "a repetition strides, how well a value is known, when two values agree within their uncertainty, and the "
            "forms a statement holds them in — `extent` and `recurrence`, what a clause of an agreement holds beside its "
            "words (`can`'s `clause`) and what a placement holds beside its position (`be`'s `placed`).")
    said = (f"GENERATED by `python3 core/translate.py measures` from std-vocab {law.get('version')}'s `aspects`, "
            "`placement` (what each placement takes of its host: `takes`), "
            + ', '.join(f"`{t}`" for t in MEASURE_TABLES) + " and the terms `clauses` and `located_at`; a change is "
            "made there, or by a RULE-CHANGE that moves these rows, never by hand here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    figs = {f.get('figure'): f for f in law.get('figures') or [] if isinstance(f, dict)}
    lines_ = []
    for a in law.get('aspects') or []:
        if not isinstance(a, dict) or not a.get('aspect'):
            continue
        fig = figs.get(a.get('figure')) or {}
        row = {'line': a['aspect'], 'region': 'true' if fig.get('extent') == 'possible' else 'false'}
        if fig.get('extent') != 'possible':
            row['why'] = fig.get('extent_why') or "a position on it is a modality with nothing between: no region, " \
                                                  "and nothing on it repeats"
        else:
            for k in ('metered', 'lines'):
                if a.get(k) is not None:
                    row[k] = a[k]
            row['systems'] = (a.get('domain') or {}).get('systems')
        if a.get('meaning'):
            row['meaning'] = a['meaning']
        lines_.append(row)
    out += _block('lines', in_core_words(lines_), '')
    takes = [{'placement': r.get('code'), 'takes': r.get('takes') or 'none'} for r in law.get('placement') or []
             if isinstance(r, dict) and r.get('code')]
    out += _block('takes', takes, '')
    for t in MEASURE_TABLES:
        out += _block(t, in_core_words(law.get(t)), '')
    terms = {t.get('term'): t for t in law.get('terms') or [] if isinstance(t, dict)}
    forms = {}
    for form, (table, meta) in FORM_RULES.items():
        rows = law.get(table) or {}
        forms[form] = {'meaning': {'extent': "one region of a line: ", 'recurrence': "a repetition along a line, by a "
                                   "rule: "}[form] + (rows.get('requires') or ''), 'replaces': table,
                       'attrs': {k: {'meaning': v} for k, v in rows.items() if k not in meta}}
        if form == 'recurrence':
            forms[form]['one_of'] = ['every', 'each']
    for form, term, taken in MEASURE_FORMS:
        schema = dict(terms[term].get('schema') or {})
        attrs = {k: v for k, v in (schema.get('attrs') or {}).items() if k not in taken}
        if form == 'placement' and isinstance(attrs.get('openness'), dict):   # how far a position reaches is said
            attrs['openness'] = {k: v for k, v in attrs['openness'].items() if k != 'required'}   # where known: a
        forms[form] = {'meaning': terms[term].get('meaning'), 'replaces': term, 'attrs': attrs}   # `be` says where
    out += _block('forms', _kind_words(in_core_words(forms)), '')
    return '\n'.join(out) + '\n'


def law_as_strings(path=LAW):
    """Today's law read as the core reads a document: every scalar a string, as written."""
    from core import read
    with open(path, encoding='utf-8') as fh:
        return read.loads(dmparse.split_front_matter(fh.read())[0] or '', path) or {}


# THE FLOW LAW (v1 part 8): which passes between layers stand. Today's row sends material to a layer, or to an ORIGIN —
# `{act, nature?, by?}`, a value placed in the estate at a position of that origin — by a `method`. The core's row is a
# pass's valency: `from` a layer, `to` a layer, `through` a method or a verb, and, for a pass into the estate, the knowing
# act what it carries is known by there (`as`). So the law is rewritten as it is generated: an origin is `to: estate` and
# its act the row's `as`; today's `take-down` is the act `say` itself, by which a person's words come into the ledger (the
# refinery named it `remove`, which reads as its opposite); `pass-on` and `upgrade` are `forward` and `adopt`, as the
# refinery named them. A value the LAW owns (`by: law`) is a row's filler, judged by its table (rule valency): no pass
# carries it, and the row goes. The SAVE's reading of the clock (`by: save`) is `through: stamp`: only the clock stamps,
# and rule `knowing` refuses a moment typed. `ratified` stays a grant: refused until a garden's own row grants a party.
FLOW_METHODS = {'take-down': 'say', 'pass-on': 'forward', 'upgrade': 'adopt'}
FLOW_ACTS = {'said': 'say', 'read': 'read', 'derived': 'derive', 'made': 'make'}
FLOW_DROPPED = {'law-owned': "a value the law owns is the filler of a role whose shape is a row, judged by its table "
                             "(rule valency): no pass carries it"}


def flows(law):
    """The text of core/law/flows.yaml: the methods a pass is made by (today's, renamed, less those that are verbs or acts
    of the core), the flow table rewritten in the pass's valency, the metadata a logged pass may carry, and the rows that
    have no place in the core, each with why."""
    what = ("The flow law (v1 part 8): how a pass between layers is made, which passes stand, and what a logged pass may "
            "carry beside its statement. A row holds a pass made `from` one of its layers, `to` one of its layers, "
            "`through` one of its methods (a method, or a verb: say, read, derive, make, take, serve, hold), and, where "
            "it names `as`, carrying statements known there by one of those acts. A pass no row holds is refused. Of the "
            "rows that hold it, the nearest decides — a row that names `as` is nearer than one that names only layers — "
            "and of two as near, a refusal. `ratified` is refused until a garden's own row grants the party it names, "
            "with the basis it grants on (a RULE-CHANGE); a garden's own rows otherwise only refuse. `keeper: release` "
            "holds only for a file the release keeps.")
    said = (f"GENERATED by `python3 core/translate.py flows` from std-vocab {law.get('version')}'s `methods`, `flows` "
            "and `pass_metadata`, each origin rewritten as `to: estate` and the act it names (`as`); a change is made "
            "there, or by a RULE-CHANGE that moves these rows, never by hand here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    verbs = {'derive', 'make', 'take', 'serve', 'hold'}
    out.append("methods:")
    for m in law.get('methods') or []:
        name = FLOW_METHODS.get(m.get('method'), m.get('method'))
        if name in verbs or name == 'say':
            continue
        out.append(f"  - {{ method: {_q(name)}, meaning: {_q(m.get('meaning', ''))} }}")
    out.append("flows:")
    dropped = []

    def names(x):
        return [FLOW_METHODS.get(str(v), str(v)) for v in (x if isinstance(x, list) else [x])]

    def one(x):
        return _q(x[0]) if len(x) == 1 else '[' + ', '.join(_q(v) for v in x) + ']'
    for f in law.get('flows') or []:
        if f.get('flow') in FLOW_DROPPED:
            dropped.append((f['flow'], FLOW_DROPPED[f['flow']]))
            continue
        to, through, as_ = f.get('to'), names(f.get('method')), None
        if isinstance(to, dict):
            if to.get('by') == 'save':
                through = ['stamp']
            else:
                as_ = FLOW_ACTS[str(to.get('act'))]
            to = ['estate']
        else:
            to = to if isinstance(to, list) else [to]
        row = [f"flow: {_q(f['flow'])}", f"from: {one(f['from'] if isinstance(f['from'], list) else [f['from']])}",
               f"to: {one([str(t) for t in to])}", f"through: {one(list(dict.fromkeys(through)))}"]
        if as_:
            row.append(f"as: {as_}")
        row.append(f"grant: {f.get('grant')}")
        if f.get('keeper'):
            row.append(f"keeper: {f['keeper']}")
        row.append(f"why: {_q(f.get('why', ''))}")
        out.append("  - { " + ', '.join(row) + " }")
    out.append("metadata:")
    for m in law.get('pass_metadata') or []:
        out.append(f"  - {{ key: {_q(m.get('key'))}, in: {_q(m.get('in'))}, meaning: {_q(m.get('meaning', ''))} }}")
    out.append("dropped:")
    for name, why in dropped:
        out.append(f"  - {{ flow: {_q(name)}, why: {_q(why)} }}")
    return '\n'.join(out) + '\n'


# THE LAW TOOLS' LAW (v1 part 9): the tools by their verbs, and what the law offers that nothing takes up yet. A tool's
# verb is no statement's — `pass` is both — so today's `verbs` is the core's `tools`, each keyed `tool`.
def tools(law):
    """The text of core/law/tools.yaml: the families of what the tools are for, and each tool by its verb, with their
    forms."""
    what = ("The tools of the language (v1 part 9), each by its verb — `python3 bin/daftar.py <verb>` runs `bin/<verb>.py` "
            "— and the family of what it is for, by which the launcher lists them. A tool's verb is the command's and no "
            "statement's: `pass` is both, so a tool is keyed `tool`.")
    said = (f"GENERATED by `python3 core/translate.py tools` from std-vocab {law.get('version')}'s `tool_families` and "
            "`verbs`; a change is made there, or by a RULE-CHANGE that moves these rows, never by hand here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    out += _block('families', law.get('tool_families') or [], '')
    out += _block('tools', [{'tool': v.get('verb'), 'family': v.get('family')} for v in law.get('verbs') or []], '')
    forms = law.get('registry_forms') or {}
    fam = dict((forms.get('verbs') or {}).get('family') or {})
    fam['in'] = {'registry': 'families', 'take': 'family'}
    out += _block('forms', {'families': forms.get('tool_families'), 'tools': {'tool': 'required', 'family': fam}}, '')
    return '\n'.join(out) + '\n'


# A VACANCY in the core's address: `table:<t>` (a row of a table of the law), `figure:<f>` (a position on a figure),
# `form:<f>[.<attribute>]` (a value of a form's attribute; the form alone, one of its `one_of`), `details:<term>.<attr>`
# (what `details` keeps under today's term, its form still today's). Today's address of each, read from its head.
VACANCY_DROPPED = {
    'owned_by.entry_one_of': "the core's `own` takes any being as `by`, an agreement's bean among them, and an owner "
                             "outside the ledger is `someone` of a kind: there is no form of an owner to keep vacant",
    'responsibility.entry_one_of': "the core's `answer` takes any being as `by`, an agreement's bean among them, and one "
                                   "outside the ledger is `someone` of a kind: there is no form of a holder to keep vacant",
    'parties.entry_one_of': "the core's `agree` takes any being as `by`, and a party outside the ledger is `someone` of "
                            "a kind: there is no form of a party to keep vacant",
    'aspect:feasibility': "the core has two figures, and today's feasibility is the necessity figure over a `can`: its "
                          "`necessary` is the figure's, which other statements take, so the position this kept apart "
                          "has no place of its own",
}
VACANCY_FORMS = {'clauses': 'clause', 'series': 'series', 'steps': 'step'}     # today's term, and the core's form of it
VACANCY_DETAILS = ('analysis_cache',)                                           # kept in `details` (spec §16 item 7)


def vacancy_at(at, position, units):
    """(the core's address, the position there) of today's vacancy `at` / `position`, or (None, why) where the core has
    no place for it. `units` is units.yaml's code of each unit by its English name."""
    if at in VACANCY_DROPPED:
        return None, VACANCY_DROPPED[at]
    kind, _, rest = at.partition(':')
    if kind == 'registry':
        if rest == 'units':
            return 'table:units', units[position]
        if rest == 'facets':
            return 'table:modes', MODES[position]
        return 'table:' + TABLE_NAMES.get(rest, rest), position
    if kind == 'aspect':
        return 'figure:' + rest, position
    term, _, attr = at.partition('.')
    position = position.lower() if position in ('True', 'False') else position
    if term == 'words' and attr == 'form':
        return 'table:forms', position
    if term in VACANCY_FORMS:
        return 'form:' + VACANCY_FORMS[term] + ('' if attr == 'entry_one_of' else '.' + attr), position
    if term in VACANCY_DETAILS:
        return 'details:' + at, position
    raise SystemExit(f"translate vacancies: today's vacancy at {at!r} has no place in the core's map (core/translate.py "
                     f"vacancy_at): a person says where it goes")


def vacancies(law):
    """The text of core/law/vacancies.yaml: the reasons a position may be vacant, each vacancy of the standard in the
    core's address, and those the core has no place for, each with why."""
    from core import read
    what = ("What the law offers that nothing takes up yet (v1 part 9): a position declared ahead of its occupant, and "
            "why — a `prediction` (expected, with what brings it), `universal` (the standard holds it for any garden), "
            "`out-of-context` or `impossible`. A vacancy is at `table:<t>` (a row of a table), `figure:<f>` (a position "
            "on a figure), `form:<f>.<attribute>` (a value of a form's attribute; `form:<f>`, one of its `one_of`) or "
            "`details:<term>.<attribute>` (what `details` keeps under today's term). The law holds each at a place it "
            "has; that one is taken is evidence (`python3 bin/review.py --law`), never a refusal. A garden says a row of "
            "its own is vacant on the row (`vacant`), as rule vacancy reads it.")
    said = (f"GENERATED by `python3 core/translate.py vacancies` from std-vocab {law.get('version')}'s `vacancy_reasons` "
            "and `vacancies`, each written at its place in the core; a change is made there, or by a RULE-CHANGE that "
            "moves these rows, never by hand here.")
    out = ["# " + line for para in (what, said) for line in textwrap.wrap(para, WIDTH - 2)]
    units = {str(u.get('name')): str(u.get('unit'))
             for u in read.data(os.path.join(HERE, 'law', 'units.yaml')).get('units') or []}
    rows, dropped = [], []
    for v in law.get('vacancies') or []:
        at, pos = vacancy_at(str(v.get('at')), str(v.get('position')), units)
        if at is None:
            dropped.append({'at': v.get('at'), 'position': v.get('position'), 'why': pos})
        else:
            rows.append({'at': at, 'position': pos, 'reason': v.get('reason'),
                         'why': ' '.join(str(v.get('why') or '').split())})
    out += _block('reasons', law.get('vacancy_reasons') or [], '')
    out += _block('vacancies', rows, '')
    out += _block('dropped', dropped, '')
    out += _block('forms', {'vacancies': (law.get('registry_forms') or {}).get('vacancies'),
                            'dropped': {'at': 'required', 'position': 'required', 'why': 'required'}}, '')
    return '\n'.join(out) + '\n'


def generated(name):
    """The text the law generates for core/law/<name>.yaml."""
    if name == 'levels':
        return levels(old_law())
    if name == 'kinds':
        return kinds(old_law())
    if name == 'layers':
        from core import read
        return layers(old_law(), read.data(os.path.join(HERE, 'law', 'core.yaml')).get('layers') or [])
    if name == 'lines':
        return lines(law_as_strings())
    if name == 'measures':
        return measures(law_as_strings())
    if name == 'flows':
        return flows(law_as_strings())
    if name == 'tools':
        return tools(law_as_strings())
    if name == 'vacancies':
        return vacancies(law_as_strings())
    return standard(law_as_strings(), name)


GENERATED = ('levels', 'kinds', 'layers') + tuple(STANDARDS) + ('lines', 'measures', 'flows', 'tools', 'vacancies')


# ================================================================================================ a garden's beans
def leaves(x, path=()):
    """[(path, text)] of every value in `x` (read as strings): a scalar, or an empty map or list, which says something."""
    if isinstance(x, dict):
        if not x:
            return [(path, '{}')]
        return [l for k, v in x.items() for l in leaves(v, path + (str(k),))]
    if isinstance(x, list):
        if not x:
            return [(path, '[]')]
        return [l for i, v in enumerate(x) for l in leaves(v, path + (i,))]
    return [(path, x)]


def at_path(x, path):
    for p in path:
        if isinstance(x, dict) and (p in x or str(p) in x):
            x = x[p] if p in x else x[str(p)]
        elif isinstance(x, list) and isinstance(p, int) and p < len(x):
            x = x[p]
        else:
            return KeyError
    return x


def slug(s):
    s = re.sub(r'[^a-z0-9_-]+', '-', str(s).lower()).strip('-')
    return s if s and re.match(r'^[a-z0-9]', s) else 'x-' + s


class Journal:
    """The moments the clock wrote: each journal heading's moment and the text of its entry."""

    def __init__(self, root):
        self.entries = []
        try:
            with open(os.path.join(root, 'log', 'journal.md'), encoding='utf-8') as fh:
                cur = None
                for line in fh.read().split('\n'):
                    if line.startswith('## '):
                        cur = [line[3:].split(' · ', 1)[0].strip(), line]
                        self.entries.append(cur)
                    elif cur is not None:
                        cur[1] += '\n' + line
        except OSError:
            pass
        self.root = root

    def moment(self, bid, path, day):
        """(moment, how) for a bean's day of knowing: the last heading that day whose entry names the bean; else the
        moment of the commit that first wrote the day into the file; else (None, why)."""
        day = str(day)
        named = re.compile(r'(?<![\w-])' + re.escape(bid) + r'(?![\w-])')
        hits = [m for m, t in self.entries if m.startswith(day + ' ') and named.search(t)]
        if hits:
            return frame.one_form(hits[-1]), 'journal'
        for how in (['-S', day], ['--diff-filter=A']):     # the commit that wrote the day, else the one that made the file
            r = subprocess.run(['git', '-C', self.root, 'log', '--follow', '--format=%cI', *how, '--', path],
                               capture_output=True, text=True)
            first = (r.stdout.strip().split('\n') or [''])[-1].strip() if r.returncode == 0 else ''
            if first.startswith(day):
                return first, 'commit'
        # A BEAN MADE LATER THAN ITS DAY (split out of another, its `as_of` carried): its statements entered it when
        # the file was made, and that commit's moment is the act's; the day it carried stays in details, not lost
        if first:
            return first, f"made {first[:10]}, after its as_of {day}, which stays in details"
        return None, f"no heading names {bid} on {day}, and no commit wrote {day} into it or made it"


class Bean2:
    """One bean being written in statements, with the place each old leaf went to."""

    def __init__(self, bid, old, ctx, path):
        self.id, self.old, self.ctx, self.path = bid, old, ctx, path
        self.statements, self.ids = [], set()
        self.details = {}
        self.placed = {}                 # old leaf path -> (where, expected text)
        self.notes = []                  # what the translation could not do: a problem
        self.readings = []               # the `reckon` statements, whose paths the garden's second pass rewrites
        self.carried = []                # what it did another way, losing nothing: for the report

    # -- placing
    def take(self, path, where, text=None):
        """Old leaf `path` goes to `where`, holding `text` (its own value, unless transformed)."""
        if path in self.placed:
            raise ValueError(f"{self.id}: {path} placed twice")
        v = at_path(self.old, path) if text is None else text
        self.placed[path] = (where, '{}' if v == {} else '[]' if v == [] else v)

    def new_id(self, want):
        i, base = slug(want), slug(want)
        n = 2
        while i in self.ids:
            i, n = f"{base}-{n}", n + 1
        self.ids.add(i)
        return i

    def add(self, verb, roles, sid=None):
        roles = dict(roles)
        if sid:
            roles = dict(id=sid, **{k: v for k, v in roles.items() if k != 'id'})
        self.statements.append((verb, roles))
        return len(self.statements) - 1

    def role(self, i, *role):
        return ('statement', i) + role

    def leftover(self, base, dest):
        """What is left under old `base` goes to details at `dest`: a subtree no verb took, whole and in its own shape;
        of one a verb took part of, each part that is left, under the same keys (a list's index read as a key)."""
        sub = at_path(self.old, base)
        mine = leaves(sub, base)
        if all(p in self.placed for p, _v in mine):
            return
        if dest and not any(p in self.placed for p, _v in mine):
            self._put(dest, sub)
            for p, _v in mine:
                self.take(p, ('details',) + dest + p[len(base):])
            return
        for k in (range(len(sub)) if isinstance(sub, list) else list(sub)):
            self.leftover(base + (k,), dest + (k,))

    def _put(self, dest, v):
        d = self.details
        for k in dest[:-1]:
            k = str(k)
            if k in d and not isinstance(d[k], dict):
                raise ValueError(f"{self.id}: details.{'.'.join(map(str, dest))} collides with a value")
            d = d.setdefault(k, {})
        last = str(dest[-1])
        if last in d:
            raise ValueError(f"{self.id}: details.{'.'.join(map(str, dest))} is written twice — an old key and a term's "
                             f"leftover share a name")
        d[last] = v


def being(ref, ctx):
    """The being a v0.48 reference names: `{bean: x}` → x; anything else None."""
    if isinstance(ref, dict) and set(ref) == {'bean'} and isinstance(ref['bean'], str):
        return ref['bean']
    return None


def position(system, at, ctx):
    """A position written short for a long one ({system, at}): bare where exactly that system reads it, else tagged;
    None where neither reads as that system."""
    for text in (str(at), f"{system}:{at}"):
        try:
            p = frame.read(text, ctx.systems, ctx.zone)
        except frame.Refused:
            continue
        if p.system == system:
            return text
    return None


def a_position(text, ctx):
    """`text` where it reads as a position, in whichever system reads it; None for an empty value (nobody said) or one
    no system reads, which then stays in details as written."""
    if not isinstance(text, str) or not text:
        return None
    try:
        frame.read(text, ctx.systems, ctx.zone)
        return text
    except frame.Refused:
        return None


def by_of(text, ctx):
    """(being, note) for a provenance's `by` prose: the bean it opens with, else unknown; the prose as the note, unless it
    is exactly the bean's id."""
    t = str(text)
    first = re.split(r'[\s,(;]', t, maxsplit=1)[0]
    if first in ctx.beans:
        return first, (None if t == first else t)
    return 'unknown', t


def knowing(b, prov, base, of=None):
    """A knowing act made from a provenance record at old path `base`; returns its statement index or None."""
    if not isinstance(prov, dict):
        return None
    act = ACTS.get(prov.get('src'))
    if act is None:
        return None
    who, note = by_of(prov.get('by', ''), b.ctx)
    moment, how = b.ctx.journal.moment(b.id, b.path, prov.get('as_of'))
    if who == 'unknown' and AGENT.search(str(prov.get('by', ''))) and moment:
        # AN AGENT'S ACT IS ITS SESSION'S (ratified 2026-10-01): the session bean whose start and stop hold the act's
        # moment, and only one; an agent's reading is `derive`, since `read` takes a body
        session = b.ctx.session_at(moment)
        if session:
            who = session
            act = 'derive' if act == 'read' else act
    roles = {'by': who}
    if of:
        roles['of'] = of
    if act == 'derive':
        roles['from'] = 'unknown'
    roles['at'] = moment if moment else 'unknown'
    there = garden_bean(b.ctx, prov.get('garden')) if moment else None
    if there:                            # KNOWN IN ANOTHER GARDEN (v1 part 8): its bean here, beside the moment
        roles['at'] = [moment, there]
    if note is not None:
        roles['note'] = note
    i = b.add(act, roles)
    b.take(base + ('src',), ('verb', i), act)           # the act, with the nature of its `by`, is the src (§3)
    if 'by' in prov:
        b.take(base + ('by',), b.role(i, 'note') if note is not None else b.role(i, 'by'), prov['by'])
    if there:
        b.take(base + ('garden',), b.role(i, 'at', 1), there)
    if 'as_of' in prov:
        if moment and str(moment).startswith(str(prov['as_of'])):
            b.take(base + ('as_of',), b.role(i, 'at', 0) if there else b.role(i, 'at'), moment)
        elif moment:
            b.carried.append(f"{'.'.join(map(str, base))}.as_of: {how}")
        else:
            b.notes.append(f"{'.'.join(map(str, base))}.as_of: {how}")
    return i


def garden_bean(ctx, gid):
    """The `garden` bean of this garden that names the garden `gid` (today's `garden_id` anchor), or None."""
    if not isinstance(gid, str):
        return None
    if getattr(ctx, '_gardens', None) is None:
        ctx._gardens = {}
        d = os.path.join(ctx.root, 'beans') if getattr(ctx, 'root', None) else None
        for f in sorted(os.listdir(d)) if d and os.path.isdir(d) else []:
            try:
                fm = dmparse.loads(dmparse.read(os.path.join(d, f))[0] or '') if f.endswith('.md') else None
            except Exception:
                fm = None
            if isinstance(fm, dict) and fm.get('genos') == 'garden':
                for a in (fm.get('identity') or {}).get('anchors') or []:
                    if isinstance(a, dict) and a.get('key') == 'garden_id':
                        ctx._gardens[str(a.get('value'))] = f[:-3]
    return ctx._gardens.get(gid)


def anchors_namespace(key):
    return f"anchor-{slug(key)}"


# THE STANDARDS' NAMESPACES ARE THE CORE'S (core/law/namespaces.yaml, ratified 2026-10-01): an anchor that establishes
# is a name its standard gives — the guides' form — and one that only corroborates keeps a row of the garden's own,
# which gives no name once, so that two beans sharing it are no clash. `mail` and `e164` give no name once anyway.
CORE_NAMESPACES = {'fqdn': 'dns', 'mac': 'ieee-eui48', 'email': 'mail', 'phone': 'e164', 'garden_id': 'garden-id',
                   'content_hash': 'sha-256', 'openpgp_fingerprint': 'openpgp', 'ssh_key_fingerprint': 'ssh',
                   'wg_pubkey': 'wireguard'}
SHARED = ('mail', 'e164')
QUALIFIED_NAME = re.compile(r'^[0-9a-f]{12}/[a-z][a-z0-9-]*:.+$')


def translate_bean(path, rel, ctx):
    """(text, Bean2) of the bean at `path` written in statements."""
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    head, body = dmparse.split_front_matter(text)
    from core import read
    old = read.loads(head or '') or {}
    bid = os.path.basename(path)[:-3]
    b = Bean2(bid, old, ctx, rel)
    header = {'bean': bid}
    is_mapping = 'mapping' in old and 'genos' not in old
    if is_mapping:
        header['kind'] = old.get('kind')
        if old.get('mapping') == bid:
            b.take(('mapping',), ('header', 'bean'), bid)
        b.take(('kind',), ('header', 'kind'))
    else:
        header['kind'] = old.get('genos')
        if 'genos' in old:
            b.take(('genos',), ('header', 'kind'))
        if old.get('bean') == bid:
            b.take(('bean',), ('header', 'bean'))
    for k in ('title', 'summary'):
        if k in old and isinstance(old[k], str):
            header[k] = old[k]
            b.take((k,), ('header', k))
    if isinstance(old.get('tags'), list) and all(isinstance(t, str) for t in old['tags']):
        header['tags'] = old['tags']
        for i, _t in enumerate(old['tags']):
            b.take(('tags', i), ('header', 'tags', i))
        if not old['tags']:
            b.take(('tags',), ('header', 'tags'), '[]')
    kind = ctx.kinds.get(header['kind']) or {}
    if 'nature' in old and NATURES.get(old['nature']) == kind.get('nature'):
        b.take(('nature',), ('derived', 'the nature of its kind'), old['nature'])

    # -- the knowing act of the whole bean
    blanket = knowing(b, old.get('provenance'), ('provenance',)) if 'provenance' in old else None

    # -- a garden recorded here as a rehearsal or a test (today's `test` on a `garden` bean): `rehearse` (v1 part 8)
    if old.get('genos') == 'garden' and isinstance(old.get('test'), str):
        j = b.add('rehearse', {'by': 'self', 'of': old['test']})
        b.take(('test',), b.role(j, 'of'), old['test'])

    # -- identity: each anchor a name — by the namespace that gives it (core/law/namespaces.yaml, an issuer's, or the
    # garden's own row); a name this garden minted for the bean itself is the bean, and no statement
    for i, a in enumerate((old.get('identity') or {}).get('anchors') or []):
        if isinstance(a, dict) and isinstance(a.get('key'), str) and isinstance(a.get('value'), str):
            key, val, est = a['key'], a['value'], a.get('establishing') == 'true'
            if key == 'identifier' and val == f"{old.get('genos')}:{bid}":
                b.take(('identity', 'anchors', i, 'key'), ('derived', 'the bean is its own name in its garden'))
                b.take(('identity', 'anchors', i, 'value'), ('derived', 'the bean is its own name in its garden'))
                b.leftover(('identity', 'anchors', i), ('identity', 'anchors', b.new_id(key)))
                continue
            issuer = being(a.get('issuer'), ctx) if isinstance(a.get('issuer'), dict) else None
            text = val
            if key == 'identifier' and QUALIFIED_NAME.match(val):
                ns = 'garden'
            elif key == 'identifier' and issuer:
                ns = issuer                          # an issuer's numbers: a namespace of the garden's, named for it
                ctx.namespace(ns, a)
            elif key in CORE_NAMESPACES and (est or CORE_NAMESPACES[key] in SHARED):
                ns = CORE_NAMESPACES[key]
                if key == 'content_hash' and val.startswith('sha256:'):
                    text = val[len('sha256:'):]       # the namespace says sha-256: the name is the digest
            else:
                ns = anchors_namespace(key)
                ctx.namespace(ns, a)
            sid = b.new_id(f"{key}")
            j = b.add('name', {'by': ns, 'of': 'self', 'as': text}, sid)
            b.take(('identity', 'anchors', i, 'key'), b.role(j, 'by'), ns)
            b.take(('identity', 'anchors', i, 'value'), b.role(j, 'as'), text)
            if issuer:
                b.take(('identity', 'anchors', i, 'issuer', 'bean'), b.role(j, 'by'), ns)
            b.leftover(('identity', 'anchors', i), ('identity', 'anchors', sid))

    # -- the four questions
    ob = old.get('owned_by')
    owner = None
    if isinstance(ob, dict):
        roles, takes = {'of': 'self'}, []
        if being(ob.get('owner'), ctx):
            owner = roles['by'] = being(ob['owner'], ctx)
            takes.append((('owned_by', 'owner', 'bean'), ('by',)))
        elif ob.get('crown') == 'true':
            owner = roles['by'] = 'theone'
            takes.append((('owned_by', 'crown'), ('by',), 'theone'))
        elif isinstance(ob.get('external'), str):
            roles['by'] = {'someone': 'org'}  # an owner outside the ledger, named in prose and by no bean here: someone
            roles['note'] = ob['external']    # nobody named here, of the kind that owns from outside (seed/COOKBOOK.md)
            takes.append((('owned_by', 'external'), ('note',)))
        elif being(ob.get('from'), ctx):
            roles['from'] = being(ob['from'], ctx)
            takes.append((('owned_by', 'from', 'bean'), ('from',)))
        if len(roles) > 1:
            if isinstance(ob.get('note'), str) and 'note' not in roles:
                roles['note'] = ob['note']
                takes.append((('owned_by', 'note'), ('note',)))
            j = b.add('own', roles, b.new_id('own'))
            for t in takes:
                b.take(t[0], b.role(j, *t[1]), *t[2:])
        b.leftover(('owned_by',), ('owned_by',))
    for facet, r in (old.get('responsibility') or {}).items() if isinstance(old.get('responsibility'), dict) else []:
        holder = being((r or {}).get('holder'), ctx) if isinstance(r, dict) else None
        if facet in MODES and holder:
            if MODES[facet] == 'law' and holder == owner:
                b.take(('responsibility', facet, 'holder', 'bean'), ('derived', 'before the law, the owner answers'), holder)
            else:
                j = b.add('answer', {'by': holder, 'of': 'self', 'as': MODES[facet]}, b.new_id(f"answer-{MODES[facet]}"))
                b.take(('responsibility', facet, 'holder', 'bean'), b.role(j, 'by'))
    if 'responsibility' in old:
        b.leftover(('responsibility',), ('responsibility',))
    if isinstance(old.get('via'), list):
        through, takes = [], []
        for i, v in enumerate(old['via']):
            if being(v, ctx):
                takes.append((('via', i, 'bean'), len(through)))
                through.append(being(v, ctx))
            elif isinstance(v, dict) and v.get('someone') in ctx.kinds:
                takes.append((('via', i, 'someone'), len(through), 'someone'))
                through.append({'someone': v['someone']})
        if through:
            j = b.add('come', {'by': 'self', 'through': through}, b.new_id('come'))
            for t in takes:
                b.take(t[0], b.role(j, 'through', t[1], *t[2:]))
        b.leftover(('via',), ('via',))

    # -- where it is
    for i, loc in enumerate(old.get('located_at') or []) if isinstance(old.get('located_at'), list) else []:
        if isinstance(loc, dict) and loc.get('system') and loc.get('at'):
            pos = position(loc['system'], loc['at'], ctx)
            if pos:
                sid = b.new_id(f"at-{i + 1}")
                host = being(loc.get('host'), ctx)        # the being whose own frame the position is in (v1 part 7)
                roles = {'by': 'self', 'at': [host, pos] if host else pos, 'as': 'location'}
                if isinstance(loc.get('note'), str):
                    roles['note'] = loc['note']
                j = b.add('be', roles, sid)
                at = ('at', 1) if host else ('at',)
                b.take(('located_at', i, 'at'), b.role(j, *at), pos)
                b.take(('located_at', i, 'system'), b.role(j, *at), pos)
                if host:
                    b.take(('located_at', i, 'host', 'bean'), b.role(j, 'at', 0), host)
                if 'note' in roles:
                    b.take(('located_at', i, 'note'), b.role(j, 'note'))
                # WHAT IT HOLDS THERE (v1 part 7): how far the position reaches, how well it is known, its zone, its
                # window and what it takes of its host — its form, `placed`
                attrs = (ctx.law.forms.get('placement') or {}).get('attrs') or {}
                form = {a: _place_form(b, ('located_at', i, a), loc[a], j, 'placed', (a,)) for a in loc if a in attrs}
                if form:
                    b.statements[j][1]['placed'] = form
                b.leftover(('located_at', i), ('located_at', sid))
    if 'located_at' in old:
        b.leftover(('located_at',), ('located_at',))
    for term, verb, roles_of in (('lives_in', 'be', lambda x: {'by': 'self', 'at': x, 'as': 'habitat'}),
                                 ('part_of', 'part', lambda x: {'by': 'self', 'of': x}),
                                 ('instance_of', 'run', lambda x: {'by': 'self', 'of': x})):
        x = being(old.get(term), ctx)
        if x:
            roles = roles_of(x)
            j = b.add(verb, roles, b.new_id(term.replace('_', '-')))
            b.take((term, 'bean'), b.role(j, 'at' if verb == 'be' else 'of'))
    if isinstance(old.get('os'), str) and old['os'] in ctx.beans:
        j = b.add('run', {'by': 'self', 'of': old['os']}, b.new_id('os'))
        b.take(('os',), b.role(j, 'of'))

    # -- what it needs
    for k, e in (old.get('depends_on') or {}).items() if isinstance(old.get('depends_on'), dict) else []:
        if being(e, ctx) or (isinstance(e, dict) and being({'bean': e.get('bean')}, ctx)):
            j = b.add('need', {'by': 'self', 'of': [e['bean']]}, b.new_id(f"needs-{k}"))
            b.take(('depends_on', k, 'bean'), b.role(j, 'of', 0))
            b.leftover(('depends_on', k), ('depends_on', b.statements[j][1]['id']))
    for i, e in enumerate(old.get('consumes') or []) if isinstance(old.get('consumes'), list) else []:
        if isinstance(e, dict) and isinstance(e.get('bean'), str):
            j = b.add('need', {'by': 'self', 'of': [e['bean']]}, b.new_id(f"consumes-{e['bean']}"))
            b.take(('consumes', i, 'bean'), b.role(j, 'of', 0))
            b.leftover(('consumes', i), ('consumes', b.statements[j][1]['id']))
    for k, e in (old.get('reaches') or {}).items() if isinstance(old.get('reaches'), dict) else []:
        to = being(e.get('to'), ctx) if isinstance(e, dict) else None
        to = to or (e.get('to') if isinstance(e, dict) and e.get('to') in ctx.beans else None)
        if to and e.get('protocol') in ctx.protocols:
            j = b.add('need', {'by': 'self', 'of': [to], 'through': e['protocol']}, b.new_id(f"reaches-{k}"))
            b.take(('reaches', k, 'to') + (('bean',) if isinstance(e.get('to'), dict) else ()), b.role(j, 'of', 0))
            b.take(('reaches', k, 'protocol'), b.role(j, 'through'))
            b.leftover(('reaches', k), ('reaches', b.statements[j][1]['id']))
    for i, e in enumerate(old.get('knowledge') or []) if isinstance(old.get('knowledge'), list) else []:
        if isinstance(e, dict) and isinstance(e.get('code'), str) and e.get('rel') in ('uses', 'draws_on', 'classified_as'):
            if e['rel'] == 'classified_as':
                j = b.add('classify', {'of': 'self', 'as': e['code']}, b.new_id(f"is-{e['code']}"))
                b.take(('knowledge', i, 'code'), b.role(j, 'as'))
            else:
                j = b.add('use', {'by': 'self', 'of': e['code']}, b.new_id(f"uses-{e['code']}"))
                b.take(('knowledge', i, 'code'), b.role(j, 'of'))
            b.take(('knowledge', i, 'rel'), ('verb', j), 'classify' if e['rel'] == 'classified_as' else 'use')
            b.leftover(('knowledge', i), ('knowledge', b.statements[j][1]['id']))

    # -- what can fail, and what it can do
    for k, e in (old.get('risks') or {}).items() if isinstance(old.get('risks'), dict) else []:
        if isinstance(e, dict) and isinstance(e.get('what'), str):
            roles = {'by': 'self', 'as': e['what']}
            if a_position(e.get('found'), ctx):
                roles['at'] = e['found']
            if isinstance(e.get('note'), str):
                roles['note'] = e['note']
            sid = b.new_id(k)
            j = b.add('fail', roles, sid)
            b.take(('risks', k, 'what'), b.role(j, 'as'))
            for r in ('at', 'note'):
                if r in roles:
                    b.take(('risks', k, 'found' if r == 'at' else 'note'), b.role(j, r))
            b.leftover(('risks', k), ('risks', sid))
    for k, e in (old.get('capabilities') or {}).items() if isinstance(old.get('capabilities'), dict) else []:
        if not isinstance(e, dict):
            continue
        sid = b.new_id(k)
        j = b.add('can', {'by': 'self', 'of': k}, sid)
        # A STANCE ON A FIELD, WITHIN A PLACE (v1 part 7): the code it is on is its `as`, the place it holds in its `at`
        if isinstance(e.get('code'), str) and not ctx.std.code(e['code']):
            b.statements[j][1]['as'] = e['code']
            b.take(('capabilities', k, 'code'), b.role(j, 'as'))
        w = e.get('within') if isinstance(e.get('within'), dict) else {}
        pos = position(w['system'], w['at'], ctx) if w.get('system') and w.get('at') else None
        if pos:
            b.statements[j][1]['at'] = pos
            b.take(('capabilities', k, 'within', 'system'), b.role(j, 'at'), pos)
            b.take(('capabilities', k, 'within', 'at'), b.role(j, 'at'), pos)
        perm = PERMISSION.get(e.get('permission', 'permitted'))
        if perm:
            imposer = e.get('by') if e.get('by') in ctx.beans else 'unknown'
            roles = {'of': sid, 'through': imposer}
            if isinstance(e.get('why'), str):
                roles['why'] = e['why']
            jp = b.add(perm, roles)
            if 'permission' in e:
                b.take(('capabilities', k, 'permission'), ('verb', jp), perm)
            if imposer != 'unknown':
                b.take(('capabilities', k, 'by'), b.role(jp, 'through'))
            if 'why' in roles:
                b.take(('capabilities', k, 'why'), b.role(jp, 'why'))
        feas = FEASIBILITY.get(e.get('feasibility', 'possible'))
        if feas and 'feasibility' in e:
            roles = {'of': sid}
            if isinstance(e.get('feasibility_why'), str):
                roles['why'] = e['feasibility_why']
            jf = b.add(feas, roles)
            b.take(('capabilities', k, 'feasibility'), ('verb', jf), feas)
            if 'why' in roles:
                b.take(('capabilities', k, 'feasibility_why'), b.role(jf, 'why'))
        b.leftover(('capabilities', k), ('capabilities', sid))
    for i, e in enumerate(old.get('roles') or []) if isinstance(old.get('roles'), list) else []:
        if isinstance(e, dict) and e.get('role') in ctx.jobs:
            roles = {'by': 'self', 'as': e['role']}
            if isinstance(e.get('why'), str):
                roles['why'] = e['why']
            sid = b.new_id(f"does-{e['role']}")
            j = b.add('do', roles, sid)
            b.take(('roles', i, 'role'), b.role(j, 'as'))
            if 'why' in roles:
                b.take(('roles', i, 'why'), b.role(j, 'why'))
            b.leftover(('roles', i), ('roles', sid))
    for i, e in enumerate(old.get('endpoints') or []) if isinstance(old.get('endpoints'), list) else []:
        if not (isinstance(e, dict) and e.get('protocol') in ctx.protocols and e.get('system') and e.get('at')):
            continue
        ip = position(e['system'], e['at'], ctx)
        if not ip:
            continue
        at = [ip]
        if isinstance(e.get('port'), str):
            transport = ctx.transport.get(e['protocol'], 'tcp')
            port = position(f"{transport}-port", e['port'], ctx)
            if not port:
                continue
            at.append(port)
        sid = b.new_id(f"serves-{e['protocol']}")
        j = b.add('serve', {'by': 'self', 'at': at, 'through': e['protocol']}, sid)
        b.take(('endpoints', i, 'at'), b.role(j, 'at', 0), ip)
        b.take(('endpoints', i, 'system'), b.role(j, 'at', 0), ip)
        if len(at) > 1:
            b.take(('endpoints', i, 'port'), b.role(j, 'at', 1), at[1])
        b.take(('endpoints', i, 'protocol'), b.role(j, 'through'))
        b.leftover(('endpoints', i), ('endpoints', sid))

    # -- agreements
    parties = old.get('parties') if isinstance(old.get('parties'), dict) else {}
    words = old.get('words') if isinstance(old.get('words'), dict) else {}
    over = old.get('over') if isinstance(old.get('over'), dict) else {}
    things, over_takes = [], []
    for k, e in over.items():
        t = being((e or {}).get('thing'), ctx) if isinstance(e, dict) else None
        if t:
            over_takes.append((('over', k, 'thing', 'bean'), len(things)))
            things.append(t)
        elif isinstance(e, dict) and isinstance(e.get('what'), str):
            over_takes.append((('over', k, 'what'), len(things)))
            things.append(e['what'])
    party_bean = {}
    first_agree = None
    for k, e in parties.items():
        if not isinstance(e, dict):
            continue
        who = being(e.get('who'), ctx)
        party_bean[k] = who or 'unknown'
        if e.get('accepted') in (None, '', {}, []):
            continue                # AN OFFER IS NOT AN ACCEPTANCE: an `agree` is a party's yes, and a party with no
                                    # acceptance on record — offered, or declined — stays a party, kept in `details`
        roles = {'by': who or 'unknown'}
        if things:
            roles['of'] = list(things)
        if words.get('form') in ctx.forms:
            roles['through'] = words['form']
        if isinstance(e.get('role'), str):
            roles['as'] = e['role']
        if a_position(e.get('accepted'), ctx):
            roles['at'] = e['accepted']
        if not who and isinstance(e.get('external'), str):
            roles['note'] = e['external']
        sid = b.new_id(f"agreed-{k}")
        j = b.add('agree', roles, sid)
        if first_agree is None:
            first_agree = sid
            for p, n in over_takes:
                b.take(p, b.role(j, 'of', n))
            if 'through' in roles:
                b.take(('words', 'form'), b.role(j, 'through'))
        if who:
            b.take(('parties', k, 'who', 'bean'), b.role(j, 'by'))
        elif 'note' in roles:
            b.take(('parties', k, 'external'), b.role(j, 'note'))
        for r, o in (('as', 'role'), ('at', 'accepted')):
            if r in roles:
                b.take(('parties', k, o), b.role(j, r))
        if isinstance(e.get('provenance'), dict):
            knowing(b, e['provenance'], ('parties', k, 'provenance'), of=[sid])
        b.leftover(('parties', k), ('parties', sid))
    for term in ('parties', 'over', 'words'):
        if term in old:
            b.leftover((term,), (term,))
    for k, e in (old.get('clauses') or {}).items() if isinstance(old.get('clauses'), dict) else []:
        if not (isinstance(e, dict) and isinstance(e.get('what'), str) and first_agree):
            continue
        who = party_bean.get(e.get('by'), 'unknown')
        sid = b.new_id(k)
        roles = {'by': who, 'of': e['what']}
        if e.get('to') in party_bean:
            roles['to'] = party_bean[e['to']]
        if isinstance(e.get('note'), str):
            roles['note'] = e['note']
        j = b.add('can', roles, sid)
        b.take(('clauses', k, 'what'), b.role(j, 'of'))
        if 'by' in e and e['by'] in party_bean:
            b.take(('clauses', k, 'by'), b.role(j, 'by'), who)
        for r, o in (('to', 'to'), ('note', 'note')):
            if r in roles:
                b.take(('clauses', k, o), b.role(j, r), roles[r])
        # WHAT A CLAUSE HOLDS BESIDE ITS WORDS (v1 part 7): when it falls due, how it repeats, when it falls due relative
        # to a position, its notice, its window, an allowance, what it occurs for, what brings it into force — its form
        attrs = (ctx.law.forms.get('clause') or {}).get('attrs') or {}
        form = {a: _place_form(b, ('clauses', k, a), e[a], j, 'clause', (a,)) for a in e if a in attrs}
        if form:
            b.statements[j][1]['clause'] = form
        perm = PERMISSION.get(e.get('permission'))
        if perm:
            jp = b.add(perm, {'of': sid, 'through': first_agree})
            b.take(('clauses', k, 'permission'), ('verb', jp), perm)
        b.leftover(('clauses', k), ('clauses', sid))
    for k, e in (old.get('transactions') or {}).items() if isinstance(old.get('transactions'), dict) else []:
        if not isinstance(e, dict) or not isinstance(e.get('amount'), dict):
            continue
        payers = [p.get('party') for p in e.get('paid_by') or [] if isinstance(p, dict)]
        if len(payers) != 1 or payers[0] not in party_bean:
            continue
        sid = b.new_id(k)
        u = e['amount'].get('unit')
        code = u if u in ctx.std.currencies else (ucum_of(str(u), ctx.law) or u)     # a currency's code, or UCUM's
        roles = {'by': party_bean[payers[0]], 'of': {'count': e['amount'].get('count'), 'unit': code}}
        if a_position(e.get('day'), ctx):
            roles['at'] = e['day']
        if isinstance(e.get('what'), str):
            roles['note'] = e['what']
        j = b.add('pay', roles, sid)
        b.take(('transactions', k, 'paid_by', 0, 'party'), b.role(j, 'by'), roles['by'])
        b.take(('transactions', k, 'amount', 'count'), b.role(j, 'of', 'count'))
        b.take(('transactions', k, 'amount', 'unit'), b.role(j, 'of', 'unit'), code)
        for r, o in (('at', 'day'), ('note', 'what')):
            if r in roles:
                b.take(('transactions', k, o), b.role(j, r))
        for n, bb in enumerate(e.get('borne_by') or []):
            if isinstance(bb, dict) and bb.get('party') in party_bean:
                broles = {'by': party_bean[bb['party']], 'of': sid}
                if 'share' in bb:
                    broles['share'] = bb['share']
                jb = b.add('bear', broles, b.new_id(f"{sid}-borne-{n + 1}"))
                b.take(('transactions', k, 'borne_by', n, 'party'), b.role(jb, 'by'), broles['by'])
                if 'share' in bb:
                    b.take(('transactions', k, 'borne_by', n, 'share'), b.role(jb, 'share'))
        pin_of(b, ('transactions', k, 'pin'), sid, ctx)
        b.leftover(('transactions', k), ('transactions', sid))

    # -- time
    t = old.get('timing') if isinstance(old.get('timing'), dict) else {}
    ends = [t.get(x) for x in ('start', 'stop')]
    if isinstance(ends[0], dict) and ends[0].get('system') and ends[0].get('at'):
        a = position(ends[0]['system'], ends[0]['at'], ctx)
        z = position(ends[1]['system'], ends[1]['at'], ctx) if isinstance(ends[1], dict) and ends[1].get('at') else None
        whole = f"{a}/{z}" if a and z else a
        if whole and z:
            try:
                frame.read(whole, ctx.systems, ctx.zone)
            except frame.Refused:
                whole = None
        if whole:
            j = b.add('be', {'by': 'self', 'at': whole, 'as': 'presence'}, b.new_id('present'))
            for x, v in (('start', a), ('stop', z)):
                if v:
                    b.take(('timing', x, 'at'), b.role(j, 'at'), whole)
                    b.take(('timing', x, 'system'), b.role(j, 'at'), whole)
    if isinstance(old.get('produces'), str) and old['produces']:
        j = b.add('produce', {'by': 'self', 'of': [old['produces']]}, b.new_id('produces'))
        b.take(('produces',), b.role(j, 'of', 0))
    ws = old.get('workspace') if isinstance(old.get('workspace'), dict) else {}
    if isinstance(ws.get('opened_at'), str):
        try:
            frame.read(ws['opened_at'], ctx.systems, ctx.zone)
            j = b.add('open', {'of': 'self', 'at': ws['opened_at']}, b.new_id('opened'))
            b.take(('workspace', 'opened_at'), b.role(j, 'at'))
        except frame.Refused:
            pass

    # -- lines: a series, a walk, a course and its moves, a reading (v1 part 6, core/lines.py)
    lines_of(b, old, ctx)

    # -- the rest, whole
    for k in old:
        b.leftover((k,), () if k == 'details' else (k,))     # the old details are the new details' own keys
    found = comments(head or '')
    kept = []
    for on, txt in found:
        if kept and kept[-1]['on'] == on:
            kept[-1]['text'] += '\n' + txt
        else:
            kept.append({'on': on, 'text': txt})
    if kept:
        if 'comments' in b.details:
            raise ValueError(f"{bid}: details.comments is a key already")
        b.details['comments'] = kept
    b.n_comments = len(found)
    b.header = header
    b.body = body
    return render(b), b


# THE FORMS OF A LINE (v1 part 6): each written as a statement of its verb, its line's own structure placed leaf by leaf
# in the statement's `form` qualifier, so the count holds; a unit written by its UCUM code, as every quantity of the core
# is; today's `genos` a reading's `kind`, and a comparator the core has a sign for written by its sign. What is not in
# the form — a step list of prose, a course whose walk is not a bean, a series whose id is taken — stays in `details`.
def _unit_text(v, ctx):
    return v if not isinstance(v, str) or v in ctx.std.currencies else (ucum_of(v, ctx.law) or v)


def _place_form(b, base, x, j, role, sub=(), rename=None, units=True, paths=False):
    """Each leaf of the old subtree `x` (at old path `base`) placed in statement `j`'s `role` at the same path below
    `sub`, a key renamed by `rename(key, old path)`, a unit by its UCUM code. Returns the new subtree as written."""
    rename = rename or (lambda k, _p: k)

    def walk(v, old_path, new_path):
        if isinstance(v, dict):
            out = {}
            for k, w in v.items():
                nk = rename(k, old_path)
                out[nk] = walk(w, old_path + (k,), new_path + (nk,))
            if not v:
                b.take(old_path, b.role(j, role, *new_path), '{}')
            return out
        if isinstance(v, list):
            if not v:
                b.take(old_path, b.role(j, role, *new_path), '[]')
            return [walk(w, old_path + (i,), new_path + (i,)) for i, w in enumerate(v)]
        text = _unit_text(v, b.ctx) if units and old_path and old_path[-1] == 'unit' else \
            'kind' + v[5:] if paths and old_path and old_path[-1] == 'path' and isinstance(v, str) \
            and re.match(r'^genos(?![\w-])', v) else v
        b.take(old_path, b.role(j, role, *new_path), text)
        return text
    return walk(x, base, tuple(sub))


def lines_of(b, old, ctx):
    before = len(b.statements)
    _lines_of(b, old, ctx)
    if len(b.statements) > before and not any(v in KNOWING for v, _r in b.statements):
        # A BEAN THAT SAID NOBODY KNEW IT (no provenance: a mapping, mostly) held nothing the core asks to be known until
        # its lines became statements; now they are, and who said them is not recorded — so the act says so
        r = subprocess.run(['git', '-C', ctx.root, 'log', '--follow', '--diff-filter=A', '--format=%cI', '--', b.path],
                           capture_output=True, text=True)
        moment = (r.stdout.strip().split('\n') or [''])[-1].strip() if r.returncode == 0 else ''
        b.add('say', {'by': 'unknown', 'at': moment or 'unknown',
                      'note': "who wrote these lines is not recorded: the bean carried no provenance"})


KNOWING = ('say', 'read', 'derive', 'make')


def _lines_of(b, old, ctx):
    series = old.get('series') if isinstance(old.get('series'), dict) else {}
    for k, e in series.items():
        if not isinstance(e, dict) or slug(k) != k or k in b.ids:
            continue
        sid = b.new_id(k)
        roles = {'of': 'self'}
        j = b.add('record', roles, sid)
        form = {kk: v for kk, v in e.items() if kk != 'note'}
        b.statements[j][1]['series'] = _place_form(b, ('series', k), form, j, 'series')
        if isinstance(e.get('note'), str):
            b.statements[j][1]['note'] = e['note']
            b.take(('series', k, 'note'), b.role(j, 'note'))
    steps = old.get('steps') if isinstance(old.get('steps'), list) else []
    if steps and all(isinstance(s, dict) and isinstance(s.get('id'), str) and isinstance(s.get('do'), str)
                     and slug(s['id']) == s['id'] for s in steps) and len({s['id'] for s in steps}) == len(steps) \
            and not any(s['id'] in b.ids for s in steps):
        for n, s in enumerate(steps):
            sid = b.new_id(s['id'])
            roles = {'as': s['do']}
            if 'by' in s:
                roles['by'] = s['by']
            nxt = [x for x in s.get('next') or [] if isinstance(x, dict) and isinstance(x.get('to'), str)]
            if nxt:
                roles['to'] = [x['to'] for x in nxt]
            j = b.add('step', roles, sid)
            b.take(('steps', n, 'id'), b.role(j, 'id'))
            b.take(('steps', n, 'do'), b.role(j, 'as'))
            if 'by' in s:
                b.take(('steps', n, 'by'), b.role(j, 'by'))
            if 'note' in s:
                b.statements[j][1]['note'] = s['note']
                b.take(('steps', n, 'note'), b.role(j, 'note'))
            walk = {}
            ways = []
            for i, x in enumerate(nxt):
                b.take(('steps', n, 'next', i, 'to'), b.role(j, 'to', i))
                words = {kk: v for kk, v in x.items() if kk != 'to'}
                if words:
                    w = {'to': x['to']}
                    for kk, v in words.items():
                        w[kk] = v
                        b.take(('steps', n, 'next', i, kk), b.role(j, 'walk', 'ways', len(ways), kk))
                    ways.append(w)
            if len(nxt) != len(s.get('next') or []):
                continue                                      # a way on that names no step: left in details, whole
            for kk, v in s.items():
                if kk not in ('id', 'do', 'by', 'next', 'note'):
                    walk[kk] = _place_form(b, ('steps', n, kk), v, j, 'walk', (kk,))
            if ways:
                walk['ways'] = ways
            if walk:
                b.statements[j][1]['walk'] = walk
    courses = old.get('courses') if isinstance(old.get('courses'), dict) else {}
    named = {}
    for k, c in courses.items():
        ref = c.get('walk') if isinstance(c, dict) else None
        wid = ref.get('mapping') or ref.get('bean') if isinstance(ref, dict) else None
        if not isinstance(wid, str) or wid not in ctx.beans or slug(k) != k or k in b.ids:
            continue
        sid = b.new_id(k)
        roles = {'by': 'self', 'at': wid, 'as': 'order'}
        if isinstance(c.get('note'), str):
            roles['note'] = c['note']
        j = b.add('be', roles, sid)
        b.take(('courses', k, 'walk', 'mapping' if 'mapping' in ref else 'bean'), b.role(j, 'at'))
        if 'note' in roles:
            b.take(('courses', k, 'note'), b.role(j, 'note'))
        named[k] = wid
    for n, m in enumerate(old.get('moves') or [] if isinstance(old.get('moves'), list) else []):
        if not (isinstance(m, dict) and m.get('course') in named and isinstance(m.get('step'), str)
                and isinstance(m.get('at'), str)):
            continue
        step = f"{named[m['course']]}#{m['step']}"
        roles = {'of': 'self', 'through': m['course'], 'at': [m['at'], step]}
        for o, r in (('by', 'by'), ('reason', 'as'), ('why', 'why'), ('note', 'note')):
            if isinstance(m.get(o), str):
                roles[r] = m[o]
        j = b.add('move', roles)
        b.take(('moves', n, 'course'), b.role(j, 'through'))
        b.take(('moves', n, 'at'), b.role(j, 'at', 0))
        b.take(('moves', n, 'step'), b.role(j, 'at', 1), step)
        for o, r in (('by', 'by'), ('reason', 'as'), ('why', 'why'), ('note', 'note')):
            if r in roles:
                b.take(('moves', n, o), b.role(j, r))
    sel = old.get('selections') if isinstance(old.get('selections'), dict) else {}
    for k, e in sel.items():
        if not isinstance(e, dict) or slug(k) != k or k in b.ids:
            continue
        sid = b.new_id(k)
        j = b.add('reckon', {}, sid)
        form = {kk: v for kk, v in e.items() if kk != 'note'}
        b.statements[j][1]['reading'] = _place_form(b, ('selections', k), form, j, 'reading',
                                                    rename=_reading_key, paths=True)
        b.readings.append(j)
        if isinstance(e.get('note'), str):
            b.statements[j][1]['note'] = e['note']
            b.take(('selections', k, 'note'), b.role(j, 'note'))


def _reading_key(k, old_path):
    """A key of a reading in the core's words: `genos` a step's `kind`; a comparator of a condition (an item of a step's
    `where`) by the core's sign — and nowhere else, so `compare`'s own `is` stays its word."""
    if k == 'genos':
        return 'kind'
    return SIGNS.get(k, k) if len(old_path) >= 2 and old_path[-2] == 'where' else k


# A READING'S PATHS ARE REWRITTEN WHERE THEIR VALUES WENT (v1 part 6). A reading in today's words reads terms; in the core
# those values are statements or are kept whole in `details`. So the garden is translated first, and each path is then
# written as the beans it reads were: a term kept whole is read in `details`; a term written as statements of one verb is
# that verb, its attributes the roles they became; a course is the `be` named by it (`be[id=<course>]`), the step it
# reaches the walk's statement (`<walk>#<step>`); a series is the statement that records it (`<bean>#<id>`). Only what
# the beans show is mapped: a path whose values went two ways is kept as written, and the gate names it.
def reading_map(beans):
    """{term: ('details',) or ('verb', verb, {attr: role})}, and {course: walk}, from where each bean's leaves went."""
    where_to, attrs, walks, steps = {}, {}, {}, {}
    for b in beans:
        for s in b.old.get('steps') or [] if isinstance(b.old.get('steps'), list) else []:
            if isinstance(s, dict) and isinstance(s.get('id'), str):
                steps.setdefault(s['id'], set()).add(b.id)
        for c, e in (b.old.get('courses') or {}).items() if isinstance(b.old.get('courses'), dict) else []:
            ref = e.get('walk') if isinstance(e, dict) else None
            if isinstance(ref, dict) and isinstance(ref.get('mapping') or ref.get('bean'), str):
                walks.setdefault(c, set()).add(ref.get('mapping') or ref.get('bean'))
        for p, (where, _v) in b.placed.items():
            term = p[0]
            if where[0] == 'details' and len(where) > 1 and where[1] == term:
                where_to.setdefault(term, collections.Counter())['details'] += 1
            elif where[0] == 'statement' and len(where) > 2:
                verb = b.statements[where[1]][0]
                where_to.setdefault(term, collections.Counter())[verb] += 1
                if len(p) > 2 and isinstance(p[2], str):
                    attrs.setdefault((term, verb), {}).setdefault(p[2], set()).add(where[2])
    out = {}
    for term, seen in where_to.items():
        if set(seen) == {'details'}:
            out[term] = ('details',)
        elif 'details' not in seen or seen.most_common(1)[0][0] != 'details':
            verb = seen.most_common(1)[0][0]
            out[term] = ('verb', verb, {a: next(iter(r)) for a, r in attrs.get((term, verb), {}).items() if len(r) == 1})
    walks = {c: next(iter(w)) for c, w in walks.items() if len(w) == 1}
    return out, (walks, {s: next(iter(w)) for s, w in steps.items() if len(w) == 1})


def _read_path(path, member, rmap):
    """A path of today's words as the core reads it, over a bean (`member` None) or over the statements a step selected
    from a term (`member` the term); None where the beans do not say."""
    head, sep, rest = path.partition('.')
    if member is not None:
        m = rmap.get(member)
        if m and m[0] == 'verb':
            return m[2].get(head, head) + sep + rest if head in m[2] else path
        return path
    if head in ('kind', 'bean', 'title', 'summary', 'tags', 'details'):
        return path
    m = rmap.get(head)
    if m is None:
        return None
    if m[0] == 'details':
        return 'details.' + path
    sub, sep2, deeper = rest.partition('.')
    if sub in ('*', '') or not rest:
        return m[1] + ('.' + deeper if deeper else '')
    return m[1] + '.' + m[2].get(sub, sub) + (sep2 + deeper if deeper else '')


def rewrite_readings(b, rmap, walks_steps):
    """Each `reckon` of bean `b` with its paths in the core's (`reading_map`), its placements following; True where any
    changed."""
    walks, step_walk = walks_steps
    changed = False
    inv = {}
    for p, (where, _v) in b.placed.items():
        inv[where] = p

    def put(where, new):
        nonlocal changed
        p = inv.get(where)
        if p is not None and b.placed[p][1] != new:
            b.placed[p] = (where, new)
            changed = True
    for j in b.readings:
        reading = b.statements[j][1].get('reading') or {}
        member = {}
        for n, s in enumerate(reading.get('steps') or []):
            if not isinstance(s, dict):
                continue
            w = ('statement', j, 'reading', 'steps', n)
            ent = s.get('entries')
            here = member.get(s.get('of'))
            if isinstance(ent, str):
                term = ent.split('.', 1)[0]
                m = rmap.get(term)
                new = (m[1] if m[0] == 'verb' else 'details.' + ent) if m else ent
                if new != ent:
                    s['entries'] = new
                    put(w + ('entries',), new)
                here = term
            if isinstance(s.get('id'), str):
                member[s['id']] = here
            for k in ('series', 'with'):
                v = s.get(k)
                hit = re.match(r'^([a-z0-9][a-z0-9_-]*):series\.([a-z0-9][a-z0-9_-]*)$', v) if isinstance(v, str) else None
                if hit:
                    s[k] = f"{hit.group(1)}#{hit.group(2)}"
                    put(w + (k,), s[k])
            for k in ('path', 'amount', 'over'):
                if isinstance(s.get(k), str):
                    new = _read_path(s[k], here, rmap)
                    if new and new != s[k]:
                        s[k] = new
                        put(w + (k,), new)
            for i, c in enumerate(s.get('where') or [] if isinstance(s.get('where'), list) else []):
                if not isinstance(c, dict) or not isinstance(c.get('path'), str):
                    continue
                course = re.match(r'^courses\.([a-z0-9][a-z0-9_-]*)$', c['path'])
                if course and here is None:
                    c['path'] = f"be[id={course.group(1)}]"
                    put(w + ('where', i, 'path'), c['path'])
                    for comp in ('reached', 'at_step'):
                        # the walk of the course, or — where no bean holds that course yet — the one walk that has a
                        # step of that name
                        walk = walks.get(course.group(1)) or step_walk.get(c.get(comp))
                        if isinstance(c.get(comp), str) and '#' not in c[comp] and walk:
                            c[comp] = f"{walk}#{c[comp]}"
                            put(w + ('where', i, comp), c[comp])
                    continue
                new = _read_path(c['path'], here, rmap)
                if new and new != c['path']:
                    c['path'] = new
                    put(w + ('where', i, 'path'), new)
    return changed


def pin_of(b, base, sid, ctx):
    """A pin today's entry carries (`pin_form`: commit, at, garden) as a `pin` statement of what rests on the reading:
    `at` its moment and the commit, `<garden>@<commit>` in the garden's object graph, `through` the garden read."""
    p = at_path(b.old, base)
    if not (isinstance(p, dict) and isinstance(p.get('commit'), str) and isinstance(p.get('at'), str)):
        return
    repo = slug(ctx.garden_name or 'garden')
    roles = {'of': [sid], 'at': [p['at'], f"{repo}@{p['commit']}"]}
    if isinstance(p.get('garden'), str):
        roles['through'] = p['garden']
    j = b.add('pin', roles, b.new_id(f"{sid}-pin"))
    b.take(base + ('at',), b.role(j, 'at', 0))
    b.take(base + ('commit',), b.role(j, 'at', 1), roles['at'][1])
    if 'through' in roles:
        b.take(base + ('garden',), b.role(j, 'through'))


def comments(head):
    """[(top-level key, text)] of each comment line of a front matter, in order: the key whose item the comment sits on,
    or for a comment on a line of its own, the item on the next line that holds one (the last, at the end). A `#` inside
    a block scalar is the value's text, not a comment. dmparse.comments names the finest item, but loops without end on
    an item whose first value ends in a full stop or holds a lone bracket; the top-level key is enough here, where the
    comment is kept in `details.comments` and counted."""
    root = yaml.compose(head, Loader=yaml.BaseLoader)
    spans, block = [], set()
    for k, v in (root.value if isinstance(root, yaml.MappingNode) else []):
        spans.append((k.start_mark.line, v.end_mark.line, k.value))
        todo = [v]
        while todo:
            n = todo.pop()
            if isinstance(n, yaml.ScalarNode) and n.style in ('|', '>'):
                block.update(range(n.start_mark.line + 1, n.end_mark.line + (1 if n.end_mark.column else 0)))
            elif isinstance(n, yaml.MappingNode):
                todo += [x for kv in n.value for x in kv]
            elif isinstance(n, yaml.SequenceNode):
                todo += n.value
    lines = head.split('\n')

    def key_at(i):
        here = [s for s in spans if s[0] <= i <= max(s[1], s[0])]
        return here[-1][2] if here else ''
    content = [i for i, l in enumerate(lines) if l.strip() and i not in block
               and (dmparse.comment_start(l) < 0 or l[:dmparse.comment_start(l)].strip())]
    out = []
    for i, l in enumerate(lines):
        c = dmparse.comment_start(l) if i not in block else -1
        if c < 0:
            continue
        on = i if l[:c].strip() else next((j for j in content if j > i), next((j for j in reversed(content) if j < i), None))
        out.append((key_at(on) if on is not None else '', l[c:].lstrip('#').strip()))
    return out


_BLOCK = re.compile(r'^(\s*)((?:- )*(?:[^\s:#][^:#]*: )?(?:- )*)XBLOCK(\d+)X$')


def _blocked(x, dump):
    """`dump` of `x` with each string of several lines written as a block scalar (`|`), its chomping as the string ends:
    a line feed is text only there (the rule `form`), and PyYAML will not write a block that holds a tab."""
    blocks = []

    def mark(v):
        if isinstance(v, dict):
            return {k: mark(w) for k, w in v.items()}
        if isinstance(v, list):
            return [mark(w) for w in v]
        if isinstance(v, str) and '\n' in v and not v.startswith((' ', '\n')):
            blocks.append(v)
            return f"XBLOCK{len(blocks) - 1}X"
        return v
    out = []
    for line in dump(mark(x)).split('\n'):
        m = _BLOCK.match(line)
        if not m:
            out.append(line)
            continue
        indent, prefix, n = m.group(1), m.group(2), int(m.group(3))
        v = blocks[n]
        body = v[:-1] if v.endswith('\n') else v
        chomp = '' if v.endswith('\n') and not v.endswith('\n\n') else ('-' if not v.endswith('\n') else '+')
        if chomp == '+':
            body = v.rstrip('\n')
        out.append(f"{indent}{prefix}|{chomp}")
        pad = indent + ' ' * (len(prefix) - len(prefix.lstrip('- ')) + 2 if prefix.strip() else 2)
        out += [(pad + ln) if ln else '' for ln in body.split('\n')]
        if chomp == '+':
            out += [''] * (len(v) - len(v.rstrip('\n')) - 1)
    return '\n'.join(out)


def block(x):
    return yaml.safe_dump(x, allow_unicode=True, sort_keys=False, width=120)


def render(b):
    """The text of a bean in statements: its header, its statements one to a line (prose of several lines in a block),
    its details, and its body."""
    def flow(x):
        return yaml.safe_dump(x, default_flow_style=True, width=10 ** 9, allow_unicode=True, sort_keys=False).strip()
    out = ['---', _blocked(b.header, block).rstrip()]
    if b.statements:
        out.append('statements:')
        for verb, roles in b.statements:
            if any('\n' in v for _k, v in leaves(roles, ())):   # prose of several lines: a block mapping, a block scalar
                out += ['  ' + ln for ln in _blocked([{verb: roles}], block).rstrip().split('\n')]
            else:
                out.append(f"  - {verb}: {flow(roles)}")
    if b.details:
        out.append(_blocked({'details': b.details}, block).rstrip())
    return '\n'.join(out) + '\n---' + (b.body if b.body.startswith('\n') else '\n' + b.body)


def verify(b, text):
    """[problem] for a written bean: an old leaf with no place, or a place that does not hold its value."""
    from core import read
    head, _body = dmparse.split_front_matter(text)
    new = read.loads(head) or {}
    sts = [next(iter(s.values())) for s in new.get('statements') or []]
    verbs = [next(iter(s)) for s in new.get('statements') or []]
    out = []
    for p, v in leaves(b.old):
        if p not in b.placed:
            out.append(f"{b.id}: {'.'.join(map(str, p))} = {v!r} has no place")
            continue
        where, want = b.placed[p]
        if where[0] == 'header':
            got = at_path(new, where[1:])
        elif where[0] == 'details':
            got = at_path(new.get('details') or {}, where[1:])
            got = '{}' if got == {} else '[]' if got == [] else got
        elif where[0] == 'statement':
            got = at_path(sts[where[1]], where[2:]) if where[1] < len(sts) else KeyError
        elif where[0] == 'verb':
            got = verbs[where[1]]
        elif where[0] == 'derived':
            continue
        else:
            got = KeyError
        if got != want:
            out.append(f"{b.id}: {'.'.join(map(str, p))} = {v!r} is not at {where} (there: {got!r}, wanted {want!r})")
    kept = sum(len(c['text'].split('\n')) for c in (new.get('details') or {}).get('comments') or [])
    if kept != b.n_comments:
        out.append(f"{b.id}: {b.n_comments} comment lines, {kept} kept")
    return out


class Context:
    """What a translation reads beside each bean: the garden's beans, its journal, the law's tables."""

    def __init__(self, root, law, std):
        self.root, self.law, self.std = root, law, std
        self.beans = set()
        for d in DOCUMENTS:
            if os.path.isdir(os.path.join(root, d)):
                self.beans |= {f[:-3] for f in os.listdir(os.path.join(root, d)) if f.endswith('.md')}
        self.journal = Journal(root)
        self.systems = law.systems           # the standards', and the garden's own (VOCAB.md `systems`, v1 part 7)
        try:
            from core import read
            manifest = read.document(os.path.join(root, 'GARDEN.md'))[0]
            self.zone, self.garden_name = manifest.get('zone'), manifest.get('garden')
        except Exception:
            self.zone, self.garden_name = None, None
        self.kinds = dict(law.kinds)
        self.protocols = set(std.protocols)
        self.transport = {p: str(r.get('transport') or 'tcp') for p, r in std.protocols.items()}
        self.jobs = set(law.table('jobs') or [])
        self.forms = set(law.table('forms') or [])
        self.namespaces = {}
        self.sessions = []                   # (start ms, stop ms, bean) of each session with both ends known
        from core import read
        p = os.path.join(root, 'beans')
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            try:
                fm = read.document(os.path.join(p, f))[0] if f.endswith('.md') else {}
            except read.Unread:
                continue
            t = fm.get('timing') if fm.get('genos') == 'session' and isinstance(fm.get('timing'), dict) else {}
            ends = []
            for x in ('start', 'stop'):
                e = t.get(x) if isinstance(t.get(x), dict) else {}
                pos = position(e.get('system'), e.get('at'), self) if e.get('system') and e.get('at') else None
                try:
                    ends.append(frame.read(pos, self.systems, self.zone).moment if pos else None)
                except frame.Refused:
                    ends.append(None)
            if len(ends) == 2 and None not in ends:
                self.sessions.append((ends[0], ends[1], f[:-3]))

    def session_at(self, moment):
        """The one session whose start and stop hold `moment`, or None (none, or more than one)."""
        try:
            ms = frame.read(moment, self.systems, self.zone).moment
        except frame.Refused:
            return None
        hits = [s for a, z, s in self.sessions if ms is not None and a <= ms <= z]
        return hits[0] if len(hits) == 1 else None

    def namespace(self, ns, anchor):
        once = anchor.get('establishing') == 'true'
        self.namespaces[ns] = self.namespaces.get(ns, True) and once


def ucum_of(name, law):
    """The UCUM code of a unit the law names, or of one named `<a>-per-<b>` from two it names (`gigabyte-per-day` is
    `GBy/d`); None where neither."""
    for code, row in law.units.items():
        if row.get('name') == name and row.get('ucum') != 'false':
            return code
    parts = name.split('-per-')
    for i in range(1, len(parts)):
        a, b = ucum_of('-per-'.join(parts[:i]), law), ucum_of('-per-'.join(parts[i:]), law)
        if a and b:
            return f"{a}/{b}" if not any(c in b for c in './') else f"{a}/({b})"
    return None


def unit_row(name, quantity, law):
    """A garden's own unit (today's `registry_additions.units`) as a row of the core's units: its UCUM code composed from
    the law's rows where its name is made of theirs, else its name kept as its code, saying why."""
    code = ucum_of(name, law)
    if code:
        return {'unit': code, 'name': name, 'quantity': quantity}
    return {'unit': name, 'name': name, 'quantity': quantity, 'ucum': 'false',
            'why': "its name is made of no units the law writes in UCUM: give its UCUM code"}


def garden(src, dst):
    """Copy the garden at `src` to `dst` with its beans in statements; returns (counts, problems)."""
    from core import read, standards
    from core.law import Law
    if os.path.exists(dst):
        raise SystemExit(f"translate: {dst} exists — a translation is written into a new copy")
    std = standards.here(src) if standards.carried(src) else standards.here()
    runs = str((std.old or {}).get('version') or '')
    if not re.match(rf'{READS}\.', runs):
        raise SystemExit(f"translate: the garden runs std-vocab {runs or '(none read)'}, and this translator reads the words "
                         f"of std-vocab {READS}: bring it to the last release of today's language first (bin/dmupgrade.py), "
                         f"then translate it")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    vocab = read.document(os.path.join(src, 'VOCAB.md'))[0] if os.path.exists(os.path.join(src, 'VOCAB.md')) else {}
    oldv = dmparse.loads(dmparse.split_front_matter(open(os.path.join(src, 'VOCAB.md'), encoding='utf-8').read())[0]) \
        if vocab else {}
    rows = {'kinds': [kind_row(g) for g in oldv.get('local_gene') or [] if isinstance(g, dict) and g.get('genos')]}
    mkinds = set()
    for d in DOCUMENTS:
        p = os.path.join(src, d)
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            if f.endswith('.md'):
                fm = read.document(os.path.join(p, f))[0]
                if 'mapping' in fm and 'genos' not in fm and isinstance(fm.get('kind'), str):
                    mkinds.add(fm['kind'])
    rows['kinds'] += [{'kind': k, 'nature': 'sayable'} for k in sorted(mkinds)]
    adds = oldv.get('registry_additions') or {}
    tables = {}
    if adds.get('net_protocols'):
        tables['protocols'] = [str(r['protocol']) for r in adds['net_protocols'] if isinstance(r, dict) and r.get('protocol')]
    if tables:
        rows['tables'] = tables
    # A GARDEN'S OWN SYSTEMS, SCHEMES AND FILES (v1 part 7): today's `registry_additions.anchor_systems` and
    # `.knowledge_schemes`, and its `registry_files`, are rows of the core's `systems`, `schemes` and `files`, as written
    sadds = vocab.get('registry_additions') if isinstance(vocab.get('registry_additions'), dict) else {}
    for key, old_rows in (('systems', sadds.get('anchor_systems')), ('schemes', sadds.get('knowledge_schemes')),
                          ('files', vocab.get('registry_files'))):
        if isinstance(old_rows, list) and old_rows:
            rows[key] = [r for r in old_rows if isinstance(r, dict)]
    base = Law.load(std=std)
    units = [unit_row(str(r['unit']), str(r.get('quantity')), base) for r in adds.get('units') or []
             if isinstance(r, dict) and r.get('unit')]
    if units:
        rows['units'] = units
    law = Law.load(('VOCAB.md', rows), std=std)
    ctx = Context(src, law, std)
    for k in tables.get('protocols', []):
        ctx.protocols.add(k)
    counts = collections.Counter()
    problems = []
    done = []
    for d in DOCUMENTS:
        p = os.path.join(src, d)
        for f in sorted(os.listdir(p)) if os.path.isdir(p) else []:
            if f.endswith('.md'):
                done.append((d, f) + translate_bean(os.path.join(p, f), f"{d}/{f}", ctx))
    rmap, walks = reading_map([b for _d, _f, _t, b in done])
    for i, (d, f, text, b) in enumerate(done):
        if b.readings and rewrite_readings(b, rmap, walks):
            done[i] = (d, f, render(b), b)
    for d, f, text, b in done:
        with open(os.path.join(dst, d, f), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        problems += verify(b, text)
        counts['beans'] += 1
        counts['statements'] += len(b.statements)
        counts['leaves'] += len(leaves(b.old))
        for where, _v in b.placed.values():
            counts['to ' + where[0]] += 1
        counts['comment lines'] += b.n_comments
        for n in b.notes:
            problems.append(f"{b.id}: {n}")
        counts['acts at the moment their bean was made'] += len(b.carried)
    rows['namespaces'] = [{'namespace': ns, 'once': 'true' if once else 'false'} for ns, once in sorted(ctx.namespaces.items())]
    # A ROW THE GARDEN SAID IS VACANT stays so: today's `vacancies` entry (its position, reason and why) is the row's
    # `vacant`, which the core's rule `vacancy` reads
    for v in oldv.get('vacancies') or []:
        if not isinstance(v, dict) or v.get('position') is None:
            continue
        for key, names in (('units', ('unit', 'name')), ('kinds', ('kind',)), ('namespaces', ('namespace',))):
            for r in rows.get(key) or []:
                if any(str(r.get(n)) == str(v['position']) for n in names):
                    r['vacant'] = f"{v.get('reason')}: {v.get('why')}" if v.get('why') else str(v.get('reason'))
    # THE GARDEN'S ROWS go into its VOCAB.md beside today's keys, which the core's law passes by; its pin leaves it, for
    # the law a garden runs is GARDEN.md's alone (v1 part 4)
    vp = os.path.join(dst, 'VOCAB.md')
    vtext = open(vp, encoding='utf-8').read() if os.path.isfile(vp) else '---\n---\n'
    vhead, vbody = dmparse.split_front_matter(vtext)
    vhead = PIN_LINE.sub('', vhead or '', count=1)
    keep = {k: v for k, v in rows.items() if v}
    add = yaml.safe_dump(keep, allow_unicode=True, sort_keys=False, width=120) if keep else ''
    with open(vp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('---\n' + (vhead.strip('\n') + '\n' if vhead.strip() else '')
                 + ('# == THE CORE\'S ROWS: written by core/translate.py ==\n' + add if add else '') + '---' + vbody)
    # GARDEN.md PINS THE CORE: the copy is a garden of statements, judged by the core's gate (core@<version>)
    gp = os.path.join(dst, 'GARDEN.md')
    if os.path.isfile(gp):
        gtext = open(gp, encoding='utf-8').read()
        gnew = PIN.sub(lambda m: m.group(1) + 'core@' + base.version, gtext, count=1)
        with open(gp, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(gnew)
    problems += proved_law(src, dst, keep, base.version)
    counts['pin'] = 'core@' + base.version
    return counts, problems


PIN = re.compile(r'(?m)^(extends:[ \t]*)std-vocab@[^\s#]*')
PIN_LINE = re.compile(r'(?m)^extends:[ \t]*std-vocab@[^\n]*(\n|$)')


def proved_law(src, dst, rows, version):
    """The manifest and VOCAB.md, read back: each holds what it held, but the pin, which moved from both to GARDEN.md's
    `core@<version>`, and the core's rows VOCAB.md gained. [] when so, else what differs."""
    out = []

    def fm(root, name):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            return None
        return dmparse.loads(dmparse.split_front_matter(open(p, encoding='utf-8').read())[0] or '') or {}
    for name, gained, pin in (('GARDEN.md', {}, 'core@' + version), ('VOCAB.md', rows, None)):
        was, now = fm(src, name), fm(dst, name)
        if was is None:
            continue
        if not isinstance(was, dict) or not isinstance(now, dict):
            out.append(f"{name}: its front matter is no mapping")
            continue
        if pin is not None and now.get('extends') != pin:
            out.append(f"{name}: `extends: {now.get('extends')}`, where the copy pins {pin}")
        rest_was = {k: v for k, v in was.items() if k != 'extends'}
        rest_now = {k: v for k, v in now.items() if k != 'extends' and k not in gained}
        if pin is None and 'extends' in now:
            out.append(f"{name}: still pins `{now['extends']}`: the law a garden runs is GARDEN.md's alone")
        if rest_was != rest_now or any(now.get(k) != v for k, v in gained.items()):
            diff = sorted(set(rest_was) ^ set(rest_now) | {k for k in rest_was if rest_now.get(k) != rest_was[k]})
            out.append(f"{name}: read back, it differs from what it held at {', '.join(map(str, diff)) or 'the rows'}")
    return out


def main(argv):
    if len(argv) == 1 and argv[0] in GENERATED:
        sys.stdout.write(generated(argv[0]))
        return 0
    if argv == ['law']:
        for name in GENERATED:
            path = os.path.join(HERE, 'law', name + '.yaml')
            text = generated(name)
            try:
                with open(path, encoding='utf-8') as fh:
                    same = fh.read() == text
            except OSError:
                same = False
            if not same:
                with open(path, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(text)
            print(f"core/law/{name}.yaml: {'as generated' if same else 'written'}")
        return 0
    if argv[:1] == ['garden'] and len(argv) == 3:
        counts, problems = garden(os.path.abspath(argv[1]), os.path.abspath(argv[2]))
        for p in problems:
            print(p)
        placed = sum(v for k, v in counts.items() if k.startswith('to '))
        print(f"translate: {counts['beans']} beans, {counts['statements']} statements; {counts['leaves']} values, "
              f"{placed} placed (" + ', '.join(f"{v} {k}" for k, v in sorted(counts.items()) if k.startswith('to '))
              + f"); {counts['comment lines']} comment lines kept; {counts['acts at the moment their bean was made']} acts "
              f"at the moment their bean was made, their day in details; GARDEN.md pins {counts['pin']} — "
              f"{len(problems)} problem(s)")
        return 1 if problems else 0
    print(__doc__.strip().split('\n\n')[0])
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
