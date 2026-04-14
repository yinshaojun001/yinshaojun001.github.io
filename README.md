# yinshaojun001.github.io

这是博客的 **Hugo 源码工程**。

## 当前目标

- 把旧的静态发布产物仓库恢复为可维护的 Hugo 项目
- 重建首页、文章页、About 页和归档页
- 通过 GitHub Actions 自动发布到 GitHub Pages
- 尽量把历史文章迁回 Markdown 内容源

## 本地开发

需要：

- Hugo Extended
- Python 3（用于迁移脚本与测试）

本地预览：

```bash
hugo server -D
```

生产构建：

```bash
hugo --minify
```

## 结构说明

- `content/`：Markdown 内容
- `layouts/`：Hugo 模板
- `assets/`：样式等前端资源
- `scripts/`：迁移与辅助脚本
- `docs/`：设计说明、实施计划、迁移说明

## 发布思路

后续会通过 GitHub Actions 在 push 后自动构建并发布到 GitHub Pages。
