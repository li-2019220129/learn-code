# -*- coding: utf-8 -*-
"""文本规范化与小工具：部首字符修复、标题清理、正则模式。"""
import re
import unicodedata

# 康熙部首 / CJK 兼容字形 -> 标准汉字
RADICAL_RANGES = [(0x2E80, 0x2EFF), (0x2F00, 0x2FDF), (0xFB00, 0xFB4F)]
# CJK 部首补充区中 NFKC 不映射的简化部首，需手工映射
EXTRA_RADICALS = {
    '⻓': '长', '⻆': '角', '⻋': '车', '⻄': '西', '⻬': '齐', '⻩': '黄', '⻔': '门',
    '⻉': '贝', '⻅': '见', '⻜': '飞', '⻮': '齿', '⻛': '风', '⻢': '马',
}


def fix_char(ch):
    if ch in EXTRA_RADICALS:
        return EXTRA_RADICALS[ch]
    o = ord(ch)
    for a, b in RADICAL_RANGES:
        if a <= o <= b:
            return unicodedata.normalize('NFKC', ch)
    return ch


def norm(s):
    """统一部首字符、不间断空格、零宽字符。"""
    if not s:
        return ''
    s = s.replace('\xa0', ' ').replace('\u200b', '')
    return ''.join(fix_char(c) for c in s)


def norm_key(s):
    """标题比对用：去空白与标点。"""
    return re.sub(r'[\s#*、，,．.:：()（）]+', '', norm(s or ''))


def clean_title(t):
    t = norm(t).strip()
    t = re.sub(r'^#+\s*', '', t)
    return t.replace('**', '').strip()


# 代码块里的推广注释（原书水印），整行剔除
PROMO_RE = re.compile(
    r'(algomooc|程序员吴师兄|吴师兄学算法|www\.algomooc|微信|wzb_3377|私聊咨询|官网获取)', re.I)

# 代码注释里的 LeetCode 题目链接
LEET_URL_RE = re.compile(r'https?://leetcode\.cn/problems/([a-z0-9\-]+)/?', re.I)

# 注释样式的行：整行中文注释常被字体启发式误判为正文，需结合上下文纠正
COMMENT_RE = re.compile(r'^\s*(//+|#+|\*\s|/\*|>>>|\$\s)')

# 夹在两段代码之间的短文本，若以此开头则视为真正的说明文字，不并入代码
CODE_LABEL_RE = re.compile(
    r'^(?:Java|C\+\+|Python|Go|JavaScript|示例|输入|输出|解释|提示|其中|注意|时间|空间|复杂度|代码|动画|图)')

# 代码块中的 URL 折行尾巴（如 from-sorted-array/submissions/）
URL_TAIL_RE = re.compile(r'^[a-z0-9\-]+(?:/[a-z0-9\-./]+)+/?\s*$', re.I)
