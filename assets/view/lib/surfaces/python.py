#!/usr/bin/env python3
"""The `view` asset's surface for the page SERVED by daftar's own host (`dmview serve`, Python's standard library): it
signs viewers in, asks the ledger's grants what each may see (`view_serve.Host.may`), sends each the page scoped to
them, reads live values through the page's monitors and runs what the host enables. Named by the code of the technology
catalogue it speaks (`python`), one surface among siblings."""
import view_report

TECHNOLOGY = "python"
OFFLINE = False         # it answers while its host runs; the page it sends polls for live values


def render(payload, live=None, **_):
    """The page for one viewer: the payload already scoped to them, and what the served page needs to stay live."""
    p = dict(payload)
    if live:
        p["live"] = live
    return view_report.build_html(p)
