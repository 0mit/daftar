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
    function one(x) {
      var about = x.opens ? w.being.show(x.opens, x.title || x.opens, {action: 'open'}) : w.name.show(x.about);
      var when = x.due ? h` · ${w.moment.show(x.due, {style: 'long', relative: true})}` : x.since ? h` · ${w.moment.show(String(x.since), {style: 'long'})}` : '';
      return h`<li class="eg-lead eg-${x.kind}${x.overdue || (x.days != null && x.days < 0) ? ' eg-late' : ''}" data-kind="${x.kind}" data-about="${x.about}">
        <div class="eg-lead-about">${about}${when}${x.overdue ? h` · <span class="eg-late-word">${t.say('queue-overdue')}</span>` : ''}</div>
        <div class="eg-lead-why">${w.text.show(x.why)}</div></li>`;
    }
    t.mount(el, h`${(data.groups || []).map(function (g) {
      return h`<section class="eg-group" data-group="${g}"><h4>${t.say('queue-' + g)}</h4><ol class="eg-leads">${
        leads.filter(function (x) { return x.kind === g; }).map(one)}</ol></section>`;
    })}`);
  };
})(typeof window !== 'undefined' ? window : this);
