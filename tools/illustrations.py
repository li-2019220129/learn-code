# -*- coding: utf-8 -*-
"""图解提取：把 PDF 页面里的矢量绘图/内嵌图聚类成图解区域，渲染为站点图片。

思路：
1. 每页收集「图形元素」——过滤掉页面背景、整页布局容器、行内代码底色芯片、
   分隔细线后，剩下的圆圈/箭头/色块/内嵌图就是图解的组成部件；
2. 部件按垂直间距聚合成图解簇（cluster）；
3. 与代码行重叠的簇视为代码框边框，丢弃；
4. 渲染簇的外包矩形（加边距）为 WebP/JPG，插入到正文流的原始位置。
"""
import os

import pymupdf

DPI = 140
PAD = 8.0            # 渲染边距
GAP = 20.0           # 聚类垂直间距阈值
ABSORB_PAD = (20.0, 8.0)   # 吸收文字标签的水平/垂直外扩量
MIN_INK_RATIO = 0.025      # 非白像素占比低于此值视为空白误提取

# 单个元素过滤阈值
MIN_ELEM_HEIGHT = 14.0     # 行内代码芯片、下划线等矮元素
MIN_ELEM_AREA = 60.0       # 零星小点
# 簇过滤阈值
MIN_CLUSTER_HEIGHT = 30.0
MIN_CLUSTER_AREA = 3000.0
SINGLE_ELEM_AREA = 8000.0  # 单个大内嵌图自成图解
MAX_CLUSTER_RATIO = 0.85   # 高度超过页高比例的簇视为可疑容器


class IllustrationExtractor:
    def __init__(self, doc, line_extractor, out_dir):
        self.doc = doc
        self.lines = line_extractor
        self.out_dir = out_dir
        self._cache = {}       # page -> clusters
        self._rendered = {}    # cluster id -> src 相对路径
        self._seq = {}         # pid -> 已渲染序号
        self.stats = {'clusters': 0, 'rendered': 0, 'bytes': 0}

    # ---------- 簇的发现 ----------

    def clusters_in_region(self, start, end=None):
        """收集 [start, end) 区域内的图解簇，按 (page, y) 排序。
        会剔除与代码行重叠的簇。"""
        p1, y1 = start
        p2, y2 = end if end else (self.doc.page_count - 1, None)
        result = []
        for pi in range(p1, p2 + 1):
            for c in self._page_clusters(pi):
                if pi == p1 and c['rect'].y1 < y1:
                    continue
                if end and pi == p2 and c['rect'].y0 >= y2:
                    continue
                c = dict(c, page=pi)
                result.append(c)
        return result

    def _page_clusters(self, pi):
        if pi in self._cache:
            return self._cache[pi]
        page = self.doc[pi]
        page_rect = page.rect
        elements = []

        for d in page.get_drawings():
            r = d['rect'] & page_rect          # 裁掉页面外的隐藏内容
            if r.is_empty or r.width < 1 or r.height < 1:
                continue
            if r.height < MIN_ELEM_HEIGHT or r.width * r.height < MIN_ELEM_AREA:
                continue
            if r.width * r.height > 0.5 * page_rect.width * page_rect.height:
                continue                        # 页面背景 / 整页布局容器
            elements.append(r)

        for info in page.get_image_info():
            r = pymupdf.Rect(info['bbox']) & page_rect
            if r.is_empty or r.height < MIN_ELEM_HEIGHT or r.width * r.height < MIN_ELEM_AREA:
                continue
            if r.width * r.height > 0.5 * page_rect.width * page_rect.height:
                continue
            elements.append(r)

        clusters = self._cluster(elements)
        # 与代码行重叠的簇是代码框边框，丢弃
        code_rects = [pymupdf.Rect(l['x0'], l['y'], l['x0'] + 1, l['y'] + max(l['size'] * 1.3, 12))
                      for l in self.lines.page_lines(pi) if l['code']]
        kept = []
        for c in clusters:
            r = c['rect']
            if r.height > MAX_CLUSTER_RATIO * page_rect.height:
                continue
            if any(r.intersects(cr) for cr in code_rects):
                continue
            kept.append(c)
        self._cache[pi] = kept
        return kept

    @staticmethod
    def _cluster(rects):
        """垂直间距近、水平范围相邻的元素合并为一簇。"""
        if not rects:
            return []
        rects = sorted(rects, key=lambda r: (r.y0, r.x0))
        groups = []
        cur = [rects[0]]
        cur_rect = pymupdf.Rect(rects[0])
        for r in rects[1:]:
            if r.y0 <= cur_rect.y1 + GAP and r.x0 < cur_rect.x1 + 40 and r.x1 > cur_rect.x0 - 40:
                cur.append(r)
                cur_rect |= r
            else:
                groups.append((cur, cur_rect))
                cur, cur_rect = [r], pymupdf.Rect(r)
        groups.append((cur, cur_rect))

        out = []
        for elems, rect in groups:
            if rect.height < MIN_CLUSTER_HEIGHT or rect.width * rect.height < MIN_CLUSTER_AREA:
                if not (len(elems) == 1 and rect.width * rect.height >= SINGLE_ELEM_AREA
                        and rect.height >= 40 and rect.width >= 80):
                    continue
            out.append({'rect': rect, 'count': len(elems)})
        return out

    # ---------- 文字标签吸收 ----------

    @staticmethod
    def absorbs(cluster, ln):
        """该文本行是否属于图解内部（节点数字、指针名等标签）。"""
        r = cluster['rect']
        dx, dy = ABSORB_PAD
        cy = ln['y'] + max(ln['size'] * 0.65, 4)
        return (r.x0 - dx <= ln['x0'] <= r.x1 + dx
                and r.y0 - dy <= cy <= r.y1 + dy)

    # ---------- 渲染 ----------

    def ensure_rendered(self, cluster, page, pid):
        """渲染簇为图片文件，返回站点相对路径。"""
        key = (cluster['rect'].x0, cluster['rect'].y0, page)
        if key in self._rendered:
            return self._rendered[key]
        seq = self._seq.get(pid, 0) + 1
        self._seq[pid] = seq
        rect = cluster['rect'] + (-PAD, -PAD, PAD, PAD)
        pix = self.doc[page].get_pixmap(clip=rect, dpi=DPI, alpha=False)
        rel = f'images/{pid}/{seq:02d}-p{page + 1}.webp'
        try:
            data = pix.tobytes('webp')
        except (ValueError, RuntimeError):
            rel = rel[:-5] + '.jpg'
            data = pix.tobytes('jpeg', jpg_quality=82)
        if self._ink_ratio(pix) < MIN_INK_RATIO:
            self.stats['skipped_blank'] = self.stats.get('skipped_blank', 0) + 1
            return None
        path = os.path.join(self.out_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        self.stats['rendered'] += 1
        self.stats['bytes'] += len(data)
        self._rendered[key] = rel
        return rel

    @staticmethod
    def _ink_ratio(pix):
        """非白像素占比（隔行采样加速）。"""
        w, h, n = pix.width, pix.height, pix.n
        buf = pix.samples
        total = kept = 0
        step = max(1, (w * h) // 40000)      # 采样约 4 万个像素
        for i in range(0, w * h, step):
            off = i * n
            r, g, b = buf[off], buf[off + 1], buf[off + 2]
            total += 1
            if r < 235 or g < 235 or b < 235:
                kept += 1
        return kept / total if total else 0.0
