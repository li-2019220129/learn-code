/* 轻量语法高亮：支持 Java / C++ / Python / Go，零依赖 */

import { esc as escCode } from './dom.js';

const KW = {
  java: ('abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while var record true false null String List Integer Arrays Map HashMap').split(' '),
  cpp: ('alignas alignof auto bool break case catch char class const constexpr continue decltype default delete do double dynamic_cast else enum explicit extern false float for friend goto if inline int long mutable namespace new noexcept nullptr operator private protected public register return short signed sizeof static static_cast struct switch template this throw true try typedef typeid typename union unsigned using virtual void volatile while std vector string cout endl include define ifndef endif').split(' '),
  python: ('and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield self print len range list dict set tuple int float str bool sorted enumerate zip map sum min max abs').split(' '),
  go: ('break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var nil true false string int make new append').split(' '),
};

const kwSet = {};
for (const [lang, words] of Object.entries(KW)) {
  kwSet[lang] = new Set(words);
}

/* 依次匹配：注释 | 字符串 | 数字 | 标识符 */
const TOKEN_RE = /(\/\*[\s\S]*?\*\/|\/\/[^\n]*|#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\b\d[\w.]*\b)|([A-Za-z_]\w*)/g;

const LANG_NAME = { java: 'Java', cpp: 'C++', python: 'Python', go: 'Go', js: 'JavaScript', text: '示例' };

export { LANG_NAME };

/** 返回高亮后的 HTML（内部已转义）。text 语言或未知语言只做转义。 */
export function highlight(code, lang) {
  if (lang === 'text' || !kwSet[lang]) return escCode(code);
  let out = '', last = 0, m;
  TOKEN_RE.lastIndex = 0;
  while ((m = TOKEN_RE.exec(code))) {
    out += escCode(code.slice(last, m.index));
    if (m[1]) out += `<span class="tok-c">${escCode(m[1])}</span>`;
    else if (m[2]) out += `<span class="tok-s">${escCode(m[2])}</span>`;
    else if (m[3]) out += `<span class="tok-n">${escCode(m[3])}</span>`;
    else if (m[4]) {
      out += kwSet[lang].has(m[4])
        ? `<span class="tok-k">${escCode(m[4])}</span>`
        : escCode(m[4]);
    }
    last = m.index + m[0].length;
  }
  return out + escCode(code.slice(last));
}
