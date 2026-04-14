# yinshaojun001.github.io

这是博客的 **Hugo 源码工程**。

## 当前目标

- 把旧的静态发布产物仓库恢复为可维护的 Hugo 项目
- 重建首页、文章页、About 页和归档页
- 通过 GitHub Actions 自动发布到 GitHub Pages
- 尽量把历史文章迁回 Markdown 内容源

## 环境准备

需要：

- Hugo Extended（当前本地已用 0.160.1 验证）
- Python 3（用于迁移脚本与测试）

如果你要运行迁移脚本或测试，先创建虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/pip install pytest beautifulsoup4
```

## 本地开发

本地预览：

```bash
hugo server -D
```

生产构建：

```bash
hugo --minify
```

## 新增文章

新建文章：

```bash
hugo new posts/my-new-post.md
```

文章默认模板：

- `archetypes/default.md`

文章内容目录：

- `content/posts/`

## 结构说明

- `content/`：Markdown 内容
- `layouts/`：Hugo 模板
- `assets/`：样式等前端资源
- `scripts/`：迁移与辅助脚本
- `docs/`：设计说明、实施计划、迁移说明

## 常见维护入口

- 写文章：`content/posts/`
- 改首页文案：`content/_index.md`
- 改首页结构：`layouts/index.html`
- 改 About：`content/about/_index.md`
- 改全站布局与文章页：`layouts/`
- 改样式：`assets/css/main.css`

## GitHub Pages 自动发布

工作流文件：

- `.github/workflows/hugo.yml`

发布方式：

1. 把默认开发分支切到 `main`
2. 在 GitHub 仓库设置里进入 **Settings → Pages**
3. 在 **Build and deployment → Source** 选择 **GitHub Actions**
4. 之后每次 push 到 `main`，GitHub Actions 会自动构建并发布

## 迁移脚本

运行旧文章迁移：

```bash
.venv/bin/python scripts/migrate_legacy_posts.py --source . --dest content/posts
```

迁移说明：

- `docs/migration/legacy-migration-notes.md`
