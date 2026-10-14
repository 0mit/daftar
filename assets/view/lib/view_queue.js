/* view_queue.js — the `queue` archetype: what waits for the reader, as bin/leads.py reads it (the server's reading,
   `view_engraved.py` `queue`), grouped by what each waits on — a decision, a case at a step, an obligation falling due, a
   failure, an open session — the most urgent first; each opens the sheet of the being it is about. Its order runs down
   the page (`axes: { block: ordinal }`). A classic script beside view_engraved.js, built only through safe.js. */
(function (root) {
  'use strict';
  var A = root.daftarArchetypes = root.daftarArchetypes || {};

  A.queue = function (el, data, t) {
    var h = t.h, w = t.w, leads = data.leads || [];
    if (!leads.length) { t.mount(el, h`<p class="eg-empty">${t.say('queue-empty')}</p>`); return; }
    // EACH LEAD SAID IN THE READER'S LANGUAGE, from what it is and what it is about (the widgets' sentences): a case by
    // its walk's own words for its step, a clause by its words and its day in the reader's calendar; bin/leads.py's
    // English `why` stays on the line as its title, for a lead of a kind no sentence names yet
    function said(x) {
      if (x.kind === 'case') return t.say('lead-case', {step: x.step_says || x.step});
      if (x.kind === 'obligation' && x.side === 'owed') {    // what another owes the reader, falling due
        return t.say(x.days != null && x.days < 0 ? 'lead-owed-past' : 'lead-owed', {what: x.what || t.say('lead-clause'),
          by: (x.owed_by_titles || []).join(t.say('sheet-tags-sep')) || t.say('flows-someone')});
      }
      if (x.kind === 'obligation') return t.say(x.days != null && x.days < 0 ? 'lead-due-past' : 'lead-due', {what: x.what || t.say('lead-clause')});
      if (x.kind === 'decision') return t.say('lead-decision', {cls: x['class'] || '—'});
      if (x.kind === 'health') return t.say('lead-health', {as: x.fails_as || ''});
      if (x.kind === 'session') return t.say('lead-session', {ahead: w.locale.inDigits(String(x.ahead || ''), w.locale.digitsOf({}))});
      return x.why;
    }
    function one(x) {
      var about = x.opens ? w.being.show(x.opens, x.title || x.opens, {action: 'open'}) : w.name.show(x.about);
      var day = x.day || x.due, when = day && w.moment.parse(String(day)) ? h` · ${w.moment.show(String(day), {style: 'long', relative: true})}`
        : x.since ? h` · ${w.moment.show(String(x.since), {style: 'long'})}` : '';
      return h`<li class="eg-lead eg-${x.kind}${x.overdue || (x.days != null && x.days < 0) ? ' eg-late' : ''}" data-kind="${x.kind}" data-about="${x.about}" title="${x.why || ''}">
        <div class="eg-lead-about">${about}${when}${x.overdue ? h` · <span class="eg-late-word">${t.say('queue-overdue')}</span>` : ''}</div>
        <div class="eg-lead-why">${w.text.show(said(x))}</div></li>`;
    }
    t.mount(el, h`${(data.groups || []).map(function (g) {
      return h`<section class="eg-group" data-group="${g}"><h4>${t.say('queue-' + g)}</h4><ol class="eg-leads">${
        leads.filter(function (x) { return x.kind === g; }).map(one)}</ol></section>`;
    })}`);
  };
})(typeof window !== 'undefined' ? window : this);
