#!/usr/bin/env python3
"""The `view` asset's adapter for a monitor that is read over HTTP as one JSON document — a device's own API, a runner's
status file served by a web server — a sibling of `prometheus.py`, chosen because the monitor's own `knowledge` says it
`uses` the technology this file is named for (`http`, the catalogue's code).

WHAT IT READS. The monitor's address is the host's configuration (`monitors.<being>.url`), as for every adapter: the
ledger says what is read and the host says where from, so no address is restated on the page. A binding's query for
this technology (`view_bindings.query`, `technology: http`) is a JSON Pointer (RFC 6901) into the document: a
live-value is the number there; a live-series is the object there, one item per key (or the list there, each item's
`name` and `value`); a live-state is whether the document is served (1) or not (0). The viewer's scope does not narrow
a device's document — a device answers for itself — so the host sends a drawing of a being only where the viewer may
see that being, and asks nothing of a being they may not.

A document holds now, and no past: `history` is empty, and a drawing that correlates over time reads another monitor.
It writes no bundle: the device is its own server.
"""
import json, urllib.request

TECHNOLOGY = "http"


def selector(scope=None):
    return None


def pointer_problem(p):
    if not isinstance(p, str) or (p and not p.startswith("/")):
        return "a JSON Pointer is empty (the whole document) or begins with `/` (RFC 6901)"
    return None


def at(doc, p):
    """The value at JSON Pointer `p` in `doc`, or None where nothing is there."""
    if p == "":
        return doc
    for tok in p[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(doc, dict):
            doc = doc.get(tok)
        elif isinstance(doc, list) and tok.isdigit() and int(tok) < len(doc):
            doc = doc[int(tok)]
        else:
            return None
    return doc


def says(b):
    return (b.get("query") or {}).get(TECHNOLOGY)


def describe(b):
    return "the document's %s" % says(b) if says(b) is not None else "whether the document is served"


def check_binding(b):
    if b.get("live") == "live-state":
        return []
    prob = pointer_problem(says(b))
    return ["its %s query is not a JSON Pointer: %s" % (TECHNOLOGY, prob)] if prob else []


def _get(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


def _number(x):
    try:
        return float(x) if x is not None and not isinstance(x, bool) else None
    except (TypeError, ValueError):
        return None


def values(url, binds, sel=None):
    """{binding id: number | [{name, value}] | None} — the document at `url` read once, each binding at its pointer."""
    try:
        doc, up = _get(url), 1.0
    except Exception:
        doc, up = None, 0.0
    out = {}
    for b in binds:
        if b.get("live") == "live-state":
            out[b["id"]] = up
            continue
        x = at(doc, says(b) or "") if doc is not None else None
        if b.get("live") == "live-series":
            if isinstance(x, dict):
                out[b["id"]] = [{"name": str(k), "value": _number(v)} for k, v in x.items()]
            elif isinstance(x, list):
                out[b["id"]] = [{"name": str(i.get("name")), "value": _number(i.get("value"))} for i in x if isinstance(i, dict)]
            else:
                out[b["id"]] = None
        else:
            out[b["id"]] = _number(x)
    return out


def history(url, binds, sel, hours, step, now):
    return {b["id"]: [] for b in binds if b.get("live") == "live-value"}


def alerts(settings, beans, binds):
    return []
