// The landing page: where a notification, a link or a platform's own lead brings a person to decide what only a
// person may (MODEL.md, Contract of Parts). Its addresses mean what they say:
//
//   /go/<garden>                          what waits for you in that garden
//   /go/<garden>/pending/<slug>           a decision an agent parked in log/pending.md
//   /go/<garden>/proposal/<PROPOSAL-…>    a proposal from another garden that no standing consent covers, or one set aside
//   /go/<garden>/sync                     the garden and its hub parted ways
//   /go/<garden>/error/<E-XXXX-XXXX>      a guided error, whole
//   /go/<garden>/case/<bean>              a case
//
// and daftar://go/… is the same address handed to `daftard open` by the system. THE ADDRESS ONLY NAMES THE CASE:
// everything shown is read from the garden, so a link cannot put words in the garden's mouth, and the decision is made
// here, on this page, never in the notification (which carries no key and no decision).
import { h, mount } from '/toolbox/safe.js';
import * as api from '/toolbox/api.js';
import * as text from '/toolbox/text.js';
import * as moment from '/toolbox/moment.js';
import { openDialog } from '/toolbox/dialog.js';
import { form, collect, showErrors } from '/toolbox/form.js';
import { table } from '/toolbox/table.js';
import { guidedError } from '/toolbox/guided.js';
import { badge, fact } from '../common.js';
import cases, { openCase } from './cases.js';
import { T } from '/toolbox/say.js';

const KINDS_ = () => ({pending: T('تصمیم پارک‌شده', 'a decision parked'), proposal: T('پیشنهاد دفتری دیگر', 'another garden\'s proposal'),
  sync: T('همگام‌سازی', 'sync'), error: T('خطا', 'an error'), case: T('پرونده', 'a case'), action: T('اقدامی منتظر تأیید', 'an action waiting to be ratified'),
  session: T('نشست باز', 'an open session'), form: T('پاسخ‌های یک فرم', 'a form\'s answers'), health: T('خرابی خوانده‌شده', 'a fault read'),
  obligation: T('تعهدی که موعدش می‌رسد', 'an obligation coming due'), passkey: T('کلید ورود تازه', 'a new passkey')});
const KINDS = new Proxy({}, {get: (_t, k) => KINDS_()[k]});
// what each class of the Contract of Parts asks a person to decide (MODEL.md)
const CLASSES_ = () => ({
  C: T('تغییر یا حذف گفته‌ای که شخصی گفته یا ایمنی به آن تکیه دارد', 'changing or taking out what a person said, or what safety rests on'),
  D: T('آنچه شخصی گفته است', 'what a person said'),
  E: T('یک گزارهٔ ایمنی: حساسیت، ممنوعیت یا خرابی در جریان', 'a statement of safety: a sensitivity, a prohibition, a fault under way'),
  F: T('نامی که هویتی را می‌سازد، یا گرفتن آن از دفتری دیگر', 'a name that makes an identity, or taking one from another garden'),
  G: T('قانون دفتر: هسته، واژگان، یا مانیفست', 'the garden\'s law: the core, its words, or its manifest'),
  J: T('حل یک تعارض ادغام یا هویتی نامطمئن', 'settling a conflicting merge, or an uncertain identity'),
});
const CLASSES = new Proxy({}, {get: (_t, k) => CLASSES_()[k]});
const CLASS = c => T('رده ', 'class ') + c;
const SHOWN = new Set(['class', 'neighborhood', 'neighbourhood', 'proposal', 'status', 'acked_by']);
const state = {pending: null, proposal: null, form: null, passkey: null, checked: false};
const day = d => (d ? moment.show(d) : '');
const classOf = c => String(c || '').trim().charAt(0).toUpperCase();
const prose = v => text.show(v, {lines: true, block: true});

export async function list(ctx) {
  const {leads} = await api.get('/api/leads');
  const about = l => l.kind === 'pending' ? text.show(l.title)
    : l.kind === 'proposal' ? h`${T('از', 'from')} ${text.show(l.from)}${l.under ? h` · ${T('زیر توافق', 'under')} ${text.show(l.under)}` : ''}${l.where === 'held' ? h` ${badge(T('کنار گذاشته شد', 'set aside'), 'late')}` : ''}`
    : l.kind === 'sync' ? T('دفتر و مرکز از هم جدا شده‌اند', 'the garden and its hub have parted')
    : l.title ? text.show(l.title) : '';
  return h`<section class="panel"><div class="panel-head"><div><h2>${T('منتظر تصمیم شما', 'Waiting for your decision')}</h2>
    <p>${T('هر مورد را باز کنید، بخوانید و همان‌جا تصمیم بگیرید. تا تصمیم نگیرید چیزی تغییر نمی‌کند.', 'Open each one, read it and decide there. Nothing changes until you decide.')}</p></div></div>
    ${table({columns: [
      {title: T('نوع', 'Kind'), cell: l => h`${badge(KINDS[l.kind] || l.kind)}${l.class ? h` ${badge(CLASS(classOf(l.class)))}` : ''}`},
      {title: T('موضوع', 'About'), cell: about},
      {title: T('از', 'Since'), cell: l => l.since ? day(l.since) : ''},
      {title: '', cell: l => h`<button class="secondary" data-action="go-lead" data-kind="${l.kind}" data-id="${l.id || ''}">${T('باز کردن', 'Open')}</button>`},
    ], rows: leads, empty: T('چیزی منتظر تصمیم شما نیست.', 'Nothing waits for your decision.')})}</section>`;
}

// AN ACTION'S PLAN, to ratify or decline (design §9): what it would change, exactly as the engine captured it, and who
// acts — the person sitting here, whose act is their own signed commit. Nothing changes until they ratify; a plan that
// changed since it was shown is shown again.
async function actionView(ctx, id) {
  const a = await api.get('/api/action?id=' + encodeURIComponent(id));
  return h`<section class="panel lead">
    <div class="panel-head"><div><h2>${KINDS.action}: ${text.show(a.bean)} · ${text.show(a.course)}</h2>
      <p>${text.show(a.stands)}</p></div></div>
    <h3>${T('برنامه — آنچه تغییر خواهد کرد', 'The plan — what would change')}</h3>
    ${a.plan ? text.show(a.plan, {lines: true, block: true}) : h`<p class="w-none">${T('برنامه‌ای ثبت نشده است.', 'No plan was recorded.')}</p>`}
    ${a.captured ? h`<p><small><bdi dir="ltr">${a.captured}</bdi></small></p>` : ''}
    <div class="dialog-actions"><button class="primary" data-action="act" data-id="${id}" data-do="ratify">${T('تأیید و اجرا', 'Ratify and run')}</button>
      <button class="secondary" data-action="act" data-id="${id}" data-do="decline">${T('رد کردن', 'Decline')}</button></div></section>`;
}

// A COURSE'S LEAD (daftar 2.22, the archetype `course`): a being of a garden of the core waits on its way — a case at
// a step, a clause falling due, a standing need crossed. Its page is the being's courses, each drawn as the archetype
// draws one wherever it is drawn: its walk's steps in their order, the one it stands at marked, the ways out and pauses
// apart, since when, who acts there, overdue past its usual time, and its needs met or not, blocking or not. An agency's
// case opens its client's case instead (cases.js).
export function courseLine(c) {
  const steps = c.steps || [], on = steps.filter(s => !s.exit && !s.resumes), off = steps.filter(s => s.exit || s.resumes);
  const pill = s => h`<li class="step${s.id === c.step ? ' here' : ''}${s.exit ? ' exit' : ''}${s.resumes ? ' pause' : ''}"${s.id === c.step ? h` aria-current="step"` : ''} title="${s.as || s.id}">${text.show(s.id)}</li>`;
  const what = c.source === 'clause' ? T('بند ' + (c.clause || c.id), 'clause ' + (c.clause || c.id))
    : c.source === 'need' ? T('نیاز ' + c.id, 'need ' + c.id) : (c.walk_title || c.walk || c.id);
  const needs = c.needs || [], open = needs.filter(n => !n.met), blocking = open.filter(n => n.blocking).length;
  return h`<div class="course-line${c.overdue ? ' late' : ''}${c.final ? ' done' : ''}" data-course="${c.id}" data-step="${c.step || ''}">
    <b>${text.show(String(what))}</b>
    <ol class="steps">${on.map(pill)}</ol>${off.length ? h`<ol class="steps off">${off.map(pill)}</ol>` : ''}
    ${c.step ? '' : h`<small class="muted">${T('آغاز نشده', 'not begun')}</small>`}
    ${c.at ? h`<small>${moment.show(String(c.at))}</small>` : ''}
    ${c.party || c.by ? h`<small>${T('با ', 'with ')}${text.show(String(c.party || c.by))}</small>` : ''}
    ${c.overdue ? badge(T('از زمان معمولش گذشته', 'past its usual time'), 'late') : ''}
    ${needs.length ? h`<small>${T(`${needs.length - open.length} از ${needs.length} نیاز برآورده، ${blocking} بازدارنده`, `${needs.length - open.length} of ${needs.length} needs met, ${blocking} blocking`)}</small>` : ''}
    ${c.words ? h`<small class="muted">${text.show(String(c.words))}</small>` : ''}</div>`;
}

async function courseView(ctx, id) {
  const b = await api.get('/api/courses?id=' + encodeURIComponent(id));
  const cs = b.courses || [];
  return h`<section class="panel lead"><div class="panel-head"><div><h2>${text.show(b.title || id)}</h2>
    ${b.summary ? h`<p>${text.show(b.summary)}</p>` : ''}</div></div>
    ${b.courses === null ? h`<p class="w-none">${T('نسخهٔ این دفتر مسیرها را نمی‌خواند.', 'This garden\'s release reads no courses.')}</p>`
      : cs.length ? h`<ol class="courses">${cs.map(c => h`<li>${courseLine(c)}</li>`)}</ol>`
      : h`<p class="w-none">${T('این در هیچ مسیری نیست.', 'It is on no way anywhere.')}</p>`}
    <div class="dialog-actions"><button class="text-button" data-action="go-lead">${T('بازگشت', 'Back')}</button></div></section>`;
}

const agencyCase = (ctx, id) => (ctx.data?.cases || []).some(c => c.id === id);

// A NEED NOT MET (core 3.7: what waits is a need on the bean it concerns) is met here by the gardener, as the law
// writes it — their `meet` of it, known by their `say` — or waits; words without meeting it are written in its bean.
const v = x => String(x || '').trim() !== '';

function needView(p) {
  const f = p.fields || {}, letter = classOf(f.class);
  const others = Object.entries(f).filter(([k]) => !SHOWN.has(k) && v(f[k]));
  return h`<section class="panel lead">
    <p class="eyebrow">${T('نیازی که منتظر است', 'a need waiting')}${letter ? h` · ${badge(CLASS(letter))} ${CLASSES[letter] || ''}` : ''}</p>
    <h2>${text.show(p.what)}</h2>
    <p class="muted">${T('در پروندهٔ', 'On')} ${text.show(p.aboutTitle)} · ${T('نشانی', 'address')} <code dir="ltr">${p.about}#${p.need}</code></p>
    <div class="detail-section"><h3>${T('آنچه برای تصمیم باید دید', 'What to see before deciding')}</h3>${prose(f.neighbourhood || '—')}</div>
    ${others.map(([k, x]) => h`<div class="detail-section"><h3><bdi dir="ltr">${k}</bdi></h3>${prose(x)}</div>`)}
    <details class="detail-section"><summary>${T('متن کامل در پرونده', 'The whole text in its bean')}</summary><pre dir="auto">${p.text}</pre></details>
    ${p.mayMeet ? h`<div class="actions"><button class="primary" data-action="lead-decide" data-decision="acked">${T('برآوردن نیاز', 'Meet the need')}</button>
      <button class="text-button" data-action="go-lead">${T('بعداً', 'Later')}</button></div>
      <p class="muted">${T('برآوردن یعنی', 'Meeting it means')} ${text.show(p.gardenerTitle)} ${T('این نیاز را همان‌گونه که نوشته شده برآورده می‌کند و در پرونده ثبت می‌شود. پاسخی بی‌آنکه برآورده شود، در همان پرونده نوشته می‌شود.', 'meets this need as written, and it is recorded in its bean. Words without meeting it are written in that bean.')}</p>`
    : h`<p class="notice">${f.blocked_by ? h`${T('این نیاز نخست منتظر', 'This need waits first on')} <bdi dir="ltr">${f.blocked_by}</bdi> ${T('است.', '.')}` : h`${T('این نیاز منتظر', 'This need waits for')} ${text.show(f.for || '—')} ${T('است.', '.')}`}</p>`}
  </section>`;
}

function needsOf(p) {
  return h`<section class="panel lead"><p class="eyebrow">${T('نیازهایی که منتظرند', 'needs waiting')}</p><h2>${text.show(p.aboutTitle)}</h2>
    ${table({columns: [
      {title: T('رده', 'Class'), cell: n => n.class ? badge(CLASS(classOf(n.class))) : ''},
      {title: T('موضوع', 'About'), cell: n => text.show(n.title)},
      {title: '', cell: n => h`<button class="secondary" data-action="go-lead" data-kind="pending" data-id="${n.id}">${T('باز کردن', 'Open')}</button>`},
    ], rows: p.needs, empty: T('چیزی منتظر نیست.', 'Nothing waits.')})}</section>`;
}

async function pendingView(ctx, id) {
  const p = state.pending = await api.get('/api/pending?id=' + encodeURIComponent(id));
  if (p.status === 'list') return needsOf(p);
  if (p.need) return needView(p);
  const f = p.fields || {}, letter = classOf(f.class), decided = p.status !== 'proposed';
  const others = Object.entries(f).filter(([k]) => !SHOWN.has(k));
  return h`<section class="panel lead">
    <p class="eyebrow">${KINDS.pending}${letter ? h` · ${badge(CLASS(letter))} ${CLASSES[letter] || ''}` : ''}</p>
    <h2>${text.show(p.what)}</h2>
    <p class="muted">${T('پیشنهاد', 'Proposed by')} ${text.show(p.by || T('نامعلوم', 'unknown'))}${p.since ? h` · ${day(p.since)}` : ''} · ${T('نشانی', 'address')} <code dir="ltr">${p.slug}</code></p>
    ${decided ? h`<p class="notice">${T('تصمیم این مورد گرفته شده است', 'This was decided')} (${text.show(p.status)})${f.acked_by ? h`: ${text.show(f.acked_by)}` : ''}.</p>` : ''}
    ${p.twice ? h`<p class="notice error">${T('این نشانی دو بار در صف آمده است؛ پیش از تصمیم با نگه‌دارندهٔ دفتر پیگیری کنید.', 'This address is in the queue twice: follow it up with the garden\'s keeper before deciding.')}</p>` : ''}
    <div class="detail-section"><h3>${T('پیشنهاد', 'The proposal')}</h3>${prose(f.proposal || '—')}</div>
    <div class="detail-section"><h3>${T('آنچه برای تصمیم باید دید', 'What to see before deciding')}</h3>${prose(f.neighborhood || f.neighbourhood || '—')}</div>
    ${others.map(([k, v]) => h`<div class="detail-section"><h3><bdi dir="ltr">${k}</bdi></h3>${prose(v)}</div>`)}
    <details class="detail-section"><summary>${T('متن کامل در صف تصمیم‌ها', 'The whole text in the queue of decisions')}</summary><pre dir="auto">${p.text}</pre></details>
    ${decided || p.twice ? '' : h`<div class="actions"><button class="primary" data-action="lead-decide" data-decision="acked">${T('تأیید پیشنهاد', 'Accept the proposal')}</button>
      <button class="secondary" data-action="lead-decide" data-decision="answered">${T('پاسخ، بدون تأیید', 'Answer, without accepting')}</button>
      <button class="text-button" data-action="go-lead">${T('بعداً', 'Later')}</button></div>
      <p class="muted">${T('تأیید یعنی پیشنهاد همان‌گونه که نوشته شده به نام', 'Accepting means the proposal, as written, is accepted in the name of')} ${text.show(p.gardenerTitle)} ${T('پذیرفته و در دفتر ثبت می‌شود. پاسخ، سخن شما را زیر آن می‌نویسد و تصمیم را باز می‌گذارد.', 'and recorded in the garden. An answer writes your words beneath it and leaves the decision open.')}</p>`}
  </section>`;
}

async function proposalView(ctx, id) {
  const p = state.proposal = await api.get('/api/proposal?id=' + encodeURIComponent(id));
  state.checked = false;
  return h`<section class="panel lead">
    <p class="eyebrow">${KINDS.proposal}${p.where === 'held' ? h` · ${badge(T('کنار گذاشته شد', 'set aside'), 'late')}` : ''}</p>
    <h2>${T('پیشنهاد', 'A proposal from')} ${text.show(p.peerTitle || p.fromName || p.from)}</h2>
    <div class="facts">${fact(T('از دفتر', 'From the garden'), p.peerTitle || p.fromName || p.from)}${fact(T('زیر توافق', 'Under'), p.under || '—')}${fact(T('پرونده‌ها', 'Beans'), String(p.beans.length))}${fact(T('نشانی', 'Address'), p.id)}</div>
    <p class="muted">${p.where === 'held' ? T('هنگام تبادل کنار گذاشته شد؛ دلیلش در زیر آمده است.', 'Set aside in the exchange; why is below.') : T('هیچ رضایت پایداری این پیشنهاد را در بر نمی‌گیرد؛ بی تصمیم شما گرفته نمی‌شود.', 'No standing consent covers this proposal: it is not taken without your decision.')}</p>
    ${p.why ? h`<details class="detail-section" open><summary>${T('دلیل کنار گذاشتن', 'Why it was set aside')}</summary><pre dir="ltr">${p.why}</pre></details>` : ''}
    <div class="detail-section"><h3>${T('آنچه می‌آورد', 'What it brings')}</h3>${table({columns: [
      {title: T('پرونده', 'Bean'), cell: b => text.show(b.title)},
      {title: T('در این دفتر', 'In this garden'), cell: b => b.here ? h`${T('همان', 'the same as')} ${text.show(b.hereTitle)} ${badge(T('به‌روز می‌شود', 'brought up to date'))}` : badge(T('تازه', 'new'))},
    ], rows: p.beans})}</div>
    <div class="detail-section" id="proposal-check"><button class="secondary" data-action="lead-check">${T('بررسی با دروازهٔ دفتر', 'Check with the garden\'s gate')}</button>
      <p class="muted">${T('بررسی چیزی را تغییر نمی‌دهد: روی نسخه‌ای جدا از دفتر نشان می‌دهد گرفتن این پیشنهاد چه می‌کند.', 'A check changes nothing: on a copy apart from the garden it shows what taking this proposal would do.')}</p></div>
    <div class="actions"><button class="primary" data-action="lead-take" disabled>${T('گرفتن در دفتر', 'Take into the garden')}</button><button class="text-button" data-action="go-lead">${T('بعداً', 'Later')}</button></div>
  </section>`;
}

// a person without a garden answered a form on the served page: their own words, laid outside the garden until the
// gardener's save takes them (design §10.5, class D)
async function formView(ctx, id) {
  const f = state.form = await api.get('/api/form?id=' + encodeURIComponent(id));
  return h`<section class="panel lead"><p class="eyebrow">${KINDS.form}</p>
    <h2>${text.show(f.person_title)} · ${text.show(f.form_title)}</h2>
    <div class="facts">${fact(T('از', 'From'), f.person_title)}${fact(T('فرم', 'Form'), f.form_title)}${fact(T('زمان', 'When'), f.at)}</div>
    <p class="muted">${T('این‌ها گفته‌های خود اوست، همان‌طور که در صفحه نوشت؛ با گرفتن آن‌ها، به نام شما در دفتر ثبت می‌شوند و چیزی از آن‌ها تغییر نمی‌کند.', 'These are their own words, as they wrote them on the page; taken, they are recorded in the garden in your name, and nothing of them is changed.')}</p>
    <div class="detail-section">${f.questions.map((x, i) => h`<h3>${String(i + 1)}. ${text.show(x.q)}</h3><p class="answer">${text.show(x.a || '—')}</p>`)}</div>
    <div class="actions"><button class="primary" data-action="lead-take-form">${T('گرفتن در دفتر', 'Take into the garden')}</button><button class="text-button" data-action="go-lead">${T('بعداً', 'Later')}</button></div>
  </section>`;
}

// a passkey a person made on the served page: naming it in their bean is the gardener's (class F)
async function passkeyView(ctx, id) {
  const k = state.passkey = await api.get('/api/passkey?id=' + encodeURIComponent(id));
  return h`<section class="panel lead"><p class="eyebrow">${KINDS.passkey} · ${badge(CLASS('F'))}</p>
    <h2>${text.show(k.person_title)}</h2>
    <div class="facts">${fact(T('برای', 'For'), k.person_title)}${fact(T('شناسهٔ کلید', 'Key id'), k.credential + '…')}</div>
    <p class="muted">${text.show(k.person_title)} ${T('در صفحهٔ بیرونی دفتر کلیدی ساخت و دفتر آن را وارسی کرد. با ثبت آن در پروندهٔ او، با همین کلید وارد می‌شود. اگر نمی‌دانید این کلید را او ساخته، از خودش بپرسید و ثبت نکنید.', 'made a key on the garden\'s outer page, and the garden checked it. Recorded in their bean, they sign in with it. If you do not know they made it, ask them, and do not record it.')}</p>
    <div class="actions"><button class="primary" data-action="lead-take-passkey">${T('ثبت به نام او', 'Record it as theirs')}</button><button class="text-button" data-action="go-lead">${T('بعداً', 'Later')}</button></div>
  </section>`;
}

async function errorView(ctx, ref) {
  const r = await fetch('/api/error?ref=' + encodeURIComponent(ref), {cache: 'no-store'});
  const e = await r.json().catch(() => ({}));
  if (!r.ok) return h`<section class="panel">${guidedError({message: e.error || T('این مرجع پیدا نشد.', 'No such reference.')})}</section>`;
  return h`<section class="panel lead"><p class="eyebrow">${KINDS.error} · <code dir="ltr">${e.ref}</code></p>
    <h2>${text.show(e.message)}</h2>
    <div class="facts">${fact(T('زمان', 'When'), e.at ? moment.show(e.at.slice(0, 16).replace('T', ' ')) : '')}${fact(T('کار', 'What'), e.action)}${fact(T('وضعیت', 'Status'), String(e.status || ''))}${fact(T('نوع', 'Kind'), e.kind === 'refused' ? T('نپذیرفت', 'refused') : T('انجام نشد', 'failed'))}</div>
    ${(e.followUp || []).length ? h`<div class="detail-section"><h3>${T('پیگیری با', 'Follow up with')}</h3>${e.followUp.map(c => h`<p>${text.show(c.title)}${c.reach ? h` · ${text.show(c.reach)}` : ''}</p>`)}</div>` : ''}
    ${e.diagnostic ? h`<details class="detail-section"><summary>${T('جزئیات برای پیگیری', 'Details for following it up')}</summary><pre dir="ltr">${e.diagnostic}</pre></details>` : ''}</section>`;
}

const SYNC_SAID_ = () => ({current: T('چیزی برای ادغام نبود', 'there was nothing to merge'), refused: T('همتایی چیزی آورد که پذیرفته نشد', 'a peer brought something refused'),
  diverged: T('ادغام به تعارض خورد؛ کار یک نفر است', 'the merge met a conflict: a person\'s to settle'), busy: T('ذخیرهٔ دیگری در جریان است', 'another save is under way'),
  dirty: T('تغییری هنوز ذخیره نشده', 'a change is not saved yet'), error: T('همتا در دسترس نبود', 'the peer was out of reach')});
const SYNC_SAID = new Proxy({}, {get: (_t, k) => SYNC_SAID_()[k]});
// a garden of the core syncs with its peers (bin/sync.py): each peer's own line, and where both sides moved, a merge
// the sitting person makes and signs; a peer that brought a refused commit is left out whole, the writer's to fix
function syncView(ctx) {
  const s = ctx.data.sync || {};
  const parted = s.state === 'diverged', refused = s.state === 'refused', peers = s.peers || null;
  const title = refused ? T('همتایی چیزی آورد که پذیرفته نشد', 'A peer brought something refused') : parted ? (peers ? T('این رایانه و همتایش هر دو تغییر کرده‌اند', 'This machine and its peer have both changed') : T('دفتر و مرکز از هم جدا شده‌اند', 'The garden and its hub have parted')) : T('همگام‌سازی', 'Sync');
  const say = refused ? T('یکی از همتاهای این دفتر کامیتی آورد که با قاعده‌های دفتر نخواند (امضا، حق نوشتن، یا دروازه). از آن همتا هیچ چیز ادغام نشد و دفتر همان است که بود. نویسندهٔ آن باید درستش کند؛ جزئیات زیر است.',
      'A peer of this garden brought a commit the garden\'s rules refuse (a signature, a right to write, or the gate). Nothing of that peer was merged, and the garden is as it was. Its author must mend it; the details are below.')
    : parted ? (peers ? T('آنچه همتا آورده بررسی شد و درست است، اما این رایانه هم ثبت‌های خودش را دارد. ادغام کار یک نفر است: با زدن «ادغام» آن را با امضای خودتان ثبت می‌کنید.',
        'What the peer brought was checked and is sound, but this machine has records of its own too. A merge is a person\'s: pressing Merge records it with your own signature.')
      : T('این رایانه و مرکز هر دو تغییرهایی دارند که با هم ادغام نشد. تا یک نفر آن را حل نکند، چیزی فرستاده نمی‌شود؛ ثبت‌های شما روی همین رایانه محفوظ است. با نگه‌دارندهٔ دفتر پیگیری کنید.',
        'This machine and the hub both have changes that did not merge. Until a person settles it, nothing is sent; your records are safe on this machine. Follow it up with the garden\'s keeper.'))
    : T('وضعیت آخرین همگام‌سازی.', 'How the last sync stands.');
  return h`<section class="panel lead"><p class="eyebrow">${KINDS.sync}</p>
    <h2>${title}</h2>
    <p>${say}</p>
    <div class="facts">${fact(T('وضعیت', 'State'), s.state || '—')}${fact(T('آخرین بار', 'Last'), s.at || '—')}${s.behind !== undefined ? fact(T('از مرکز عقب', 'Behind the hub'), String(s.behind)) : ''}${s.ahead !== undefined ? fact(T('جلوتر از مرکز', 'Ahead of the hub'), String(s.ahead)) : ''}</div>
    ${peers ? h`<div class="detail-section"><h3>${T('همتاها', 'Peers')}</h3>${Object.entries(peers).map(([p, line]) => h`<p dir="ltr"><code>${p}</code> ${text.show(String(line))}</p>`)}</div>` : ''}
    ${s.why ? h`<details class="detail-section"><summary>${T('جزئیات', 'Details')}</summary><pre dir="ltr">${String(s.why)}</pre></details>` : ''}
    <div class="actions">${parted && peers ? h`<button data-action="lead-sync-merge">${T('ادغام، با امضای من', 'Merge, signed by me')}</button>` : ''}<button class="secondary" data-action="lead-sync">${T('همگام‌سازی اکنون', 'Sync now')}</button></div></section>`;
}

// one decision through a dialog: the person's words, then the call; the request id is the dialog's, reused on a retry
function decide({title, note, words, submit, call}) {
  const request = api.newRequest();
  const fields = words ? [{name: 'words', label: words.label, type: 'lines', max: 1000, required: words.required, hint: words.hint}] : [];
  openDialog({title, note, submit, body: words ? form(fields) : h`<p>${note}</p>`, onSubmit: async f => {
    const {values, errors} = collect(f, fields);
    if (!showErrors(f, errors)) return false;
    await call(values.words || '', request);
    return true;
  }});
}

export const actions = {
  'go-lead': (el, ctx) => ctx.go(el.dataset.kind || '', el.dataset.id || ''),
  'lead-decide': (el, ctx) => {
    const p = state.pending, acked = el.dataset.decision === 'acked';
    decide({
      title: p.need ? T('برآوردن نیاز', 'Meet the need') : acked ? T('تأیید پیشنهاد', 'Accept the proposal') : T('پاسخ، بدون تأیید', 'Answer, without accepting'),
      note: p.need ? T(`«${p.what}» به نام ${p.gardenerTitle} برآورده و در پروندهٔ آن ثبت می‌شود.`, `“${p.what}” is met in the name of ${p.gardenerTitle} and recorded in its bean.`)
        : acked ? T(`«${p.what}» به نام ${p.gardenerTitle} تأیید و با یادداشتش در دفتر ثبت می‌شود.`, `“${p.what}” is accepted in the name of ${p.gardenerTitle} and recorded in the garden with its note.`) : T('سخن شما زیر این مورد نوشته می‌شود و تصمیم باز می‌ماند.', 'Your words are written beneath it, and the decision stays open.'),
      words: acked ? {label: T('سخن شما (اختیاری)', 'Your words (optional)'), hint: T('مثلاً شرطی یا توضیحی که می‌خواهید کنار تأیید بماند.', 'For example a condition, or a remark to keep beside the acceptance.')} : {label: T('پاسخ شما', 'Your answer'), required: true},
      submit: p.need ? T('برآوردن و ثبت', 'Meet and record') : acked ? T('تأیید و ثبت', 'Accept and record') : T('ثبت پاسخ', 'Record the answer'),
      call: async (words, request) => {
        await api.post('/api/pending/decide', {id: p.slug, decision: el.dataset.decision, words, digest: p.digest, request});
        ctx.notice(p.need ? T('نیاز برآورده و در پرونده ثبت شد.', 'The need is met, and recorded in its bean.') : acked ? T('تأیید شد و در دفتر ثبت شد.', 'Accepted and recorded in the garden.') : T('پاسخ شما در دفتر ثبت شد.', 'Your answer is recorded in the garden.'));
        ctx.go();
      },
    });
  },
  'lead-check': async (el, ctx) => {
    const box = document.getElementById('proposal-check');
    mount(box, h`<p class="muted">${T('در حال بررسی… (ممکن است کمی طول بکشد)', 'Checking… (it may take a moment)')}</p>`);
    try {
      const p = await api.get('/api/proposal?check=1&id=' + encodeURIComponent(state.proposal.id));
      state.checked = p.read?.ok === true;
      mount(box, h`<p class="${state.checked ? 'notice' : 'notice error'}">${state.checked ? T('دروازهٔ دفتر گرفتن این پیشنهاد را می‌پذیرد.', 'The garden\'s gate takes this proposal.') : T('دروازهٔ دفتر این پیشنهاد را نمی‌پذیرد؛ گرفتن آن ممکن نیست. با نگه‌دارندهٔ دفتر پیگیری کنید.', 'The garden\'s gate refuses this proposal: it cannot be taken. Follow it up with the garden\'s keeper.')}</p>
        <details><summary>${T('آنچه بررسی گفت', 'What the check said')}</summary><pre dir="ltr">${p.read?.said || ''}</pre></details>`);
      const take = document.querySelector('[data-action="lead-take"]');
      if (take) take.disabled = !state.checked;
    } catch (e) { mount(box, guidedError(e)); }
  },
  'lead-take-passkey': (el, ctx) => {
    const k = state.passkey;
    decide({
      title: T('ثبت کلید ورود', 'Record a passkey'),
      note: T(`کلید ورود ${k.person_title} در پروندهٔ او به نام شما ثبت می‌شود (رده F).`, `${k.person_title}'s passkey is recorded in their bean, in your name (class F).`),
      words: null,
      submit: T('ثبت', 'Record'),
      call: async (_words, request) => {
        await api.post('/api/passkey/take', {id: k.id, request});
        ctx.notice(T('کلید به نام او ثبت شد.', 'The key is recorded as theirs.'));
        ctx.go();
      },
    });
  },
  'lead-take-form': (el, ctx) => {
    const f = state.form;
    decide({
      title: T('گرفتن پاسخ‌ها در دفتر', 'Take the answers into the garden'),
      note: T(`پاسخ‌های ${f.person_title} به «${f.form_title}» همان‌طور که نوشته، به نام شما در دفتر ثبت می‌شود.`, `${f.person_title}'s answers to “${f.form_title}” are recorded in the garden as written, in your name.`),
      words: null,
      submit: T('گرفتن و ثبت', 'Take and record'),
      call: async (_words, request) => {
        await api.post('/api/form/take', {id: f.id, request});
        ctx.notice(T('پاسخ‌ها در دفتر گرفته و ثبت شد.', 'The answers are taken into the garden and recorded.'));
        ctx.go();
      },
    });
  },
  'lead-take': (el, ctx) => {
    const p = state.proposal;
    if (!state.checked) return;
    decide({
      title: T('گرفتن پیشنهاد در دفتر', 'Take the proposal into the garden'),
      note: T(`${p.beans.length} پرونده از ${p.peerTitle || p.fromName || p.from} به نام ${p.gardenerTitle} در دفتر گرفته و ثبت می‌شود. این تأیید فقط برای همین پیشنهاد است.`,
        `${p.beans.length} bean(s) from ${p.peerTitle || p.fromName || p.from} are taken into the garden and recorded in the name of ${p.gardenerTitle}. This acceptance is for this proposal alone.`),
      words: null,
      submit: T('گرفتن و ثبت', 'Take and record'),
      call: async (_words, request) => {
        await api.post('/api/proposal/take', {id: p.id, fingerprint: p.fingerprint, request});
        ctx.notice(T('پیشنهاد در دفتر گرفته و ثبت شد.', 'The proposal is taken into the garden and recorded.'));
        ctx.go();
      },
    });
  },
  'lead-sync': async (el, ctx) => { await api.post('/api/sync'); ctx.notice(T('همگام‌سازی آغاز شد.', 'Sync started.')); },
  'lead-sync-merge': async (el, ctx) => {
    const s = await api.post('/api/sync/merge');
    ctx.notice(s.state === 'merged' ? T('ادغام شد و با امضای شما ثبت شد.', 'Merged, and recorded with your signature.') : T('ادغام انجام نشد — ', 'The merge did not go ahead — ') + (SYNC_SAID[s.state] || s.state || ''));
    ctx.go();
  },
  act: async (el, ctx) => {
    const r = await api.post('/api/action', {id: el.dataset.id, do: el.dataset.do});
    ctx.notice(r.said || T('انجام شد.', 'Done.'));
    ctx.go();
  },
};

export default {
  id: 'lead', get nav() { return T('منتظر شما', 'Waiting for you'); }, get title() { return T('منتظر تصمیم شما', 'Waiting for your decision'); }, actions,
  async render(ctx) {
    const kind = ctx.params.get('kind') || '', id = ctx.params.get('id') || '';
    switch (kind) {
      case 'pending': return pendingView(ctx, id);
      case 'proposal': return proposalView(ctx, id);
      case 'error': return errorView(ctx, id);
      case 'sync': return syncView(ctx);
      case 'case': if (!agencyCase(ctx, id)) return courseView(ctx, id);
        setTimeout(() => openCase(ctx, id)); return cases.render(ctx);
      case 'action': return actionView(ctx, id);
      case 'form': return formView(ctx, id);
      case 'passkey': return passkeyView(ctx, id);
      case 'health': case 'obligation': if (!agencyCase(ctx, id)) return courseView(ctx, id);
        setTimeout(() => openCase(ctx, id)); return cases.render(ctx);
      default: return list(ctx);
    }
  },
};
