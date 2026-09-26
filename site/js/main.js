/* 入口：路由 + 顶栏 + 全局事件 */

import { $ } from './dom.js';
import { PROBLEMS, order, orderIdx, applyTheme, applyLangPref, toggleTheme, updateProgressChip } from './state.js';
import { buildSidebar, highlightSidebar, openDay } from './sidebar.js';
import { initSearch, hideResults } from './search.js';
import { renderHome } from './home.js';
import { renderProblem } from './problem.js';

/* ---------- 路由 ---------- */
function route() {
  const m = location.hash.match(/^#\/p\/(.+)$/);
  closeSidebarMobile();
  hideResults();
  if (m && PROBLEMS[m[1]]) {
    openDay(PROBLEMS[m[1]].day);
    buildSidebar();
    renderProblem(m[1]);
    highlightSidebar(m[1]);
  } else {
    buildSidebar();
    renderHome();
  }
}

/* ---------- 移动端侧栏 ---------- */
function closeSidebarMobile() {
  $('sidebar').classList.remove('open');
  $('overlay').classList.remove('show');
}

/* ---------- 初始化 ---------- */
applyTheme();
applyLangPref();
updateProgressChip();
buildSidebar();
initSearch();

window.addEventListener('hashchange', route);
route();

$('themeBtn').addEventListener('click', toggleTheme);
$('menuBtn').addEventListener('click', () => {
  $('sidebar').classList.toggle('open');
  $('overlay').classList.toggle('show');
});
$('overlay').addEventListener('click', closeSidebarMobile);

/* Esc 关闭弹层；题目页 ← / → 切换上下一题 */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { hideResults(); closeSidebarMobile(); return; }
  if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
  const m = location.hash.match(/^#\/p\/(.+)$/);
  if (!m) return;
  const idx = orderIdx[m[1]];
  if (e.key === 'ArrowLeft' && idx > 0) location.hash = '#/p/' + order[idx - 1];
  if (e.key === 'ArrowRight' && idx < order.length - 1) location.hash = '#/p/' + order[idx + 1];
});
