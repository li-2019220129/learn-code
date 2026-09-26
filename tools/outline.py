# -*- coding: utf-8 -*-
"""PDF 书签结构 -> 天 / 题目 / 小节 的解析。"""
import re

from .textnorm import norm, clean_title

DAY_RE = re.compile(r'^第.{1,4}天$')
LEET_RE = re.compile(r'^LeetCode\s*(\d+)\s*[、,，.．:：]?\s*(.*)$', re.I)
LCOF_RE = re.compile(r'^剑指\s*Offer\s*(\w+)\s*[、,，.．]?\s*(.*)$', re.I)
MS_RE = re.compile(r'^面试题\s*([\d.]+)\s*[、.．,，]?\s*(.*)$')
# 书签层级不统一：部分小节（一、题目描述…）被放在了题目层
SECTION_HEAD_RE = re.compile(r'^([一二三四五六七八九十]+、|#|\d+、|复杂度)')


def parse_outline(doc):
    """把 PDF 书签整理为 [天 -> 题目 -> 小节] 的三级结构。"""
    days, cur_day, cur_prob = [], None, None
    for e in doc.get_toc(simple=False):
        lvl, title, page = e[0], e[1], e[2]
        dest = e[3] if len(e) > 3 and isinstance(e[3], dict) else {}
        to = dest.get('to')
        y = float(to.y) if (to is not None and hasattr(to, 'y')) else 0.0
        if page is None or page < 1 or page > doc.page_count:
            continue
        entry = {'lvl': lvl, 'title': norm(title).strip(),
                 'page': page - 1, 'y': max(0.0, y)}

        if entry['lvl'] == 1 and DAY_RE.match(entry['title']):
            cur_day = {'n': len(days) + 1, 'title': entry['title'],
                       'page': entry['page'], 'problems': []}
            days.append(cur_day)
            cur_prob = None
        elif entry['lvl'] == 2 and cur_day is not None:
            if cur_prob is not None and SECTION_HEAD_RE.match(entry['title']):
                # 层级错位的小节，归属当前题目
                cur_prob['subs'].append({'lvl': 3, 'title': clean_title(entry['title']),
                                         'page': entry['page'], 'y': entry['y']})
            else:
                cur_prob = {'title': entry['title'], 'page': entry['page'], 'y': entry['y'],
                            'subs': [], 'day': cur_day}
                cur_day['problems'].append(cur_prob)
        elif entry['lvl'] >= 3 and cur_prob is not None:
            cur_prob['subs'].append({'lvl': entry['lvl'], 'title': clean_title(entry['title']),
                                     'page': entry['page'], 'y': entry['y']})
    return days


def problem_meta(raw_title):
    """从书签标题解析 (题号, 题名, 类型)。类型: leetcode / lcof / mianshi / intro"""
    m = LEET_RE.match(raw_title)
    if m:
        return m.group(1), m.group(2).strip(' 、,，.．-—'), 'leetcode'
    m = LCOF_RE.match(raw_title)
    if m:
        return m.group(1), m.group(2).strip(' 、,，.．-—'), 'lcof'
    m = MS_RE.match(raw_title)
    if m:
        return m.group(1).rstrip('.'), m.group(2).strip(' 、,，.．-—'), 'mianshi'
    return None, clean_title(raw_title), 'intro'


def problem_id_prefix(num, tag):
    if tag == 'leetcode':
        return 'lc' + str(num)
    if tag == 'lcof':
        return 'offer' + str(num)
    if tag == 'mianshi':
        return 'ms' + str(num)
    return 'extra'
