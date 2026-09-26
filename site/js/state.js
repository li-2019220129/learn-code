/* 全局状态：题库引用、学习进度、主题、代码语言偏好（均持久化到 localStorage） */

import { $ } from './dom.js';

const LS_PROGRESS = 'algo200.progress.v1';
const LS_THEME = 'algo200.theme';
const LS_LANG = 'algo200.lang';

export const DATA = window.ALGO_DATA;
export const PROBLEMS = DATA.problems;
export const DAYS = DATA.days;

/** 题目顺序表（用于上一题/下一题与总体进度） */
export const order = [];
export const orderIdx = {};
DAYS.forEach(d => d.problems.forEach(pid => {
  if (PROBLEMS[pid]) { orderIdx[pid] = order.length; order.push(pid); }
}));

/* ---------- 学习进度 ---------- */
let progress = {};
try { progress = JSON.parse(localStorage.getItem(LS_PROGRESS) || '{}') || {}; } catch { progress = {}; }

export function isDone(pid) { return !!progress[pid]; }
export function toggleDone(pid) {
  if (progress[pid]) delete progress[pid];
  else progress[pid] = true;
  localStorage.setItem(LS_PROGRESS, JSON.stringify(progress));
  return !!progress[pid];
}
export function doneCount() { return order.filter(isDone).length; }
export function dayDone(day) { return day.problems.filter(isDone).length; }
export function resetProgress() {
  progress = {};
  localStorage.setItem(LS_PROGRESS, JSON.stringify(progress));
}
export function firstUndone() { return order.find(pid => !progress[pid]) || order[0]; }
export function updateProgressChip() {
  const n = doneCount();
  const pct = order.length ? Math.round(n / order.length * 100) : 0;
  $('progressChip').textContent = pct + '% · ' + n + '/' + order.length;
}

/* ---------- 主题 ---------- */
export let theme = localStorage.getItem(LS_THEME) ||
  (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

export function toggleTheme() {
  theme = theme === 'dark' ? 'light' : 'dark';
  applyTheme();
}
export function applyTheme() {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  $('themeBtn').textContent = theme === 'dark' ? '☀️' : '🌙';
  localStorage.setItem(LS_THEME, theme);
}

/* ---------- 代码语言偏好 ---------- */
export let langPref = localStorage.getItem(LS_LANG) || 'all';

export function setLangPref(v) {
  langPref = v;
  localStorage.setItem(LS_LANG, v);
  applyLangPref();
}
export function applyLangPref() {
  document.body.classList.remove('pref-java', 'pref-cpp', 'pref-python');
  if (langPref !== 'all') document.body.classList.add('pref-' + langPref);
  document.querySelectorAll('.lang-btn').forEach(b => {
    b.classList.toggle('on', b.dataset.lang === langPref);
  });
}

/* ---------- 题目相关工具 ---------- */
export function problemLabel(p) {
  if (p.tag === 'leetcode') return 'LC ' + p.num;
  if (p.tag === 'lcof') return '剑指 ' + p.num;
  if (p.tag === 'mianshi') return '面试 ' + p.num;
  return '前言';
}
export function problemFull(p) {
  if (p.tag === 'intro') return p.name;
  return 'LeetCode ' + p.num + ' · ' + p.name;
}
export function lcLink(p) {
  return p.url || 'https://leetcode.cn/problemset/?search=' + encodeURIComponent(p.name);
}
export function dayOf(p) { return DAYS[p.day - 1]; }
