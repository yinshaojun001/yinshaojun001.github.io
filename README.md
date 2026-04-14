# yinshaojun001.github.io

这是博客的 **Hugo 源码工程**，用于长期维护我的个人介绍、技术文章和持续输出。

## 仓库定位

这个仓库不是单纯的静态页面产物，而是博客的可维护源码，主要承载：

- 首页与个人品牌表达
- 技术文章内容
- About 页面与作者信息
- GitHub Pages 自动发布配置

当前博客的主方向是：

- Java 后端
- AI Agent / Agent Engineering
- 性能优化、系统排障、长期技术写作

## 技术栈与环境

本地维护这个博客主要需要：

- **Hugo Extended**：当前已用 `0.160.1` 验证
- **Python 3**：用于迁移脚本和测试

如果你要运行迁移脚本或相关测试，可以先创建本地虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/pip install pytest beautifulsoup4
```

## 本地启动

本地预览博客：

```bash
hugo server -D
```

启动后访问：

- `http://localhost:1313/`

## 本地构建检查

正式提交前建议先做一次生产构建：

```bash
hugo --minify
```

如果你还需要运行迁移脚本相关测试，可在虚拟环境中执行：

```bash
.venv/bin/python -m pytest -q
```

## 新建文章

创建一篇新文章：

```bash
hugo new posts/my-new-post.md
```

文章默认模板位于：

- `archetypes/default.md`

文章内容目录位于：

- `content/posts/`

## 常见维护入口

平时最常改动的位置如下：

- 写文章：`content/posts/`
- 改首页文案：`content/_index.md`
- 改首页结构：`layouts/index.html`
- 改 About 内容：`content/about/_index.md`
- 改列表页/全站模板：`layouts/`
- 改样式：`assets/css/main.css`
- 改站点导航与基础配置：`hugo.toml`

## 项目结构

- `content/`：Markdown 内容
- `layouts/`：Hugo 模板
- `assets/`：样式和前端资源
- `scripts/`：迁移与辅助脚本
- `tests/`：迁移脚本相关测试
- `docs/`：设计说明、计划、迁移记录

## 自动发布方式

当前博客通过 **GitHub Actions** 自动发布到 **GitHub Pages**。

工作流文件：

- `.github/workflows/hugo.yml`

当前发布分支：

- `master`

日常发布流程：

```bash
git add .
git commit -m "docs: update blog content"
git push origin master
```

只要 push 到 `master`，GitHub Actions 就会自动构建并部署站点。

## GitHub Pages 设置与查看发布结果

第一次检查或排查发布时，去 GitHub 仓库中确认：

1. 打开 **Settings → Pages**
2. 在 **Build and deployment → Source** 里选择 **GitHub Actions**

查看是否发布成功：

1. 打开仓库的 **Actions**
2. 查看工作流 **Build and deploy Hugo site**
3. 如果最新一次运行是绿色对勾，说明发布成功

线上地址：

- `https://yinshaojun001.github.io/`

## 历史文章迁移

如果需要重新运行旧文章迁移脚本：

```bash
.venv/bin/python scripts/migrate_legacy_posts.py --source . --dest content/posts
```

迁移说明参考：

- `docs/migration/legacy-migration-notes.md`
