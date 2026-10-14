/* view_timeline.js — the `timeline` archetype: the members of a reading at their moments — a happening's time, a
   clause's due day and each occurrence of its repetition — as the server read them within the drawing's span
   (`view_engraved.py` `timeline`, the occurrences walked by bin/stale.py: never walked here). Three readings of one line,
   chosen by a switch: a WEEK (its days side by side, each a timeline of its hours; its first the day the reader's
   region begins a week on — CLDR's `firstDay`, through Intl, never typed), a MONTH of the reader's calendar, and a LIST. Time runs along the reader's line
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
    /* A DAY'S HOURS, AND WHAT IS KEPT IN VIEW (the operator, 2026-10-14). The day's width is divided among what takes
       hours — an attendance or a session with its time and length that does not say it leaves them free
       (`transparency`, core 2.7) — each its share by its minutes, opaque, earlier at the start of the reader's line, its
       title under the day's label. What is kept in view without taking them — an attendance said transparent, a due
       day, a moment with no length — is laid over them below that, the day's height divided among them. The label's
       title is the day in the reader's calendars beside the one shown. */
    var clock = function (tm) { return Number(tm.slice(0, 2)) * 60 + Number(tm.slice(3, 5)); };
    var takes = function (e) { return Boolean(e.time && e.minutes && e.transparency !== 'transparent'); };
    var EQUIV = ['persian', 'gregory', 'islamic-umalqura'];
    function equivalents(day) {
      var at = new Date(ms(day));
      return EQUIV.filter(function (c) { return c !== cal; }).map(function (c) {
        try {
          return new Intl.DateTimeFormat(w.locale.tagWith(t.lang, {ca: c, nu: ns}), {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC'}).format(at);
        } catch (err) { return ''; }
      }).filter(Boolean).join(' · ');
    }
    function strip(e) {
      var a = clock(e.time), b = Math.min(1440, a + Number(e.minutes));
      var span = w.moment.timeAsText(e.time) + '–' + w.moment.timeAsText(String(Math.floor(b / 60)).padStart(2, '0') + ':' + String(b % 60).padStart(2, '0'));
      return h`<span class="eg-take" data-minutes="${String(e.minutes)}" title="${(e.title || '') + ' · '}${span}">${w.being.show(e.bean, e.title, {action: 'open'})}</span>`;
    }
    function cell(day, gc, gr) {
      var cls = 'eg-day' + (day === data.today ? ' eg-today' : '') + (inSpan(day) ? '' : ' eg-beyond');
      var all = by[day] || [], kept = all.filter(function (e) { return !takes(e); });
      var taken = all.filter(takes).sort(function (x, y) { return clock(x.time) - clock(y.time); });
      var shares = taken.map(function (e) { return String(Math.max(1, Math.round(Number(e.minutes)))) + 'fr'; }).join(' ');
      return h`<div class="${cls}${taken.length ? ' eg-has-hours' : ''}" data-day="${day}"${gc ? h` data-gc="${String(gc)}"` : ''}${gr ? h` data-gr="${String(gr)}"` : ''}${
        inSpan(day) ? '' : h` title="${t.say('timeline-beyond')}"`}>
        ${taken.length ? h`<div class="eg-hours" data-cols="${shares}">${taken.map(strip)}</div>` : ''}
        <div class="eg-day-head" title="${equivalents(day)}"><span class="eg-wd">${dayName.format(new Date(ms(day)))}</span> <span class="eg-dn">${dayNum(day)}</span></div>
        <ol class="eg-events eg-kept">${kept.map(ev)}</ol></div>`;
    }
    /* THE WEEK AS DAY TIMELINES (the operator, 2026-10-14). Each day is a column of its hours, top to bottom, the hours
       the week's own — from the hour its earliest begins to the hour its latest ends, 08:00 to 20:00 where nothing has a
       time — on a scale at the start of the reader's line. What takes hours is a block at them, opaque; what overlaps
       stands side by side, each cluster of overlaps sharing the column. What is kept in view at a time — an attendance
       said transparent — is an outlined block in a narrow lane at the column's end, never over what takes the hours; what
       has no time — a due day, a whole day — is listed under the day's label. Today's column carries the hour it is now.
       A screen too narrow for seven columns shows one day, and moves a day at a time. Every place is a grid line set
       through safe.js (`data-gr`, `data-gc`, `data-rows`, `data-cols`), never a style a page writes. */
    var SLOT = 5;                                  // the minutes a row of a day's column stands for: 12 rows an hour
    var gcd = function (a, b) { return b ? gcd(b, a % b) : a; };
    var hhmm = function (m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
    function span(e) { var a = clock(e.time); return [a, Math.min(1440, a + Math.max(SLOT, Number(e.minutes) || 0))]; }
    function timed(e) { return Boolean(e.time && e.minutes); }
    function hoursOf(days) {
      var lo = 1440, hi = 0;
      days.forEach(function (d) { (by[d] || []).filter(timed).forEach(function (e) { var x = span(e); lo = Math.min(lo, x[0]); hi = Math.max(hi, x[1]); }); });
      if (lo >= hi) return [480, 1200];
      return [Math.floor(lo / 60) * 60, Math.min(1440, Math.ceil(hi / 60) * 60)];
    }
    // overlaps side by side: each cluster of what overlaps shares the column in as many lanes as it needs at once
    function lanes(items) {
      items.sort(function (x, y) { return x.a - y.a || y.b - x.b; });
      var cluster = [], until = -1, ends = [];
      function close() { cluster.forEach(function (x) { x.k = ends.length; }); cluster = []; ends = []; }
      items.forEach(function (x) {
        if (x.a >= until) { close(); until = -1; }
        var l = ends.findIndex(function (e) { return e <= x.a; });
        if (l < 0) { l = ends.length; ends.push(x.b); } else ends[l] = x.b;
        x.lane = l; cluster.push(x); until = Math.max(until, x.b);
      });
      close();
      return items;
    }
    function dayLine(day, hours) {
      var lo = hours[0], rows = (hours[1] - hours[0]) / SLOT;
      var all = by[day] || [];
      var takers = lanes(all.filter(function (e) { return timed(e) && e.transparency !== 'transparent'; })
        .map(function (e) { var x = span(e); return {e: e, a: x[0], b: x[1]}; }));
      var keeps = all.filter(function (e) { return timed(e) && e.transparency === 'transparent'; })
        .map(function (e) { var x = span(e); return {e: e, a: x[0], b: x[1]}; });
      var L = takers.reduce(function (acc, x) { return acc * x.k / gcd(acc, x.k); }, 1);
      var cols = 'repeat(' + L + ', minmax(0, 1fr))' + (keeps.length ? ' 8px' : '');
      var row = function (m) { return Math.max(1, Math.min(rows + 1, Math.round((m - lo) / SLOT) + 1)); };
      function block(x, gc, cls) {
        var when = w.moment.timeAsText(x.e.time) + '–' + w.moment.timeAsText(hhmm(x.b));
        var r0 = row(x.a), r1 = Math.max(r0 + 1, row(x.b));
        return h`<div class="eg-block${cls}" data-gr="${r0 + ' / ' + r1}" data-gc="${gc}" data-minutes="${String(x.e.minutes)}" title="${(x.e.title || '') + ' · ' + when}">${w.being.show(x.e.bean, x.e.title, {action: 'open'})} <span class="eg-when">${w.moment.showTime(x.e.time)}–${w.moment.showTime(hhmm(x.b))}</span></div>`;
      }
      var now = '';
      if (day === data.today) {
        var d = new Date(), m = d.getHours() * 60 + d.getMinutes();
        if (m >= lo && m < hours[1]) now = h`<div class="eg-now" data-gr="${row(m) + ' / ' + (row(m) + 1)}" data-gc="1 / -1" title="${w.moment.timeAsText(hhmm(m))}"></div>`;
      }
      return h`<div class="eg-dayline" data-rows="${'repeat(' + rows + ', 5px)'}" data-cols="${cols}">${takers.map(function (x) {
        var n = L / x.k;
        return block(x, (x.lane * n + 1) + ' / ' + ((x.lane + 1) * n + 1), '');
      })}${keeps.map(function (x) { return block(x, String(L + 1), ' eg-keep'); })}${now}</div>`;
    }
    function week() {
      var narrow = el.clientWidth > 0 && el.clientWidth < 560;
      var start = narrow ? state.focus : add(state.focus, -((weekday(state.focus) - first + 7) % 7)), days = [];
      for (var i = 0; i < (narrow ? 1 : 7); i++) days.push(add(start, i));
      var hours = hoursOf(days), n = days.length;
      var marks = [];
      for (var m = hours[0]; m < hours[1]; m += 60) marks.push(m);
      var gutter = h`<div class="eg-wt-gutter" data-gr="3" data-gc="1" data-rows="${'repeat(' + ((hours[1] - hours[0]) / SLOT) + ', 5px)'}">${marks.map(function (m) {
        var r = (m - hours[0]) / SLOT + 1;
        return h`<span class="eg-wt-hour" data-gr="${r + ' / ' + (r + 12)}">${w.moment.showTime(hhmm(m))}</span>`;
      })}</div>`;
      var cols = days.map(function (d, i) {
        var gc = String(fwd ? i + 2 : n + 1 - i);
        var cls = (d === data.today ? ' eg-today' : '') + (inSpan(d) ? '' : ' eg-beyond');
        var kept = (by[d] || []).filter(function (e) { return !timed(e); });
        return h`<div class="eg-wt-head${cls}" data-day="${d}" data-gr="1" data-gc="${gc}" title="${equivalents(d)}"><span class="eg-wd">${dayName.format(new Date(ms(d)))}</span> <span class="eg-dn">${dayNum(d)}</span></div>
          <ol class="eg-events eg-kept eg-wt-strip${cls}" data-day="${d}" data-gr="2" data-gc="${gc}">${kept.map(ev)}</ol>
          <div class="eg-wt-day${cls}" data-day="${d}" data-gr="3" data-gc="${gc}"${inSpan(d) ? '' : h` title="${t.say('timeline-beyond')}"`}>${dayLine(d, hours)}</div>`;
      });
      return {label: n === 1 ? w.moment.show(days[0], {style: 'weekday'}) : h`${w.moment.show(days[0], {style: 'long'})} – ${w.moment.show(days[n - 1], {style: 'long'})}`,
              body: h`<div class="eg-weektime" data-hours="${hours.join('-')}" data-cols="${'auto repeat(' + n + ', minmax(0, 1fr))'}">${gutter}${cols}</div>`,
              step: n};
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
