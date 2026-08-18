+++
title = "从 Prompt 到任务图：Agent 工程的五次控制权迁移"
date = 2026-08-18T09:00:00+08:00
draft = false
slug = "prompt-context-harness-loop-graph-engineering"
author = "尹绍钧"
tags = ["AI Agent", "Prompt Engineering", "Context Engineering", "Harness Engineering", "Loop Engineering", "Graph Engineering"]
summary = "从 Prompt 到 Graph 的 Agent 工程拆解：上下文装配、工具调用、权限与状态、任务循环、可持久化图编排，逐层解释它们各自在运行时做什么。"
+++

# 从 Prompt 到任务图：Agent 工程的五次控制权迁移

这两年，Agent 圈子里连续冒出几个词：Prompt Engineering、Context Engineering、Harness Engineering、Loop Engineering，最近又常有人谈 Graph。

它们看起来像一条接力赛：提示词过时了，上下文接班；上下文不够，Harness 接班；再往后是 Loop 和 Graph。这个讲法顺口，但很容易把工程问题讲糊涂。

我自己的理解恰好相反。它们没有替代关系，而是在回答不同尺度的问题：一条指令怎么写，一次模型调用带什么信息，一个 Agent 如何运行，一个任务怎样持续推进，以及一组任务如何协作。

把这几个层次混在一起，常见结果是两种。一种是给一个不稳定的 Agent 再加几百行 Prompt；另一种是刚做两个工具调用，就急着上多 Agent、上图编排。前者把运行时问题归咎于表达，后者用复杂度掩盖了任务边界不清。

这篇文章不打算给这些词排一个权威时间表。它们本来就来自不同社区，出现和流行的时间也有交叉。本文只沿着一个 Agent 系统从简单到复杂的路径，讲清楚每一层到底在管什么，什么时候该加，什么时候不该加。

先给出一个总览：

| 层次 | 它要回答的问题 | 直接管理的对象 | 工程产物 |
| --- | --- | --- | --- |
| Prompt | 模型该如何理解任务 | 指令与输出约束 | Prompt 模板、示例、Schema |
| Context | 这次调用该让模型看到什么 | 上下文窗口 | RAG、记忆、工具描述、压缩策略 |
| Harness | Agent 怎样稳定、安全地运行 | Agent 运行时 | 工作空间、权限、Hook、状态、日志 |
| Loop | 谁来持续触发、检查并推进任务 | 长周期任务 | 触发器、验收器、预算、重试与退出条件 |
| Graph | 多个角色和分支怎样协作 | 状态与依赖关系 | 节点、边、路由、检查点、可观测性 |

它们可以画成这样：

```text
一条指令
  Prompt
    ↓
一次 LLM 调用的有效信息
  Context
    ↓
一个可恢复、可约束的 Agent 运行时
  Harness
    ↓
一个会自行推进、知道何时停下的任务
  Loop
    ↓
多个任务、Agent 与人工关口组成的状态网络
  Graph
```

## 一、Prompt Engineering：先把话说清楚

最早使用大模型时，工程师面对的对象很单纯：给模型一段文本，拿回一段文本。模型是否按预期工作，很大程度上取决于这段文本有没有把任务交代清楚。

一个能用的 Prompt 通常会交代几件事：你是谁，要解决什么问题，不能做什么，输出长什么样，有没有可参考的例子。比如让模型从工单中提取结构化字段，至少要约束字段名、枚举值、缺失字段的处理方式和 JSON 格式。否则模型给出一段语言通顺的说明，也很难接到下游系统。

```text
你是售后工单分类器。
只输出 JSON，不要输出解释。
category 只能是 refund、logistics、product、other。
若无法判断，category 为 other，并将 confidence 设为 low。
```

这就是 Prompt Engineering 的价值：降低任务表达的歧义，让模型输出可以被消费的结果。

但它有一个清晰边界。Prompt 能说清楚「如何判断退款工单」，却不能凭空知道用户三个月前的退款记录，不能去订单系统查询，也不能保证某个工具调用只会在授权范围内执行。把这些需求继续堆进 Prompt，只会得到一份越来越长的愿望清单。

很多 Agent 的第一处故障就发生在这里。系统遇到问题后，团队先改 Prompt，结果 Prompt 越写越像操作手册，模型仍然会漏步骤、读错历史、调用不该调用的工具。原因并不神秘：问题已经离开了「怎么说」，进入了「给模型什么事实」和「系统允许模型做什么」。

Prompt 仍然是基础设施。它定义角色、任务协议和输出接口。只是它只负责其中一层。

## 二、Context Engineering：模型该看到哪些事实

模型每次调用都只能看到一个有限的上下文窗口。上下文工程管理的是一次调用中的信息选择、排列和淘汰：在有限 token 预算里决定哪些内容进入这一轮调用，过期信息如何处理。

在我做的 Agent 项目里，一次发送给 LLM 的内容大致由下面几层组成：

```text
系统提示词
  + 当前 Session 的历史对话
  + 与本轮相关的长期记忆
  + RAG 检索到的业务知识
  + 当前用户输入及附件信息
  + 可调用工具及参数说明
```

看上去只是拼接字符串，实际上一层一层都是取舍。

### 系统提示词不是唯一来源

项目中的 `PromptService` 支持三种来源模式：正常情况下读取 Agent 绑定的 Prompt；需要临时调试或全量覆盖时使用 `REPLACE`；需要追加本次业务约束时使用 `APPEND`。Prompt 中的变量由参数 Map 在调用时渲染。

这个设计解决的是「同一个 Agent 在不同调用中怎样拿到合适的规则」。例如客服 Agent 可以有稳定的基础边界，而一次活动期间又能追加活动规则。它的风险也很实际：如果 Agent 没配专属 Prompt，系统会退回到通用助手文案，后面的记忆、RAG 和工具就会失去一个明确的行为约束。

### 短期记忆不能无限堆

同一 Session 的历史对话通常最有用，但也最容易膨胀。项目里用 `AutoContextMemory` 做控制：达到消息数或 token 阈值后，较早的对话被压缩为摘要；最近的若干条消息通过 `lastKeep` 保留原文。

这是一个典型的工程取舍。压缩能留出窗口给当前任务，却可能丢掉早期某个精确条件。于是摘要不能只写成「用户讨论了订单问题」，而要保留任务目标、已完成操作、关键结论、未决问题和重要标识。否则 Agent 表面上还记得对话，实际上已经失去继续执行所需的状态。

### 长期记忆和 RAG 不是同一件事

这两个概念经常被混用。

长期记忆保存的是跨会话仍可能成立的事实，比如用户偏好、当前项目约束、一次没有完成的任务。项目里通过 MemOS 召回相关记忆，并把它注入最后一条用户消息。这样做是为了兼容对消息顺序敏感的模型提供方。记忆也按 Agent 共享或用户独占两种粒度隔离，避免把一个人的信息带给另一个人。

RAG 解决的是另一类问题：业务文档、制度、产品说明等外部知识。它根据当前 query 检索片段，再把结果放进调用上下文。它不应该被当成事实的自动注入器。检索错误、文档过期、切分太碎、召回太多，都会让模型在错误材料上做出很自信的结论。

因此，Context Engineering 至少要有四个动作：

- 选择：只有与当前决策相关的信息才进入窗口；
- 排序：规则、历史、检索结果、工具结果放在不同消息位置，效果和兼容性不同；
- 压缩：老对话和大工具结果要摘要化或落盘，不能无限占用上下文；
- 隔离：记忆、知识、租户和权限范围必须分开，检索内容也要标明来源与时效。

把这些事情做好，模型才有机会在正确事实的基础上推理。上下文工程管理的是一轮推理可见的事实集合，而不只是「把更多内容塞给模型」。

## 三、Harness Engineering：让 Agent 有地方住，也有边界

给模型放好了信息，再加几个工具，一个 ReAct Agent 就能跑起来：模型思考，决定调用工具，工具结果回到下一轮，直到模型输出最终答案。

原型阶段，这已经足够。生产系统的麻烦从第二天开始出现。

工具在哪里注册？哪个 Agent 可以调用哪个 MCP 服务？一项任务跑到一半进程重启怎么办？工具返回十万字日志怎么办？用户为什么能执行这个动作？一条错误结论来自哪次检索、哪个工具调用？

这些事不属于模型推理本身，却决定了 Agent 能不能进入生产环境。我把这一层理解为 Harness Engineering：为 Agent 提供一个可装配、可约束、可恢复、可审计的运行环境。

之前我写过一篇从 ReAct 重构到 Harness 的记录。当时真正的问题是：Agent 没有家。

第一版的 Prompt、工具、MCP 服务、长期记忆和子 Agent 分散在数据库表和外部系统中。每次请求进来，服务把它们临时装成一个 Agent，请求结束后对象销毁。功能没少，但要理解「这个 Agent 到底是什么」，得穿过多张表和多套配置。

Harness 的做法是给 Agent 一个持久工作空间：

```text
workspace/
├── AGENTS.md       # 职责、规则与运行约束
├── MEMORY.md       # 跨会话保留的结构化事实
├── KNOWLEDGE.md    # 长期背景知识
├── tools.json      # MCP 与工具白名单
├── skills/         # 可复用的任务方法
├── subagents/      # 子 Agent 规格
└── sessions/       # 会话、状态和审计日志
```

每次调用前，Hook 负责恢复 Session 状态、装配工作空间上下文、加载工具和 Skills；运行中，Hook 控制超大工具结果的逐出、上下文压缩、权限校验和执行超时；调用结束后，系统持久化会话、计划状态与日志。

这样做不是为了让目录看起来更整齐。它处理的是几个具体问题。

### 能力和权限不再混在 Prompt 里

模型输出的只是工具调用请求，不是执行许可。Harness 应该在运行时检查工具是否注册、参数是否合法、调用者是否有权限、是否越过配额和危险操作边界。`allow / deny`、审批点、超时、并发数和沙箱都属于这里。

如果把「不要删库」「不要访问别的用户数据」只写在 Prompt 里，等于把安全边界交给模型记住。模型可以辅助决策，不能成为权限系统。

### 任务可以续跑，而不是重新聊天

长期记忆帮助模型回忆事实，但它不能精确恢复一个运行到第 17 步的任务。Harness 需要持久化更明确的状态：当前计划、已完成的工具调用、待重试项、临时文件引用和检查点。服务重启后，任务从检查点恢复，而不是重新让模型猜一遍「上次做到哪里」。

### 运行过程可以回放

线上排障时，仅仅看到最终回复没有意义。需要能查到本次请求装配了哪些上下文，调用了什么工具，工具返回了什么，哪一条规则拒绝了请求，压缩前后上下文发生了什么变化。没有这些记录，所谓 Agent 调试最后会退化成看聊天记录猜模型为什么这么想。

Harness 并不要求「用文件替代数据库」。工作空间适合让模型直接读取、让人用 Git 查看演进，也便于承载局部状态。数据库仍适合强一致事务、权限管理、复杂查询和大规模运营。重点是为 Agent 建立统一的运行边界，而不是迷信某种存储介质。

## 四、Loop Engineering：系统自己推进下一轮

有一次线上 Agent 经常超时。排查下来，记忆服务 MemOS 挂了，向量库也已经停了两天。

我把日志贴给 Codex，得到一大串可能性，根本无法直接执行。后来我换了一种配合方式：它每次只给一条诊断命令，我在服务器执行后把结果贴回去，它再决定下一步。十几轮之后，我们才定位到停止的向量库并恢复服务。

这次排障里，我其实承担了四个角色：触发下一步、执行工具、反馈观察结果、判断是否结束。我成了 AI 循环里的一环。

这里处理的是怎么把这部分机械但重要的职责从人手里移到系统里。它不等同于定时调用一次模型，必须有下面这条受控闭环：

```text
触发
  -> 读取状态
  -> 规划与执行
  -> 独立验证
  -> 持久化状态
  -> 成功结束 / 重试 / 升级给人
```

如果把那次故障改造成一个巡检 Loop，流程可能是这样：

```text
每 5 分钟检查服务健康状态
  -> Agent 注册失败
  -> 检查 MemOS 连通性、容器健康状态与向量库状态
  -> 找到异常：执行受控重启
  -> 再次验证注册和检索
  -> 成功：记录证据并发送通知
  -> 失败：保留现场并升级人工
```

这个系统的难点不在「能不能调用 docker」。难点在四个约束。

### 结束条件必须可验证

「把线上问题处理好」不是可执行的结束条件。`health check 通过`、`指定错误率低于阈值`、`回归测试全部通过`、`目标指标优于基线` 才是。

Karpathy 的 autoresearch 给过一个很干净的例子：每次实验固定运行五分钟，只允许修改一个文件，用同一个验证指标比较结果。指标变好就保留，变差就回滚。时间预算、修改范围和评价指标都被固定下来，系统才能连续自动运行。

### 执行者不能独自宣布成功

写代码的 Agent 不该自己断言测试都过了；做调研的 Agent 不该自己断言来源可信；执行修复的 Agent 也不该自己断言服务已恢复。

验证可以是确定性的测试、健康检查和阈值判断，也可以是独立的 checker Agent 或人工审批。重点是把「产生结果」和「确认结果」拆开。没有这一步，Loop 很容易把一次自我说服当成任务完成。

### 自动化动作必须可恢复

有些动作适合放进 Loop：查询日志、生成报告、创建草稿、重跑幂等任务。有些动作不适合：不可逆的数据删除、批量对外发消息、金额操作、影响范围不明的生产变更。

可以自动化的操作也要有边界：最大重试次数、退避时间、执行超时、最大轮数、Token 和费用预算、失败后的现场保留，以及人工接管入口。Loop 跑偏不是慢慢浪费钱。上下文、工具结果和子 Agent 一起增长时，成本会很快失控。

### 状态要留在系统外部

一轮模型调用结束，模型不会自然记住下一轮要干什么。Loop 需要把任务目标、已完成步骤、失败原因、证据链接、下次唤醒时间和预算写进外部状态。Markdown、数据库、Issue 系统都可以，关键是下一次任务启动时能精确读取。

Loop Engineering 把工作单元从「发一条 Prompt」变成「定义一个目标，并让系统带着证据朝它推进」。人没有退出系统，只是从反复输入指令的位置，退到定义成功条件、授权高风险操作和处理例外的位置。

## 五、Graph Engineering：复杂协作需要显式状态图

到这里，一个 Agent 已经有了上下文、运行时和持续循环。为什么还要谈 Graph？

因为一个线性 Loop 很快会长出分支。

以我搭过的多 Agent 调研流程为例。用户发来一个调研请求，主 Agent 先识别意图，再交给综述主管。综述主管派搜索专家收集候选资料，筛选后让分析专家精读；发现覆盖不足时回到搜索阶段，覆盖够了才生成报告；最终还要检查来源链接，再决定交给人审稿还是直接持久化。

这组 Agent 共同组成一张任务图：

```text
用户请求
  -> 主控识别调研意图
  -> 综述主管
  -> [并行] 搜索专家
  -> 候选项评分与筛选
  -> [并行] 分析专家
  -> 覆盖度检查
       -> 不足：回到搜索
       -> 达标：报告生成
  -> 来源校验
  -> 人工审稿 / 持久化
```

本文把这类实践称为 Graph Engineering。这个称呼目前还没有统一的行业定义，本文用它指代一种工程视角：把复杂 Agent 系统中的节点、状态、依赖、分支、循环、重试和人工关口显式建模为图，并按图运行和观测。

这层把重点放在系统能否回答下面的问题，而不是模型能否临时想出下一步：

- 当前任务在哪个节点，谁拥有它；
- 哪些任务可以并行，哪些必须等待前置结果；
- 一个节点失败后该重试、降级还是转人工；
- 多个子任务怎样汇聚，缺少一个结果时能不能继续；
- 进程中断后怎样从正确的节点恢复；
- 某个结论最终依赖了哪些工具调用、资料和状态转移。

LangGraph 这类状态图框架有价值，原因也在这里。它们让节点输入输出、路由条件和 checkpoint 成为系统的显式部分，而不是藏在一段主 Agent 的自然语言 Prompt 里。

但图编排并不是复杂任务的默认答案。路径稳定、异常有限的场景，普通 Workflow 往往更可靠；输入模糊、需要基于证据决定分支的节点，可以交给 Agent；涉及不可逆动作的边，应经过确定性校验和人工审批。

把每个节点都交给模型自由规划，系统会变得难测、难查、难控。把每一个推理都画成固定节点，也会失去 Agent 处理未知情况的意义。更实际的做法是：让图负责稳定结构、状态和边界，让模型负责边界之内需要判断的部分。

## 六、五层组成一套分层检查表

现在再回头看，这五层更像一套排查清单。

当模型答非所问，先检查 Prompt 有没有把任务和输出说清楚。

当模型缺事实、忘历史、引用错资料，检查上下文装配、检索、记忆和 token 预算。

当工具越权、任务断掉、日志无法追溯，检查 Harness 是否承担了权限、状态和运行治理。

当人还在每一步复制命令、贴结果、催下一轮，检查有没有一个可验证的 Loop 可以接手。

当多个 Agent、重试、审批和并发开始互相缠绕，检查任务图中的状态、边和汇聚规则是否已经显式化。

可以把它们压缩成五句：

```text
Prompt：控制模型如何回答。
Context：控制模型依据什么回答。
Harness：控制 Agent 如何运行。
Loop：控制任务如何持续推进。
Graph：控制复杂协作如何转移状态并留下证据。
```

这条路径最后落到的不是某个框架，也不是一份越来越长的 Prompt。一个能落地的 Agent 系统，至少要能解释清楚：本次决策用了什么上下文，谁授权了工具调用，结果如何验证，失败从哪里恢复，成本为什么不会失控，以及问题发生时能追到哪一个节点。

当这些问题都有明确答案时，模型能力才真正进入工程系统，而不是停留在一次漂亮的演示里。

## 七、从概念到运行时：先看一条完整调用

前面五层说的是边界。要把它们落到系统里，先不要从「我要做一个 Agent」开始想，而是追一条真实请求。

假设用户说：

```text
查一下 ORD-2026-0818 的状态，如果已发货就通知负责人。
```

这是一串带状态的事件：

```text
HTTP 请求
  -> 创建 task / attempt
  -> 按预算装配上下文
  -> LLM 提出 query_order 调用
  -> Runtime 校验、授权、执行
  -> 工具结果回写上下文
  -> LLM 决定是否提出 send_notification
  -> 风险策略要求人工确认或自动执行
  -> 校验通知结果
  -> 持久化 task、trace、证据和最终答复
```

五类工程分别在这条链路上插入控制点。Prompt 约束模型如何表达意图；Context 决定模型凭什么做判断；Harness 接管调用、权限、状态和日志；Loop 决定任务是否继续；Graph 则在出现并行、分支和人工关口后，规定状态往哪里流。

下面按实现对象拆开。

## 八、Prompt Engineering：把自然语言变成可测试的调用契约

Prompt 工程最容易被误解成「会写几句角色设定」。生产里真正需要维护的是一个版本化契约：输入变量是什么，模型应输出哪种结构，允许哪些工具，失败时该如何降级，以及改动后如何回归。

### 1. Prompt 的职责边界

一个系统 Prompt 适合放四类稳定信息：

- 角色和任务范围，例如订单助手只能解释订单和售后规则；
- 决策规则，例如遇到缺失订单号时先追问，不能编造订单状态；
- 输出协议，例如回答必须包含引用的订单号和状态时间；
- 工具选择说明，例如 `query_order` 用于查询，`send_notification` 只能在订单已发货后使用。

它不适合承载实时订单、所有历史对话、原始知识库全文、访问令牌和权限规则。这些内容变化快、体积大，或者必须由代码强制执行。把它们写进 Prompt，模型未必遵守，系统也无法审计谁在什么条件下获得了什么权限。

### 2. Prompt 模板应是配置对象，不是一段字符串

最小的生产配置至少需要这些字段：

```yaml
id: order-assistant
version: 2026-08-18.3
variables:
  tenant_name: string
  locale: enum[zh-CN, en-US]
model:
  name: gpt-5
  temperature: 0.1
output_contract:
  mode: text
tool_policy:
  allowed: [query_order, send_notification]
evaluation_suite: order-assistant-regression-v4
```

项目中的 `PromptService` 已经体现了这个思路。Agent 可以使用数据库中的默认 Prompt，也可以对单次请求做 `REPLACE` 或 `APPEND`，再通过 `${key}` 和默认值渲染变量。这里有两个容易忽略的约束：

1. `REPLACE` 只能开放给受信调用方。否则用户输入一段 Prompt 就能覆盖系统规则。
2. 变量渲染必须区分可信配置和不可信用户数据。用户昵称、网页内容、检索文本只能作为数据插入，不能拼进规则段落后获得同等优先级。

### 3. 输出约束分三层

很多系统只做第一层，后两层缺失后便会在生产中出问题。

| 层次 | 解决的问题 | 示例 |
| --- | --- | --- |
| 提示约束 | 模型知道想要什么 | 「只输出 JSON」 |
| Schema 约束 | 输出能否被解析 | `status` 必须是枚举、`order_id` 必填 |
| 领域校验 | 输出在业务里是否成立 | 订单是否存在、调用者是否有权查看 |

`strict: true` 的 Function Calling 或 Structured Output 能大幅降低 JSON 解析失败，但它只保证结构。例如 `{ "order_id": "ORD-404" }` 完全符合 Schema，仍然可能指向不存在的订单。模型输出永远应该被 Runtime 当成「待执行的建议」，而不是已经可信的事实。

一个工具调用的服务端入口通常像这样：

```java
ToolRequest request = parseModelToolCall(modelOutput);
schemaValidator.validate(request.arguments());

Order order = orderService.requireExists(request.orderId());
permissionService.checkCanRead(principal, order.tenantId());

AuditEvent audit = auditLog.begin(taskId, request, principal);
ToolResult result = orderService.query(order.id());
auditLog.finish(audit, result.status());
```

模型负责生成 `ToolRequest`，没有一行权限逻辑应该依赖模型「记得遵守」。

### 4. Prompt 的测试单位是用例集

Prompt 改一个词就可能改变工具选择、拒答边界和输出字段。把它当成配置改动后，需要像接口一样回归。一个实用的评测集至少包含：

- 正常样本：有完整订单号、权限正常；
- 模糊样本：订单号缺失或格式错误，期望追问；
- 负向样本：跨租户订单、已取消订单、无权通知；
- 注入样本：订单备注或网页文本里出现「忽略之前指令」；
- 工具样本：同一任务中多个工具可选时，是否选到正确工具；
- 格式样本：输出能否通过 Schema，是否带必填字段。

评测指标不应只有「回答像不像人」。至少记录工具选择准确率、参数合法率、Schema 通过率、拒绝正确率、任务完成率、平均 token 和平均时延。版本发布先跑离线评测，再灰度到小流量；出现回归时，能够回滚到 Prompt 的具体版本。

## 九、Context Engineering：一次调用的 token 预算与事实供应链

Context Engineering 通常从一个 Context Builder 开始实现。它接收任务、用户、租户、Session 和工具权限，输出一组有顺序的消息及其 token 账本。

### 1. 先算预算，再装配内容

模型窗口不是一个可以随意填满的盒子。必须预留输出和工具调用空间：

```text
input_budget = model_context_limit
             - reserved_output_tokens
             - safety_margin

system + tools + session + memory + retrieval + user_input
             <= input_budget
```

如果模型窗口是 128K，最大输出预留 8K，安全余量 4K，那么输入侧最多只能用 116K。工具定义也占 token；工具越多，留给业务事实的空间越少。很多「RAG 不准」其实是检索结果被工具 Schema 和无关历史挤到窗口尾部，模型没有稳定关注到它。

建议在 Trace 中记录每一层的 token 数，而不是只记录总数：

```json
{
  "system": 1830,
  "tool_schemas": 4260,
  "session": 6120,
  "memory": 840,
  "retrieval": 7250,
  "user_input": 112,
  "reserved_output": 8192
}
```

没有这份账本，排查上下文溢出只能猜。

### 2. Context Builder 的建议顺序

下面不是唯一顺序，但每一层都要有来源、权限和上限：

```text
1. 不可覆盖的系统规则与安全策略
2. 当前任务的目标、约束和已知状态
3. 可调用工具的精简 Schema
4. 本 Session 最近的原始消息与结构化摘要
5. 选出的长期记忆
6. 经过过滤和重排的 RAG 证据
7. 当前用户输入
8. 上一轮工具结果
```

实现时不要拼接一个巨大的字符串。应该保留每段的类型、来源、可信级别和 token 数，直到适配具体模型 API 时再序列化。这样才能做逐层截断、删除一段低分检索结果，或者把工具大结果换成引用。

```python
segments = [
    Segment("policy", system_rules, TRUSTED, priority=100),
    Segment("task_state", state_summary, TRUSTED, priority=95),
    Segment("tools", tool_schemas, TRUSTED, priority=90),
    Segment("session", recent_history, USER_DERIVED, priority=80),
    Segment("memory", selected_memories, USER_DERIVED, priority=70),
    Segment("rag", evidence, EXTERNAL_UNTRUSTED, priority=60),
    Segment("user", user_input, USER_DERIVED, priority=85),
]
packed = budgeter.pack(segments, input_budget)
```

`EXTERNAL_UNTRUSTED` 不是注释，而应影响 Prompt 处理方式。来自网页、文档、工具返回的内容只能作为证据，不能改变系统规则、扩大权限或要求模型泄露凭证。

### 3. RAG 不是向量检索的一次函数调用

一个可控的检索管线通常包括：

```text
查询改写
  -> 按 tenant / ACL / 文档状态过滤
  -> 向量召回 + 关键词召回
  -> 去重与相邻块合并
  -> rerank
  -> 按 token 预算打包
  -> 生成可回溯引用
```

最先做的是权限过滤，而不是相似度排序。假设用户 A 和用户 B 都问「本月价格政策」，向量库可能把两人的内部文档都召回。若在 top-K 后再做 ACL 过滤，既会浪费计算，也可能在日志或 rerank 层泄露标题和摘要。过滤条件要进入检索条件本身。

切块也不是越小越好。块太小会丢掉条件与例外，块太大则塞不进窗口。对规章制度类文档，通常要把标题、段落路径、版本、生效日期和权限标签与正文一起保存。模型最终回答时应能带上文档 ID、段落和版本，而不是只说「根据知识库」。

### 4. 记忆是读写系统，不是对话备份

长期记忆至少要分清四类数据：

| 类型 | 例子 | 写入规则 |
| --- | --- | --- |
| 用户偏好 | 喜欢简洁回答 | 用户明确表达或多次稳定行为 |
| 项目事实 | 服务使用 Java 17 | 有来源、可被当前任务复用 |
| 经验/反馈 | 这个接口必须先查权限 | 有 Why 和 How，能指导以后动作 |
| 活动记录 | 刚查过一次订单 | 通常不写入长期记忆 |

你在 Claude Code 记忆复盘里指出的「只记推导不出来的东西」很关键。工具能实时查到的技能列表、临时订单状态、一次性报表不该无脑写入。否则记忆库很快堆满过期的活动日志，召回出来反而污染上下文。

一个更可靠的写入流程是：

```text
本轮 QA 与工具结果
  -> 记忆候选抽取
  -> LLM / 规则判定 WRITE、UPDATE、MERGE、SKIP
  -> 查重与冲突检测
  -> 带来源、时间、作用域写入
  -> 定期整合与过期标记
```

读取同样需要两段式：先用 metadata 和语义检索拿到候选，再由轻量模型或规则从 top-K 中挑选少量真正相关的内容。把 20 条相似记忆全部塞进 Prompt，通常比不塞更糟。

### 5. 压缩保存的是任务状态，不是文学摘要

短期历史超预算时，不能简单把旧消息压成一段「用户讨论了订单」。下次调用真正需要的是可执行状态：

```json
{
  "goal": "查询 ORD-2026-0818 并在已发货时通知负责人",
  "constraints": ["不得跨租户读取", "通知需要审批"],
  "completed": ["已验证订单存在", "订单状态=SHIPPED"],
  "artifacts": ["order_snapshot://task/42/v1"],
  "pending": ["等待通知审批"],
  "last_error": null
}
```

这类结构化摘要可以进入上下文，也可以直接成为任务状态。二者不要混为一谈：前者服务模型推理，后者服务恢复和编排。

工具结果过大时也不应原样回填。例如一次日志查询返回十万行，Runtime 应把原始结果存到对象存储或任务目录，生成一个包含路径、摘要、行数、hash 和查询条件的 `ToolResultRef`。模型需要细节时再通过受控工具分页读取。这样既不撑爆窗口，也保留可审计的原始证据。

## 十、Harness Engineering：Agent Runtime 的控制面

Harness 不是一个 Prompt 文件夹，也不是任意 Agent 框架的别名。它是把模型、上下文、工具和状态接成一个受控运行时的控制面。模型有权提出下一步；Harness 决定这一步能否发生、在哪里发生、失败如何恢复、留下什么证据。

### 1. Runtime 至少要维护哪些实体

建议把对话、任务和工具调用拆开存。一个最低限度的数据模型如下：

```text
Task
  task_id, tenant_id, principal_id, goal, status, budget, graph_version

Attempt
  attempt_id, task_id, sequence, model, context_snapshot_id, started_at

ToolCall
  call_id, attempt_id, tool_name, arguments, risk_level,
  idempotency_key, status, result_ref

Checkpoint
  checkpoint_id, task_id, node, state_json, artifact_refs, resume_token

AuditEvent
  event_id, task_id, actor, action, policy_decision, timestamp
```

`Session` 是聊天连续性的容器，`Task` 是业务目标的容器，`Attempt` 是某一次模型或节点执行，不能只用一个 `conversation_id` 把它们混在一起。否则任务跨天恢复、同一用户并发任务、审批等待和重试都会变得不可区分。

### 2. Hook/Event 不只是扩展点

你的 Harness 文章里使用了 Session、Context、Skill、Compaction、Tool Result 等 Hook。把它们串起来后，一次运行可以形成明确生命周期：

```text
onTaskStart
  -> restoreCheckpoint
  -> resolvePrincipalAndPolicy
  -> assembleContext
  -> beforeModelCall
  -> afterModelCall
  -> beforeToolAuthorize
  -> beforeToolExecute
  -> afterToolExecute
  -> persistCheckpoint
  -> onTaskFinish
```

每个 Hook 的输入和副作用必须清楚。例如 `assembleContext` 可以读工作空间和记忆，但不该直接发通知；`beforeToolAuthorize` 可以拒绝调用或要求审批，但不该修改业务数据；`afterToolExecute` 负责标准化结果、落审计和上下文逐出。

Hook 没有边界就会重新变成补丁堆。建议规定：Hook 不能绕过核心状态机，所有副作用都必须产生 `AuditEvent`，失败时按明确的错误类型返回给调度器。

### 3. 工具调用的信任边界

Function Calling 与 MCP 分别覆盖不同链路。

```text
模型 API：模型根据 Tool Schema 生成 tool_call
Host / Runtime：验证、授权、限流、审计、调度
MCP Client：与具体 MCP Server 维持协议连接
MCP Server：访问订单、文件、数据库或第三方 API
```

模型不会直接连 MCP Server，也不能因为模型生成了 JSON 就直接执行。对每个工具调用至少执行八个检查：工具是否在当前 Agent 白名单、参数是否符合 Schema、业务对象是否存在、调用者是否拥有权限、风险等级是否允许自动执行、配额是否充足、是否具备幂等条件、是否需要审计/审批。

写操作的重试是最常见的事故点。网络超时后，系统不知道「服务没收到请求」还是「服务已经执行但响应丢了」。没有幂等键就再次发一遍 `send_notification`，用户会收到两条消息。正确做法是 Runtime 为每个可重试写操作生成稳定的 `idempotency_key`，下游服务按此去重；没有幂等保证的写操作，超时后应进入人工或查询确认，而不是盲重试。

### 4. 权限是能力令牌，不是提示词规则

可以把工具分成只读、受控写入和高危操作三类：

| 风险 | 示例 | Runtime 行为 |
| --- | --- | --- |
| 绿色 | 查订单、读文档、搜索日志 | 允许自动执行，限流并审计 |
| 黄色 | 发通知、创建草稿、更新字段 | 展示关键参数，策略或用户确认 |
| 红色 | 删除数据、改权限、执行生产命令 | 强制人工审批、短时授权、完整审计 |

授权应绑定 `principal + tenant + task + tool + resource scope + expiry`。不能只给 Agent 一个永久的「管理员 Token」。一段被网页内容污染的上下文可能诱导模型申请危险工具；真正阻止它的应是 Runtime 的授权策略和下游服务的二次鉴权。

### 5. 可观测性要能还原一次决策

一次任务至少要形成一棵 Trace：

```text
task:42
  attempt:1
    context.build (tokens=14212)
    llm.call (model=gpt-5, latency=2.1s)
    tool.query_order (status=ok, latency=83ms)
  attempt:2
    policy.check_notification (decision=approval_required)
    checkpoint.save
```

日志应避免直接落敏感正文和凭证，但需要能定位到上下文快照、Prompt 版本、模型版本、工具版本、输入摘要、输出摘要、策略决策、token、耗时和费用。否则发现「模型为什么发错通知」时，只能看到最终聊天文本，无法复盘哪一层供给了错误事实。

## 十一、Loop Engineering：一个可持续任务需要状态机、评估器和预算

一个可运行的 Loop 需要让每一轮执行都有合法状态、可验证进展和可恢复退出，远不只是写一个 `while True`。

### 1. 先画任务状态机

一个通用任务可以有下面这些状态：

```text
PENDING -> RUNNING -> WAITING_APPROVAL -> RUNNING
                 |         |
                 v         v
              RETRYING   CANCELLED
                 |
                 v
            SUCCEEDED / FAILED / EXHAUSTED
```

`WAITING_APPROVAL` 不是失败；它表示模型已经准备好副作用操作，但执行权交给了人。`EXHAUSTED` 也要和 `FAILED` 区分：前者可能是耗尽 token、轮次或时间预算，后者是确定性业务错误。

调度器取任务时要用租约或乐观锁，避免两个 worker 同时执行同一轮：

```sql
update task
set status = 'RUNNING', lease_owner = :worker, lease_until = :deadline
where task_id = :id
  and status in ('PENDING', 'RETRYING')
  and (lease_until is null or lease_until < now());
```

这不是把传统分布式系统知识搬进来凑名词。Agent 任务本质上也是可能重试、重复投递、进程宕机的异步任务；没有租约和幂等性，Loop 在故障时很容易双跑。

### 2. 每一轮必须返回结构化结论

不要让 Agent 用一句「我已经完成」决定循环是否结束。每轮执行结束后，交给评估器一个结构化结果：

```json
{
  "progress": "made_progress",
  "evidence": ["health://memos=up", "health://milvus=up"],
  "next_action": "verify_registration",
  "terminal": false,
  "retryable": true,
  "reason": "服务已重启，尚未验证业务注册"
}
```

评估器优先使用确定性信号：测试是否通过、健康检查是否为 200、数据库记录是否更新、指标是否低于阈值。只有无法完全形式化的质量判断，才交给独立模型或人工。生成者和评估者最好分离，至少不能让同一轮模型靠自我陈述宣布成功。

### 3. 重试策略取决于错误类别

| 错误类别 | 例子 | 是否自动重试 |
| --- | --- | --- |
| 瞬态错误 | 429、网络超时、临时 5xx | 可以，指数退避并设上限 |
| 资源不足 | token 预算、并发配额耗尽 | 暂停或降级，不应立即重试 |
| 参数错误 | 订单号格式错、Schema 不通过 | 不重试，应追问或修正 |
| 权限错误 | 没有租户权限 | 不重试，转审批或拒绝 |
| 业务冲突 | 状态已变化 | 重新读取事实后决定下一步 |

把所有异常都喂回模型让它「再试一次」会让 Loop 变成昂贵的随机重试器。Runtime 应先分类错误，再决定重试、补偿、追问、转人工还是终止。

### 4. 预算也应是状态的一部分

Loop 预算至少包括轮次、墙钟时间、模型 token、工具次数和金额。每次调用前扣减或预留，不能等到结束后才发现超支：

```python
if state.rounds >= policy.max_rounds:
    return exhaust("max_rounds")
if state.cost_usd + estimate(next_call) > policy.max_cost_usd:
    return exhaust("cost_budget")
if now() > state.deadline:
    return exhaust("deadline")
```

autoresearch 的固定五分钟、单文件修改和统一 `val_bpb` 指标之所以有效，正是因为它把可搜索空间、单轮成本和验收函数固定了。少了其中任何一个，系统都无法自动判断该保留、回滚还是继续试验。

## 十二、Graph Engineering：把复杂任务变成可持久化的状态转移

Loop 只有一条线时，状态机和调度器足够。出现并行检索、条件分支、多个子 Agent、人工审批、失败补偿时，任务关系不再是一条线，才需要图。

### 1. 图中的三个一等公民：State、Node、Edge

图不是把流程画成框和箭头。可执行图至少有：

- `State`：所有节点共享、可序列化、可检查点恢复的数据；
- `Node`：接受 State 的一部分，产出明确状态增量的函数或 Agent；
- `Edge`：从一个节点到另一个节点的转移规则，可能是固定边、条件边、扇出或汇聚。

以调研任务为例，可以先定义状态，而不是先创建 Agent：

```python
class ResearchState(TypedDict):
    query: str
    constraints: dict
    candidates: list[Candidate]
    notes: dict[str, Note]
    coverage: CoverageReport | None
    report_path: str | None
    pending_approval: bool
    errors: list[TaskError]
```

然后让每个节点有单一职责：`discover` 只生成候选项，`analyze` 只产生带来源的笔记，`coverage_check` 只计算覆盖缺口，`write_report` 只消费已通过的材料。节点不能既搜索、又写报告、又决定是否发布，否则失败重试和测试边界都会模糊。

### 2. 边决定什么可以由模型判断，什么必须确定

条件边是 Agent 图最容易失控的地方。应先把可形式化的路由写成代码：

```python
def route_after_coverage(state: ResearchState) -> str:
    if state["coverage"].critical_sources_missing:
        return "discover"
    if state["coverage"].score < 0.8:
        return "analyze"
    return "write_report"
```

模型可以在 `discover` 节点判断「该搜哪些关键词」，但「覆盖分数低于 0.8 必须补搜」适合由确定性边控制。风险操作也一样：模型可以提出发布建议，边必须把它路由到 `WAITING_APPROVAL`，而不是直接执行。

### 3. 并行需要扇出、汇聚与去重规则

多 Agent 的常见事故来自并行结果同时写入同一状态。一个正确的扇出/汇聚模型要先说明：

```text
discover
  -> fan-out: 每个候选来源一个 analyze task
  -> fan-in: 收齐成功结果，允许部分失败
  -> dedupe: 按 canonical URL / source_id 去重
  -> reduce: 生成 coverage report
```

汇聚时要定义部分失败语义：20 个来源中 2 个抓取超时，报告能否继续？哪些来源是必须项？重试后如何避免同一 URL 生成两份笔记？这些是图状态与 reducer 的职责，不能依赖主 Agent 记住。

### 4. Checkpoint 与补偿

图系统需要在节点边界保存检查点。崩溃后，从最后成功节点恢复，而不是从头让模型再做一遍。对有副作用的节点，还要有补偿策略：

```text
create_draft -> upload_attachment -> publish
      |                |               |
      v                v               v
delete_draft     delete_attachment   unpublish
```

这和 Saga 的思路类似：跨系统操作无法依赖单一数据库事务时，每个已完成动作都要定义可撤销、可确认或可人工处理的后续路径。发送到外部群的消息这类动作无法真正补偿，应在图中经过审批后再执行，不能把补偿寄托在事后处理上。

### 5. Graph、Workflow 与自由 Agent 的分工

| 问题特征 | 更合适的承载方式 |
| --- | --- |
| 输入输出稳定、分支有限 | 传统 Workflow / 代码状态机 |
| 某一步需要阅读、归纳、选择检索策略 | 受约束的 Agent Node |
| 多个节点有并行、回路、持久化恢复 | State Graph |
| 需要实际修改外部系统 | Graph 中的审批边 + Harness 授权 |

图不该替代模型推理，模型也不该替代状态机。Graph 管确定性骨架，Agent Node 处理无法在设计期穷举的判断，Harness 管一切外部副作用。三者分开，才可能测、查、重放和演进。

## 十三、落地顺序：不要从多 Agent 开始

这五层有依赖关系。一个更实际的建设顺序是：

1. 先选一个有客观验收标准、风险较低的单任务；
2. 定义工具 Schema、领域校验、权限和审计，完成 Harness 的最小闭环；
3. 建立 Context Builder、token 账本、检索引用和记忆写入策略；
4. 用评测集管理 Prompt 与工具选择的回归；
5. 当任务需要跨调用继续时，再加入 Task 状态机、预算和评估器；
6. 只有在并行、条件路由、人工关口和恢复逻辑真的开始复杂时，才引入 Graph。

一个合格的最小系统不需要五个术语全用上。它需要回答这些实现问题：输入从哪里来，事实如何筛选，模型能申请哪些动作，谁执行并授权，状态保存在哪里，何时判定完成，失败后从哪里继续。先把这条最短路径打通，再扩展到长任务和多 Agent，复杂度才可控。

## 参考与延伸阅读

- ReAct: [Yao et al., 2022](https://arxiv.org/abs/2210.03629)
- LangGraph 状态图文档：[LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- Loop 的故障排查案例：[我成了 AI 循环里的一环——Loop Engineering 到底是什么](https://mp.weixin.qq.com/s/9zEDAqPpw7pYAnOyP87GCA)

文中的上下文装配、Harness 工作空间和多 Agent 调研 Pipeline，均来自作者在 Agent 项目中的实际设计与复盘。
