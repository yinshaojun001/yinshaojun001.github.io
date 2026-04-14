from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import html
import re
from typing import Iterable

from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class LegacyPost:
    title: str
    date: str
    slug: str
    body_markdown: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def strip_heading_anchor_suffix(text: str) -> str:
    return re.sub(r"\[#\]\(#.*?\)", "", text).rstrip()


def html_to_markdown(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    root_nodes = soup.contents

    def render(node) -> str:
        if isinstance(node, NavigableString):
            text = str(node)
            return html.unescape(text)
        if not isinstance(node, Tag):
            return ""

        name = node.name.lower()
        if name in {"div", "section", "article"}:
            return "\n\n".join(filter(None, [render(child) for child in node.children]))
        if name == "p":
            text = "".join(render(child) for child in node.children).strip()
            return f"{text}\n"
        if name in {"h1", "h2", "h3", "h4"}:
            level = int(name[1])
            text = "".join(render(child) for child in node.children).strip()
            return f"{'#' * level} {strip_heading_anchor_suffix(text)}\n"
        if name == "ul":
            items = []
            for li in node.find_all("li", recursive=False):
                items.append(f"- {''.join(render(child) for child in li.children).strip()}")
            return "\n".join(items) + "\n"
        if name == "ol":
            items = []
            for idx, li in enumerate(node.find_all("li", recursive=False), start=1):
                items.append(f"{idx}. {''.join(render(child) for child in li.children).strip()}")
            return "\n".join(items) + "\n"
        if name == "pre":
            code = node.get_text("", strip=False).strip("\n")
            return f"```\n{code}\n```\n"
        if name == "code":
            return node.get_text("", strip=False)
        if name == "blockquote":
            text = normalize_whitespace(node.get_text("\n", strip=True))
            return "\n".join(f"> {line}" for line in text.splitlines()) + "\n"
        if name == "br":
            return "\n"
        if name == "a":
            href = node.get("href", "").strip()
            text = "".join(render(child) for child in node.children).strip() or href
            return f"[{text}]({href})" if href else text
        return "".join(render(child) for child in node.children)

    rendered = []
    for node in root_nodes:
        piece = render(node)
        if piece.strip():
            rendered.append(piece.strip())
    return normalize_whitespace("\n\n".join(rendered)) + "\n"


def parse_post_html(path: str, html_text: str) -> LegacyPost:
    soup = BeautifulSoup(html_text, "html.parser")
    title = (
        (soup.find("meta", attrs={"property": "og:title"}) or {}).get("content")
        or (soup.title.string.strip() if soup.title and soup.title.string else None)
        or Path(path).parent.name
    )
    date = (
        (soup.find("meta", attrs={"property": "article:published_time"}) or {}).get("content")
        or "1970-01-01T00:00:00+08:00"
    )
    slug = Path(path).parent.name
    content_node = soup.select_one(".post-content") or soup.find("article") or soup.body
    body_html = "".join(str(child) for child in content_node.children) if content_node else ""
    body_markdown = html_to_markdown(body_html)
    return LegacyPost(title=title.strip(), date=date.strip(), slug=slug.strip(), body_markdown=body_markdown)


def serialize_post(post: LegacyPost) -> str:
    safe_title = post.title.replace('"', '\\"')
    return (
        "+++\n"
        f'title = "{safe_title}"\n'
        f"date = {post.date}\n"
        "draft = false\n"
        f'slug = "{post.slug}"\n'
        "tags = []\n"
        "series = []\n"
        'summary = ""\n'
        "+++\n\n"
        f"{post.body_markdown.strip()}\n"
    )


def infer_summary_from_body(body: str, max_length: int = 110) -> str:
    cleaned = body
    cleaned = re.sub(r"(?m)^#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^>\s?", "", cleaned)
    cleaned = re.sub(r"(?m)^[-*+]\s+", "", cleaned)
    cleaned = normalize_whitespace(cleaned.replace("\n", " "))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rstrip() + "…"


def infer_tags_from_text(text: str) -> list[str]:
    keyword_map = [
        ("Java", [r"\bjava\b", r"\bjvm\b"]),
        ("JVM", [r"\bjvm\b", r"虚拟机"]),
        ("MySQL", [r"\bmysql\b", r"\bmvcc\b", r"\binnodb\b"]),
        ("并发", [r"并发", r"多线程", r"completablefuture", r"parallelstream"]),
        ("排障", [r"排查", r"arthas", r"问题", r"故障"]),
        ("性能优化", [r"性能", r"压测", r"负载", r"\bgc\b", r"\bqps\b", r"\btps\b"]),
        ("AI Agent", [r"\bai agent\b", r"agent engineering", r"\bagent\b.*\bai\b", r"\bai\b.*\bagent\b"]),
    ]
    haystack = text.lower()
    tags: list[str] = []
    for tag, patterns in keyword_map:
        if any(re.search(pattern, haystack) for pattern in patterns):
            tags.append(tag)
    return tags


def replace_obsidian_embeds(text: str) -> str:
    return re.sub(r"!\[\[(.*?)\]\]", r"> 历史图片占位：\1", text)


def cleanup_markdown_document(path: Path, raw: str) -> str:
    front_matter_match = re.match(r"(?s)\+\+\+\n(.*?)\n\+\+\+\n(.*)", raw)
    if not front_matter_match:
        return raw

    front_matter = front_matter_match.group(1)
    body = front_matter_match.group(2)

    body = replace_obsidian_embeds(body)
    body = body.replace("⸻", "")
    body = re.sub(r"\[#\]\(#.*?\)", "", body)
    body = re.sub(r"(?m)^[ \t]+$", "", body)
    body = normalize_whitespace(body)

    summary = infer_summary_from_body(body)
    tags = infer_tags_from_text(f"{path.stem}\n{body}")

    summary_value = summary.replace('"', '\\"')
    front_matter = re.sub(r'summary = ".*?"', f'summary = "{summary_value}"', front_matter)
    if tags:
        tags_literal = ", ".join(f'"{tag}"' for tag in tags)
        front_matter = re.sub(r"tags = \[.*?\]", f"tags = [{tags_literal}]", front_matter)

    return f"+++\n{front_matter}\n+++\n\n{body.strip()}\n"


def iter_legacy_post_files(source: Path):
    posts_dir = source / "posts"
    if not posts_dir.exists():
        return
    for child in sorted(posts_dir.iterdir()):
        if not child.is_dir() or child.name == "page":
            continue
        index_file = child / "index.html"
        if index_file.exists():
            yield index_file


def iter_markdown_posts(dest: Path) -> Iterable[Path]:
    for path in sorted(dest.glob("*.md")):
        if path.name == "_index.md":
            continue
        yield path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert legacy static HTML posts into Hugo markdown files.")
    parser.add_argument("--source", default=".", help="Root directory containing legacy HTML posts.")
    parser.add_argument("--dest", default="content/posts", help="Destination directory for markdown files.")
    parser.add_argument("--clean-existing", action="store_true", help="Clean existing markdown posts in destination.")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    if args.clean_existing:
        cleaned = 0
        for path in iter_markdown_posts(dest):
            path.write_text(cleanup_markdown_document(path, path.read_text(encoding="utf-8")), encoding="utf-8")
            cleaned += 1
            print(f"cleaned {path}")
        print(f"cleaned {cleaned} posts")
        return

    written = 0
    for index_file in iter_legacy_post_files(source):
        post = parse_post_html(str(index_file.relative_to(source)), index_file.read_text(encoding="utf-8"))
        output_path = dest / f"{post.slug}.md"
        output_path.write_text(serialize_post(post), encoding="utf-8")
        written += 1
        print(f"wrote {output_path}")

    print(f"migrated {written} posts")


if __name__ == "__main__":
    main()
