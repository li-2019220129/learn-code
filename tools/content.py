# -*- coding: utf-8 -*-
"""页面行提取与内容块构建：正文段落 / 标题 / 代码块。"""
import re

from .textnorm import (PROMO_RE, LEET_URL_RE, COMMENT_RE, CODE_LABEL_RE,
                       URL_TAIL_RE, norm)

MONO_FONT = 'LucidaConsole'      # 代码字体
MONO_RATIO = 0.3                 # 行内等宽字符占比阈值
PROMO_URL = 'https://leetcode.cn/problems/'


def join_spans(spans):
    """按 x 间距拼接同一行的 span，间距大时补空格。"""
    parts, prev = [], None
    for s in spans:
        t = s['text']
        if prev is not None:
            gap = s['bbox'][0] - prev['bbox'][2]
            if gap > 1.0 and parts and not parts[-1].endswith(' ') and not t.startswith(' '):
                parts.append(' ')
        parts.append(t)
        prev = s
    return ''.join(parts)


class LineExtractor:
    """按页提取文本行，缓存；每行带 code 标记（等宽字体占比）。"""

    def __init__(self, doc):
        self.doc = doc
        self._cache = {}

    def page_lines(self, pi):
        if pi in self._cache:
            return self._cache[pi]
        lines = []
        for b in self.doc[pi].get_text('dict')['blocks']:
            if b.get('type') != 0:
                continue
            for l in b.get('lines', []):
                spans = [s for s in l.get('spans', []) if s['text'].strip()]
                if not spans:
                    continue
                total = sum(len(s['text']) for s in spans)
                mono = sum(len(s['text']) for s in spans if s['font'].startswith(MONO_FONT))
                lines.append({
                    'page': pi, 'y': l['bbox'][1], 'x0': l['bbox'][0],
                    'text': norm(join_spans(l.get('spans', []))).rstrip(),
                    'code': total > 0 and mono / total > MONO_RATIO,
                    'size': max(s['size'] for s in spans),
                })
        lines.sort(key=lambda x: (x['y'], x['x0']))
        self._cache[pi] = lines
        return lines

    def lines_in_region(self, start, end=None):
        """取 [start, end) 页面区域内的行，start/end = (page, y)。"""
        p1, y1 = start
        p2, y2 = end if end else (self.doc.page_count - 1, None)
        res = []
        for pi in range(p1, p2 + 1):
            for ln in self.page_lines(pi):
                if pi == p1 and ln['y'] < y1 - 2.0:
                    continue
                if end and pi == p2 and ln['y'] >= y2 - 2.0:
                    continue
                res.append(ln)
        return res


# ---------- 语言识别 ----------

def lang_from_hint(hint):
    """从书签小节标题推断语言，如 '1、Java 代码'。"""
    if not hint:
        return None
    h = hint.lower()
    if 'javascript' in h:
        return 'js'
    if 'python' in h:
        return 'python'
    if 'c++' in h or 'cpp' in h:
        return 'cpp'
    if 'java' in h:
        return 'java'
    if re.search(r'\bgo\b', h):
        return 'go'
    return None


def detect_lang(code_lines, hint=None):
    lang = lang_from_hint(hint)
    if lang:
        return lang
    body = '\n'.join(code_lines)
    if re.search(r'^\s*def\s+\w+|\bself\b|^\s*#\s', body, re.M):
        return 'python'
    if '#include' in body or 'std::' in body or 'vector<' in body or '->' in body or 'cout' in body:
        return 'cpp'
    if 'public ' in body or 'System.out' in body or 'int[]' in body:
        return 'java'
    if ';' in body and '{' in body:
        return 'java'
    return 'text'


# ---------- 块构建 ----------

def _is_new_para(prev, ln):
    if prev is None:
        return True
    t = ln['text'].strip()
    if re.match(r'^(?:[•●▪]|[(（]\d+[)）]|\d+[、.)]\s|\d+\.\s)', t):
        return True
    return ln['y'] - prev['y'] > prev['size'] * 1.7


def _reclassify(lines_):
    """紧邻代码的注释样式正文行（整行中文注释）重新归为代码行。"""
    for i, ln in enumerate(lines_):
        if ln.get('cluster'):
            continue
        if ln.get('code') or not COMMENT_RE.match(ln.get('text', '')):
            continue
        near_prev = any(x.get('code') for x in lines_[max(0, i - 3):i])
        near_next = any(x.get('code') for x in lines_[i + 1:i + 4])
        if near_prev or near_next:
            ln['code'] = True


def build_blocks(lines_, hint=None, url_out=None, pid=None, illus=None):
    """把行序列转为内容块列表：
    {t:'p'|'h'|'code'|'note'|'img', x, lang?, src?, page?}
    行流中可混入 {'cluster': 簇, 'page': 页码, 'y': y} 形式的图解标记，
    由 illus（IllustrationExtractor）按需渲染并产出 img 块。
    url_out: 可选列表，用于带回代码注释里发现的 LeetCode 链接。
    """
    _reclassify(lines_)
    blocks, para, code = [], [], []
    prev = None

    def flush_para():
        nonlocal para
        if para:
            txt = re.sub(r'\s+', ' ', ' '.join(x['text'].strip() for x in para)).strip()
            if txt:
                if len(para) == 1 and re.match(r'^#{1,4}\s+\S', txt):
                    blocks.append({'t': 'h', 'x': re.sub(r'^#{1,4}\s+', '', txt)})
                elif len(para) == 1 and re.match(r'^[一二三四五六七八九十]+、\s*\S', txt) and len(txt) < 30:
                    blocks.append({'t': 'h', 'x': txt})
                else:
                    blocks.append({'t': 'p', 'x': txt})
            para = []

    def flush_code():
        nonlocal code
        if code:
            if url_out is not None and url_out[0] is None:
                for c in code:
                    mu = LEET_URL_RE.search(c)
                    if mu:
                        url_out[0] = PROMO_URL + mu.group(1) + '/'
                        break
            body = [c for c in code if not PROMO_RE.search(c) and not LEET_URL_RE.search(c)
                    and not URL_TAIL_RE.match(c.strip())]
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            if body:
                blocks.append({'t': 'code', 'lang': detect_lang(body, hint), 'x': '\n'.join(body)})
            code = []

    for ln in lines_:
        if ln.get('cluster'):
            flush_para()
            flush_code()
            src = illus.ensure_rendered(ln['cluster'], ln['page'], pid)
            if src:
                blocks.append({'t': 'img', 'src': src, 'page': ln['page'] + 1})
            prev = None
            continue
        txt = ln['text'].strip()
        if not txt:
            flush_para()
            flush_code()
            prev = None
            continue
        if ln['code']:
            flush_para()
            code.append(ln['text'])
        else:
            flush_code()
            if _is_new_para(prev, ln):
                flush_para()
            para.append(ln)
        prev = ln
    flush_para()
    flush_code()

    return _merge_blocks(blocks)


def _merge_blocks(blocks):
    """合并：注释折行尾巴并入前代码块；空行断开的相邻同语言代码块。"""
    out = []
    for idx, b in enumerate(blocks):
        if (b['t'] == 'p' and out and out[-1]['t'] == 'code'
                and idx + 1 < len(blocks) and blocks[idx + 1]['t'] == 'code'
                and len(b['x']) < 90 and not CODE_LABEL_RE.match(b['x'])):
            out[-1]['x'] += '\n' + b['x']
        else:
            out.append(b)
    merged = []
    for b in out:
        if (b['t'] == 'code' and merged and merged[-1]['t'] == 'code'
                and merged[-1]['lang'] == b['lang']):
            merged[-1]['x'] += '\n\n' + b['x']
        else:
            merged.append(b)
    return merged
