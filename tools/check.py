#!/usr/bin/env python3
"""LoopForge 静态站点护栏：链接/锚点/重复 id/标题层级/元信息检查。

仅使用 Python 标准库，可在任意目录运行；脚本以自身位置定位仓库根目录。
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    "index.html",
    "philosophy.html",
    "modules.html",
    "sop.html",
    "mindset.html",
    "start.html",
]
STRUCTURED_PAGES = PAGES + ["404.html"]
BASE = "https://binbinao.github.io/LoopForge-Demo/"
OG_IMAGE = BASE + "assets/og-cover.png"
THEME_COLOR = "#0a0d14"
UNESCAPED_AMP = re.compile(
    r"&(?!#\d+;|#x[0-9a-fA-F]+;|amp;|lt;|gt;|quot;|apos;|nbsp;)"
)
SKIP_SCHEMES = ("http://", "https://", "//", "mailto:", "tel:", "javascript:", "data:")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self.links: list[tuple[str, str]] = []
        self.metas: dict[str, str] = {}
        self.svg_without_hidden = 0
        self.current_count = 0
        self.main_ids: list[str] = []
        self._title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}

        if "id" in a:
            self.ids.append(a["id"])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append((int(tag[1]), tag))
        if a.get("aria-current", "").lower() == "page":
            self.current_count += 1
        if tag == "main":
            self.main_ids.append(a.get("id", ""))
        if tag == "svg" and a.get("aria-hidden") != "true":
            self.svg_without_hidden += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key and a.get("content"):
                self.metas[key] = a["content"]
        if tag == "a" and "href" in a:
            self.links.append(("a", a["href"]))
        if tag == "link" and "href" in a:
            self.links.append(("link", a["href"]))
            if a.get("rel", "").lower() == "canonical":
                self.metas["canonical"] = a["href"]
        if tag == "script" and "src" in a:
            self.links.append(("script", a["src"]))

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    @property
    def title(self) -> str:
        return "".join(self._title_parts).strip()


def parse_page(name: str) -> PageParser:
    parser = PageParser()
    parser.feed((ROOT / name).read_text(encoding="utf-8"))
    parser.close()
    return parser


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def heading_issues(headings: list[tuple[int, str]]) -> list[str]:
    issues: list[str] = []
    if not headings or headings[0][0] != 1:
        issues.append("首个标题不是 h1")
    if sum(1 for level, _ in headings if level == 1) != 1:
        issues.append("h1 不等于 1 个")
    previous = 0
    for level, tag in headings:
        if previous and level > previous + 1:
            issues.append(f"{tag} 从 h{previous} 跳级")
        previous = level
    return issues


def is_external(value: str) -> bool:
    value = value.strip()
    return value.startswith(SKIP_SCHEMES) or value == "#"


def check_links(
    parsers: dict[str, PageParser],
) -> tuple[list[str], list[str]]:
    broken: list[str] = []
    bad_anchors: list[str] = []
    ids_by_page = {name: set(parser.ids) for name, parser in parsers.items()}

    for page, parser in parsers.items():
        for kind, raw in parser.links:
            value = unquote(raw.strip())
            if not value or is_external(value):
                continue
            path, sep, fragment = value.partition("#")
            if path.startswith("/"):
                continue

            if not path:
                target_page = page
            elif path in ids_by_page:
                target_page = path
            else:
                resource = ROOT / path
                if resource.exists():
                    continue
                broken.append(f"{page}: {kind} {raw} -> 文件不存在")
                continue

            if sep and fragment and fragment not in ids_by_page[target_page]:
                bad_anchors.append(
                    f"{page}: {kind} {raw} -> {target_page} 缺少 id={fragment}"
                )

    return sorted(set(broken)), sorted(set(bad_anchors))


def meta_issues(page: str, parser: PageParser) -> list[str]:
    issues: list[str] = []
    description = parser.metas.get("description", "").strip()
    canonical = BASE if page == "index.html" else BASE + page
    expected = {
        "theme-color": THEME_COLOR,
        "og:title": parser.title,
        "og:description": description,
        "og:url": canonical,
        "og:image": OG_IMAGE,
        "twitter:card": "summary_large_image",
        "twitter:image": OG_IMAGE,
    }

    if "canonical" not in parser.metas:
        issues.append("缺少 canonical")
    elif parser.metas["canonical"] != canonical:
        issues.append(f"canonical 应为 {canonical}")
    for key, expected_value in expected.items():
        actual = parser.metas.get(key, "").strip()
        if not actual:
            issues.append(f"缺少 {key}")
        elif actual != expected_value:
            issues.append(f"{key} 应为 {expected_value}")

    return issues


def main() -> int:
    parsers = {name: parse_page(name) for name in STRUCTURED_PAGES}

    broken, bad_anchors = check_links(parsers)
    duplicate_ids: list[str] = []
    heading_problems: list[str] = []
    unescaped_amps: list[str] = []
    svg_problems: list[str] = []
    missing_title_or_desc: list[str] = []
    meta_problems: list[str] = []
    current_problems: list[str] = []
    main_problems: list[str] = []

    for page, parser in parsers.items():
        for dup in duplicate_values(parser.ids):
            duplicate_ids.append(f"{page}: 重复 id={dup}")
        for issue in heading_issues(parser.headings):
            heading_problems.append(f"{page}: {issue}")
        if not parser.title or not parser.metas.get("description", "").strip():
            missing_title_or_desc.append(f"{page}: title/description 为空")
        if parser.svg_without_hidden:
            svg_problems.append(
                f"{page}: {parser.svg_without_hidden} 个 SVG 缺少 aria-hidden"
            )

        for match in UNESCAPED_AMP.finditer((ROOT / page).read_text(encoding="utf-8")):
            line = (ROOT / page).read_text(encoding="utf-8").count("\n", 0, match.start()) + 1
            unescaped_amps.append(f"{page}:{line}: 未转义 &")

        if page in PAGES:
            if parser.current_count != 1:
                current_problems.append(f"{page}: aria-current=page 数量为 {parser.current_count}")
            if parser.main_ids != ["main"]:
                main_problems.append(f"{page}: main#main 异常 -> {parser.main_ids}")
            meta_problems.extend(f"{page}: {issue}" for issue in meta_issues(page, parser))
            raw = (ROOT / page).read_text(encoding="utf-8")
            if 'rel="icon" type="image/svg+xml" href="assets/favicon.svg"' not in raw:
                meta_problems.append(f"{page}: 缺少本地 favicon 引用")

    for asset in ("assets/favicon.svg", "assets/og-cover.png"):
        if not (ROOT / asset).exists():
            broken.append(f"缺失静态资源: {asset}")

    results = [
        ("站内链接", broken),
        ("锚点", bad_anchors),
        ("重复 id", duplicate_ids),
        ("标题层级", heading_problems),
        ("未转义 &", unescaped_amps),
        ("title/description", missing_title_or_desc),
        ("6 页 head 元信息", meta_problems),
        ("aria-current", current_problems),
        ("main#main", main_problems),
        ("装饰 SVG aria-hidden", svg_problems),
    ]

    print("LoopForge site check")
    print(f"扫描页面: {', '.join(STRUCTURED_PAGES)}")
    failed = False
    for name, issues in results:
        status = "PASS" if not issues else "FAIL"
        print(f"[{status}] {name}: {len(issues)}")
        for issue in issues:
            print(f"       - {issue}")
        failed = failed or bool(issues)

    counts = {
        "断链": len(broken),
        "失效锚点": len(bad_anchors),
        "重复 id": len(duplicate_ids),
        "标题跳级": len(heading_problems),
        "未转义 &": len(unescaped_amps),
        "元信息问题": len(meta_problems)
        + len(missing_title_or_desc)
        + len(current_problems)
        + len(main_problems)
        + len(svg_problems),
    }
    print("汇总: " + " / ".join(f"{k} {v}" for k, v in counts.items()))
    print("RESULT: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
