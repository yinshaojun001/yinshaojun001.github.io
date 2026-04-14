# Legacy Migration Notes

## Source

当前旧文章来自仓库根目录下现有的静态站点目录：

- `posts/<slug>/index.html`
- `about/...`

## 脚本

运行方式：

```bash
python3 scripts/migrate_legacy_posts.py --source . --dest content/posts
```

## 当前保留字段

- 标题
- 发布时间
- slug
- 正文主体

## 手动复查项

- 标签和系列
- 个别 HTML 转 Markdown 的格式细节
- About 页内容整理
