# Legacy Migration Notes

## Source

当前旧文章来自仓库根目录下现有的静态站点目录：

- `posts/<slug>/index.html`
- `about/关于我/index.html`

## 脚本

运行方式：

```bash
.venv/bin/python scripts/migrate_legacy_posts.py --source . --dest content/posts
```

## 当前保留字段

- 标题
- 发布时间
- slug
- 正文主体

## 当前迁移结果

- 已识别并迁移旧文章 12 篇
- 再加上新工程里的示例文章，`content/posts/` 当前共有 14 个 Markdown 文件
- 迁移后的站点已通过一次 Hugo 构建验证

## About 页说明

旧站 `about/关于我/index.html` 基本只有标题和时间信息，正文内容为空，因此当前 About 页保留为新版本草稿，需要后续手工完善。

## 手动复查项

- 标签和系列
- 个别 HTML 转 Markdown 的格式细节
- 图片与 Obsidian 风格引用（如 `![[...]]`）
- About 页内容补充
