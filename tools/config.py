# -*- coding: utf-8 -*-
"""路径与全局配置。"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_PATH = os.path.join(BASE_DIR, '0282.吴师兄学算法Leetcode精讲200题.pdf')
PASSWORD = 'WPFX.LINK'

# 生成的站点数据文件
OUTPUT_PATH = os.path.join(BASE_DIR, 'site', 'data', 'data.js')

SITE_TITLE = '算法精讲 200 题'
SITE_SUBTITLE = '吴师兄学算法 · LeetCode 精讲'
