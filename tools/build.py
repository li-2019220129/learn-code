# -*- coding: utf-8 -*-
"""构建入口：PDF -> site/data/data.js。用法: python -m tools.build"""
import json
import os

import pymupdf

from . import config
from .outline import parse_outline
from .problem import ProblemParser


def main():
    doc = pymupdf.open(config.PDF_PATH)
    if doc.needs_pass:
        assert doc.authenticate(config.PASSWORD), 'PDF 解密失败，请检查 tools/config.py 中的密码'
    print(f'PDF 页数: {doc.page_count}')

    days = parse_outline(doc)
    n_probs = sum(len(d['problems']) for d in days)
    print(f'解析目录: {len(days)} 天, {n_probs} 道题目')

    problems = ProblemParser(doc, day_titles=[d['title'] for d in days]).parse_all(days)
    order = [p['pid'] for d in days for p in d['problems']]

    data = {
        'meta': {
            'title': config.SITE_TITLE,
            'subtitle': config.SITE_SUBTITLE,
            'days': len(days),
            'problems': len(order),
        },
        'days': [{'n': d['n'], 'title': d['title'],
                  'problems': [p['pid'] for p in d['problems']]} for d in days],
        'problems': {pid: problems[pid] for pid in order},
    }

    os.makedirs(os.path.dirname(config.OUTPUT_PATH), exist_ok=True)
    with open(config.OUTPUT_PATH, 'w', encoding='utf-8') as f:
        js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        f.write('window.ALGO_DATA=' + js + ';\n')

    size_mb = os.path.getsize(config.OUTPUT_PATH) / 1024 / 1024
    print(f'已生成 {config.OUTPUT_PATH} ({size_mb:.2f} MB)')

    # 统计
    n_code, langs = 0, {}
    for pr in problems.values():
        for s in pr['sections']:
            for b in s['blocks']:
                if b['t'] == 'code':
                    n_code += 1
                    langs[b['lang']] = langs.get(b['lang'], 0) + 1
    n_url = sum(1 for pr in problems.values() if pr['url'])
    print(f'代码块 {n_code} 个 (语言分布: {langs}), 带 LeetCode 链接 {n_url} 题')


if __name__ == '__main__':
    main()
