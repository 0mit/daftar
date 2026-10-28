#!/usr/bin/env python3
"""The worker's `view_html`: the view's page, and the scripts its asset wrote into it — as the asset declares them
(`view_report.SCRIPTS`), or in a release before it declared them, its script constants — so daftard lets only those
run (security audit 2026-10-10, 2.4). A script found in the page is never among them: a bean's text the page carried
unescaped would be one.

    python3 test/worker/view_test.py
"""
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
start = src.index('def view_html(')
end = src.index('def save(')
INJECTED = 'fetch("/api/stop")'
ns = {'KIND': 'dashboard', 'sys': sys, 'nowhere': lambda p: (_ for _ in ()).throw(LookupError('nowhere'))}


def garden(view_report, view_kit=None):
    """A stand-in dashboard model whose page is drawn by `view_report`, with a bean's title carried unescaped."""
    sys.modules['view_report'] = view_report
    if view_kit is not None:
        sys.modules['view_kit'] = view_kit
    else:
        sys.modules.pop('view_kit', None)
    scripts = [s for s in (getattr(view_report, n, None) for n in ('DIRECTION_JS', 'SCRIPT')) if s] + \
              ([view_kit.RUNTIME_JS] if view_kit else [])
    page = '<html><body><h1>A title <script>%s</script></h1>%s</body></html>' % (
        INJECTED, ''.join('<script>%s</script>' % s for s in scripts))
    ns['model'] = types.SimpleNamespace(view_html=lambda: page)
    exec(compile(src[start:end], 'garden_worker.py', 'exec'), ns)
    return ns['view_html'](None), page


# a release that declares its scripts: those, in its order, and nothing else
vr = types.SimpleNamespace(SCRIPTS=('direction()', 'runtime()', 'page()'), DIRECTION_JS='direction()', SCRIPT='page()')
got, page = garden(vr, types.SimpleNamespace(RUNTIME_JS='runtime()'))
assert isinstance(got, dict) and got.get('page') == page, 'view_html answers the page and its scripts: %r' % (got,)
assert got['scripts'] == ['direction()', 'runtime()', 'page()'], got['scripts']
assert INJECTED not in got['scripts']
print('PASS: worker view — a release that declares its scripts: those, never one found in the page')

# a release before SCRIPTS (two scripts, the runtime in view_kit): its constants
vr = types.SimpleNamespace(SCRIPT='page()')
got, page = garden(vr, types.SimpleNamespace(RUNTIME_JS='runtime()'))
assert sorted(got['scripts']) == ['page()', 'runtime()'] and INJECTED not in got['scripts'], got['scripts']
print('PASS: worker view — an earlier release: its script constants, never one found in the page')

# a model that draws no view asset: no script runs
sys.modules.pop('view_report', None)
sys.modules.pop('view_kit', None)
ns['model'] = types.SimpleNamespace(view_html=lambda: '<p>no view here <script>%s</script></p>' % INJECTED)
exec(compile(src[start:end], 'garden_worker.py', 'exec'), ns)
got = ns['view_html'](None)
assert got['scripts'] == [], got
print('PASS: worker view — a page drawn without the view asset runs no script')
