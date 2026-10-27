#!/usr/bin/env python3
"""Repo Wiki 静态文档站构建脚本。

用法（先执行 pip install -r wiki-site/requirements.txt）:
    python build.py               # 全流程：同步 .qoder 内容 → 转换链接 → 生成 mkdocs.yml → 构建 → 后处理
    python build.py sync          # 仅同步 .qoder Wiki 内容到 docs/
    python build.py links         # 仅执行 file:// → 相对路径转换
    python build.py config        # 仅重新生成 mkdocs.yml（nav 保持目录层级）
    python build.py postprocess   # 仅对 site/ 产物做外部链接重写
    python build.py deploy        # 仅同步构建产物到仓库根 docs/（GitHub Pages 分支部署）

两套目录互不干扰：
- .qoder/repowiki/zh/content/ 由 Qoder 后台独占维护（不入库）；
- wiki-site/docs/ 是文档站自己的文档源目录（入库），每次构建从 .qoder 全量同步并在
  此完成链接转换，绝不回写 .qoder。

GitHub Pages 部署：构建完成后会把 wiki-site/site/ 同步到仓库根 docs/（入库），
Pages 设置选择「Deploy from a branch」→ main + /docs 即可。
"""
from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Match

import yaml

ROOT = Path(__file__).resolve().parent.parent  # 仓库根目录
CONTENT = ROOT / ".qoder" / "repowiki" / "zh" / "content"  # Qoder Wiki 内容目录（只读来源）
WIKI_DIR = ROOT / "wiki-site"  # 文档站工程目录
DOCS_DIR = WIKI_DIR / "docs"  # 文档站自己的文档源目录（入库，与 .qoder 互不干扰）
SITE_DIR = WIKI_DIR / "site"  # 构建产物目录
REPO_DOCS = ROOT / "docs"  # GitHub Pages 分支部署目录（仓库根 /docs）
MKDOCS_YML = WIKI_DIR / "mkdocs.yml"

# GitCode 源码浏览地址：文档站中指向仓库源码文件的链接统一重写到这里
GITCODE_BLOB_BASE = "https://gitcode.com/jiashaoying/quant-ai/blob/main"

FILE_LINK_RE = re.compile(r"\]\((file://[^)\s\"<]+)\)")

# 文档站首页（由 prepare_docs 写入 content 目录，避免被 Wiki 同步进程清理）
INDEX_MD = """# quant-ai 项目文档

欢迎来到**股票量化策略查看与回测系统**的 Repo Wiki 文档站。

本系统提供 8 种内置量化策略、5 个数据源（含智能降级）与完整的回测引擎，前端 React 可视化展示回测结果。

## 快速导航

- [项目概述](项目概述.md) — 系统功能与项目结构总览
- [快速开始](快速开始.md) — 安装依赖、启动服务与首个回测
- [回测系统](回测系统.md) — 回测引擎与绩效指标说明
- [系统架构](系统架构/系统架构.md) — 前后端架构与数据流设计
- [量化策略](量化策略/量化策略.md) — 8 种内置策略详解
- [API参考文档](API参考文档/API参考文档.md) — 后端 REST 接口规范
"""


def sync_docs() -> None:
    """把 Qoder Wiki 内容全量同步到 docs/ 文档源目录。

    .qoder/ 由 Qoder 后台独占维护（不入库）；docs/ 是文档站自己的源目录（入库）。
    每次构建先清空 docs/ 再整体复制，保证 Qoder 的增删改不会在 docs/ 留下过期文件，
    且本脚本绝不回写 .qoder。
    """
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    shutil.copytree(CONTENT, DOCS_DIR)
    n = sum(1 for _ in DOCS_DIR.rglob("*.md"))
    print(f"[sync] 已同步 {n} 个文档到 docs/")


def prepare_docs() -> None:
    """生成 MkDocs 构建所需的附加文件（首页与自定义样式），写入 docs/。"""
    (DOCS_DIR / "index.md").write_text(INDEX_MD, encoding="utf-8")
    css_dir = DOCS_DIR / "stylesheets"
    css_dir.mkdir(exist_ok=True)
    shutil.copyfile(WIKI_DIR / "extra.css", css_dir / "extra.css")
    print("[prepare] 已生成 docs/index.md 与 docs/stylesheets/extra.css")


def fix_file_links() -> None:
    """把 docs/ 中的 file:// 引用链接转换为相对 Markdown 链接（GitCode 网页中可直接点击）。"""
    converted = missing = 0
    for md in sorted(DOCS_DIR.rglob("*.md")):
        text = md.read_text(encoding="utf-8")

        def _replace(match: Match) -> str:
            nonlocal converted, missing
            raw = match.group(1)  # 形如 file://backend/main.py#L9-L27
            path = raw[len("file://"):].strip("/")
            anchor = ""
            if "#" in path:
                path, anchor = path.split("#", 1)
                anchor = "#" + anchor
            target = (ROOT / path).resolve()
            if not target.exists():
                missing += 1
            rel = os.path.relpath(target, md.parent).replace(os.sep, "/")
            converted += 1
            return f"]({rel}{anchor})"

        new_text = FILE_LINK_RE.sub(_replace, text)
        if new_text != text:
            md.write_text(new_text, encoding="utf-8")
    print(f"[links] 转换 {converted} 个 file:// 链接（其中目标缺失 {missing} 个）")


def _nav_entries(dir_path: Path) -> list:
    """为一个目录生成导航条目：节索引页置首，其余文件、子目录保持层级。"""
    entries = []
    index_md = dir_path / f"{dir_path.name}.md"
    if index_md.exists():
        entries.append({index_md.stem: str(index_md.relative_to(DOCS_DIR))})
    for child in sorted(dir_path.iterdir(), key=lambda p: p.name):
        if child.name.startswith(".") or child == index_md or child.name == "index.md":
            continue
        if child.is_dir():
            entries.append({child.name: _nav_entries(child)})
        elif child.suffix == ".md":
            entries.append({child.stem: str(child.relative_to(DOCS_DIR))})
    return entries


def generate_mkdocs_config() -> None:
    """按 docs 目录层级生成 mkdocs.yml（导航与目录结构一一对应）。"""
    nav = []
    if (DOCS_DIR / "index.md").exists():
        nav.append({"首页": "index.md"})
    # 总览类页面优先，其余顶层文件按名称排序
    for preferred in ("项目概述", "快速开始", "回测系统"):
        f = DOCS_DIR / f"{preferred}.md"
        if f.exists():
            nav.append({preferred: str(f.relative_to(DOCS_DIR))})
    for f in sorted(p for p in DOCS_DIR.iterdir() if p.is_file() and p.suffix == ".md"):
        if f.name == "index.md" or f.stem in {"项目概述", "快速开始", "回测系统"}:
            continue
        nav.append({f.stem: str(f.relative_to(DOCS_DIR))})
    for d in sorted(p for p in DOCS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")):
        nav.append({d.name: _nav_entries(d)})

    nav_text = yaml.safe_dump(nav, allow_unicode=True, sort_keys=False)
    indent_nav = "\n".join("  " + line for line in nav_text.splitlines())
    config = f"""# 本文件由 wiki-site/build.py 生成，请勿手工编辑 nav 部分
site_name: quant-ai 量化策略查看系统文档
site_description: 股票量化策略查看与回测系统（Repo Wiki）静态文档站
docs_dir: docs
site_dir: site
theme:
  name: material
  language: zh
  features:
    - navigation.indexes
    - navigation.top
    - navigation.sections
    - content.code.copy
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-night
        name: 切换至深色模式
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-sunny
        name: 切换至浅色模式
extra_css:
  - stylesheets/extra.css
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tasklist:
      custom_checkbox: true
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true
plugins:
  - search
validation:
  links:
    not_found: ignore
    absolute_links: ignore
    unrecognized_links: ignore
nav:
{indent_nav}
"""
    MKDOCS_YML.write_text(config, encoding="utf-8")
    print(f"[config] 已生成 {MKDOCS_YML.relative_to(ROOT)}")


def build_site() -> None:
    """调用 mkdocs 构建静态站。"""
    print("[build] 运行 mkdocs build ...")
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-f", str(MKDOCS_YML)],
        cwd=WIKI_DIR,
        check=True,
    )


def post_process_site() -> None:
    """把站点中指向仓库源码文件的相对链接重写为 GitCode blob URL。

    MkDocs 会原样保留指向 docs_dir 之外的相对链接，但这些链接的层级是相对
    源 md 文件计算的；同时站内链接已被 MkDocs 改写为相对 HTML 页面的层级。
    因此：先在 HTML 层级解析，命中站点内文件则保留；否则回到源 md 层级
    解析，命中仓库文件则重写为 GitCode 源码浏览地址。
    """
    if not SITE_DIR.exists():
        print("[post] site 目录不存在，跳过")
        return
    rewritten = kept = 0
    for f in sorted(SITE_DIR.rglob("*.html")):
        changed = False
        # HTML 页面 ↔ 源 md 的映射（use_directory_urls: page.md → page/index.html）
        try:
            rel_site = f.relative_to(SITE_DIR)
        except ValueError:
            continue
        md_file = None
        if rel_site.name == "index.html":
            parent = rel_site.parent
            candidate = DOCS_DIR / (parent.with_suffix(".md") if str(parent) != "." else Path("index.md"))
            if candidate.exists():
                md_file = candidate
        md_dir = md_file.parent if md_file else None

        def _rewrite(match: Match) -> str:
            nonlocal rewritten, kept, changed
            raw_href = match.group(1)
            if not raw_href or raw_href.startswith(
                ("#", "http://", "https://", "mailto:", "javascript:", "data:")
            ):
                kept += 1
                return match.group(0)
            # 锚点保持原样，仅解码路径部分（中文路径在 HTML 中是百分号编码的）
            path_part, anchor_part = raw_href, ""
            if "#" in raw_href:
                path_part, anchor_part = raw_href.split("#", 1)
                anchor_part = "#" + anchor_part
            path_decoded = urllib.parse.unquote(html.unescape(path_part))
            if not path_decoded:
                return match.group(0)
            # 1) 在站点 HTML 层级解析：命中 → 站内链接，保持不变
            target_html = (f.parent / path_decoded).resolve()
            if target_html.exists():
                kept += 1
                return match.group(0)
            # 2) 回到源 md 层级解析：命中仓库文件 → 重写为 GitCode 源码浏览地址
            if md_dir:
                target_md = (md_dir / path_decoded).resolve()
                try:
                    rel = target_md.relative_to(ROOT)
                except ValueError:
                    return match.group(0)
                if target_md.exists():
                    rewritten += 1
                    changed = True
                    url = f"{GITCODE_BLOB_BASE}/{urllib.parse.quote(rel.as_posix())}{anchor_part}"
                    return f'href="{html.escape(url, quote=True)}"'
            return match.group(0)

        text = re.sub(r'href="([^"]+)"', _rewrite, f.read_text(encoding="utf-8"))
        if changed:
            f.write_text(text, encoding="utf-8")
    print(f"[post] 重写 {rewritten} 个仓库文件链接（保留 {kept} 个站内/外部链接）")


def deploy_docs() -> None:
    """把构建产物同步到仓库根 docs/（供 GitHub Pages 分支部署使用）。

    GitHub Pages 的「Deploy from a branch」只认仓库根 / 或 /docs 两个位置，
    因此将 site/ 整体复制到根级 docs/ 并入库。每次构建先清空再复制，保持幂等。
    """
    if REPO_DOCS.exists():
        shutil.rmtree(REPO_DOCS)
    shutil.copytree(SITE_DIR, REPO_DOCS)
    # GitHub Pages 分支部署默认会跑 Jekyll 构建，加 .nojekyll 跳过（站点已是纯静态产物）
    (REPO_DOCS / ".nojekyll").write_text("", encoding="utf-8")
    n = sum(1 for _ in REPO_DOCS.rglob("*.html"))
    print(f"[deploy] 已同步构建产物到 docs/（{n} 个 HTML）")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "sync"):
        sync_docs()
    if mode in ("all", "links"):
        fix_file_links()
    if mode in ("all", "prepare"):
        prepare_docs()
    if mode in ("all", "config"):
        generate_mkdocs_config()
    if mode in ("all", "build"):
        build_site()
    if mode in ("all", "postprocess"):
        post_process_site()
    if mode in ("all", "deploy"):
        deploy_docs()
    if mode == "all":
        print(f"✅ 文档站构建完成：{SITE_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
