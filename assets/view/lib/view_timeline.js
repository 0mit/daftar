/* view_timeline.js — the `timeline` archetype: the members of a reading at their moments — a happening's time, a
   clause's due day and each occurrence of its repetition — as the server read them within the drawing's span
   (`view_engraved.py` `timeline`, the occurrences walked by bin/stale.py: never walked here). Three readings of one line,
   chosen by a switch: a WEEK (a grid of days, its first the day the reader's region begins a week on — CLDR's
   `firstDay`, through Intl, never typed), a MONTH of the reader's calendar, and a LIST. Time runs along the reader's line
   (`axes: { inline: time }`): earlier at its start, in either script, as widgets/direction.js says; the keys and the
   swipe that move it are named by meaning, `earlier` and `later`. A classic script, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};
  var DAY = 86400000;
  var iso = function (ms) { return new Date(ms).toISOString().slice(0, 10); };
  var ms = function (day) { var p = day.split('-').map(Number); return Date.UTC(p[0], p[1] - 1, p[2], 12); };
  var add = function (day, n) { return iso(ms(day) + n * DAY); };
  var weekday = function (day) { return new Date(ms(day)).getUTCDay(); };   // 0 Sunday … 6 Saturday, as Date counts

  /* the day the reader's region begins a week on (CLDR, through Intl.Locale's week info) as Date counts days; where
     the runtime holds no week info, ISO 8601's Monday, the standard the law writes its days in */
  function firstDay(lang) {
    try {
      var L = new Intl.Locale(lang).maximize();
      var info = typeof L.getWeekInfo === 'function' ? L.getWeekInfo() : L.weekInfo;
      if (info && info.firstDay) return info.firstDay % 7;
    } catch (e) { /* a tag the runtime does not read: the standard's week */ }
    return 1;
  }

  A.timeline = function (el, data, t, view) {
    var h = t.h, w = t.w, layouts = (data.layouts && data.layouts.length) ? data.layouts : ['week', 'month', 'list'];
    var axes = (view && view.engraved && view.engraved.axes) || {inline: 'time'};
    var order = axes.inline || 'time', fwd = t.forward(order);
    var cal = w.locale.calendarOf({}), first = firstDay(t.lang), ns = w.locale.digitsOf({});
    var by = {};
    (data.events || []).forEach(function (e) { (by[e.day] = by[e.day] || []).push(e); });
    var state = {layout: layouts[0], focus: data.today};
    var inSpan = function (day) { return day >= data.from && day <= data.to; };
    var dayName = new Intl.DateTimeFormat(t.lang, {weekday: 'short', timeZone: 'UTC'});
    var dayNum = function (day) { return w.locale.inDigits(String(w.moment.toCalendar(day, cal).d), ns); };

    function ev(e) {
      var what = e.kind === 'due'
        ? h`${e.time ? h`${w.moment.showTime(e.time)} ` : ''}${e.what ? w.text.show(e.what) : ''}${e.amount ? h` · ${t.w.money.show(e.amount.count, e.amount.unit)}` : ''}${
            e.times && e.times !== '1' ? h` · <span class="eg-nth">${t.say('timeline-nth', {i: w.locale.inDigits(String(e.index), ns), n: w.locale.inDigits(String(e.times), ns)})}</span>` : ''}`
        : (e.time ? w.moment.showTime(e.time) : '');
      return h`<li class="eg-event eg-${e.kind}" data-day="${e.day}">${w.being.show(e.bean, e.title, {action: 'open'})} ${what}</li>`;
    }
    function cell(day, gc, gr) {
      var cls = 'eg-day' + (day === data.today ? ' eg-today' : '') + (inSpan(day) ? '' : ' eg-beyond');
      return h`<div class="${cls}" data-day="${day}"${gc ? h` data-gc="${String(gc)}"` : ''}${gr ? h` data-gr="${String(gr)}"` : ''}${
        inSpan(day) ? '' : h` title="${t.say('timeline-beyond')}"`}>
        <div class="eg-day-head"><span class="eg-wd">${dayName.format(new Date(ms(day)))}</span> <span class="eg-dn">${dayNum(day)}</span></div>
        <ol class="eg-events">${(by[day] || []).map(ev)}</ol></div>`;
    }
    function week() {
      var start = add(state.focus, -((weekday(state.focus) - first + 7) % 7)), days = [];
      for (var i = 0; i < 7; i++) days.push(add(start, i));
      return {label: h`${w.moment.show(days[0], {style: 'long'})} – ${w.moment.show(days[6], {style: 'long'})}`,
              body: h`<div class="eg-grid eg-week">${days.map(function (d, i) { return cell(d, fwd ? i + 1 : 7 - i, 1); })}</div>`,
              step: 7};
    }
    function month() {
      var p = w.moment.toCalendar(state.focus, cal), start = w.moment.fromCalendar(cal, p.y, p.m, 1) || state.focus;
      var days = [], d = start;
      while (w.moment.toCalendar(d, cal).m === p.m && days.length < 40) { days.push(d); d = add(d, 1); }
      var lead = (weekday(start) - first + 7) % 7;
      var label = new Intl.DateTimeFormat(w.locale.tagWith(t.lang, {ca: cal, nu: w.locale.digitsOf({})}), {month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(ms(start)));
      return {label: label,
              body: h`<div class="eg-grid eg-month" data-rows="${'repeat(' + Math.ceil((lead + days.length) / 7) + ', auto)'}">${days.map(function (dd, i) {
                var k = lead + i, c = k % 7;
                return cell(dd, fwd ? c + 1 : 7 - c, Math.floor(k / 7) + 1);
              })}</div>`,
              step: 'month', days: days};
    }
    function list() {
      var days = Object.keys(by).sort();
      return {label: h`${w.moment.show(data.from, {style: 'long'})} – ${w.moment.show(data.to, {style: 'long'})}`,
              body: days.length ? h`<ol class="eg-list">${days.map(function (d) {
                return h`<li class="eg-list-day${d === data.today ? ' eg-today' : ''}" data-day="${d}"><div class="eg-list-when">${
                  w.moment.show(d, {style: 'weekday'})}</div><ol class="eg-events">${by[d].map(ev)}</ol></li>`;
              })}</ol>` : h`<p class="eg-empty">${t.say('timeline-empty')}</p>`, step: 0};
    }
    function move(dir) {
      var v = state.layout === 'week' ? week() : state.layout === 'month' ? month() : null;
      if (!v) return;
      var next = v.step === 'month'
        ? (dir > 0 ? add(v.days[v.days.length - 1], 1) : add(v.days[0], -1))
        : add(state.focus, dir * v.step);
      if (dir > 0 ? next > data.to : next < data.from) return;
      state.focus = next;
      draw();
    }
    function draw() {
      var v = state.layout === 'week' ? week() : state.layout === 'month' ? month() : list();
      var earlier = h`<button type="button" class="eg-btn" data-move="-1" aria-label="earlier">${t.D ? t.D.glyph('earlier') : ''}</button>`;
      var later = h`<button type="button" class="eg-btn" data-move="1" aria-label="later">${t.D ? t.D.glyph('later') : ''}</button>`;
      t.mount(el, h`<div class="eg-bar"><span class="eg-layouts">${layouts.map(function (l) {
          return h`<button type="button" class="eg-btn${l === state.layout ? ' eg-on' : ''}" data-layout="${l}">${t.say('timeline-' + l)}</button>`;
        })}</span>${v.step ? h`<span class="eg-nav">${fwd ? [earlier, later] : [later, earlier]}</span>` : ''}<span class="eg-label">${v.label}</span></div>
        ${v.body}${(data.notes || []).length ? h`<ul class="eg-notes">${data.notes.map(function (n) { return h`<li>${w.text.show(n)}</li>`; })}</ul>` : ''}`);
      el.querySelectorAll('[data-layout]').forEach(function (b) {
        b.addEventListener('click', function () { state.layout = b.getAttribute('data-layout'); draw(); });
      });
      el.querySelectorAll('[data-move]').forEach(function (b) {
        b.addEventListener('click', function () { move(+b.getAttribute('data-move')); });
      });
      t.wire(el);
    }
    if (t.D) {
      el.setAttribute('tabindex', '0');
      t.D.bind(el, [order], {earlier: function () { move(-1); }, later: function () { move(1); }});
      t.D.swipe(el, [order], {earlier: function () { move(-1); }, later: function () { move(1); }});
    }
    draw();
  };
})(typeof window !== 'undefined' ? window : this);
