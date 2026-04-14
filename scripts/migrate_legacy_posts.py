from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import html
import re

from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class LegacyPost:
    title: str
    date: str
    slug: str
    body_markdown: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


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
            return f"{'#' * level} {text}\n"
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert legacy static HTML posts into Hugo markdown files.")
    parser.add_argument("--source", default=".", help="Root directory containing legacy HTML posts.")
    parser.add_argument("--dest", default="content/posts", help="Destination directory for markdown files.")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

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
