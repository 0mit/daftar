"""A garden's own drawings for its page — copy it into the garden (as `bin/drawings.py`, or any name that is not
`bin/dm*.py`) and name it in the page bean: `view: { drawings: file:bin/drawings.py }`.

A drawing is a function that returns (title, svg, caption, claim), drawn ONLY with the kit, so every element it draws
is recorded — its pattern, its id (the slug of its label), its box, and the being it depicts (`bean=`). `COMPOSERS`
lists the drawings under the keys the page's `views` entries have. The kit is the asset's `view_kit`: the asset puts it
on the path before the module is loaded.
"""
from view_kit import node, store, gate, flow, band, action_btn, figure


def orders():
    b = []
    b.append(band(20, 16, 560, "An order is checked, then baked"))
    b.append(node(20, 50, 180, 48, "Customer", "places an order", cls="ext"))
    b.append(gate(290, 74, "in stock?", 110, 44))
    b.append(node(380, 50, 200, 48, "Oven", "bakes the order", bean="oven-a"))
    b.append(flow(200, 74, 235, 74, "order"))
    b.append(flow(345, 74, 380, 74, "yes", cls="accent"))
    b.append(action_btn(380, 120, 200, "Preheat", "preheats the oven"))
    cap = "A <b>customer</b> orders; the <b>gate</b> checks the stock; the <b>oven</b> bakes."
    return ("Orders", figure(600, 170, "".join(b), "an order checked, then baked"), cap, "Every order in stock is baked.")


COMPOSERS = {"orders": orders}
