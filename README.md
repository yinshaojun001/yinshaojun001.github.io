
# ✨ yinshaojun001.github.io

这是我的个人技术博客，使用 [Hugo](https://gohugo.io/) + GitHub Pages 搭建，托管于 `master` 分支。

📍 在线访问地址 👉 [https://yinshaojun001.github.io](https://yinshaojun001.github.io)

---

## 🚀 技术栈

- [Hugo](https://gohugo.io/) - 一款快速、现代的静态网站生成器
- GitHub Pages - 静态站点托管
- SSH 部署 - 使用 `deploy.sh` 脚本自动发布

---

## 🧪 本地预览

确保本地已安装 Hugo：

```bash
brew install hugo  # macOS 安装 Hugo

运行本地服务器：

hugo server

访问：http://localhost:1313

⸻

🔧 发布部署

每次更新文章后，执行以下命令一键部署：

./deploy.sh

该脚本会自动：
	•	清空 public/ 文件夹
	•	使用 Hugo 构建静态网页（包含草稿与未来文章）
	•	初始化 Git 并推送到 master 分支（SSH）

⸻

📁 目录结构

.
├── content/         # 博客文章目录（Markdown 格式）
├── layouts/         # 自定义页面布局
├── themes/          # 使用的 Hugo 主题
├── config.toml      # 网站配置文件
├── deploy.sh        # 一键部署脚本
└── public/          # Hugo 生成的静态网页（部署用）


⸻

📄 License

本博客内容遵循 MIT License 许可，欢迎引用，转载请注明出处 🙌。

---
