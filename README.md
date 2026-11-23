# LoopForge 学习中心

纯静态、零依赖的学习站点，直接由 GitHub Pages 从仓库根目录发布。

## 站点结构

- 六个页面：`index.html`、`philosophy.html`、`modules.html`、`sop.html`、`mindset.html`、`start.html`
- 站点资源：`assets/site.css`、`assets/site.js`、`assets/favicon.svg`、`assets/og-cover.png`
- 站点附属文件：`404.html`、`robots.txt`、`sitemap.xml`、`.nojekyll`
- 工程护栏：`tools/check.py`、`tools/contrast.py`、`tools/make_og.py`
- CI：`.github/workflows/site-check.yml`（PR 与 push 到 `main` 时运行）

## 本地预览

在仓库根目录执行：

```bash
python3 -m http.server 8000
```

然后访问 <http://localhost:8000/>。站点无需构建，也不要引入框架或第三方 CDN。

## 质量检查

```bash
python3 tools/check.py       # 链接/锚点/重复 id/标题层级/元信息
python3 tools/contrast.py    # --faint 小字颜色对比度
python3 tools/make_og.py     # 如需重新生成本地 1200x630 OG 图
```

`tools/check.py` 只使用 Python 标准库，可在任意目录运行；失败时退出码非 0，并列出具体文件与问题。CI 会在 PR 和 push 到 `main` 时运行前两个脚本。

## PR/MR 术语约定

- 跨平台泛称首次出现写 `PR/MR（按托管平台命名）`，之后写 `PR/MR`。
- 明确是 `gh`、`GitHub API` 等 GitHub 操作时可写 `PR`；明确 GitLab 语境可写 `MR`。
- 同一页面不得把独立的 `PR` 和 `MR` 当作同义词交替使用。
- `start.html` 以 GitHub CLI 命令为主，正文统一写 `PR`，属于平台特定用法。

## 新增一页必须同步的文件

导航与页脚目前由六个页面各自复制，新增页面时必须同步：

1. 六个页面的导航栏（含当前页 `aria-current="page"`）。
2. 六个页面的页脚。
3. 相邻文档页的“上一站 / 下一站”链接。
4. `sitemap.xml`。
5. 新页的 `title` / `description` / `canonical` / OG / Twitter / favicon 引用。
6. `tools/check.py` 中的 `PAGES` 硬编码清单。
7. 若新页使用 `.reveal`，在 `<head>` 补相同的 `<noscript>` 兜底。

## 工作流约定

- 从 `main` 切功能分支，所有改动提交到功能分支。
- 通过 PR 合并到 `main`：不直推、不强推、不自行合并。
- PR 描述需附检查脚本输出、三档宽度 `scrollWidth` 实测、对比度数值与无 JS 验证方式。

## 授权

授权待定。尚未确定开源协议，不提供 `LICENSE`，也不擅自选择 MIT / Apache / GPL 等协议。
