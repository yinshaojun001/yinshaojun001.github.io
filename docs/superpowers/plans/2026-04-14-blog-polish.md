# Blog Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the rebuilt blog by formalizing the About page, doing a first-pass cleanup across all migrated legacy posts, and upgrading the homepage presentation without changing the content model.

**Architecture:** Keep the existing Hugo structure intact and focus this iteration on three narrow slices: content prose in `content/about/_index.md`, batch content cleanup in `content/posts/*.md`, and homepage/template styling updates in `content/_index.md`, `layouts/index.html`, and `assets/css/main.css`.

**Tech Stack:** Hugo, Markdown, Hugo templates, CSS, Python 3, pytest

---

## Planned File Structure

- Modify: `content/about/_index.md`
- Modify: `content/_index.md`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`
- Modify: `content/posts/*.md`
- Modify: `scripts/migrate_legacy_posts.py` (only if cleanup automation is needed)
- Create: `tests/test_post_cleanup.py` (if scripted cleanup is introduced)

---

### Task 1: Replace the About draft with the approved hybrid bio

**Files:**
- Modify: `content/about/_index.md`

- [ ] Write the approved v2 About copy into `content/about/_index.md`
- [ ] Run `hugo --destination /tmp/yinshaojun001-about-check`
- [ ] Verify `/tmp/yinshaojun001-about-check/about/index.html` exists and includes `Java 后端工程师` and `AI Agent`
- [ ] Commit with `git commit -m "content: refine about page narrative"`

---

### Task 2: Do a first-pass cleanup across migrated legacy posts

**Files:**
- Modify: `content/posts/*.md`
- Optionally modify: `scripts/migrate_legacy_posts.py`
- Optionally create: `tests/test_post_cleanup.py`

- [ ] Inspect a representative sample of migrated posts and identify repeated cleanup patterns
- [ ] Apply a consistent first-pass cleanup across all migrated posts:
  - remove `⸻`
  - remove or replace `![[...]]`
  - normalize headings / list spacing
  - add basic `summary`
  - add initial `tags`
- [ ] If automation is introduced, write a failing test first, run it, then implement cleanup logic
- [ ] Run `hugo --destination /tmp/yinshaojun001-post-cleanup-check`
- [ ] Spot-check at least 3 cleaned posts in generated HTML
- [ ] Commit with `git commit -m "content: clean migrated legacy posts"`

---

### Task 3: Upgrade homepage copy and presentation

**Files:**
- Modify: `content/_index.md`
- Modify: `layouts/index.html`
- Modify: `assets/css/main.css`

- [ ] Update homepage content fields to better express the author identity and transition direction
- [ ] Refine homepage template sections: hero, author card, latest posts, topic section
- [ ] Improve CSS for a more distinctive but still restrained brand feel
- [ ] Run `hugo --destination /tmp/yinshaojun001-home-polish`
- [ ] Verify homepage contains the refined identity messaging and latest-posts section
- [ ] Commit with `git commit -m "feat: polish homepage presentation"`

---

### Task 4: Final verification

**Files:**
- Modify docs only if behavior materially changed

- [ ] Run `.venv/bin/pytest -q tests/test_migrate_legacy_posts.py`
- [ ] Run `hugo --minify --destination /tmp/yinshaojun001-polish-final`
- [ ] Verify key routes still exist: `/`, `/posts/`, `/about/`, `/tags/`
- [ ] Commit any final doc touch-ups if needed

---

## References

- Spec: `docs/superpowers/specs/2026-04-14-blog-polish-design.md`
