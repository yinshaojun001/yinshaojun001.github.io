from pathlib import Path

from scripts.migrate_legacy_posts import cleanup_markdown_document, infer_tags_from_text, infer_summary_from_body


def test_cleanup_markdown_document_removes_separator_and_heading_anchor_suffixes():
    raw = """+++
title = \"Performance\"
date = 2025-07-28T11:36:08+08:00
draft = false
slug = \"performance\"
tags = []
series = []
summary = \"\"
+++

⸻

## 标题[#](#title)

正文
"""
    cleaned = cleanup_markdown_document(Path("content/posts/performance.md"), raw)
    assert "⸻" not in cleaned
    assert "[#](#title)" not in cleaned
    assert "## 标题" in cleaned


def test_cleanup_markdown_document_replaces_obsidian_embed_with_notice():
    raw = """+++
title = \"Report\"
date = 2025-07-28T11:36:08+08:00
draft = false
slug = \"report\"
tags = []
series = []
summary = \"\"
+++

![[Pasted image 20250721172208.png]]
"""
    cleaned = cleanup_markdown_document(Path("content/posts/report.md"), raw)
    assert "![[" not in cleaned
    assert "历史图片占位" in cleaned


def test_infer_summary_from_body_returns_first_meaningful_sentence():
    body = "这是第一段。\n\n第二段继续解释具体细节。"
    summary = infer_summary_from_body(body)
    assert "这是第一段" in summary
    assert len(summary) <= 120


def test_infer_tags_from_text_detects_domain_keywords():
    text = "这篇文章讨论 Java、JVM、MySQL 和性能优化。"
    tags = infer_tags_from_text(text)
    assert "Java" in tags
    assert "JVM" in tags
    assert "MySQL" in tags
    assert "性能优化" in tags


def test_infer_tags_from_text_does_not_add_ai_agent_for_unrelated_text():
    text = "这篇文章讨论性能优化、QPS、TPS 和系统负载。"
    tags = infer_tags_from_text(text)
    assert "AI Agent" not in tags


def test_infer_summary_from_body_strips_markdown_markers():
    body = "# 标题\n\n> 引用说明\n\n- 列表项一\n- 列表项二"
    summary = infer_summary_from_body(body)
    assert "#" not in summary
    assert ">" not in summary


def test_cleanup_markdown_document_rewrites_existing_summary_and_tags():
    raw = """+++
title = \"Performance\"
date = 2025-07-28T11:36:08+08:00
draft = false
slug = \"performance\"
tags = [\"AI Agent\"]
series = []
summary = \"旧摘要\"
+++

# 标题

正文讨论性能优化、QPS、TPS 和系统负载。
"""
    cleaned = cleanup_markdown_document(Path("content/posts/performance.md"), raw)
    assert 'summary = "旧摘要"' not in cleaned
    assert 'tags = ["AI Agent"]' not in cleaned


def test_infer_tags_from_text_avoids_ai_agent_false_positive():
    text = "这篇文章讨论性能优化、QPS、TPS 和系统负载，没有 agent 相关内容。"
    tags = infer_tags_from_text(text)
    assert "AI Agent" not in tags
