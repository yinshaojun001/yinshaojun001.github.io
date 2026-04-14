from pathlib import Path

from scripts.migrate_legacy_posts import html_to_markdown, parse_post_html, serialize_post


def test_extract_title_from_legacy_post():
    html = """
    <html>
      <head>
        <meta property="og:title" content="示例文章标题">
        <meta property="article:published_time" content="2025-06-24T08:58:00+08:00">
      </head>
      <body>
        <article class="post-single">
          <div class="post-content"><p>第一段内容</p><h2>小节</h2><p>第二段内容</p></div>
        </article>
      </body>
    </html>
    """
    post = parse_post_html("posts/example/index.html", html)
    assert post.title == "示例文章标题"


def test_extract_publish_date_and_slug_from_legacy_post():
    html = """
    <html>
      <head>
        <meta property="og:title" content="另一个标题">
        <meta property="article:published_time" content="2024-11-01T09:10:00+08:00">
      </head>
      <body>
        <article><div class="post-content"><p>正文</p></div></article>
      </body>
    </html>
    """
    post = parse_post_html("posts/mysql_事务与mvcc行为详解/index.html", html)
    assert post.date == "2024-11-01T09:10:00+08:00"
    assert post.slug == "mysql_事务与mvcc行为详解"


def test_convert_html_fragment_to_markdown():
    html = "<p>第一段</p><h2>标题</h2><ul><li>项目一</li><li>项目二</li></ul><pre><code>hugo server -D</code></pre>"
    markdown = html_to_markdown(html)
    assert "第一段" in markdown
    assert "## 标题" in markdown
    assert "- 项目一" in markdown
    assert "```" in markdown
    assert "hugo server -D" in markdown


def test_serialize_post_to_markdown_document():
    html = "<p>正文内容</p>"
    post = parse_post_html(
        "posts/example/index.html",
        f"""
        <html>
          <head>
            <meta property=\"og:title\" content=\"示例文章标题\">
            <meta property=\"article:published_time\" content=\"2025-06-24T08:58:00+08:00\">
          </head>
          <body>
            <article><div class=\"post-content\">{html}</div></article>
          </body>
        </html>
        """,
    )
    document = serialize_post(post)
    assert 'title = "示例文章标题"' in document
    assert 'slug = "example"' in document
    assert 'date = 2025-06-24T08:58:00+08:00' in document
    assert "正文内容" in document
