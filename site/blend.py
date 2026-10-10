"""site/blend.py — the one page, rendered from what site/board.py proved: a sentence you write, the ladder you climb, a
garden played back, and yours (the site redesign of 2026-10-10: concept 2's opening, concept 1's ladder, concept 3's
time). Every form, refusal, rule, count, level and role is the release's — the data board.py proved in a garden grown
from it, the core's law (core/law/core.yaml, levels.yaml, profiles.yaml), README.md — and the story's words are
site/blend.yaml. Nothing of daftar's language is typed here.

    page = blend.render(DATA, boards, release_dir)
"""
import html
import json
import os
import re

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
DATA = BOARDS = CORE = LEVELS = README = W = MECH = SCENE = ITEMS = LENSES = UI = MOMENT = FILL = LV = LINE_ORDER = None
REL = None


def _load(data, boards, rel):
    global DATA, BOARDS, CORE, LEVELS, README, W, MECH, SCENE, ITEMS, LENSES, UI, MOMENT, FILL, LV, LINE_ORDER, REL
    DATA, BOARDS, REL = data, boards, rel
    CORE = yaml.safe_load(open(os.path.join(rel, 'core/law/core.yaml'), encoding='utf-8'))
    LEVELS = yaml.safe_load(open(os.path.join(rel, 'core/law/levels.yaml'), encoding='utf-8'))['levels']
    README = open(os.path.join(rel, 'README.md'), encoding='utf-8').read()
    W = yaml.safe_load(open(os.path.join(HERE, 'blend.yaml'), encoding='utf-8'))
    MECH = {m['id']: m for m in DATA['mechanisms']}
    SCENE = {m['id']: m['scene'] for m in BOARDS['mechanisms']}
    ITEMS = {k['id']: k for m in DATA['mechanisms'] for k in m['keeper']}
    LENSES = DATA['lenses']
    UI = DATA['ui']
    MOMENT = {mo['id']: mo for mo in W['moments']}
    FILL = {'release': DATA['release'], 'version': DATA['version']}
    LINE_ORDER = [ln['line'] for ln in CORE['lines']]
    LV = all_levels()


def esc(s):
    return html.escape(str(s), quote=True)


def prose(s, lang):
    """Escaped prose; `code` becomes <code>, isolated left to right inside Persian."""
    s = esc(s.format(**FILL) if '{' in s and '}' in s else s)
    d = ' dir="ltr"' if lang == 'fa' else ''
    return re.sub(r'`([^`]+)`', lambda m: f'<code{d}>{m.group(1)}</code>', s)


def num(n, lang):
    return str(n).translate(FA_DIGITS) if lang == 'fa' else str(n)


def both(tag, en, fa, cls='', raw=False, attrs=''):
    """The same words in both languages; the page shows the one the reader chose (with or without script)."""
    c = f' class="{cls}"' if cls else ''
    e = en if raw else prose(en, 'en')
    f = fa if raw else prose(fa, 'fa')
    return (f'<{tag}{c}{attrs} data-l="en" lang="en">{e}</{tag}>'
            f'<{tag}{c}{attrs} data-l="fa" lang="fa" dir="rtl">{f}</{tag}>')


def w(key, **kw):
    en, fa = W['ui']['en'][key], W['ui']['fa'][key]
    if kw:
        en = en.format(**kw)
        fa = fa.format(**{k: num(v, 'fa') if isinstance(v, int) else v for k, v in kw.items()})
    return en, fa


def sui(key):
    return W['ui']['en'][key], W['ui']['fa'][key]


def ui(key, **kw):
    en, fa = UI['en'][key], UI['fa'][key]
    return (en.format(**kw), fa.format(**kw)) if kw else (en, fa)


# ------------------------------------------------------------------------------------------- a form, and its refusal
def film(mid, mode='both'):
    """The form as the gate passed it, with the scene's break folded in as what was written first, and the gate's
    own line for the break (concept 3's renderer)."""
    m, sc = MECH[mid], SCENE[mid]
    brk = sc['break']
    lines = m['form'].split('\n')
    out, hit = [], False
    reps = [brk['replace'][i:i + 2] for i in range(0, len(brk.get('replace', [])), 2)]
    shown = brk['bean'] in {s.get('bean') for s in sc['show']} and not brk.get('copy_of') and not brk.get('staged')
    for ln in lines:
        e = esc(ln)
        if shown and any(a in ln for a, _ in reps):
            was = ln
            for a, b in reps:
                was = was.replace(a, b)
            out.append(f'<span class="ln was">{esc(was)}</span><span class="ln now">{e}</span>')
            hit = True
        elif shown and any(ln.lstrip().startswith(d) for d in brk.get('drop', [])):
            out.append(f'<span class="ln now add">{e}</span>')
            hit = True
        elif ln.startswith('# '):
            out.append(f'<span class="ln cmt">{e}</span>')
        else:
            out.append(f'<span class="ln">{e}</span>')
    frag = ''
    if not hit:   # the break touched a bean the form does not show: say what the scene changed
        parts = []
        if brk.get('copy_of'):
            parts.append(f'copy_of <code>{esc(brk["copy_of"])}</code>')
        for a, b in reps:
            parts.append(f'<code class="fw">{esc(b)}</code> <span aria-hidden="true">→</span> <code>{esc(a)}</code>')
        for d in brk.get('drop', []):
            parts.append(f'drop <code>{esc(d)}</code>')
        if brk.get('staged'):
            parts.append('staged')
        we, wf = sui('was')
        frag = (f'<p class="frag"><span class="wl">{both("span", we, wf)}</span> <span dir="ltr"><code class="file">'
                f'beans/{esc(brk["bean"])}.md</code> ' + ' · '.join(parts) + '</span></p>')
    re_, rf = ui('refusal_label')
    refusal = (f'<div class="refusal" role="note"><p class="rl">{both("span", re_, rf)} '
               f'<span class="rule" dir="ltr">rule <code>{esc(m["rule"])}</code></span></p>'
               f'<pre dir="ltr"><code>{esc(m["error"])}</code></pre></div>')
    fe, ff = ui('form_label')
    return (f'<figure class="film" data-mode="{mode}">'
            f'<figcaption>{both("span", fe, ff)}</figcaption>{frag}'
            f'<pre dir="ltr"><code>' + ''.join(out) + f'</code></pre>{refusal}</figure>')


def keeper_items(ids):
    out = []
    for iid in ids:
        k = ITEMS.get(iid)
        if not k:
            continue
        meta = [x for x in (ui('item_rules', n=k['nrules'])[0] if k['nrules'] else '',
                            ui('item_checks', n=k['checks'])[0] if k['checks'] else '',
                            ui('item_relations', n=k['relations'])[0] if k['relations'] else '') if x]
        suites = ', '.join(f'<code>{esc(s)}</code>' for s in k['suites'])
        out.append('<li class="item" dir="ltr" lang="en">'
                   f'<p class="ih"><code>{esc(k["id"])}</code></p><p class="im">{prose(k["meaning"], "en")}</p>'
                   + (f'<p class="iv"><code>{esc(k["valency"])}</code></p>' if k['valency'] else '')
                   + (f'<p class="ir">{prose(k["reason"], "en")}</p>' if k['reason'] else '')
                   + f'<p class="ix">{esc(" · ".join(meta))}' + (f' · {suites}' if suites else '') + '</p></li>')
    return '<ul class="items">' + ''.join(out) + '</ul>' if out else ''


def lens(lid, body):
    L = next(x for x in LENSES if x['id'] == lid)
    return (f'<div class="lens" data-lens="{lid}">' + both('p', esc(L['who']), esc(L['fa']['who']), cls='lw', raw=True)
            + body + '</div>')


def lenses_of(mid):
    m = MECH[mid]
    save, again = DATA['commands']['save'], DATA['commands']['again']
    return ('<div class="lenses">'
            + lens('person', both('p', m['person'], m['fa']['person']))
            + lens('gardener', both('p', m['gardener'], m['fa']['gardener']))
            + lens('agent', both('p', m['agent_note'], m['fa']['agent_note'])
                   + f'<pre class="cmd" dir="ltr"><code>{esc(save)}\n{esc(again)}</code></pre>')
            + lens('keeper', keeper_items([k['id'] for k in m['keeper']]))
            + '</div>')


def lenses_told(mo):
    en, fa = mo['en'], mo['fa']
    return ('<div class="lenses">' + lens('person', both('p', en['person'], fa['person']))
            + lens('gardener', both('p', en['gardener'], fa['gardener']))
            + lens('agent', both('p', en['agent'], fa['agent']))
            + lens('keeper', keeper_items(mo.get('items', []))) + '</div>')


def mech_head(mid, tag='h3'):
    m = MECH[mid]
    return (f'<header class="mh" id="m-{mid}"><span class="glyph" aria-hidden="true">{esc(m["glyph"])}</span>'
            + both(tag, esc(m['name']), esc(m['fa']['name']), raw=True) + '</header>')


def story_line(mid):
    mo = MOMENT.get(mid) or next(x for x in W['moments'] if x.get('mechanism') == mid)
    return both('p', mo['en']['line'], mo['fa']['line'], cls='story')


# ============================================================================================ ① the sentence
def roles():
    out = []
    for r in CORE['roles']:
        out.append(f'<li class="role role-{r["role"]}"><code class="rw" dir="ltr">{esc(r["role"])}</code>'
                   + both('span', prose(r['meaning'], 'en'), esc(W['roles_fa'][r['role']]), cls='rm', raw=True)
                   + f'<span class="rs" dir="ltr" lang="sa">{esc(r["source"].split(" — ")[0])}</span></li>')
    return '<ol class="roles">' + ''.join(out) + '</ol>'


def sentence_card(mid):
    fe, ff = w('s_first')
    me, mf = w('s_mended')
    te, tf = w('s_taken')
    ae, af = w('s_again')
    return (f'<article class="card sentence-card" data-mech="{mid}">' + mech_head(mid) + story_line(mid)
            + '<div class="try js-only">'
            + f'<button type="button" class="save first" data-save="first">{both("span", fe, ff)}</button>'
            + f'<button type="button" class="save mended" data-save="mended">{both("span", me, mf)}</button>'
            + f'<p class="answer taken" hidden>{both("span", te, tf)}</p>'
            + f'<p class="answer again" hidden>{both("span", ae, af)}</p></div>'
            + film(mid) + lenses_of(mid) + '</article>')


def movement_sentence():
    ke, kf = w('s_kicker')
    he, hf = w('s_head')
    le, lf = w('s_lede')
    re_, rf = w('s_roles')
    te, tf = w('s_try')
    cards = ''.join(sentence_card(mid) for mid in W['movements']['sentence'])
    return (f'<section class="movement" id="sentence" aria-labelledby="sentence-h">'
            + both('p', ke, kf, cls='kicker') + both('h2', he, hf, attrs=' id="sentence-h"') + both('p', le, lf, cls='lede')
            + '<div class="line" aria-hidden="true"><span class="rule-line"></span><span class="caret"></span></div>'
            + both('h3', re_, rf, cls='sub') + roles()
            + both('h3', te, tf, cls='sub') + f'<div class="cards">{cards}</div></section>')


# ============================================================================================ ② the ladder
def all_levels():
    """Every step of the ladder, the face's and the knowledge tree's, each with its line, meaning and stands."""
    out = {}
    for lv in CORE['levels']:
        out[lv['level']] = {'line': lv['line'], 'meaning': lv.get('meaning', ''), 'stands': lv.get('stands') or []}
    for lv in LEVELS:
        out[lv['level']] = {'line': lv['line'], 'meaning': lv.get('meaning', ''), 'stands': lv.get('stands') or []}
    return out


def by_line(line):
    order = [lv['level'] for lv in CORE['levels']] + [lv['level'] for lv in LEVELS]
    return [x for x in order if LV[x]['line'] == line]


def stands_text(lid):
    parts = []
    for s in LV[lid]['stands']:
        way = 'l_made_of' if s.get('as') == 'made-of' else 'l_possible_on'
        e, f = w(way)
        wh = ''
        if s.get('while'):
            we, wf = w('l_while')
            wh = (f' <span data-l="en" lang="en">{we}</span><span data-l="fa" lang="fa">{wf}</span>'
                  f' <code dir="ltr">{esc(s["while"])}</code>')
        parts.append(f'<span data-l="en" lang="en">{e}</span><span data-l="fa" lang="fa">{f}</span> '
                     f'<a href="#lv-{esc(s["at"])}"><code dir="ltr">{esc(s["at"])}</code></a>{wh}')
    return ' · '.join(parts)


def ladder_figure():
    """The ladder as a body: its foundation at the bottom, never mirrored (DIRECTION.md: the ladder's stands)."""
    rows = []
    for line in LINE_ORDER:                                   # in the law's order, bottom first: drawn bottom-up
        le, lf = W['lines']['en'][line], W['lines']['fa'][line]
        steps = ''.join(f'<li class="step" data-level="{esc(x)}"><a href="#lv-{esc(x)}" dir="ltr">{esc(x)}</a></li>'
                        for x in by_line(line))
        rows.append(f'<li class="rung line-{line}" data-line="{line}"><a class="rl" href="#place-{line}">'
                    + both('span', le, lf, raw=True) + f'</a><ol class="steps">{steps}</ol></li>')
    he, hf = w('l_here')
    return (f'<nav class="ladder" aria-label="ladder" tabindex="0"><p class="here">{both("span", he, hf)}</p>'
            f'<ol class="rungs">' + ''.join(rows) + '</ol></nav>')


def place(line, mechs):
    le, lf = W['lines']['en'][line], W['lines']['fa'][line]
    se, sf = w('l_levels')
    steps = []
    for x in by_line(line):
        st = stands_text(x)
        steps.append(f'<li class="lv" id="lv-{esc(x)}"><p class="ln"><code dir="ltr">{esc(x)}</code>'
                     + (f'<span class="st">{st}</span>' if st else '') + '</p>'
                     + (f'<p class="lm" dir="ltr" lang="en">{prose(LV[x]["meaning"], "en")}</p>' if LV[x]['meaning'] else '')
                     + '</li>')
    body = ''
    if mechs:
        me, mf = w('l_mechs')
        body = (both('h4', me, mf, cls='sub') + '<div class="cards">'
                + ''.join(f'<article class="card">{mech_head(mid)}{story_line(mid)}{film(mid)}{lenses_of(mid)}</article>'
                          for mid in mechs) + '</div>')
    return (f'<section class="place line-{line}" id="place-{line}" data-line="{line}">'
            + both('h3', le, lf, raw=True)
            + f'<details class="steps-of"{" open" if line in ("frame", "said") else ""}><summary>{both("span", se, sf)} '
            f'<span class="n" dir="ltr">{len(by_line(line))}</span></summary><ol class="lvs">' + ''.join(steps) + '</ol></details>'
            + body + '</section>')


def movement_ladder():
    ke, kf = w('l_kicker')
    he, hf = w('l_head')
    le, lf = w('l_lede')
    ce, cf = w('l_crown')
    crown = CORE['crown'][0]
    places = ''.join(place(line, W['movements']['ladder'].get(line, [])) for line in LINE_ORDER)
    return (f'<section class="movement" id="ladder" aria-labelledby="ladder-h">'
            + both('p', ke, kf, cls='kicker') + both('h2', he, hf, attrs=' id="ladder-h"') + both('p', le, lf, cls='lede')
            + '<div class="climb">' + f'<div class="places">{places}'
            + f'<section class="place crown" id="place-crown">{both("h3", ce, cf)}<p class="cr" dir="ltr" lang="en">'
            f'<code>{esc(crown["crown"])}</code> — {esc(crown["law"])}</p></section></div>'
            + ladder_figure() + '</div></section>')


# ============================================================================================ ③ time
def moment(i, mid, n):
    mo = MOMENT.get(mid)
    if mo and mo.get('kind') in ('grown', 'vacant', 'you'):
        en, fa = mo['en'], mo['fa']
        told = ''
        if mo['kind'] == 'vacant':
            te, tf = w('t_told')
            told = both('p', te, tf, cls='told')
        body = (both('h3', esc(en['title']), esc(fa['title']), raw=True) + both('p', en['line'], fa['line'], cls='story') + told
                + (lenses_told(mo) if mo['kind'] != 'you' else ''))
        if mo['kind'] == 'you':
            body += '<p><a class="go" href="#yours">' + both('span', *w('m4')) + '</a></p>'
        kind = mo['kind']
    else:
        kind = 'mechanism'
        body = mech_head(mid) + story_line('saved' if mid == 'gate' else mid) + film(mid) + lenses_of(mid)
    me, mf = sui('moment')
    tick = f'<span class="tick" dir="ltr">{i + 1}</span>'
    return (f'<li class="moment kind-{kind}" id="t-{mid}" data-i="{i}">{tick}'
            + both('p', me.format(i=i + 1, n=n), mf.format(i=num(i + 1, 'fa'), n=num(n, 'fa')), cls='mi') + body + '</li>')


def movement_time():
    ke, kf = w('t_kicker')
    he, hf = w('t_head')
    ho, hof = w('t_how')
    ids = W['movements']['time']
    n = len(ids)
    ee, ef = sui('earlier')
    la, lf = sui('later')
    rail = ('<div class="rail js-only" role="group" aria-label="time">'
            f'<button type="button" class="step-btn" data-cmd="earlier" aria-label="earlier"><span class="g" data-glyph="earlier"></span> {both("span", ee, ef)}</button>'
            '<ol class="ticks">' + ''.join(f'<li><button type="button" data-goto="{i}" aria-label="{i + 1}">'
                                          f'<span dir="ltr">{i + 1}</span></button></li>' for i in range(n)) + '</ol>'
            f'<button type="button" class="step-btn" data-cmd="later" aria-label="later">{both("span", la, lf)} <span class="g" data-glyph="later"></span></button>'
            '</div>')
    return (f'<section class="movement" id="time" aria-labelledby="time-h">'
            + both('p', ke, kf, cls='kicker') + both('h2', he, hf, attrs=' id="time-h"') + both('p', ho, hof, cls='lede')
            + rail + '<ol class="moments" tabindex="0">' + ''.join(moment(i, mid, n) for i, mid in enumerate(ids)) + '</ol></section>')


# ============================================================================================ ④ yours
def movement_yours():
    ke, kf = w('y_kicker')
    he, hf = w('y_head')
    you = MOMENT['you']
    m = re.search(r'Tell the agent:\s*\n\s*\n> (.*?)\n\n', README, re.S)
    quote = ' '.join(l.lstrip('> ').strip() for l in m.group(1).splitlines()) if m else ''
    le, lf = sui('you_label')
    ne, nf = sui('next_time')
    return (f'<section class="movement" id="yours" aria-labelledby="yours-h">'
            + both('p', ke, kf, cls='kicker') + both('h2', he, hf, attrs=' id="yours-h"')
            + both('p', you['en']['line'], you['fa']['line'], cls='lede')
            + both('p', le, lf, cls='sub') + f'<blockquote class="tell" dir="ltr" lang="en"><p>{prose(quote, "en")}</p></blockquote>'
            + both('p', ne, nf) + '</section>')


# ============================================================================================ the page
def head_controls():
    lens_inputs = ''.join(f'<input type="radio" name="lens" id="lens-{L["id"]}" value="{L["id"]}"{" checked" if i == 0 else ""}>'
                          for i, L in enumerate(LENSES))
    lens_labels = ''.join(f'<label for="lens-{L["id"]}">' + both('span', esc(L['who']), esc(L['fa']['who']), raw=True) + '</label>'
                          for L in LENSES)
    lg_e, lg_f = w('lens_group')
    la_e, la_f = w('lang_group')
    return (lens_inputs + '<input type="radio" name="lang" id="lang-en" value="en" checked>'
            '<input type="radio" name="lang" id="lang-fa" value="fa">'
            '<header class="top"><a class="brand" href="#top"><span lang="en">daftar</span> <span lang="fa" dir="rtl">دفتر</span></a>'
            + both('p', UI['en']['tagline'], UI['fa']['tagline'], cls='tagline')
            + f'<p class="ver" dir="ltr">{esc(DATA["release"])} · core {esc(DATA["version"])}</p>'
            + f'<div class="controls"><div class="lens-pick" role="radiogroup">{both("span", lg_e, lg_f, cls="cl")}{lens_labels}</div>'
            + f'<div class="lang-pick">{both("span", la_e, la_f, cls="cl")}<label for="lang-en" lang="en">English</label>'
              '<label for="lang-fa" lang="fa">فارسی</label></div></div>'
            + '<nav class="movements"><ol>' + ''.join(f'<li><a href="#{a}">' + both('span', *w(k)) + '</a></li>'
                                                   for a, k in (('sentence', 'm1'), ('ladder', 'm2'), ('time', 'm3'), ('yours', 'm4')))
            + '</ol></nav></header>')


def orientations():
    """The view profile's `orientations` table where the release has it; the design's rows until it does."""
    prof = os.path.join(REL, 'core/law/profiles.yaml')
    try:
        p = yaml.safe_load(open(prof, encoding='utf-8'))
        rows = [r for r in (p.get('profiles') or []) if isinstance(r, dict) and r.get('profile') == 'view'][0].get('orientations')
        if rows:
            return {r['order']: [r['axis'], r.get('sense', 1), r.get('follows', True)] for r in rows}
    except Exception:
        pass
    return None


def orientations():
    """The view profile's `orientations` rows, as widgets/direction.js reads them from the page."""
    p = yaml.safe_load(open(os.path.join(REL, 'core/law/profiles.yaml'), encoding='utf-8'))
    keep = ('order', 'axis', 'sense', 'follows', 'commands')
    return [{k: r[k] for k in keep if k in r} for r in (p.get('orientations') or [])]


def render(data, boards, rel):
    _load(data, boards, rel)
    c = DATA['counts']
    ce, cf = w('f_counts', release=DATA['release'], **c)
    be, bf = w('f_built')
    links = ' · '.join(f'<a href="https://github.com/0mit/daftar/blob/{esc(DATA["release"])}/{f}" dir="ltr">{f}</a>'
                       for f in ('README.md', 'MANIFESTO.md', 'MODEL.md'))
    body = (head_controls() + '<main id="top">' + movement_sentence() + movement_ladder() + movement_time() + movement_yours()
            + '</main>' + f'<footer class="foot">{both("p", ce, cf)}{both("p", be, bf)}<p>{links}</p></footer>')
    title = f'daftar — {UI["en"]["tagline"].split(".")[0]}'
    data_json = json.dumps(DATA, ensure_ascii=False).replace('</', '<\\/')
    ori = json.dumps(orientations()).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; base-uri 'none'">
<title>{esc(title)}</title>
<link rel="icon" href="assets/icon.svg">
<link rel="stylesheet" href="assets/blend.css">
<script src="assets/direction.js" defer></script>
<script src="assets/blend.js" defer></script>
</head>
<body>
<a class="skip" href="#top">{esc(W["ui"]["en"]["skip"])}</a>
{body}
<script type="application/json" id="data">{data_json}</script>
<script type="application/json" id="orientations">{ori}</script>
</body>
</html>
'''
