// One dialog for every form: what was typed is kept across a failed save, and the failure is shown as a guided error.
// onSubmit(formEl) returns true to close; a GuidedError it throws is shown in the dialog, nothing typed is lost.
import { h, mount } from './safe.js';
import { guidedError, bindGuided } from './guided.js';
import { T } from './say.js';
let dlg;
function ensure() {
  if (dlg) return dlg;
  dlg = document.createElement('dialog');
  dlg.className = 'w-dialog';
  document.body.appendChild(dlg);
  bindGuided(dlg);
  dlg.addEventListener('click', e => { if (e.target.closest('[data-close]')) dlg.close(); });
  return dlg;
}
export const isOpen = () => Boolean(dlg && dlg.open);
export function openDialog({title, body, note, submit = T('ذخیره در دفتر', 'Save in the garden'), cancel = T('انصراف', 'Cancel'), onSubmit, onClose, wide = false}) {
  const d = ensure();
  mount(d, h`<form class="w-dialog-form${wide ? ' wide' : ''}" novalidate><div class="dialog-top"><h2>${title}</h2><button type="button" data-close aria-label="${T('بستن', 'Close')}">×</button></div>
    ${note ? h`<p class="w-dialog-note">${note}</p>` : ''}<div class="w-dialog-body form-grid">${body}</div><div class="w-dialog-error"></div>
    <div class="dialog-actions">${onSubmit ? h`<button class="primary" type="submit">${submit}</button>` : ''}<button type="button" class="secondary" data-close>${onSubmit ? cancel : T('بستن', 'Close')}</button></div></form>`);
  const f = d.querySelector('form'), err = d.querySelector('.w-dialog-error'), btn = f.querySelector('button[type=submit]');
  f.addEventListener('submit', async e => {
    e.preventDefault();
    if (!onSubmit || btn.disabled) return;
    mount(err, h``);
    btn.disabled = true; const label = btn.textContent; btn.textContent = T('در حال ذخیره…', 'Saving…');
    try { if (await onSubmit(f)) d.close(); }
    catch (x) { mount(err, guidedError(x)); }
    finally { btn.disabled = false; btn.textContent = label; }
  });
  d.addEventListener('close', () => onClose && onClose(), {once: true});
  d.showModal();
  f.querySelector('.w-input')?.focus();
  return d;
}
