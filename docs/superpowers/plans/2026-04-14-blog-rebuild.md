# Blog Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `yinshaojun001.github.io` into a maintainable Hugo source project with custom key templates, GitHub Pages auto-deploy, and full legacy post migration from the current static HTML snapshot.

**Architecture:** Keep Hugo as the content engine and own the presentation layer with custom templates for the homepage, post list, post detail, about page, and taxonomy pages. Use GitHub Actions for Pages deployment, and add a Python migration utility that converts the current static HTML articles into Hugo Markdown content while preserving titles, dates, and slugs as much as possible.

**Tech Stack:** Hugo (extended), Hugo templates, CSS, GitHub Actions, Python 3, pytest

---

## Planned File Structure

### Repository / deployment

- Create: `.github/workflows/hugo.yml`
- Create: `README.md`
- Modify: `.gitignore`

### Hugo project

- Create: `hugo.toml`
- Create: `archetypes/default.md`
- Create: `content/_index.md`
- Create: `content/about/_index.md`
- Create: `content/posts/_index.md`
- Create: `content/posts/welcome-back.md`
- Create: `layouts/_default/baseof.html`
- Create: `layouts/_default/list.html`
- Create: `layouts/_default/single.html`
- Create: `layouts/_default/terms.html`
- Create: `layouts/index.html`
- Create: `layouts/partials/head.html`
- Create: `layouts/partials/header.html`
- Create: `layouts/partials/footer.html`
- Create: `layouts/partials/post-card.html`
- Create: `assets/css/main.css`

### Migration tooling

- Create: `scripts/migrate_legacy_posts.py`
- Create: `tests/test_migrate_legacy_posts.py`
- Create: `docs/migration/legacy-migration-notes.md`

### Migrated content

- Create: `content/posts/<slug>.md` for each restored article
- Modify: `content/about/_index.md` after extracting legacy about-page content

---

### Task 1: Establish the Hugo source scaffold

**Files:**
- Create: `hugo.toml`
- Create: `archetypes/default.md`
- Create: `content/_index.md`
- Create: `content/about/_index.md`
- Create: `content/posts/_index.md`
- Create: `content/posts/welcome-back.md`
- Modify: `README.md`

- [ ] **Step 1: Verify the current repo is not yet a Hugo source project**

Run:

```bash
test -f hugo.toml && echo "unexpected: hugo.toml exists" || echo "expected: hugo.toml missing"
test -d content && echo "unexpected: content exists" || echo "expected: content missing"
```

Expected:

```text
expected: hugo.toml missing
expected: content missing
```

- [ ] **Step 2: Create the minimal Hugo configuration and content roots**

Add `hugo.toml` with site metadata, taxonomies, permalink rules, menu entries, and build options:

```toml
baseURL = "https://yinshaojun001.github.io/"
languageCode = "zh-cn"
title = "尹绍钧"

[params]
  author = "尹绍钧"
  tagline = "个人介绍 + 技术输出"
  description = "以技术文章为主，兼顾个人介绍与长期积累"

[taxonomies]
  tag = "tags"
  series = "series"

[permalinks]
  posts = "/posts/:slug/"
```

Create `content/_index.md`, `content/about/_index.md`, and `content/posts/_index.md` with front matter only. Create `archetypes/default.md` for future article creation. Add `content/posts/welcome-back.md` as a seed article used for template verification.

- [ ] **Step 3: Run Hugo to verify the scaffold builds**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-scaffold
```

Expected:

```text
Build completes without config errors and writes HTML into /tmp/yinshaojun001-build-scaffold
```

- [ ] **Step 4: Document the new source-project entry point**

Update `README.md` with:

- what this repo now contains
- required Hugo version
- local preview command
- deploy overview

- [ ] **Step 5: Commit**

```bash
git add hugo.toml archetypes/default.md content README.md
git commit -m "feat: scaffold Hugo source project"
```

---

### Task 2: Build the shared layout shell and global styling

**Files:**
- Create: `layouts/_default/baseof.html`
- Create: `layouts/partials/head.html`
- Create: `layouts/partials/header.html`
- Create: `layouts/partials/footer.html`
- Create: `assets/css/main.css`

- [ ] **Step 1: Define the shared HTML shell**

Create `layouts/_default/baseof.html` with:

- `<html lang="zh-CN">`
- shared `<head>` partial
- shared header / footer partials
- a `<main>` block for page content
- a generated stylesheet from `assets/css/main.css`

- [ ] **Step 2: Create a failing build check for custom chrome**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-layout
rg "个人介绍 \\+ 技术输出" /tmp/yinshaojun001-build-layout/index.html
```

Expected before implementation:

```text
No match found because the shared shell and site copy are not yet rendered
```

- [ ] **Step 3: Implement the head, header, footer, and CSS**

Add:

- metadata + SEO defaults in `layouts/partials/head.html`
- top nav with `Home / Posts / About / Tags` in `layouts/partials/header.html`
- concise footer in `layouts/partials/footer.html`
- typography, spacing, card, list, and article styles in `assets/css/main.css`

- [ ] **Step 4: Rebuild and verify shared UI is present**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-layout
rg "Home" /tmp/yinshaojun001-build-layout/index.html
rg "Posts" /tmp/yinshaojun001-build-layout/index.html
```

Expected:

```text
Both strings appear in the generated homepage HTML
```

- [ ] **Step 5: Commit**

```bash
git add layouts assets/css/main.css
git commit -m "feat: add shared site layout and styles"
```

---

### Task 3: Implement homepage, post list, tag terms, and about-page rendering

**Files:**
- Create: `layouts/index.html`
- Create: `layouts/_default/list.html`
- Create: `layouts/_default/terms.html`
- Create: `layouts/partials/post-card.html`
- Modify: `content/_index.md`
- Modify: `content/about/_index.md`
- Modify: `content/posts/_index.md`

- [ ] **Step 1: Add page-specific content fields**

Update content front matter with fields needed by the templates:

```yaml
title: "首页"
hero_title: "技术写作与长期积累"
hero_intro: "以文章为主，个人介绍作为辅助入口。"
```

Use similar front matter for About and Posts list pages.

- [ ] **Step 2: Verify homepage sections are currently missing**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-home
rg "最新文章" /tmp/yinshaojun001-build-home/index.html
```

Expected before template implementation:

```text
No match found
```

- [ ] **Step 3: Implement the custom homepage**

Create `layouts/index.html` to render:

- hero block with short personal positioning
- latest posts section
- featured tags / topics area
- compact personal summary card linking to `/about/`

Use `layouts/partials/post-card.html` for reusable article cards.

- [ ] **Step 4: Implement list and terms pages**

Create `layouts/_default/list.html` to render:

- posts archive page
- about page body
- future list pages with a consistent layout

Create `layouts/_default/terms.html` for tags overview and tag term cards.

- [ ] **Step 5: Rebuild and verify key routes**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-home
test -f /tmp/yinshaojun001-build-home/index.html
test -f /tmp/yinshaojun001-build-home/posts/index.html
test -f /tmp/yinshaojun001-build-home/about/index.html
test -f /tmp/yinshaojun001-build-home/tags/index.html
rg "最新文章" /tmp/yinshaojun001-build-home/index.html
```

Expected:

```text
All pages exist and the homepage contains 最新文章
```

- [ ] **Step 6: Commit**

```bash
git add layouts content
git commit -m "feat: implement homepage and list pages"
```

---

### Task 4: Implement post detail rendering and the long-form writing baseline

**Files:**
- Create: `layouts/_default/single.html`
- Modify: `archetypes/default.md`
- Modify: `content/posts/welcome-back.md`
- Modify: `assets/css/main.css`

- [ ] **Step 1: Define the article front matter shape**

Update `archetypes/default.md` to include:

```yaml
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
date: {{ .Date }}
draft: true
tags: []
series: []
summary: ""
slug: ""
```

- [ ] **Step 2: Create a failing article-route verification**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-single
test -f /tmp/yinshaojun001-build-single/posts/welcome-back/index.html
rg "目录" /tmp/yinshaojun001-build-single/posts/welcome-back/index.html
```

Expected before implementation:

```text
The page may build, but article-specific presentation markers like 目录 / metadata layout are not present yet
```

- [ ] **Step 3: Implement the single-post template**

Create `layouts/_default/single.html` with:

- title
- publish date
- tags / series display
- optional table of contents
- article content
- prev / next navigation if available

Extend `assets/css/main.css` for article typography, code blocks, blockquotes, and metadata rows.

- [ ] **Step 4: Expand the seed article for verification**

Update `content/posts/welcome-back.md` with:

- meaningful title
- tags
- summary
- headings and code block content for visual testing

- [ ] **Step 5: Build and verify article rendering**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-single
test -f /tmp/yinshaojun001-build-single/posts/welcome-back/index.html
rg "welcome-back" /tmp/yinshaojun001-build-single/sitemap.xml
```

Expected:

```text
The article page exists and appears in the sitemap
```

- [ ] **Step 6: Commit**

```bash
git add layouts/_default/single.html archetypes/default.md content/posts/welcome-back.md assets/css/main.css
git commit -m "feat: add article template baseline"
```

---

### Task 5: Add automated GitHub Pages deployment

**Files:**
- Create: `.github/workflows/hugo.yml`
- Modify: `README.md`
- Modify: `hugo.toml`

- [ ] **Step 1: Check that no Pages workflow exists yet**

Run:

```bash
test -f .github/workflows/hugo.yml && echo "unexpected: workflow exists" || echo "expected: workflow missing"
```

Expected:

```text
expected: workflow missing
```

- [ ] **Step 2: Add the GitHub Actions workflow**

Create `.github/workflows/hugo.yml` that:

- triggers on pushes to `main`
- installs Hugo extended
- runs `hugo --minify`
- uploads the build artifact
- deploys to GitHub Pages

Use the official GitHub Pages deployment pattern rather than committing generated HTML to the source branch.

- [ ] **Step 3: Align configuration with Actions deployment**

Adjust `hugo.toml` for production-safe settings such as:

- canonical base URL
- enable `relativeURLs = false`
- enable `canonifyURLs = false`

- [ ] **Step 4: Document the publishing flow**

Update `README.md` with:

- local preview: `hugo server -D`
- production build: `hugo --minify`
- publish model: push to `main`, let Actions deploy
- GitHub Pages repo settings that must be enabled

- [ ] **Step 5: Validate workflow syntax locally**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
path = Path(".github/workflows/hugo.yml")
assert path.exists(), "workflow missing"
text = path.read_text()
assert "actions/configure-pages" in text
assert "hugo --minify" in text
print("workflow contains required actions")
PY
```

Expected:

```text
workflow contains required actions
```

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/hugo.yml README.md hugo.toml
git commit -m "ci: add GitHub Pages deployment workflow"
```

---

### Task 6: Build and test the legacy HTML migration utility

**Files:**
- Create: `scripts/migrate_legacy_posts.py`
- Create: `tests/test_migrate_legacy_posts.py`
- Create: `docs/migration/legacy-migration-notes.md`

- [ ] **Step 1: Write the failing tests for HTML-to-Markdown extraction**

Create `tests/test_migrate_legacy_posts.py` with focused tests for:

- title extraction from legacy article HTML
- publish-date extraction
- article body extraction
- slug inference from directory name
- Markdown serialization with front matter

Example:

```python
def test_extract_title_from_legacy_post():
    html = "<html><head><meta property='og:title' content='示例文章'></head></html>"
    post = parse_post_html("posts/example/index.html", html)
    assert post.title == "示例文章"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
pytest -q tests/test_migrate_legacy_posts.py
```

Expected:

```text
FAIL because parse_post_html and serialization helpers do not exist yet
```

- [ ] **Step 3: Implement the migration script minimally**

Create `scripts/migrate_legacy_posts.py` with:

- `parse_post_html(path: str, html: str) -> LegacyPost`
- `html_to_markdown(fragment: str) -> str`
- `serialize_post(post: LegacyPost) -> str`
- `main()` that scans legacy HTML post directories and writes Markdown into `content/posts/`

Keep the parser narrow and explicit. Prefer:

- `html.parser` or `BeautifulSoup` if already available
- deterministic slug handling
- conservative fallback behavior for missing fields

- [ ] **Step 4: Re-run tests until they pass**

Run:

```bash
pytest -q tests/test_migrate_legacy_posts.py
```

Expected:

```text
All migration tests pass
```

- [ ] **Step 5: Add operator notes**

Write `docs/migration/legacy-migration-notes.md` covering:

- where legacy HTML comes from
- how to run the migration script
- what fields are preserved
- what must be manually checked after import

- [ ] **Step 6: Commit**

```bash
git add scripts/migrate_legacy_posts.py tests/test_migrate_legacy_posts.py docs/migration/legacy-migration-notes.md
git commit -m "feat: add legacy post migration tool"
```

---

### Task 7: Migrate the legacy posts and about-page content

**Files:**
- Modify: `content/about/_index.md`
- Create: `content/posts/<slug>.md` for each migrated post
- Modify: `docs/migration/legacy-migration-notes.md`

- [ ] **Step 1: Take inventory of legacy content before writing**

Run:

```bash
find posts -mindepth 1 -maxdepth 1 -type d ! -name page | sort
```

Expected:

```text
A deterministic list of legacy post directories to migrate
```

- [ ] **Step 2: Run the migration utility**

Run:

```bash
python3 scripts/migrate_legacy_posts.py --source . --dest content/posts
```

Expected:

```text
Markdown files are generated under content/posts for each legacy post
```

- [ ] **Step 3: Restore the About page**

Extract the current legacy About page content into `content/about/_index.md`, preserving:

- personal introduction
- profile details
- any contact / profile links still relevant

- [ ] **Step 4: Spot-check the migrated files**

Run:

```bash
ls content/posts | wc -l
sed -n '1,40p' content/posts/my-first-post.md
sed -n '1,40p' content/about/_index.md
```

Expected:

```text
The post count roughly matches the legacy inventory and the Markdown files contain front matter + readable body text
```

- [ ] **Step 5: Build the site and verify legacy routes**

Run:

```bash
hugo --destination /tmp/yinshaojun001-build-migrated
test -f /tmp/yinshaojun001-build-migrated/posts/my-first-post/index.html
```

Expected:

```text
Migrated posts render as Hugo pages
```

- [ ] **Step 6: Commit**

```bash
git add content/about/_index.md content/posts docs/migration/legacy-migration-notes.md
git commit -m "feat: migrate legacy posts into Hugo content"
```

---

### Task 8: Verify the rebuilt site, clean docs, and prepare cutover

**Files:**
- Modify: `README.md`
- Modify: `docs/migration/legacy-migration-notes.md`
- Modify: `docs/superpowers/specs/2026-04-14-blog-rebuild-design.md` (only if implementation decisions materially differ)

- [ ] **Step 1: Run the full build verification**

Run:

```bash
hugo --minify --destination /tmp/yinshaojun001-build-final
test -f /tmp/yinshaojun001-build-final/index.html
test -f /tmp/yinshaojun001-build-final/posts/index.html
test -f /tmp/yinshaojun001-build-final/about/index.html
test -f /tmp/yinshaojun001-build-final/tags/index.html
```

Expected:

```text
All critical routes build successfully
```

- [ ] **Step 2: Verify migrated-content count and route presence**

Run:

```bash
find content/posts -maxdepth 1 -name '*.md' | wc -l
rg "/posts/" /tmp/yinshaojun001-build-final/sitemap.xml | head
```

Expected:

```text
The content count is non-trivial and sitemap entries include migrated posts
```

- [ ] **Step 3: Update operator documentation**

Finalize `README.md` with:

- install / preview / build / deploy instructions
- how to create a new post
- where to edit the homepage
- where to edit the About page

Finalize migration notes with any manual cleanup still pending.

- [ ] **Step 4: Manual smoke test checklist**

Open locally with:

```bash
hugo server -D
```

Check:

- homepage article cards
- posts archive
- migrated article layout
- about page content
- tag pages
- mobile-width readability

- [ ] **Step 5: Commit**

```bash
git add README.md docs/migration/legacy-migration-notes.md docs/superpowers/specs/2026-04-14-blog-rebuild-design.md
git commit -m "docs: finalize blog rebuild operator guidance"
```

---

## Execution Notes

- Keep commits small and aligned with the task boundaries above.
- Do not delete the legacy static snapshot until the migrated Hugo site has been built and checked successfully.
- If GitHub Pages currently points to `master`, switch it to the GitHub Actions workflow only after the rebuilt site is validated on `main`.
- If permalink compatibility requires aliases, add them during Task 7 while inspecting migrated slugs.
- If Hugo is missing locally, install it before Task 1:

```bash
brew install hugo
```

## References

- Spec: `docs/superpowers/specs/2026-04-14-blog-rebuild-design.md`
