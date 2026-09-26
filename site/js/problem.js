/* 题目页：题面 / 解析 / 多语言参考代码 / 上下一题 */

import { h, $ } from './dom.js';
import { highlight, LANG_NAME } from './highlight.js';
import {
  PROBLEMS, order, orderIdx, isDone, toggleDone, langPref, setLangPref,
  problemFull, problemLabel, lcLink, dayOf, updateProgressChip,
} from './state.js';
import { buildSidebar, highlightSidebar } from './sidebar.js';

export function renderProblem(pid) {
  const p = PROBLEMS[pid];
  if (!p) { location.hash = '#/'; return; }
  const main = $('main');
  main.innerHTML = '';
  document.title = `${problemFull(p)} · 算法精讲 200 题`;

  const c = h('div', 'content');
  c.appendChild(buildHead(p));
  if (hasCode(p)) c.appendChild(buildLangToolbar());
  c.appendChild(buildSections(p));
  c.appendChild(buildPrevNext(pid));
  c.appendChild(buildFooter(p));
  main.appendChild(c);

  window.scrollTo(0, 0);
}

function buildHead(p) {
  const c = h('div', 'content-head');

  const crumbs = h('div', 'crumbs');
  const home = h('a', null, '首页');
  home.href = '#/';
  crumbs.appendChild(home);
  crumbs.appendChild(document.createTextNode(' / ' + (dayOf(p) ? dayOf(p).title : '')));
  c.appendChild(crumbs);

  const head = h('div', 'prob-head');
  const h1 = h('h1');
  if (p.tag !== 'intro') h1.appendChild(h('span', 'lc-num', problemLabel(p)));
  h1.appendChild(document.createTextNode(p.name));
  head.appendChild(h1);

  const meta = h('div', 'meta-row');
  meta.appendChild(h('span', 'badge accent', dayOf(p) ? dayOf(p).title : ''));
  p.complexity.forEach(cx => meta.appendChild(h('span', 'badge', cx)));

  const doneBtn = h('button', 'done-btn' + (isDone(p.id) ? ' on' : ''), isDone(p.id) ? '✓ 已完成' : '标记完成');
  doneBtn.addEventListener('click', () => {
    const done = toggleDone(p.id);
    doneBtn.className = 'done-btn' + (done ? ' on' : '');
    doneBtn.textContent = done ? '✓ 已完成' : '标记完成';
    updateProgressChip();
    buildSidebar();
    highlightSidebar(p.id);
  });
  meta.appendChild(doneBtn);

  const link = h('a', 'meta-link', '↗ 在 LeetCode 打开');
  link.href = lcLink(p);
  link.target = '_blank';
  link.rel = 'noopener';
  meta.appendChild(link);

  head.appendChild(meta);
  c.appendChild(head);
  return c;
}

function hasCode(p) {
  return p.sections.some(s => s.blocks.some(b => b.t === 'code' && b.lang !== 'text'));
}

function buildLangToolbar() {
  const toolbar = h('div', 'lang-toolbar');
  toolbar.appendChild(h('span', 'lt-label', '参考代码语言：'));
  [['all', '全部'], ['java', 'Java'], ['cpp', 'C++'], ['python', 'Python']].forEach(([v, label]) => {
    const b = h('button', 'lang-btn' + (langPref === v ? ' on' : ''), label);
    b.dataset.lang = v;
    b.addEventListener('click', () => setLangPref(v));
    toolbar.appendChild(b);
  });
  return toolbar;
}

function buildSections(p) {
  const secs = h('div', 'prob-sections');
  p.sections.forEach(s => {
    const sec = h('div', 'sec');
    if (s.title) sec.appendChild(h('h2', null, s.title));
    s.blocks.forEach(b => sec.appendChild(renderBlock(b)));
    secs.appendChild(sec);
  });
  return secs;
}

function renderBlock(b) {
  if (b.t === 'p') return h('p', null, b.x);
  if (b.t === 'h') return h('h3', 'blk-h', b.x);
  if (b.t === 'note') return h('div', 'sec-note', b.x);

  /* 代码块 */
  const wrap = h('div', 'codeblock' + (b.lang !== 'text' ? ' is-code' : '') + ' lang-' + b.lang);
  const head = h('div', 'codeblock-head');
  head.appendChild(h('span', 'codeblock-lang', LANG_NAME[b.lang] || b.lang));
  const copy = h('button', 'copy-btn', '复制');
  copy.addEventListener('click', () => {
    navigator.clipboard.writeText(b.x).then(() => {
      copy.textContent = '已复制 ✓';
      setTimeout(() => { copy.textContent = '复制'; }, 1600);
    }, () => { copy.textContent = '复制失败'; });
  });
  head.appendChild(copy);
  wrap.appendChild(head);

  const pre = h('pre');
  pre.innerHTML = highlight(b.x, b.lang);
  wrap.appendChild(pre);
  return wrap;
}

function buildPrevNext(pid) {
  const idx = orderIdx[pid];
  const prev = idx > 0 ? PROBLEMS[order[idx - 1]] : null;
  const next = idx < order.length - 1 ? PROBLEMS[order[idx + 1]] : null;

  const nav = h('div', 'pn-nav');
  const pc = h(prev ? 'a' : 'div', 'pn-card prev' + (prev ? '' : ' pn-empty'));
  if (prev) {
    pc.href = '#/p/' + prev.id;
    pc.appendChild(h('div', 'pn-label', '← 上一题'));
    pc.appendChild(h('div', 'pn-title', problemFull(prev)));
  }
  nav.appendChild(pc);

  const nc = h(next ? 'a' : 'div', 'pn-card next' + (next ? '' : ' pn-empty'));
  if (next) {
    nc.href = '#/p/' + next.id;
    nc.appendChild(h('div', 'pn-label', '下一题 →'));
    nc.appendChild(h('div', 'pn-title', problemFull(next)));
  }
  nav.appendChild(nc);
  return nav;
}

function buildFooter(p) {
  const footer = h('div', 'site-footer');
  footer.appendChild(h('div', null,
    `内容整理自《吴师兄学算法 · LeetCode 精讲》PDF（原书第 ${p.page} 页起），仅供个人学习，版权归原作者所有。`));
  return footer;
}
