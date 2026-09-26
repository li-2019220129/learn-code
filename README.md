# ⚡ 算法精讲 200 题

基于《吴师兄学算法 · LeetCode 精讲》PDF 整理的**纯静态学习网站**：55 天刷题计划、231 道题解、Java / C++ / Python 三语言参考代码，零依赖、零后端，托管在 GitHub Pages。

> 内容仅供个人学习使用，版权归原书作者所有。

## ✨ 功能

- **55 天刷题计划**：按天分组的题目导航，天数折叠展开
- **题目详情**：题面 / 解析 / 三语言题解 / 复杂度分析，代码语法高亮 + 一键复制
- **语言过滤**：全部 / Java / C++ / Python 一键切换，只看想看的题解
- **搜索**：支持题号、题名、正文关键词，结果高亮
- **学习进度**：标记完成、按天/总体进度统计，保存在浏览器 localStorage
- **深色模式**：跟随系统 + 手动切换
- **键盘导航**：题目页 `←` `→` 切换上/下一题
- **响应式**：移动端侧栏抽屉

## 📁 项目结构

```
learn-code/
├── tools/                      # 构建工具（Python，从 PDF 生成站点数据）
│   ├── config.py               # 路径、密码等全局配置
│   ├── textnorm.py             # 文本规范化（部首字符修复等）
│   ├── outline.py              # PDF 书签 -> 天/题目/小节 结构
│   ├── content.py              # 页面行提取、代码/正文分块
│   ├── problem.py              # 单题解析编排
│   └── build.py                # 构建入口: python -m tools.build
├── site/                       # 纯静态站点（部署产物，无需构建）
│   ├── index.html
│   ├── css/                    # base / sidebar / home / problem
│   ├── js/                     # ES Modules: main(路由) / state / sidebar /
│   │                           #   home / problem / search / highlight / dom
│   └── data/
│       └── data.js             # 构建生成的题库数据（window.ALGO_DATA）
└── .github/workflows/
    └── deploy.yml              # GitHub Pages 自动部署
```

## 🔧 重新生成数据

改动 `tools/` 后重新生成 `site/data/data.js`：

```bash
pip install pymupdf
python -m tools.build
```

## 🚀 部署

推送到 `main` 分支后，GitHub Actions 自动把 `site/` 发布到 GitHub Pages（见 `.github/workflows/deploy.yml`），无需手动操作。

本地预览：

```bash
cd site
python -m http.server 8765
# 打开 http://127.0.0.1:8765
```
