// A guided error (daftar design §3): what did not go ahead, its reference, whom to follow it up with (the source of the
// privilege it needed, up to the gardener), and its detail as far as the reader's privileges reach, on request.
import { h, mount } from './safe.js';
import { T } from './say.js';
export class GuidedError extends Error {
  constructor({message, ref, followUp, status} = {}) {
    super(message || T('انجام نشد.', 'It did not go ahead.'));
    this.ref = ref || ''; this.followUp = followUp || []; this.status = status || 0;
  }
}
export function guidedError(err) {
  const e = err instanceof GuidedError ? err : new GuidedError({message: err?.message});
  const who = e.followUp.map(c => (c.title || c.who) + (c.reach ? ` (${c.reach})` : ''));
  return h`<div class="w-guided" role="alert"><p class="w-guided-message">${e.message}</p>${e.ref ? h`<p class="w-guided-ref">${T('مرجع', 'Reference')}: <bdi dir="ltr" class="w-ref">${e.ref}</bdi>
    <button type="button" class="text-button" data-action="guided-copy" data-ref="${e.ref}">${T('رونوشت', 'Copy')}</button>
    <button type="button" class="text-button" data-action="guided-detail" data-ref="${e.ref}">${T('جزئیات', 'Details')}</button></p>` : ''}${who.length ? h`<p class="w-guided-who">${T('پیگیری با', 'Follow up with')}: ${who.join(T('، ', ', '))}</p>` : ''}<pre class="w-guided-detail" hidden></pre></div>`;
}
export function bindGuided(root) {
  root.addEventListener('click', async e => {
    const b = e.target.closest('[data-action^="guided-"]');
    if (!b) return;
    if (b.dataset.action === 'guided-copy') {
      try { await navigator.clipboard.writeText(b.dataset.ref); b.textContent = T('رونوشت شد', 'Copied'); } catch { b.textContent = b.dataset.ref; }
    } else {
      const pre = b.closest('.w-guided').querySelector('.w-guided-detail');
      try {
        const r = await fetch('/api/error?ref=' + encodeURIComponent(b.dataset.ref), {cache: 'no-store'});
        const rec = await r.json();
        pre.textContent = rec.diagnostic || rec.error || T('جزئیاتی بیش از این برای شما نیست.', 'There is no more detail for you.');
      } catch { pre.textContent = T('جزئیات خوانده نشد.', 'The details could not be read.'); }
      pre.hidden = false;
    }
  });
}
