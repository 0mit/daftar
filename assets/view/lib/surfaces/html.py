#!/usr/bin/env python3
"""The `view` asset's surface for a page kept as ONE FILE — read offline, from any disk (`file://`) or any static host:
every drawing at its four lenses, the reference, the author mode, the runtime and the page's data inline, nothing loaded
from outside. It carries no live value: what it shows is the ledger at the commit it was drawn from. Named by the code
of the technology catalogue it speaks (`html`), one surface among siblings; `view report` writes it."""
import view_report

TECHNOLOGY = "html"
OFFLINE = True          # it opens with no network, and says what it shows is as of the commit it was drawn from


def render(payload, **_):
    """The page, one self-contained file."""
    return view_report.build_html(payload)
