+++
title = "superpowers 实战经验"
date = 2026-03-22T22:30:00+08:00
draft = false
slug = "superpowers-experience"
tags = ["AI", "Agent", "Superpowers", "开发工具", "工程化"]
series = []
summary = "Superpowers 是一个 Agentic Skills Framework，把工程纪律编码为 AI 的行为约束。"
+++

![图片](/images/wechat/superpowers-experience/image_0.jpg)

调研时间：2026-03-21
项目地址：https://github.com/obra/superpowers
当前热度：今日新增 2,078 stars，强势登顶 GitHub Trending。"Agentic Skills Framework" 或将定义下一代 AI 原生开发方法论，值得密切关注其技能规范与社区采纳度。

## 一、它是什么

Superpowers 是一个 Agentic Skills Framework——把「如何做软件开发」这件事本身，编码成可复用的结构化技能包，让 AI Agent 强制遵循工程最佳实践。

### 核心洞察

> AI coding assistant 的瓶颈不是模型能力，而是缺乏纪律性。

没有框架约束时，AI 往往会：

- 跳过测试，直接开写实现
- 过度工程化，添加没有要求的功能
- 遗忘之前的设计决策
- 凭感觉输出，质量参差不齐

Superpowers 的解法：把「好的开发纪律」打包成技能，强制 Agent 走标准流程。

## 二、核心概念：Skill

Skill 不只是一段 Prompt，而是一个完整的工作流单元，包含四个关键要素：

| 要素 | 说明 |
|------|------|
| 触发条件 | 何时调用这个 Skill |
| 执行步骤 | 强制的操作序列，带 `<HARD-GATE>` 标记，不可跳过 |
| 质量门控 | 每步完成后的验证机制 |
| 移交协议 | 完成后如何交接给下一个 Skill |

### 与普通 Prompt 的本质区别

普通 Prompt：
```
"帮我写代码" → AI 直接输出 → 质量随机
```

Skill 工作流：
```
触发 → 澄清需求 → 拆解任务 → TDD 实现 → 双重 Review → 收尾
每步设有检查点，不达标不允许进入下一环节
```

## 三、7 个核心技能（完整工作流）

```
用户描述需求
    ↓
brainstorming               澄清需求，禁止跳过，每次只问一个问题
    ↓
using-git-worktrees         创建隔离分支，保护主工作区
    ↓
writing-plans               拆成 2-5 分钟的小任务，含完整代码和测试命令
    ↓
subagent-driven-development 派 subagent 执行 + 双重 Review
    ↓
test-driven-development     红 → 绿 → 重构循环
    ↓
requesting-code-review      对照原始 Spec 验证实现
    ↓
finishing-a-development-branch  Merge / PR 收尾
```

额外技能：
- **systematic-debugging** — 根因分析，禁止凭感觉猜测
- **dispatching-parallel-agents** — 独立任务并行分发执行
- **verification-before-completion** — 禁止在无证据的情况下声称「已完成」

## 四、实际体验：一次完整执行记录

以「扫描目录 .md 文件并生成 Obsidian 索引」为例，全程由 Superpowers 驱动：

### Step 1：Brainstorming

触发 brainstorming Skill 后，AI 没有直接写代码，而是：

1. 先读取当前项目文件，理解上下文（发现是 Obsidian 双链格式的文档库）
2. 逐一澄清关键问题：
   - 索引给谁看？→ Obsidian 双链格式
   - 覆盖现有文件还是新建？→ 新建 INDEX.md
   - 每个文件显示什么信息？→ H1 标题 + 所有 H2 标题列表

> `<HARD-GATE>`：在设计方案获得用户明确批准之前，禁止编写任何代码。

### Step 2：Writing Plans

AI 生成完整实现计划，保存至 `docs/superpowers/plans/`：

- 共 4 个子任务，每个任务预计耗时 2-5 分钟
- 每步包含：完整代码片段、运行命令、预期输出
- TDD 顺序严格执行：先写测试 → 确认失败 → 写实现 → 确认通过

### Step 3：Subagent-Driven Development

每个任务派一个独立 Subagent 执行，流程如下：

```
Task N 开始
  ↓ implementer subagent：实现功能 + 自我 Review
  ↓ spec reviewer subagent：实现是否符合规格？
  ↓ 不符合 → 修复 → 重新 Review（最多 3 轮）
  ↓ code quality reviewer subagent：代码质量是否达标？
  ↓ 不达标 → 修复 → 重新 Review
  ↓ 两项均通过 → Task 标记完成
```

> 双重 Review 顺序不可颠倒：必须先通过 Spec Review，再进行 Quality Review。

## 五、五大设计原则

### 1. HARD-GATE 强制门控

关键节点设置硬性检查点，条件未满足则流程中止。例如：

> 「在用户明确批准设计方案之前，禁止调用任何实现技能、编写任何代码、搭建任何项目结构。无论任务看起来多么简单，这条规则一律适用。」

### 2. 子 Agent 上下文隔离

每个 Subagent 获得精确构造的上下文，而非继承主会话的完整历史。核心优势：

- 避免上下文污染与信息干扰
- Subagent 专注于当前子任务
- 主会话不被实现细节撑爆

### 3. 证据先于结论

verification-before-completion Skill 的核心约束：

> 禁止在未实际运行命令、未亲眼看到输出的情况下，声称「完成了」或「测试通过了」。

### 4. TDD 不可绕过

写测试 → 确认失败 → 写实现 → 确认通过，每一步都是必须执行的操作序列，而非可选建议。

### 5. YAGNI + DRY + 简单优先

计划阶段主动删除「可能用到」的功能，拒绝为假设性的未来需求过度设计。

## 六、与 OpenSpec 的对比

| 维度 | Superpowers | OpenSpec |
|------|-------------|----------|
| 本质定位 | Agent 行为工作流约束 | 需求规格持久化系统 |
| 核心产物 | 结构化执行流程 | `openspec/` 规格文件 |
| 上下文持久性 | 会话内有效 | 跨会话、跨团队共享 |
| 适合场景 | 单次开发任务的流程纪律 | 长期项目、团队协作 |
| 安装方式 | CLI Plugin | Repo 内创建目录 |
| GitHub Stars | ~3k（快速增长中） | ~28k |

> 两者可以配合使用：OpenSpec 管理「做什么」（需求规格），Superpowers 管理「怎么做」（执行流程），形成完整的 AI 辅助开发体系。

![图片](/images/wechat/superpowers-experience/image_1.png)

## 七、安装方式

| CLI 工具 | 安装命令 |
|----------|---------|
| Claude Code | `/plugin install superpowers@claude-plugins-official` |
| Cursor | `/add-plugin superpowers` |
| Gemini CLI | `gemini extensions install https://github.com/obra/superpowers` |

安装完成后执行 `/reload-plugins` 激活技能。

## 八、适用场景评估

**适合使用：**
- 需要 AI 稳定产出高质量代码的场景
- 多步骤、高复杂度的功能开发
- 团队希望统一 AI 编码行为与质量标准
- 对代码质量有明确要求，不接受「能跑就行」

**不适合使用：**
- 快速原型验证、一次性脚本（流程相对偏重）
- 极简修改（单行 Bug Fix 不需要走完整 7 步流程）
- 纯探索性代码，需求完全未明确

## 九、总结

Superpowers 代表了一个值得重点关注的趋势方向：把工程纪律编码为 AI 的行为约束，而非依赖提示词质量或模型自身能力的随机发挥。

它的价值不在于让 AI 变得更聪明，而在于让 AI 更可预期、更值得信赖——这或许正是 AI 进入生产级工程实践的必经之路。
