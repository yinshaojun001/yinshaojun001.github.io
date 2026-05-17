+++
title = '本周值得关注的 5 个技术作品：Agent 工程化、Rust 终端工具与 Agent 经济的雏形'
date = 2026-05-18T11:00:00+08:00
draft = false
slug = "inshocking-picks-v2"
tags = ["精选", "AI Agent", "开源", "开发者工具", "CLI", "Zed", "Rust"]
series = ["Inshocking Picks"]
summary = "第二期 Inshocking Picks：Claude Code 技能工程化、Rust 终端 Agent、持久记忆层、Zed 1.0 发布，以及 Agent 原生支付的第一个实现。"
+++

这是 **Inshocking Picks** 的第二期。

每周从 GitHub Trending、ProductHunt、Medium 中挑选值得关注的技术作品，重点收录 AI Agent、开发者工具、CLI、自动化方向的项目和文章。

---

## 1. mattpocock/skills — Claude Code 工程化技能集

**作者**: [Matt Pocock](https://github.com/mattpocock)（Total TypeScript 作者）
**仓库**: [mattpocock/skills](https://github.com/mattpocock/skills)
**本周新增**: +17,059 stars
**技术栈**: Shell
**一句话**: 一套让 Claude Code 产出更可控、更工程化的 slash command 集合。

**解决了什么问题**: AI 编程 Agent 的最大问题不是"不会写代码"，而是"写出来的代码你不想要"——架构乱、命名随意、不符合你的领域语言。Matt Pocock 的解法是：在写代码之前，先用 `/grill-me` 让 Agent 反复追问你的意图，直到对齐；用 `CONTEXT.md` 建立项目的领域词汇表，让 Agent 用你的语言说话。

**为什么值得看**: 两个细节让我觉得这个项目想清楚了。第一，`/caveman` 命令——把 Agent 的输出压缩到最精简，声称减少 75% token 用量，同时保留技术准确性。第二，`/diagnose` 命令——强制 Agent 走"复现 → 最小化 → 假设 → 验证 → 修复"的调试流程，而不是乱猜。这两个命令背后的逻辑是：**控制 Agent 的行为比给 Agent 更多能力更重要**。

**适合谁**: 深度使用 Claude Code、对 Agent 产出质量不满意的工程师。

---

## 2. Hmbown/DeepSeek-TUI — Rust 写的终端编程 Agent

**作者**: [Hmbown](https://github.com/Hmbown)
**仓库**: [Hmbown/DeepSeek-TUI](https://github.com/Hmbown/DeepSeek-TUI)
**本周新增**: +11,303 stars
**技术栈**: Rust（94.9%）
**一句话**: 纯终端的 DeepSeek 编程 Agent，三种操作模式，OS 级沙箱，1M token 上下文。

**解决了什么问题**: Claude Code 很好，但绑定了 Anthropic 的 API。DeepSeek-TUI 做了一个类似的终端编程 Agent，但支持 DeepSeek、OpenRouter、Ollama、vLLM 等多个 provider，让你可以在不同模型之间切换，同时保持终端工作流不变。

**为什么值得看**: 三个操作模式的设计很有意思：Plan 模式（只读，不执行）、Agent 模式（每步需要确认）、YOLO 模式（全自动）。这个分级和 Claude Code 的 `--dangerously-skip-permissions` 思路一致，但做成了可以随时切换的模式。另外，Rust 写的，有 OS 级沙箱（macOS 用 Seatbelt，Linux 用 Landlock），安全性比大多数同类工具认真。

**适合谁**: 喜欢终端工具、想用 DeepSeek 或本地模型做编程 Agent 的开发者。

---

## 3. rohitg00/agentmemory — AI 编程 Agent 的持久记忆层

**作者**: [rohitg00](https://github.com/rohitg00)
**仓库**: [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory)
**本周新增**: +6,467 stars
**技术栈**: TypeScript
**一句话**: 替换 CLAUDE.md 的持久记忆系统，混合搜索 + 四层记忆架构，声称减少 92% token 用量。

**解决了什么问题**: 我之前写过 [Claude Code 的 Memory 系统](/posts/claude-code-memory-system/)，核心问题是：CLAUDE.md 有行数限制，会过时，而且每次都全量加载到上下文里。agentmemory 用一个可搜索的数据库替代它——通过 hook 自动捕获 Agent 的工具调用和会话摘要，下次启动时只注入相关的记忆片段。

**为什么值得看**: 技术架构比较扎实。搜索层用了 BM25 关键词匹配 + 向量嵌入 + 知识图谱三路融合（Reciprocal Rank Fusion），记忆分四层（工作记忆 → 情节记忆 → 语义记忆 → 程序记忆），有自动衰减和遗忘机制。51 个 MCP 工具，兼容 Claude Code、Cursor、Gemini CLI 等主流工具。在 LongMemEval-S 基准上 R@5 准确率 95.2%。

**适合谁**: 深度使用 AI 编程工具、觉得 CLAUDE.md 不够用的开发者。

---

## 4. Zed 1.0 — Atom 创始人做的 GPU 加速开源编辑器

**作者**: [Zed Industries](https://github.com/zed-industries)
**仓库**: [zed-industries/zed](https://github.com/zed-industries/zed)
**发布时间**: 2026 年 4 月 29 日
**技术栈**: Rust
**一句话**: Rust 写的 GPU 加速代码编辑器，1.0 正式发布，内置并行 Agent 和 Agent Client Protocol。

**解决了什么问题**: 现有编辑器（VS Code、Cursor）都是 Electron 架构，UI 渲染走 Web 技术栈，有性能上限。Zed 用自研的 GPU UI 引擎（GPUI）直接渲染，启动快、响应快。1.0 版本的重点是 AI 集成：并行 Agent（多个 Agent 同时跑，互不干扰）、Agent Client Protocol（ACP，让 Claude Code、Codex CLI、Cursor 等外部 Agent 直接接入 Zed）。

**为什么值得看**: ACP 是这次发布里最值得关注的东西。它把编辑器从"AI 工具的宿主"变成了"Agent 的协作界面"——外部 Agent 可以通过 ACP 读写文件、导航代码、运行工具，速度是原生的。Zed 的创始人是 Atom 和 Tree-sitter 的作者，这个团队对编辑器底层的理解比大多数人深。

**适合谁**: 对编辑器性能有要求、想在编辑器里直接跑多个 Agent 的开发者。

---

## 5. pay.sh — Agent 原生的 API 支付网关

**来源**: Solana Foundation × Google Cloud，2026 年 5 月 5 日发布
**链接**: [pay.sh](https://pay.sh)
**ProductHunt 票数**: 32,026
**一句话**: 让 AI Agent 自主发现、访问、按请求付费 API，无需账号、无需 API Key、无需订阅。

**解决了什么问题**: 现在的 AI Agent 调用 API 还是人类的方式——注册账号、填信用卡、管理 API Key。这套流程对自主 Agent 来说是障碍：Agent 不能自己注册账号，不能自己管理订阅。pay.sh 用 Solana 上的 USDC 稳定币做按请求计费，Agent 只需要一个 Solana 钱包，就能自主发现并调用 50+ API provider（包括 Google Cloud 的 Gemini、BigQuery、Vertex AI）。

**为什么值得看**: 这是"Agent 经济"从概念变成基础设施的第一个具体实现。同一周，AWS 也预览了 Amazon Bedrock AgentCore Payments（和 Coinbase、Stripe 合作）。两个大玩家同时在做这件事，说明"Agent 自主消费 API"这个需求已经到了需要解决的阶段。用区块链做支付层的逻辑也很清晰：无需账号体系，天然支持微支付，结算透明。

**适合谁**: 正在构建 Agent 系统、需要 Agent 自主调用外部 API 的开发者；对 Agent 经济方向感兴趣的人。

---

## 写在最后

这期的 5 个作品，覆盖了 Agent 工程化的几个不同层次：

- **行为控制**（mattpocock/skills）：怎么让 Agent 按你的意图工作
- **运行时**（DeepSeek-TUI）：怎么在终端里跑一个完整的编程 Agent
- **记忆层**（agentmemory）：怎么让 Agent 跨会话保持上下文
- **编辑器集成**（Zed 1.0）：怎么让编辑器成为 Agent 的协作界面
- **经济层**（pay.sh）：怎么让 Agent 自主消费资源

从工具到基础设施，Agent 工程化的栈正在一层一层补齐。

如果你有值得展示的个人技术作品，欢迎投稿。

---

*Inshocking Picks 是一个关注 AI Agent、开发者工具和个人技术作品的精选栏目。*
