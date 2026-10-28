// The served page (design §10.1): signing in by a link, then what is the signed-in person's own — their leads, and a
// bean a grant opens to them. Everything the garden says is set as text, never as markup.
const $ = id => document.getElementById(id);
let csrf = '';
const say = msg => { $('notice').textContent = msg || ''; };
const el = (tag, text, cls) => { const e = document.createElement(tag); e.textContent = text; if (cls) e.className = cls; e.dir = 'auto'; return e; };

async function call(path, body) {
  const init = body === undefined ? {cache: 'no-store'}
    : {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify(body)};
  const r = await fetch(path, init);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(j.error || j.said || ('(' + r.status + ')')); e.status = r.status; e.signin = j.signin; throw e; }
  return j;
}

// A sign-in link carries its token after '#in=', which no request carries and so no server's log keeps (security
// audit 1.7): it is taken off the address at once, and sent once, in a POST from this page's own origin, whose answer
// begins the session.
async function redeem() {
  const m = /^#in=([A-Za-z0-9_-]+)$/.exec(location.hash);
  if (!m) return;
  history.replaceState(null, '', location.pathname);
  try { await call('/served/in', {t: m[1]}); }
  catch (e) { say(e.message); }
}

async function start() {
  await redeem();
  try {
    const me = await call('/served/me');
    csrf = me.csrf;
    $('title').textContent = me.title || 'دفتر';
    $('who').textContent = me.me + ' · ' + me.garden;
    $('out').hidden = false; $('mine').hidden = false; $('signin').hidden = true;
    renderForms(await call('/served/forms'));
    const leads = await call('/served/leads');
    $('leads').replaceChildren(...(leads.length ? leads.map(l => el('li', [l.title || l.kind, l.about, l.since].filter(Boolean).join(' · ')))
      : [el('li', 'چیزی منتظر شما نیست.', 'muted')]));
  } catch (e) {
    if (e.signin) { $('signin').hidden = false; $('mine').hidden = true; return; }
    say(e.message);
  }
}

// each form open to the person: its questions, what they gave before if it still waits, and a send
function renderForms(forms) {
  $('forms').replaceChildren(...forms.map(f => {
    const form = document.createElement('form');
    form.append(el('h2', f.title));
    if (f.given) form.append(el('p', 'آنچه پیش‌تر فرستادید، هنوز در انتظار گرفته شدن است (' + f.at + '). فرستادن دوباره جای آن را می‌گیرد.', 'muted'));
    f.questions.forEach((q, i) => {
      const label = el('label', (i + 1) + '. ' + q);
      const area = document.createElement('textarea');
      area.name = 'a' + i; area.rows = 3; area.maxLength = 4000; area.dir = 'auto';
      area.value = (f.given && f.given[i]) || '';
      label.append(area); form.append(label);
    });
    const send = el('button', 'فرستادن'); form.append(send);
    form.addEventListener('submit', async ev => {
      ev.preventDefault();
      const answers = f.questions.map((_q, i) => form.elements['a' + i].value);
      try { const r = await call('/served/form', {id: f.id, answers}); say('فرستاده شد (' + r.at + '). نگه‌دارندهٔ دفتر آن را می‌خواند و می‌گیرد.'); }
      catch (e) { say(e.message); }
    });
    return form;
  }));
}

// passkeys (WebAuthn): made here, named in the person's bean by the gardener, and signed in with after
const bytes = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), c => c.charCodeAt(0));
const text64 = b => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
$('pk-new').addEventListener('click', async () => {
  try {
    const o = await call('/served/passkey/new', {});
    const cred = await navigator.credentials.create({publicKey: {challenge: bytes(o.challenge), rp: o.rp,
      user: {id: bytes(o.user.id), name: o.user.name, displayName: o.user.displayName},
      pubKeyCredParams: o.algorithms.map(alg => ({type: 'public-key', alg})), attestation: 'none',
      authenticatorSelection: {residentKey: 'required', userVerification: 'required'}}});
    const r = await call('/served/passkey/made', {clientDataJSON: text64(cred.response.clientDataJSON),
      attestationObject: text64(cred.response.attestationObject)});
    say(r.said);
  } catch (e) { say(e.message); }
});
$('pk-in').addEventListener('click', async () => {
  try {
    const c = await call('/served/passkey/challenge', {});
    const got = await navigator.credentials.get({publicKey: {challenge: bytes(c.challenge), rpId: c.rpId, userVerification: 'required'}});
    await call('/served/passkey/in', {id: text64(got.rawId), clientDataJSON: text64(got.response.clientDataJSON),
      authenticatorData: text64(got.response.authenticatorData), signature: text64(got.response.signature),
      userHandle: got.response.userHandle ? text64(got.response.userHandle) : ''});
    location.reload();
  } catch (e) { say(e.message); }
});

$('ask').addEventListener('submit', async ev => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  try { const r = await call('/served/link', {g: f.get('g'), person: f.get('person')}); say(r.said); }
  catch (e) { say(e.message); }
});
$('read').addEventListener('submit', async ev => {
  ev.preventDefault();
  const id = new FormData(ev.target).get('id');
  $('bean').replaceChildren();
  try {
    const b = await call('/served/bean?id=' + encodeURIComponent(id));
    $('bean').replaceChildren(el('h3', b.title), el('p', b.kind, 'muted'),
      ...(b.statements || []).map(s => el('div', JSON.stringify(s), 'line')));
  } catch (e) { say(e.message); }
});
$('out').addEventListener('click', async () => { try { await call('/served/out', {}); } catch { /* ended either way */ } location.reload(); });
// a link opened where this page is open already changes only the address's '#': no load, so it is taken here
window.addEventListener('hashchange', () => { if (location.hash.startsWith('#in=')) start(); });
start();
