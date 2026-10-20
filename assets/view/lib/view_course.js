/* view_course.js — the `course` archetype: the one way a course is drawn (core 2.22), wherever a page draws one — a
   drawing of a being's courses, a table's `stands` column, the courses beneath a being on its sheet, a run on a host's
   page. A course is the server's reading (`view_engraved.py` `stands_of`, bin/seq.py `courses`): a course written, a
   clause's occurrence or a standing need, each with its steps in their order. Drawn as one line: what it is, its steps
   along the reader's line with the one it stands at marked (`aria-current="step"`) and the ways out and pauses apart
   after them, since when, who acts there, overdue where its step's usual time has passed, and its needs — met or not,
   blocking or not. The steps follow the reader's script (`axes: { inline: walk }`): a right-to-left reader reads the
   first step at the right. A classic script beside view_engraved.js, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};

  // ONE COURSE IN ONE LINE: what every page that shows a course draws, and nothing else draws one
  function line(t, c, opts) {
    var h = t.h, w = t.w;
    opts = opts || {};
    if (!c) return h`<span class="w-none">—</span>`;
    var steps = c.steps || [];
    var on = steps.filter(function (s) { return !s.exit && !s.resumes; });
    var off = steps.filter(function (s) { return s.exit || s.resumes; });
    function pill(s) {
      var here = s.id === c.step;
      return h`<li class="eg-step${here ? ' eg-here' : ''}${s.final ? ' eg-final' : ''}${s.exit ? ' eg-exit' : ''}${s.resumes ? ' eg-pause' : ''}"${here ? h` aria-current="step"` : ''} title="${s.as || s.id}">${w.text.show(s.id)}</li>`;
    }
    var what = c.source === 'clause' ? t.say('course-clause', {what: c.clause || c.id})
      : c.source === 'need' ? t.say('course-need', {what: c.id})
      : (c.walk_title || c.walk || c.id);
    var when = c.due && c.step === 'ahead' ? h`<span class="eg-course-when">${t.say('course-due', {})} ${w.moment.show(String(c.due), {style: 'long', relative: true})}</span>`
      : c.at && w.moment.parse(String(c.at)) ? h`<span class="eg-course-when">${w.moment.show(String(c.at), {style: 'long', relative: true})}</span>` : '';
    var who = c.party ? t.say('course-who', {who: c.party}) : c.by ? t.say('course-who', {who: c.by}) : '';
    var needs = c.needs || [], open = needs.filter(function (n) { return !n.met; });
    var blocked = open.filter(function (n) { return n.blocking; }).length;
    var needWords = needs.length ? t.say('course-needs', {met: w.locale.inDigits(String(needs.length - open.length), w.locale.digitsOf({})),
      all: w.locale.inDigits(String(needs.length), w.locale.digitsOf({})), blocking: w.locale.inDigits(String(blocked), w.locale.digitsOf({}))}) : '';
    return h`<div class="eg-course eg-course-${c.source || 'course'}${c.overdue ? ' eg-late' : ''}${c.final ? ' eg-done' : ''}" data-course="${c.id}" data-step="${c.step || ''}">
      ${opts.bare ? '' : h`<span class="eg-course-what">${w.text.show(what)}</span>`}
      <ol class="eg-steps" aria-label="${t.say('course-steps')}">${on.map(pill)}</ol>${off.length ? h`<ol class="eg-steps eg-steps-off">${off.map(pill)}</ol>` : ''}
      ${c.step ? '' : h`<span class="eg-course-none">${t.say('course-not-begun')}</span>`}
      ${when}${who ? h` <span class="eg-course-who">${w.text.show(who)}</span>` : ''}${c.overdue ? h` <span class="eg-late-word">${t.say('queue-overdue')}</span>` : ''}
      ${needWords ? h` <span class="eg-course-needs">${w.text.show(needWords)}</span>` : ''}${c.words ? h` <span class="eg-course-words">${w.text.show(String(c.words))}</span>` : ''}</div>`;
  }

  root.daftarCourse = {line: line};

  A.course = function (el, data, t) {
    var h = t.h, cs = (data && data.courses) || [];
    if (!cs.length) { t.mount(el, h`<p class="eg-empty">${t.say('course-empty')}</p>`); return; }
    t.mount(el, h`<ol class="eg-courses">${cs.map(function (c) { return h`<li>${line(t, c)}</li>`; })}</ol>`);
    t.wire(el);
  };
})(typeof window !== 'undefined' ? window : this);
