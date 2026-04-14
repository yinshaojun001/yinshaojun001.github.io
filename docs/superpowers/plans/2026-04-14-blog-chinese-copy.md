# Blog Chinese Copy & README Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将博客导航与核心栏目文案统一为中文表达，并把 README 升级为与当前 `master + GitHub Actions` 发布方式一致的长期维护手册。

**Architecture:** 这次改动只触碰 Hugo 配置、首页与列表页模板，以及仓库根目录 README。实现上保持现有布局与样式不变，仅替换导航/栏目文案、补齐维护说明，并通过 Hugo 构建结果验证页面输出是否符合预期。

**Tech Stack:** Hugo, Go template, Markdown, GitHub Pages, GitHub Actions

---

## File Responsibilities

- `hugo.toml`
  - 维护主导航文案与站点级基础配置
- `layouts/index.html`
  - 维护首页的中文栏目眉标与辅助文案
- `layouts/_default/list.html`
  - 维护列表页、About 页的辅助标签文案
- `README.md`
  - 提供仓库用途、开发方式、发布方式与常用维护入口说明

### Task 1: Update Navigation Labels in Hugo Config

**Files:**
- Modify: `hugo.toml`

- [ ] **Step 1: Replace main menu labels with Chinese navigation text**

Update the menu item names from:

- `Home` → `首页`
- `Posts` → `文章`
- `About` → `关于`
- `Tags` → `标签`

- [ ] **Step 2: Review surrounding config for consistency**

Confirm the change does not alter `pageRef`, taxonomy, permalink, or deployment-related config.

- [ ] **Step 3: Commit the config change with related template work**

Use a combined commit once template copy changes are complete.

### Task 2: Localize Homepage Section Copy

**Files:**
- Modify: `layouts/index.html`

- [ ] **Step 1: Replace homepage eyebrow/section helper copy with Chinese labels**

Update:

- `Author` → `作者`
- `Writing` → `写作`
- `Focus` → `关注`
- `Journey` → `转型记录`

- [ ] **Step 2: Keep brand/technical nouns in English where appropriate**

Do not translate `GitHub`, `Email`, or `AI Agent`.

- [ ] **Step 3: Preserve existing layout structure**

Do not add or remove blocks; only adjust rendered text.

### Task 3: Localize List/About Auxiliary Copy

**Files:**
- Modify: `layouts/_default/list.html`

- [ ] **Step 1: Replace list page eyebrow copy with Chinese text**

Update:

- `Archive` → `文章归档` when `.Section == "posts"`
- `Page` → `页面` for other list pages

- [ ] **Step 2: Replace About card label**

Update:

- `Profile` → `个人信息`

- [ ] **Step 3: Keep About metadata field labels aligned with existing Chinese style**

Retain `城市 / GitHub / 邮箱 / 微信 / 公众号` as-is.

### Task 4: Rewrite README as a Practical Maintenance Guide

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Reframe README around ongoing maintenance**

Cover:

- 仓库用途
- 技术栈与依赖
- 本地预览
- 新建文章
- 常改文件入口
- 本地构建与测试
- 自动发布方式
- GitHub Pages 查看发布结果的方法

- [ ] **Step 2: Correct branch/deploy documentation**

Ensure all publishing instructions reference:

- branch: `master`
- source: `GitHub Actions`

- [ ] **Step 3: Keep commands copy-paste friendly**

Prefer short sections with explicit shell commands and file paths.

### Task 5: Verify Rendered Output

**Files:**
- Verify: `hugo.toml`
- Verify: `layouts/index.html`
- Verify: `layouts/_default/list.html`
- Verify: `README.md`

- [ ] **Step 1: Run production build**

Run:

```bash
hugo --minify --destination /tmp/yinshaojun001-chinese-copy
```

Expected:

- Hugo exits with code 0
- `/tmp/yinshaojun001-chinese-copy/index.html` exists
- `/tmp/yinshaojun001-chinese-copy/about/index.html` exists
- `/tmp/yinshaojun001-chinese-copy/posts/index.html` exists
- `/tmp/yinshaojun001-chinese-copy/tags/index.html` exists

- [ ] **Step 2: Verify key Chinese labels in rendered HTML**

Check for:

- 首页 / 文章 / 关于 / 标签
- 作者 / 写作 / 关注 / 转型记录
- 文章归档 / 页面 / 个人信息

- [ ] **Step 3: Review README for branch accuracy**

Confirm README references `master`, not `main`, for push/deploy instructions.

- [ ] **Step 4: Commit implementation**

```bash
git add hugo.toml layouts/index.html layouts/_default/list.html README.md
git commit -m "docs: localize site copy and refine maintenance guide"
```
