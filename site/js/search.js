/* 顶栏搜索：题号 / 题名 / 正文关键词 */

import { h, esc, $ } from './dom.js';
import { PROBLEMS, order, dayOf, problemFull, isDone } from './state.js';

const index = {};
order.forEach(pid => {
  const p = PROBLEMS[pid];
  const texts = [];
  p.sections.forEach(s => s.blocks.forEach(b => { if (b.x) texts.push(b.x); }));
  index[pid] = ((p.num || '') + ' ' + p.name + ' ' + texts.join(' ')).toLowerCase();
});

let timer = null;

export function initSearch() {
  const input = $('searchInput');
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => doSearch(input.value), 120);
  });
  input.addEventListener('focus', () => { if (input.value) doSearch(input.value); });
  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) hideResults();
  });
}

export function hideResults() {
  $('searchResults').classList.add('hidden');
  $('searchResults').innerHTML = '';
}

export function doSearch(q) {
  const box = $('searchResults');
  q = q.trim().toLowerCase();
  if (!q) { hideResults(); return; }

  const results = [];
  order.forEach(pid => {
    const p = PROBLEMS[pid];
    const label = problemFull(p).toLowerCase();
    let score = -1, snippet = '';
    if (p.num && p.num === q) score = 100;
    else if (label.startsWith(q)) score = 90;
    else if (label.includes(q)) score = 70;
    else {
      const pos = index[pid].indexOf(q);
      if (pos >= 0) {
        score = 30;
        snippet = index[pid].slice(Math.max(0, pos - 20), pos + 50).replace(/\s+/g, ' ');
      }
    }
    if (score > 0) results.push({ pid, score, snippet });
  });
  results.sort((a, b) => b.score - a.score);
  renderResults(box, q, results.slice(0, 20));
}

function renderResults(box, q, results) {
  box.innerHTML = '';
  if (!results.length) {
    box.appendChild(h('div', 'search-empty', `没有找到「${q}」相关的题目`));
  }
  const escRe = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
  results.forEach(r => {
    const p = PROBLEMS[r.pid];
    const a = h('a', 'search-item');
    a.href = '#/p/' + r.pid;
    const t = h('div');
    let titleHtml = esc(problemFull(p));
    if (r.score >= 70) titleHtml = titleHtml.replace(escRe, '<mark>$1</mark>');
    t.innerHTML = `<span class="si-title">${titleHtml}</span><span class="si-meta">` +
      `${dayOf(p) ? dayOf(p).title : ''}${isDone(r.pid) ? ' · 已完成' : ''}</span>`;
    a.appendChild(t);
    if (r.snippet) {
      const sn = h('div', 'si-snippet');
      sn.innerHTML = esc('…' + r.snippet + '…').replace(escRe, '<mark>$1</mark>');
      a.appendChild(sn);
    }
    box.appendChild(a);
  });
  box.classList.remove('hidden');
}
