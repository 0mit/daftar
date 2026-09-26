#!/usr/bin/env python3
"""view_export — what a page gives away as a file: a table's lines as CSV, a document rendered from a template, and a
calendar of a reading's members (24.0: N36, N38, N40).

Each reads what the page declares — `views.<key>.columns` with its `selection` or `series`, `renders`, `feed` — through
the one grammar (bin/dmreckon.py, bin/dmseq.py) and writes where it is asked to. Nothing enters the ledger but a kept
render, which is a `document` bean saved through bin/dmsave.py like any other write. Every file is scoped by whoever
runs it: from the command line, the garden's own clone; from the host, the viewer, through `Host.may`.
"""
import csv, datetime, hashlib, io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm


# ---------------------------------------------------------------------------------------------------------------------
# a table, as CSV (N36)
# ---------------------------------------------------------------------------------------------------------------------
def csv_text(table, keep=None):
    """The table's lines as CSV: a header of its column labels, one line per row whose being `keep` lets through."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(table["columns"])
    for r in table["rows"]:
        if keep is None or keep(r["bean"]):
            w.writerow(r["cells"])
    return buf.getvalue()


def tables():
    """{view key: table} — every table the page draws."""
    return {k: vm.table(v) for k, v in vm.views_raw() if v.get("archetype") == "table"}


# ---------------------------------------------------------------------------------------------------------------------
# a document rendered from a template (N38)
# ---------------------------------------------------------------------------------------------------------------------
SLOT = re.compile(r"\{\{\s*([a-z_][a-z0-9_.\-\[\]=*]*)\s*\}\}")


def render_text(template, member):
    """The template with each `{{ path }}` replaced by the values at that field path of the member (`bean`: its id)."""
    import dmreckon
    f = vm.fm(member)

    def one(m):
        p = m.group(1)
        if p == "bean":
            return member
        return vm._cell(dmreckon.path_values(f, p, root=vm.ROOT))
    return SLOT.sub(one, template)


def template_of(entry):
    p = entry.get("template")
    if not (isinstance(p, str) and p.startswith("file:")):
        raise ValueError("a template is a file of the garden, `file:<path>`")
    path = os.path.join(vm.ROOT, *p[5:].split("/"))
    if not os.path.isfile(path):
        raise ValueError("the garden holds no file %s" % p[5:])
    return p[5:], open(path, encoding="utf-8").read()


def renders(key):
    """[(entry, [members])] — each render a drawing declares, with the members it renders: a reading's, or the being
    the drawing draws."""
    v = vm.view_entry(key)
    out = []
    for e in v.get("renders") or []:
        if not isinstance(e, dict):
            continue
        if e.get("selection"):
            ms = vm.members(e["selection"])
        else:
            k, i, folder = vm.draws_of(v)
            ms = [i] if k == "bean" else []
        out.append((e, ms))
    return out


def sha256(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def document_bean(bid, title, digest, path, keeper, member):
    """A `document` bean for a kept render: named by its content, where its copy is, and what it was rendered from."""
    return ("---\nbean: %s\ngenos: document\ntitle: \"%s\"\nstatus: active\nsummary: \"%s\"\nnature: lekton\n"
            "identity:\n  status: confirmed\n  anchors:\n    - { key: content_hash, value: \"%s\", class: logical, establishing: true }\n"
            "provenance: { src: generated-by-tool, by: \"dmview render\", as_of: now }\n"
            "owned_by: { legal: { owner: { bean: %s } } }\nresponsibility: { legal: { holder: { bean: %s } } }\n"
            "refs: { rendered-from: { bean: %s, rel: rendered-from } }\n"
            "located_at:\n  - { system: unix-filesystem, openness: here, at: \"%s\", observed: now }\n"
            "---\n%s, rendered from [[%s]] by the page's template and kept by its content.\n"
            % (bid, title.replace('"', "'"), ("A document rendered from %s's record." % member), digest, keeper, keeper,
               member, path.replace('"', "'"), title.replace('"', "'"), member))


# ---------------------------------------------------------------------------------------------------------------------
# a calendar of a reading's members (N40)
# ---------------------------------------------------------------------------------------------------------------------
def _ics_escape(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics_time(at):
    """A gregorian-civil position as an iCalendar DATE, or DATE-TIME — in UTC where its offset is written, floating where
    none is: None where it is not one."""
    s = str(at).strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?(Z|[+-]\d{2}:\d{2})?)?", s)
    if not m:
        return None
    y, mo, d, h, mi, se, off = m.groups()
    if h is None:
        return ("VALUE=DATE", y + mo + d)
    if not off:
        return ("", "%s%s%sT%s%s%s" % (y, mo, d, h, mi, se or "00"))
    t = datetime.datetime.fromisoformat("%s-%s-%sT%s:%s:%s%s" % (y, mo, d, h, mi, se or "00", "+00:00" if off == "Z" else off))
    return ("", t.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))


def _duration(secs):
    secs = int(secs)
    d, r = divmod(secs, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    t = "".join(x for x in ("%dH" % h if h else "", "%dM" % m if m else "", "%dS" % s if s else "") if x)
    return "P" + ("%dD" % d if d else "") + ("T" + t if t else ("" if d else "T0S"))


def feed_events(key):
    """[(member, moment-name, at, title, notice seconds or None)] — each member of each `feed` reading of the drawing, one
    per `timing` entry it holds in the civil calendar."""
    v = vm.view_entry(key)
    out = []
    for e in v.get("feed") or []:
        if not isinstance(e, dict):
            continue
        notice = vm.seconds(e.get("notice")) if e.get("notice") else None
        for m in vm.members(e["selection"]):
            f = vm.fm(m)
            for name, t in sorted((f.get("timing") or {}).items()):
                if isinstance(t, dict) and t.get("system") == "gregorian-civil" and _ics_time(t.get("at")):
                    out.append((m, name, t.get("at"), f.get("title") or m, notice))
            for name, c in sorted((f.get("clauses") or {}).items()):         # a clause's `due` (its first, where it repeats)
                if isinstance(c, dict) and c.get("state") not in ("met", "waived") and _ics_time(c.get("due")):
                    out.append((m, name, c["due"], "%s: %s" % (f.get("title") or m, c.get("what") or name), notice))
    return out


def ics_text(events, garden_id, stamp=None):
    """RFC 5545: one VEVENT per event, its UID the garden's and the member's, a VALARM `notice` before where one is given."""
    stamp = stamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//daftar//dmview ics//EN", "CALSCALE:GREGORIAN"]
    for m, name, at, title, notice in events:
        kind, when = _ics_time(at)
        lines += ["BEGIN:VEVENT", "UID:%s-%s@%s" % (m, name, garden_id), "DTSTAMP:" + stamp,
                  "DTSTART%s:%s" % (";" + kind if kind else "", when), "SUMMARY:" + _ics_escape(title)]
        if notice:
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + _ics_escape(title), "TRIGGER:-" + _duration(notice),
                      "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
