/* The blend's behaviour. Without it the page is whole: every form, refusal, moment and lens is in the document, and
   the language and the lens are chosen by CSS. With it: the page takes its direction (<html dir>), the reader's save
   decides what the gate says, the ladder marks where the reader stands, and time is stepped one moment at a time —
   every key, glyph and swipe through direction.js, named by meaning, never by side. */
(function () {
  'use strict';
  var D = window.daftarDirection, doc = document, html = doc.documentElement;
  html.classList.add('js');

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; }
  var params = new URLSearchParams(location.search);

  // ---------------------------------------------------------------- language: the page's direction follows it
  function setLang(l) {
    var fa = l === 'fa';
    html.lang = fa ? 'fa' : 'en';
    html.dir = fa ? 'rtl' : 'ltr';
    var r = doc.getElementById(fa ? 'lang-fa' : 'lang-en'); if (r) r.checked = true;
    store('daftar-lang', l);
    glyphs();
  }
  function glyphs() {
    [].forEach.call(doc.querySelectorAll('[data-glyph]'), function (el) { el.textContent = D.glyph(el.getAttribute('data-glyph')); });
  }
  [].forEach.call(doc.querySelectorAll('input[name="lang"]'), function (r) { r.addEventListener('change', function () { setLang(r.value); }); });

  // ---------------------------------------------------------------- the lens
  function setLens(id) { var r = doc.getElementById('lens-' + id); if (r) { r.checked = true; store('daftar-lens', id); } }
  [].forEach.call(doc.querySelectorAll('input[name="lens"]'), function (r) { r.addEventListener('change', function () { store('daftar-lens', r.value); }); });

  setLang(params.get('lang') || store('daftar-lang') || (navigator.language || '').slice(0, 2) === 'fa' && 'fa' || 'en');
  setLens(params.get('lens') || store('daftar-lens') || 'person');

  // ---------------------------------------------------------------- ① the reader saves; the gate answers as it did
  [].forEach.call(doc.querySelectorAll('.sentence-card'), function (card) {
    var taken = card.querySelector('.answer.taken'), again = card.querySelector('.answer.again');
    [].forEach.call(card.querySelectorAll('[data-save]'), function (b) {
      b.addEventListener('click', function () {
        var s = b.getAttribute('data-save');
        card.setAttribute('data-state', s);
        taken.hidden = s !== 'mended';
        again.hidden = s !== 'first';
        (s === 'first' ? card.querySelector('.refusal') : taken).setAttribute('tabindex', '-1');
        (s === 'first' ? card.querySelector('.refusal') : taken).focus({ preventScroll: true });
      });
    });
  });

  // ---------------------------------------------------------------- ② the ladder: where the reader stands
  var rungs = {};
  [].forEach.call(doc.querySelectorAll('.rung'), function (r) { rungs[r.getAttribute('data-line')] = r; });
  var places = [].slice.call(doc.querySelectorAll('.place[data-line]'));
  function here(line) {
    Object.keys(rungs).forEach(function (k) { if (k === line) rungs[k].setAttribute('data-here', ''); else rungs[k].removeAttribute('data-here'); });
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) here(e.target.getAttribute('data-line')); });
    }, { rootMargin: '-40% 0px -55% 0px' });
    places.forEach(function (p) { io.observe(p); });
  }
  var ladder = doc.querySelector('.ladder');
  function climb(step) {                                    // up the ladder is further down the page: it is a body
    var cur = places.findIndex(function (p) { return rungs[p.getAttribute('data-line')].hasAttribute('data-here'); });
    var next = places[Math.max(0, Math.min(places.length - 1, (cur < 0 ? 0 : cur) + step))];
    if (next) { next.scrollIntoView({ block: 'start' }); here(next.getAttribute('data-line')); }
  }
  if (ladder) D.bind(ladder, ['ladder'], { up: function () { climb(1); }, down: function () { climb(-1); },
                                           first: function () { climb(-99); }, last: function () { climb(99); } });

  // ---------------------------------------------------------------- ③ time, one moment at a time
  var moments = [].slice.call(doc.querySelectorAll('.moment')), ticks = [].slice.call(doc.querySelectorAll('[data-goto]'));
  var at = 0;
  function show(i) {
    at = Math.max(0, Math.min(moments.length - 1, i));
    moments.forEach(function (m, j) { if (j === at) m.setAttribute('data-on', ''); else m.removeAttribute('data-on'); });
    ticks.forEach(function (t, j) { if (j === at) t.setAttribute('aria-current', 'step'); else t.removeAttribute('aria-current'); });
  }
  ticks.forEach(function (t) { t.addEventListener('click', function () { show(+t.getAttribute('data-goto')); }); });
  [].forEach.call(doc.querySelectorAll('.step-btn'), function (b) {
    b.addEventListener('click', function () { show(at + (b.getAttribute('data-cmd') === 'later' ? 1 : -1)); });
  });
  var line = doc.querySelector('.moments'), rail = doc.querySelector('.rail');
  var timeKeys = { later: function () { show(at + 1); }, earlier: function () { show(at - 1); },
                   first: function () { show(0); }, last: function () { show(moments.length - 1); } };
  [line, rail].forEach(function (el) { if (el) { D.bind(el, ['time'], timeKeys); D.swipe(el, ['time'], timeKeys); } });
  if (moments.length) show(0);
  glyphs();
})();
