/* 首页：统计概览 + 55 天计划卡片 */

import { h, $ } from './dom.js';
import {
  DATA, PROBLEMS, DAYS, order, doneCount, dayDone, isDone, firstUndone,
  resetProgress,
} from './state.js';

export function renderHome() {
  const main = $('main');
  main.innerHTML = '';
  document.title = `${DATA.meta.title} · 刷题学习手册`;

  const c = h('div', 'content');
  c.appendChild(buildHero());
  c.appendChild(h('h2', 'section-title', `📅 ${DATA.meta.days} 天刷题计划`));

  const grid = h('div', 'days-grid');
  DAYS.forEach(day => grid.appendChild(buildDayCard(day)));
  c.appendChild(grid);

  const footer = h('div', 'site-footer');
  footer.appendChild(h('div', null, '内容整理自《吴师兄学算法 · LeetCode 精讲》PDF，仅供个人学习使用，版权归原作者所有。'));
  footer.appendChild(h('div', null, '⚡ 静态站点 · 数据本地渲染 · 进度保存在浏览器 localStorage'));
  c.appendChild(footer);

  main.appendChild(c);
}

function buildHero() {
  const hero = h('div', 'hero');
  hero.appendChild(h('h1', null, '⚡ ' + DATA.meta.title));
  hero.appendChild(h('p', null,
    `${DATA.meta.subtitle} —— ${DATA.meta.days} 天刷题计划，每天 3~5 道高频题，配套 Java / C++ / Python 三语言题解。`));

  const stats = h('div', 'hero-stats');
  [['天数', `${DATA.meta.days} 天`], ['题目', `${DATA.meta.problems} 题`], ['已完成', `${doneCount()} 题`]]
    .forEach(([label, value]) => {
      const s = h('div', 'hero-stat');
      s.appendChild(h('b', null, value));
      s.appendChild(h('span', null, label));
      stats.appendChild(s);
    });
  hero.appendChild(stats);

  const pct = order.length ? doneCount() / order.length * 100 : 0;
  const bar = h('div', 'hero-bar');
  const fill = h('i');
  fill.style.width = pct + '%';
  bar.appendChild(fill);
  hero.appendChild(bar);

  const btns = h('div', 'hero-btns');
  const btnGo = h('button', 'btn btn-light', '▶ 继续学习');
  btnGo.addEventListener('click', () => { location.hash = '#/p/' + firstUndone(); });
  btns.appendChild(btnGo);
  if (doneCount() > 0) {
    const btnReset = h('button', 'btn btn-ghost', '重置进度');
    btnReset.addEventListener('click', () => {
      if (confirm('确定要清空所有学习进度吗？')) {
        resetProgress();
        renderHome();
      }
    });
    btns.appendChild(btnReset);
  }
  hero.appendChild(btns);
  return hero;
}

function buildDayCard(day) {
  const card = h('div', 'day-card');
  const head = h('div', 'day-card-head');
  head.appendChild(h('h3', null, day.title));
  head.appendChild(h('span', 'day-card-problems', `${day.problems.length} 题 · 已完成 ${dayDone(day)}`));
  card.appendChild(head);

  const bar = h('div', 'day-bar');
  const fill = h('i');
  fill.style.width = (day.problems.length ? dayDone(day) / day.problems.length * 100 : 0) + '%';
  bar.appendChild(fill);
  card.appendChild(bar);

  const chips = h('div', 'day-chips');
  day.problems.forEach(pid => {
    const p = PROBLEMS[pid];
    if (!p) return;
    const chip = h('a', 'chip' + (isDone(pid) ? ' done' : ''), (p.tag === 'intro' ? '' : p.num + '. ') + p.name);
    chip.href = '#/p/' + pid;
    chips.appendChild(chip);
  });
  card.appendChild(chips);
  return card;
}
