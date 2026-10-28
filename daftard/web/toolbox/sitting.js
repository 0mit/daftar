// Who sits at the keyboard (design §6). A garden that takes only its people's own signed writes asks once per sitting:
// a choice of the people who write here, confirmed by that person's passphrase, which opens their key on this machine
// and is held by daftard for the sitting alone. A writer with no key here makes one: the passphrase given twice, and
// the key's fingerprint shown with the line the gardener adds to their bean (an identity, the gardener's to settle).
import { h } from './safe.js';
import { openDialog } from './dialog.js';
import { settings } from './settings.js';
const T = {
  en: {who: 'Who is at the keyboard?', person: 'I am', pass: 'Your passphrase', again: 'The passphrase again',
       begin: 'Begin my sitting', make: 'Make my key', mismatch: 'The two passphrases differ.',
       short: 'A passphrase is at least eight characters.',
       note: 'Your saves here are signed with your own key. Your passphrase stays on this machine, for this sitting only.',
       nokey: 'This machine keeps no key for you yet: give a passphrase twice, and one is made.',
       made: 'Your key is made', give: 'Give this line to the gardener, who adds it to your bean; until then the hub takes nothing you sign.',
       fpr: 'Its fingerprint'},
  fa: {who: 'چه کسی پشت صفحه‌کلید است؟', person: 'من', pass: 'گذرواژهٔ شما', again: 'گذرواژه، دوباره',
       begin: 'آغاز نشست من', make: 'ساختن کلید من', mismatch: 'دو گذرواژه یکی نیستند.',
       short: 'گذرواژه دست‌کم هشت نویسه است.',
       note: 'ذخیره‌های شما در اینجا با کلید خودتان امضا می‌شود. گذرواژه‌تان روی همین رایانه و فقط برای همین نشست می‌ماند.',
       nokey: 'این رایانه هنوز کلیدی برای شما ندارد: گذرواژه را دو بار بنویسید تا ساخته شود.',
       made: 'کلید شما ساخته شد', give: 'این سطر را به باغبان بدهید تا به برگهٔ شما بیفزاید؛ تا آن زمان هاب چیزی را که امضا می‌کنید نمی‌پذیرد.',
       fpr: 'اثر انگشت آن'},
};
const t = k => (T[settings.lang] || T.en)[k] ?? T.en[k];

// askSitting asks who is at the keyboard and begins their sitting; true once one is begun.
export async function askSitting(api) {
  api.setSession(await api.get('/api/session'));   // the token a sitting is begun with, though the garden is closed
  const st = await api.get('/api/sitting');
  const writers = st.writers || [];
  let begun = false;
  return new Promise(resolve => {
    openDialog({
      title: t('who'), note: t('note'), submit: t('begin'),
      body: h`<label>${t('person')}<select class="w-input" name="person">${writers.map(w =>
        h`<option value="${w.person}">${w.person}${w.key ? '' : ' *'}</option>`)}</select></label>
        <label>${t('pass')}<input class="w-input" name="passphrase" type="password" autocomplete="current-password"></label>
        <label>${t('again')} <small>(${t('nokey')})</small><input class="w-input" name="again" type="password" autocomplete="new-password"></label>`,
      onSubmit: async f => {
        const person = f.person.value, pass = f.passphrase.value;
        const w = writers.find(x => x.person === person);
        if (w && !w.key) {
          if (pass.length < 8) throw new Error(t('short'));
          if (pass !== f.again.value) throw new Error(t('mismatch'));
          const made = await api.post('/api/keys/make', {person, passphrase: pass});
          w.key = true;
          openMade(made);
        }
        await api.post('/api/sitting/begin', {person, passphrase: pass});
        begun = true;
        return true;
      },
      onClose: () => resolve(begun),
    });
  });
}

function openMade(made) {
  setTimeout(() => openDialog({title: t('made'), note: t('give'),
    body: h`<p>${t('fpr')}: <bdi dir="ltr"><code>${made.fingerprint}</code></bdi></p><p><bdi dir="ltr"><code>${made.statement}</code></bdi></p>`}), 0);
}

// endSitting ends the sitting: the passphrase is forgotten.
export const endSitting = api => api.post('/api/sitting/end', {});
