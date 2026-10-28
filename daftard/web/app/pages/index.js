// Every page, in the order the navigation shows them, and the actions any page may use (a case opens from anywhere).
import { h } from '/toolbox/safe.js';
import home from './home.js';
import core from './core.js';
import cases, { actions as caseActions } from './cases.js';
import people from './people.js';
import followups from './followups.js';
import report from './report.js';
import lead, { actions as leadActions } from './lead.js';
import accounts from './accounts.js';
import categorize from './categorize.js';
import exchange from './exchange.js';
import calendar from './calendar.js';
import posting from './posting.js';
import vouchers from './vouchers.js';
import finance from './finance.js';
import chart from './chart.js';
import { actions as booksActions } from '../books.js';
import boardHome from './board/summary.js';
import boardPays from './board/pays.js';
import boardAgreements from './board/agreements.js';
import boardExchange from './board/exchange.js';
import { actions as boardActions } from './board/board.js';
import { now, peoplePage, time, moneyPage, books, reportPage, between, boardNow, boardMoney, boardBetween, hidden } from './seven.js';
const map = {id: 'map', nav: 'نقشهٔ دفتر', title: 'نقشهٔ دفتر', render: () => h`<section class="panel"><p>نقشهٔ دفتر، همهٔ پرونده‌ها و پیوندهایشان در یک نگاه.</p><a class="primary" href="/view" target="_blank" rel="noopener">باز کردن نقشه</a></section>`};
// each kind of garden its pages (daftard's `kind`): a garden with its own dashboard, one a board serves, and one of the
// core alone, which has no front page of its own yet (pages/core.js: what it offers here). The navigation is the seven
// problems (pages/seven.js), each page made of the parts that solved it before; the old pages stay routable by their
// own addresses, out of the navigation, and «منتظر شما» (lead) answers /go/ addresses.
export const pageSets = {
  dashboard: [now, peoplePage, time, moneyPage, books, reportPage, between,
    ...hidden(home, lead, cases, people, followups, report, calendar, posting, vouchers, finance, chart, accounts,
      categorize, exchange, map)],
  board: [boardNow, boardMoney, boardBetween, ...hidden(boardHome, lead, boardPays, boardAgreements, boardExchange)],
  core: [core, ...hidden(lead)],
};
export const pages = pageSets.dashboard;
export const actions = {...caseActions, ...leadActions, ...booksActions, ...boardActions};
