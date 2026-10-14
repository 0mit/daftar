#!/usr/bin/env python3
"""A day's hours, and what is kept in view (the operator, 2026-10-14; `transparency`, core 2.7).

The server's timeline gives each event the minutes of its day it takes and whether it takes them
(`view_engraved.py` `timeline`: an attendance's extent, a session's `lasts`; its `transparency`), and the week's cell
draws them apart (view_timeline.js). Read here, then drawn in a browser, in Persian, from a day of invented events —
yoga at 08:30 for 150 minutes, a course kept in view (transparent) at 10:00 for an hour, a weekly session at 15:30 for
90 minutes, a rent due with no time:

  minutes    the server reads an extent's minutes of its day (to the day's end where it runs on), a repetition's `lasts`
             in minutes or hours, and nothing for a moment or a day
  hours      the day's width is divided among what takes hours, opaque: one strip for the yoga and one for the session,
             each its share by its minutes (150 to 90), the two filling the width, and earlier at the start of the
             reader's line — at the right, in Persian; its title under the day's label
  kept       what is kept in view — the transparent course, the rent — is laid below the day's label, the day's height
             divided between them, over the hours; never a strip
  label      the day's label holds, in its title, the day in the reader's other calendars (here the Gregorian and the
             Hijri beside the Persian shown)

Run: python3 test/view_timeline_hours.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'assets', 'view', 'lib'), os.path.join(ROOT, 'bin'), ROOT]
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


import view_engraved as ve  # noqa: E402

check("minutes: an extent's minutes of its day, to the day's end where it runs on; a repetition's `lasts`; nothing for "
      "a moment or a day",
      ve._minutes('2026-10-14T08:30+03:00/2026-10-14T11:00+03:00') == 150
      and ve._minutes('2026-10-14T23:00+03:00/2026-10-15T01:00+03:00') == 60
      and ve._minutes('2026-10-14T08:30+03:00') is None and ve._minutes('2026-10-14') is None
      and ve._lasts({'lasts': {'measure': {'count': 150, 'unit': 'minute'}}}) == 150
      and ve._lasts({'lasts': {'measure': {'count': '1.5', 'unit': 'hour'}}}) == 90 and ve._lasts({}) is None)

DAY = '2026-10-14'
DATA = {'today': DAY, 'from': '2026-10-01', 'to': '2026-10-31', 'layouts': ['week'], 'events': [
    {'day': DAY, 'time': '08:30', 'bean': 'yoga', 'title': 'یوگا', 'kind': 'happening', 'minutes': 150, 'transparency': 'opaque'},
    {'day': DAY, 'time': '10:00', 'bean': 'course', 'title': 'دوره', 'kind': 'happening', 'minutes': 60, 'transparency': 'transparent'},
    {'day': DAY, 'time': '15:30', 'bean': 'class', 'title': 'کلاس', 'kind': 'due', 'clause': 'weekly', 'what': None,
     'at_time': '15:30', 'minutes': 90, 'transparency': 'opaque', 'index': 3, 'times': None},
    {'day': DAY, 'time': None, 'bean': 'rent', 'title': 'اجاره', 'kind': 'due', 'clause': 'monthly', 'what': 'اجاره',
     'minutes': None, 'transparency': None, 'index': 1, 'times': None},
]}
E = {'settings': {'garden': {'lang': 'fa'}, 'currencies': []}, 'drawings': {'t': DATA}}

browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
if not browser:
    print("NOTE  the day was not drawn in a browser: none on this machine")
else:
    T = tempfile.mkdtemp(prefix='view-timeline-hours-')
    try:
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_timeline.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="t" class="vw light" dir="rtl" style="width:980px"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), el = document.getElementById('t');
  window.daftarArchetypes.timeline(el, E.drawings.t, t, {engraved: {axes: {inline: 'time'}}});
  const cell = el.querySelector('.eg-day[data-day="%(day)s"]'), cw = cell.getBoundingClientRect().width;
  out.takes = [...cell.querySelectorAll('.eg-take')].map(s => { const r = s.getBoundingClientRect(), cs = getComputedStyle(s);
    return {who: s.innerText.trim(), minutes: Number(s.dataset.minutes), share: r.width / cw, x: r.left + r.width / 2,
            col: cs.gridColumnStart + '/' + cs.gridColumnEnd, opacity: cs.opacity, title: s.title}; });
  out.kept = [...cell.querySelectorAll('.eg-kept .eg-event')].map(li => ({who: li.innerText.trim(), h: li.getBoundingClientRect().height}));
  const head = cell.querySelector('.eg-day-head');
  out.headTitle = head.title; out.headBelow = cell.querySelector('.eg-kept').getBoundingClientRect().top >= head.getBoundingClientRect().bottom - 1;
  out.over = [...cell.querySelectorAll('.eg-kept, .eg-day-head')].every(x => Number(getComputedStyle(x).zIndex) > Number(getComputedStyle(cell.querySelector('.eg-hours')).zIndex));
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'day.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(E, ensure_ascii=False), 'day': DAY})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180, env=dict(os.environ, TMPDIR=T))     # what the browser leaves, in the folder that goes
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        takes = {x['minutes']: x for x in B.get('takes') or []}
        check("hours: what takes hours is a strip, opaque, one for the yoga and one for the session — never the course "
              "kept in view or the rent",
              not B['errs'] and sorted(takes) == [90, 150] and all(x['opacity'] == '1' for x in takes.values())
              and 'یوگا' in takes[150]['who'] and 'کلاس' in takes[90]['who'], B)
        check("...the day's width divided between them by their minutes (150 to 90), the two filling it",
              takes and abs(takes[150]['share'] - 150 / 240) < 0.03 and abs(takes[90]['share'] - 90 / 240) < 0.03
              and abs(takes[150]['share'] + takes[90]['share'] - 1) < 0.04, B.get('takes'))
        check("...earlier at the start of the reader's line: the morning's strip right of the afternoon's, in Persian",
              takes and takes[150]['x'] > takes[90]['x'], B.get('takes'))
        kept = B.get('kept') or []
        check("kept: the course kept in view and the rent are laid below the day's label, over the hours, the height "
              "divided between them",
              [k['who'].split()[0] for k in kept] == ['دوره', 'اجاره'] and B.get('headBelow') and B.get('over')
              and len(kept) == 2 and abs(kept[0]['h'] - kept[1]['h']) < 3, B)
        check("label: its title is the day in the reader's other calendars — the Gregorian and the Hijri beside the "
              "Persian shown", '۲۰۲۶' in (B.get('headTitle') or '') and '۱۴۴۸' in (B.get('headTitle') or ''), B.get('headTitle'))
    finally:
        shutil.rmtree(T, ignore_errors=True)

print(f"\nview_timeline_hours: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
