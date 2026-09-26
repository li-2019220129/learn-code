# -*- coding: utf-8 -*-
"""单道题目的完整解析：区域切分、小节归属、内容块组装。"""
import re

from .content import LineExtractor, build_blocks
from .outline import problem_meta, problem_id_prefix
from .textnorm import LEET_URL_RE, norm_key

# 图解 / 动画小节（原书为视频演示，文字版给提示）
ANIM_RE = re.compile(r'动画|视频')


class ProblemParser:
    def __init__(self, doc, day_titles=()):
        self.doc = doc
        self.day_titles = {norm_key(t) for t in day_titles}
        self.lines = LineExtractor(doc)

    # ---- 对外入口 ----

    def parse_all(self, days):
        """解析全部天/题目，返回 (problems 有序 dict, days 索引列表)。"""
        flat = [p for d in days for p in d['problems']]
        problems, used = {}, set()
        for i, p in enumerate(flat):
            nxt = flat[i + 1] if i + 1 < len(flat) else None
            prob = self._parse_problem(p, nxt, used)
            problems[prob['id']] = prob
        return problems

    # ---- 内部步骤 ----

    def _parse_problem(self, p, nxt, used_ids):
        start = (p['page'], p['y'])
        end = (nxt['page'], nxt['y']) if nxt else None
        lines = self.lines.lines_in_region(start, end)

        num, name, tag = problem_meta(p['title'])
        pid = self._unique_id(problem_id_prefix(num, tag), used_ids)

        subs = sorted(p['subs'], key=lambda s: (s['page'], s['y']))
        self._mark_children(subs)
        intro_lines = self._split_lines(lines, subs,
                                        skip_titles=self._skip_titles(p, subs, self.day_titles))

        url = [None]
        sections = []
        if intro_lines:
            blocks = build_blocks(intro_lines, url_out=url)
            if blocks:
                sections.append({'title': None, 'blocks': blocks})
        for s in subs:
            sub_lines = s.pop('_lines', [])
            blocks = build_blocks(sub_lines, hint=s['title'], url_out=url)
            if url[0] is None:
                for ln in sub_lines:
                    mu = LEET_URL_RE.search(ln['text'])
                    if mu:
                        url[0] = 'https://leetcode.cn/problems/' + mu.group(1) + '/'
                        break
            sections.append({'title': s['title'], 'blocks': blocks,
                             '_children': s.get('_children', False)})

        final = self._finalize_sections(sections, pdf_page=p['page'] + 1)

        prob = {
            'id': pid, 'num': num, 'tag': tag, 'name': name or p['title'],
            'day': p['day']['n'], 'url': url[0],
            'complexity': self._extract_complexity(final),
            'page': p['page'] + 1, 'sections': final,
        }
        p['pid'] = pid
        return prob

    @staticmethod
    def _unique_id(base, used_ids):
        pid, k = base, 2
        while pid in used_ids:
            pid = f'{base}-{k}'
            k += 1
        used_ids.add(pid)
        return pid

    @staticmethod
    def _skip_titles(p, subs, all_day_titles):
        """需要从正文中剔除的标题行：本题标题、所有天标题、小节标题。"""
        skip = {norm_key(p['title']), norm_key(p['day']['title'])} | all_day_titles
        for s in subs:
            skip.add(norm_key(s['title']))
        return skip

    @staticmethod
    def _mark_children(subs):
        """标记每个小节是否有更低层级的孩子（用于空小节的取舍）。"""
        for j, s in enumerate(subs):
            s['_children'] = False
            for s2 in subs[j + 1:]:
                if s2['lvl'] <= s['lvl']:
                    break
                s['_children'] = True

    @staticmethod
    def _split_lines(lines, subs, skip_titles):
        """按小节坐标把行分给各小节；小节之前的行进引言。命中的标题行丢弃。
        容差 -2pt：书签坐标偏差下宁可让个别正文行串到相邻小节，
        也不能把代码块错位到别的小节（+2pt 阈值会错位数十个代码块）。"""
        intro = []
        first = (subs[0]['page'], subs[0]['y']) if subs else None
        for ln in lines:
            key = norm_key(ln['text'])
            if not ln['code'] and key and key in skip_titles:
                continue
            if first and (ln['page'], ln['y']) < (first[0], first[1] - 2.0):
                intro.append(ln)
                continue
            owner = None
            for s in subs:
                if (ln['page'], ln['y']) >= (s['page'], s['y'] - 2.0):
                    owner = s
                else:
                    break
            if owner is None:
                intro.append(ln)
            else:
                owner.setdefault('_lines', []).append(ln)
        return intro

    @staticmethod
    def _finalize_sections(sections, pdf_page):
        """空小节处理：有孩子的父级直接丢弃；空叶子（图解/动画）替换为提示。"""
        final = []
        for s in sections:
            title, blocks = s['title'], s['blocks']
            has_content = any(b.get('x', '').strip() for b in blocks)
            if title and ANIM_RE.search(title):
                final.append({'title': title,
                              'blocks': [{'t': 'note', 'x': f'此部分为动画演示，请配合原 PDF（第 {pdf_page} 页起）学习。'}]})
                continue
            if not has_content:
                if title is None or s.get('_children'):
                    continue
                final.append({'title': title,
                              'blocks': [{'t': 'note',
                                          'x': f'此部分在原 PDF 中为图解/动画（第 {pdf_page} 页起），'
                                               f'文字版未收录，建议对照原书图示理解。'}]})
                continue
            final.append({'title': title, 'blocks': blocks})
        return final

    @staticmethod
    def _extract_complexity(sections):
        cx = []
        for s in sections:
            if s['title'] and '复杂度' in s['title']:
                for b in s['blocks']:
                    if b['t'] == 'p':
                        cx += re.findall(r'[OoΩΘ]\s*\([^)]*\)', b['x'])
        return list(dict.fromkeys(cx))[:4]
