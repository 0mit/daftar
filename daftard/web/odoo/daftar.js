// daftard's own part of Odoo's page (design §10.3): the moment the garden is read as of. A systray item of Odoo's own
// navbar shows it — "now", or the commit and its moment, marked so nobody takes the past for the present — and lets the
// reader choose another: a day, a moment or a commit. The choice is the seat's (POST /odoo/asof); every call the page
// makes is then answered from the garden at that commit, by what the reader's grants open now.
odoo.define('@daftar/asof', ['@odoo/owl', '@web/core/registry', '@web/session'], function (require) {
    'use strict';
    const { Component, useState, xml } = require('@odoo/owl');
    const { registry } = require('@web/core/registry');
    const info = require('@web/session').session.daftar || {};    // Odoo's session, as its own module keeps it
    const WORDS = {
        en: { now: 'Now', asof: 'As of', go: 'Show', back: 'Back to now', hint: 'A day, a moment or a commit',
              title: 'The moment this garden is read as of' },
        fa: { now: 'اکنون', asof: 'به تاریخ', go: 'نشان بده', back: 'بازگشت به اکنون', hint: 'یک روز، یک لحظه یا یک نسخه',
              title: 'لحظه‌ای که این دفتر از آن خوانده می‌شود' },
        tr: { now: 'Şimdi', asof: 'Tarihindeki hâli', go: 'Göster', back: 'Şimdiye dön', hint: 'Bir gün, bir an ya da bir sürüm',
              title: 'Bu bahçenin okunduğu an' },
    };
    const words = WORDS[String(info.lang || 'en').slice(0, 2)] || WORDS.en;

    class AsOf extends Component {
        static template = xml`
            <div class="o_daftar_asof dropdown d-flex align-items-center" t-att-title="words.title">
                <button type="button" class="btn btn-sm" t-att-class="asof.commit ? 'btn-warning' : 'btn-light'"
                        t-on-click="() => this.state.open = !this.state.open">
                    <t t-if="asof.commit"><t t-esc="words.asof"/> <bdi t-esc="asof.at"/> · <bdi t-esc="asof.commit.slice(0, 7)"/></t>
                    <t t-else="" t-esc="words.now"/>
                </button>
                <div t-if="state.open" class="dropdown-menu dropdown-menu-end show p-2" style="min-width: 18rem">
                    <input class="form-control form-control-sm mb-2" t-att-placeholder="words.hint" t-model="state.at"
                           t-on-keydown="(ev) => ev.key === 'Enter' and this.look(state.at)"/>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-primary" t-on-click="() => this.look(state.at)" t-esc="words.go"/>
                        <button t-if="asof.commit" class="btn btn-sm btn-secondary" t-on-click="() => this.look('')" t-esc="words.back"/>
                    </div>
                    <div t-if="state.error" class="text-danger small mt-2" t-esc="state.error"/>
                </div>
            </div>`;
        setup() {
            this.words = words;
            this.asof = info.asof || {};
            this.state = useState({ open: false, at: '', error: '' });
        }
        async look(at) {
            const r = await fetch('/odoo/asof', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                  body: JSON.stringify({ at: String(at || '').trim() }) });
            const got = await r.json().catch(() => ({}));
            if (!r.ok) {
                this.state.error = got.error || String(r.status);
                return;
            }
            window.location.reload();   // every view read again, from the garden at that commit
        }
    }
    registry.category('systray').add('daftar.asof', { Component: AsOf }, { sequence: 1 });
    return { AsOf };
});
