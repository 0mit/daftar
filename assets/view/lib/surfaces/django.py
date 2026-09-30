#!/usr/bin/env python3
"""The `view` asset's surface for a FRAMEWORK'S OWN PAGES — a Django site that shows a drawing beside its own content.
A view of the site renders one drawing as a fragment, and its template places it (`{{ drawing|safe }}`, the fragment made
safe in the view with `django.utils.safestring.mark_safe`):

    from surfaces.django import render
    drawing = mark_safe(render(payload, key="orders", level="understand"))

WHAT IT IS GIVEN IS SCOPED ALREADY. The payload is the one the ledger's grants open to the viewer
(`view_serve.Host.scoped_payload`): the site maps its signed-in user to a viewer being, as the host's configuration
does, and never passes the whole page. The fragment carries its own stylesheet under `.vw`, so the site keeps its own,
and the one runtime every surface mounts drawings with. Named by the code of the technology catalogue it speaks
(`django`), one surface among siblings."""
import json

import view_kit as kit

TECHNOLOGY = "django"
OFFLINE = False         # it is part of the site's pages, served while the site runs


def render(payload, key=None, level=None, **_):
    """One drawing of the page as a fragment: its container, its stylesheet, the runtime and the mount."""
    key = key or (payload.get("order") or [None])[0]
    view = (payload.get("views") or {}).get(key)
    if view is None:
        raise KeyError("the page draws no %r" % key)
    levels = view.get("levels") or payload.get("levels") or []
    level = level or next((lv.get("id") for lv in levels if lv.get("form") == "schematic"), None) or \
        (levels[0].get("id") if levels else None)
    uid = "vw-%s" % key
    data = json.dumps({"view": view, "level": level}, ensure_ascii=False).replace("</", "<\\/")
    return ('<div class="vw" id="%s"></div><style>%s</style><script>%s</script>'
            '<script>(function(){var d=%s;window.viewMount(document.getElementById("%s"),d.view,{level:d.level});})();</script>'
            % (uid, kit.SCHEMA_CSS, kit.RUNTIME_JS, data, uid))
