"""Render HTML snippets in headless Chromium and report each one's VISUAL order: its glyphs read left to right as
they land on screen (one Range per character, sorted by x). Usage: lab.py cases.json -> prints one line per case."""
import json, subprocess, sys, tempfile, pathlib, html
cases = json.load(open(sys.argv[1], encoding='utf-8'))
page = """<!doctype html><html><head><meta charset="utf-8"><style>body{font:20px 'Noto Sans Arabic',sans-serif}
.box{width:900px;margin:4px;border:1px solid #ccc}</style></head><body>%s
<script>
const out = [];
for (const box of document.querySelectorAll('.box')) {
  const w = document.createTreeWalker(box, NodeFilter.SHOW_TEXT); const glyphs = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) for (let i = 0; i < n.data.length; i++) {
    const ch = n.data[i]; if (/[\\u200e\\u200f\\u061c\\u2066-\\u2069\\u202a-\\u202e]/.test(ch)) continue;
    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const b = r.getBoundingClientRect();
    if (b.width > 0 || ch.trim()) glyphs.push([b.left + b.width / 2, ch]); }
  glyphs.sort((a, b) => a[0] - b[0]);
  out.push({id: box.id, visual: glyphs.map(g => g[1]).join('')});
}
document.body.innerHTML = '<pre id="out">' + JSON.stringify(out).replace(/</g, '\\\\u003c') + '</pre>';
</script></body></html>"""
boxes = ''.join(f'<div class="box" id="c{i}" dir="{c["dir"]}">{c["html"]}</div>' for i, c in enumerate(cases))
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
    f.write(page % boxes)
r = subprocess.run(['chromium', '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=3000', '--dump-dom',
                    'file://' + f.name], capture_output=True, text=True, timeout=120)
start = r.stdout.find('<pre id="out">') + len('<pre id="out">')
res = json.loads(html.unescape(r.stdout[start:r.stdout.find('</pre>', start)]))
for c, x in zip(cases, res):
    ok = '' if 'want' not in c else ('PASS ' if x['visual'] == c['want'] else 'FAIL ')
    print(f"{ok}{c['dir']:3} {c['name']:<44} visual L→R: {x['visual']}" + ('' if not ok or ok == 'PASS ' else f"   want: {c['want']}"))
