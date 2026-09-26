/* 侧边栏：按天分组的题目导航 */

import { h, $ } from './dom.js';
import { PROBLEMS, DAYS, isDone, dayDone, problemLabel } from './state.js';

const openDays = {};

export function openDay(n) { openDays[n] = true; }

export function buildSidebar() {
  const nav = $('sidebarNav');
  nav.innerHTML = '';
  DAYS.forEach(day => {
    const group = h('div', 'day-group');
    group.dataset.n = day.n;
    if (openDays[day.n]) group.classList.add('open');

    const head = h('button', 'day-head');
    head.appendChild(h('span', null, day.title));
    head.appendChild(h('span', 'day-count', `${dayDone(day)}/${day.problems.length}`));
    head.appendChild(h('span', 'chev', '▶'));
    head.addEventListener('click', () => {
      openDays[day.n] = !openDays[day.n];
      group.classList.toggle('open', !!openDays[day.n]);
    });
    group.appendChild(head);

    const list = h('div', 'day-list');
    day.problems.forEach(pid => {
      const p = PROBLEMS[pid];
      if (!p) return;
      const a = h('a', 'prob-link');
      a.href = '#/p/' + pid;
      a.dataset.pid = pid;
      a.appendChild(h('span', 'prob-num', problemLabel(p)));
      a.appendChild(h('span', 'prob-title-text', p.name));
      if (isDone(pid)) a.appendChild(h('span', 'prob-done', '✓'));
      list.appendChild(a);
    });
    group.appendChild(list);
    nav.appendChild(group);
  });
}

/** 高亮当前题目，自动展开所在天并滚动到可见位置 */
export function highlightSidebar(pid) {
  const links = $('sidebarNav').querySelectorAll('.prob-link');
  for (const link of links) {
    const on = link.dataset.pid === pid;
    link.classList.toggle('active', on);
    if (on) {
      const group = link.closest('.day-group');
      if (group) {
        if (!group.classList.contains('open')) {
          openDays[+group.dataset.n] = true;
          group.classList.add('open');
        }
        link.scrollIntoView({ block: 'nearest' });
      }
    }
  }
}
