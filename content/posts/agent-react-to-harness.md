+++
title = '我把 Agent 重构了一遍，因为它"没有家"'
date = 2026-06-08T10:00:00+08:00
draft = false
slug = "agent-react-to-harness"
author = "尹绍钧"
tags = ["AI Agent", "架构", "ReAct", "Harness", "LLM", "工程化"]
summary = "一名 Agent 开发者从 ReAct 到 Harness 的架构思想演进记录。第一版基于 ReAct 思想开发，靠一块一块打补丁撑起来；Harness 思想出来之后，我意识到 Agent 缺的不是更多补丁，而是一个「家」。"
+++

我是一名 Agent 开发者。

第一版上线时，我以为 ReAct 加上一堆补丁就够了。系统越来越大之后，我开始意识到这套架构从根子上就有一个问题，但一直说不清楚是什么。直到看到 Harness 的设计，才想明白：

**Agent 没有家。**

这篇文章记录我从 ReAct 到 Harness 的思想转变。

---

## 一切的起点：ReAct 解决了什么

最早写 Agent，代码极其简单——一个循环：

```
用户输入
   ↓
Reason：LLM 思考，下一步是什么？
   ↓
Act：需要用工具吗？
   ├── 需要 → 执行工具 → 结果回到 Reason
   └── 不需要 → 直接输出，任务结束
```

这叫 **ReAct（Reasoning + Acting）**。解决的核心问题是：让 LLM 从"只会输出文字"变成"能自主分步完成任务"。

伪代码十几行搞定：

```python
def react_loop(user_input, tools, llm, memory):
    memory.add(user_input)
    for _ in range(max_iters):
        response = llm.call(memory.get_all())   # Reason
        if response.has_tool_call():
            result = tools.execute(response.tool_call)   # Act
            memory.add(result)
        else:
            return response.text   # 没有工具调用，任务结束
```

然后问题就来了。

---

## 第一版：一次一次打补丁

### 补丁一：Agent 需要人格

裸 ReAct 不知道自己是谁，回答风格杂乱、没有边界感。加上 System Prompt：

```python
system_prompt = config.load_prompt(agent_id)
all_messages  = [system_prompt] + memory.get_all()
response      = llm.call(all_messages)
# 加上之后，Agent 有了身份
# 但：提示词写死在配置里，每次修改都要走发布流程
```

---

### 补丁二：工具体系

LLM 只能生成文字，无法查数据库、调接口。工具能力的演进经历了三层：

**第一层：静态注册工具**——写死在代码里，想加新工具必须改代码重新部署：

```python
toolkit = Toolkit()
toolkit.register(WeatherTool())       # 查天气
toolkit.register(DatabaseTool())      # 查数据库
toolkit.register(CodeExecutorTool())  # 执行代码
# 想加一个新工具，必须改代码 + 重新部署
```

**第二层：MCP 协议**——工具的定义权从 Agent 侧转移到工具服务侧，Agent 动态拉取：

```python
mcp_client      = MCPClient.connect("http://tool-server/sse")
available_tools = mcp_client.list_tools()
# 返回：[{name: "query_log", desc: "..."}, {name: "alert", desc: "..."}, ...]

toolkit.register_from_mcp(mcp_client, allow=["query_log"], deny=["delete"])
# MCP 服务端上线新工具，Agent 下次请求自动感知，不改代码
```

工具描述（description）仍然是核心——LLM 靠描述决定调不调某个工具。

**第三层：MCP 配置中心**——连哪些 MCP 服务器本身也做成动态管理：

```python
def build_agent_toolkit(agent_id):
    mcp_configs = db.query(
        "SELECT * FROM mcp_config WHERE agent_id = ?", agent_id
    )
    # 在管理后台增删记录，无需改代码、无需重启

    toolkit = Toolkit()
    for cfg in mcp_configs:
        if cfg.status == "enabled":
            client = MCPClient.connect(cfg.url)
            toolkit.register_from_mcp(
                client,
                allow=cfg.allow_tools,
                deny=cfg.deny_tools
            )
    return toolkit
```

到这里，工具定义由 MCP 服务端管，MCP 服务器列表由 DB 管，两者都可以不改代码热变更。

---

### 补丁三：记忆层

每次对话结束，Agent 忘得一干二净。加上短期记忆 + 向量数据库长期记忆：

```python
def call_with_memory(user_input, user_id):
    # 从长期记忆里检索与当前问题相关的历史
    recalled = long_term.retrieve(query=user_input, user_id=user_id, top_k=5)
    short_term.add(recalled)
    short_term.add(user_input)
    response = react_loop(short_term.get_all(), ...)
    long_term.record(user_input, response, user_id=user_id)
    return response
```

然后历史消息越存越多，上下文窗口撑不住。

---

### 补丁四：控制上下文膨胀

**裁剪**：超出就砍掉最老的消息，简单粗暴，容易丢上下文。

**摘要压缩**：用 LLM 把旧消息压缩成精华：

```python
def compress_if_needed(messages, threshold=50):
    if len(messages) < threshold:
        return messages

    old_messages = messages[:-10]       # 保留最近 10 条原文
    summary      = llm.summarize(old_messages)
    return [summary] + messages[-10:]
```

**超大工具结果落盘**：工具返回了一个 10 万字的报告，不能整个塞进上下文：

```python
def handle_tool_result(result, max_chars=5000):
    if len(result.text) <= max_chars:
        return result

    path = storage.write(result.text)
    return ToolResult(text=f"[结果太大已存储，读取路径：{path}]")
```

---

### 补丁五：多 Agent 协作

单 Agent 什么都干，System Prompt 越写越长，效果越来越差。主 Agent 调度，子 Agent 专职：

```python
# 主 Agent 的工具箱里有一个特殊工具：调用子 Agent
toolkit.register(SubAgentTool(
    name="code_agent",
    description="专门负责编写和执行代码的子 Agent，适合代码类任务",
    factory=lambda: build_agent(role="code_specialist")
))
# LLM 推理时自主决定是否把子任务交给 code_agent
# 生成：tool_call: {name: "code_agent", input: "帮我写一个排序函数"}
```

---

### 打完所有补丁，系统长成了什么样

```python
def handle_request(request):
    # ① 从配置中心加载 Agent 的所有零件
    model         = config.load_model(request.agent_id)
    system_prompt = config.load_prompt(request.agent_id)
    mcp_servers   = config.load_mcp_configs(request.agent_id)
    long_term_mem = init_memory(request.user_id)
    sub_agents    = config.load_sub_agents(request.agent_id)

    # ② 逐个初始化并拼装
    toolkit = Toolkit()
    for mcp in mcp_servers:
        toolkit.register_from_mcp(MCPClient.connect(mcp.url))
    for sub in sub_agents:
        toolkit.register(SubAgentTool(sub))

    # ③ 组装成一个 Agent 实例（每次请求都重新组装）
    agent = ReActAgent(
        system_prompt = system_prompt,
        model         = model,
        toolkit       = toolkit,
        memory        = AutoCompressMemory(long_term_mem),
        hooks         = [LogHook(), SessionHook(), MonitorHook()],
        max_iters     = 50,
    )

    # ④ 执行，响应后销毁
    return agent.call(request.message)
```

看这段代码的注释顺序就明白了：Agent 是每次请求临时组装的，配置中心才是真正活着的那个东西。Agent 是短命的组装品，配置中心是它的灵魂。

这套思路在 Agent 复杂度不高时运转良好。但规模变大后，我遇到了五个补丁解决不了的问题。

---

## v1 的问题，不是功能缺失，是设计错了

**问题一：没有地方能给你这个 Agent 的完整画像**

人格在提示词表，工具在工具配置表，MCP 服务器在 MCP 配置表，记忆服务又是另一个外部系统。想搞清楚"这个 Agent 到底是什么"，要跑遍好几个地方。改一个 Agent 的行为，要同时在多处修改并保证一致性——这很容易出错。

**问题二：Agent 是只读的**

配置的拥有者是管理后台和数据库，不是 Agent 本身。Agent 在某次任务中发现"我需要一个新的 MCP 工具服务"，它做不到——无法写入配置中心，告诉下次调用"从现在起，还需要接入这个服务"。

**问题三：Agent 不会成长**

跑了一万次，能力还是部署时配置的那些。成功处理某类复杂任务的方法、踩过的坑，没有地方沉淀。

**问题四：进程重启就断了**

Agent 实例是内存对象。服务重启，正在进行的长任务推理状态丢失。长期记忆只能恢复"记住了什么事实"，无法恢复"做到哪一步了"。

**问题五：上下文管理是插件，不是基础设施**

AutoCompress 是作为内存实现插进来的，不是框架内置的系统性机制。超长任务、多日会话面前，容易出现 Agent 忘了自己在做什么的情况。

---

## Harness：换一个问题

Harness 不是再加一块补丁。它换了一个问：

v1 问的是——这次请求，我需要给 Agent 装配什么？

Harness 问的是——Agent 住在哪里？它的家里有什么？

两个问法，完全不同的结论。

v1 把 Agent 的配置散在各个数据库表里：

```
提示词表里的记录
工具配置表里的记录
MCP 服务器配置表
子 Agent 配置记录
外部长期记忆服务
```

Harness 把这些东西都放到 Agent 自己的工作空间里：

```
workspace/
├── AGENTS.md      ← 人格 + 职责 + 规则
├── MEMORY.md      ← 跨会话积累的关键事实
├── KNOWLEDGE.md   ← 领域背景知识
├── tools.json     ← 工具接入（含 MCP 服务器）
├── skills/        ← 成功模式（可自动增长）
├── subagents/     ← 子 Agent 规格声明
└── agents/<id>/
    ├── context/   ← 会话状态（持久）
    └── sessions/  ← 完整对话日志
```

工作空间是 Agent 的"家"，持续存在。Agent 每次调用时读自己的家，不是等工厂装配。Agent 也可以**写自己的家**——成功的经验沉淀到 `skills/`，重要事实更新到 `MEMORY.md`。

---

## Harness 是怎么跑起来的

### 上下文注入

每次调用开始前，有一个专门的 Hook 读取工作空间文件，拼接成系统提示词注入：

```python
class WorkspaceContextHook:
    def on_pre_call(self, agent, messages):
        # 动态读取，文件改了立即生效，无需重启
        personality     = workspace.read("AGENTS.md")
        long_term_facts = workspace.read("MEMORY.md")
        knowledge       = workspace.read("KNOWLEDGE.md")

        system_context = f"""
{personality}

## 你记住的重要信息
{long_term_facts}

## 背景知识
{knowledge}
"""
        agent.set_system_prompt(system_context)
        return messages
```

改 `AGENTS.md` 就等于改 Agent 的人格，改 `MEMORY.md` 就等于给 Agent "植入记忆"，无需重启、无需发布。

---

### 配置归 Agent 自己管

v1 的 MCP 配置住在外部 DB，Agent 是只读消费者。v2 的配置住在 Agent 自己的工作空间：

```python
# v1：Agent 是只读消费者
def build_toolkit_v1(agent_id):
    mcp_configs = db.query("SELECT * FROM mcp_config WHERE agent_id=?", agent_id)
    # 动态✅：管理员在后台加一条记录，下次调用即生效
    # 但 Agent 自身无法修改：无法写 DB，无法告诉下次调用"我需要新接入这个服务"

# v2/Harness：Agent 是配置的拥有者
def build_toolkit_v2(workspace):
    tools_config = workspace.read_json("tools.json")
    # {
    #   "mcpServers": [
    #     {"name": "log-server", "url": "http://log.internal/mcp"},
    #     {"name": "alert",      "url": "http://alert.internal/mcp"}
    #   ],
    #   "allow": ["query_log", "send_alert"],
    #   "deny":  ["drop_table"]
    # }
    # Agent 在执行中发现需要新工具 → 自己修改 tools.json → 下次调用自动接入
```

两种方式都能做到"改配置不改代码"，区别在于谁是配置的拥有者。一旦要实现"Agent 在任务执行中自主扩展能力"，v1 做不到，v2 天然支持。

`skills/` 目录也是每次调用动态读取的：

```python
class DynamicSkillHook:
    def on_pre_reasoning(self, agent, messages):
        skill_files = workspace.list_files("skills/*.md")
        skills      = [parse_skill(f) for f in skill_files]
        agent.update_skills(skills)
        return messages
    # skills/ 里的文件可以由 Agent 自己在运行时写入
```

---

### 三层记忆

```
第一层：上下文窗口内的对话（当次推理可见）
第二层：MEMORY.md（跨会话的结构化事实，每次调用注入）
         示例内容：
           - 用户偏好：简洁回答，不喜欢列表格式
           - 项目背景：正在做 AI 平台升级，技术栈 Java + Spring
           - 上次未完成：日志查询功能还差权限校验
第三层：sessions/ 完整日志（永不压缩，永久归档）
```

```python
class MemoryFlushHook:
    def on_post_call(self, agent, response):
        # 每次对话结束，把完整消息追加到 sessions/ 日志
        session_log = workspace.path(f"agents/{agent.id}/sessions/{today}.jsonl")
        workspace.append(session_log, serialize(agent.memory.get_all()))

class MemoryMaintenanceHook:
    def on_pre_call(self, agent, messages):
        # 定期把 sessions/ 里的新内容提炼成事实，更新 MEMORY.md
        if should_consolidate():
            new_facts = llm.extract_facts(recent_sessions())
            workspace.update("MEMORY.md", new_facts)
        return messages
```

长期记忆不再依赖外部向量数据库，就在工作空间里，由 LLM 自己维护。

---

### 会话状态精确恢复

```python
class SessionPersistenceHook:
    def on_pre_call(self, agent, messages, ctx):
        session_path = f"agents/{agent.id}/context/{ctx.session_id}/"

        saved_state = workspace.read_json(session_path + "state.json")
        if saved_state:
            agent.memory.restore(saved_state["memory"])
            agent.toolkit.restore(saved_state["toolkit_state"])
            agent.plan.restore(saved_state["plan_state"])
            # Agent 精确知道上次停在哪一步

        return messages

    def on_post_call(self, agent, response, ctx):
        session_path = f"agents/{agent.id}/context/{ctx.session_id}/"
        workspace.write_json(session_path + "state.json", {
            "memory":        agent.memory.dump(),
            "toolkit_state": agent.toolkit.dump(),
            "plan_state":    agent.plan.dump(),
        })
        # 进程重启后，同一个 session_id 进来，从这里恢复，精确续点
```

---

### 上下文压缩作为 Hook 内置

这不是打进去的补丁，是框架的一部分：

```python
class CompactionHook:
    def on_pre_reasoning(self, agent, messages):
        if len(messages) < self.trigger_threshold:
            return messages

        recent  = messages[-self.keep_last:]
        old     = messages[:-self.keep_last]

        # 摘要包含：任务目标、已完成步骤、关键发现、当前状态、待办事项
        summary = llm.structured_summarize(old, schema=COMPACTION_SCHEMA)

        # 重要事实同时沉淀到 MEMORY.md
        workspace.append("MEMORY.md", summary.key_facts)

        return [summary.as_message()] + recent


class ToolResultEvictionHook:
    def on_post_acting(self, agent, tool_use, result):
        if len(result.text) <= self.max_chars:
            return result

        evicted_path = workspace.path(f"agents/{agent.id}/evicted/{tool_use.id}.txt")
        workspace.write(evicted_path, result.text)

        return ToolResult(
            text=f"[结果已存储，大小 {len(result.text)} 字，路径：{evicted_path}]"
        )
```

---

### 子 Agent 动态声明

```python
class DynamicSubagentsHook:
    def on_pre_call(self, agent, messages):
        spec_files = workspace.list_files("subagents/*.md")
        agent.toolkit.clear_subagents()

        for spec_file in spec_files:
            spec = parse_subagent_spec(spec_file)
            # spec 包含：name, description, model, system_prompt, tools
            agent.toolkit.register_subagent(
                name=spec.name,
                description=spec.description,   # LLM 靠这个决定何时调用
                factory=lambda: build_sub_agent(spec)
            )
        # 加一个 code-agent.md 文件，下次调用就多一个子 Agent
        return messages
```

---

### 完整调用流程

把这些 Hook 串起来，一次请求长这样：

```python
def harness_call(user_message, session_id, user_id):
    ctx = Context(session_id=session_id, user_id=user_id)

    # ── 调用开始前（由各 Hook 依次执行）────────────────────────────────
    # 1. SessionPersistenceHook：恢复上次的完整会话状态
    # 2. WorkspaceContextHook：读 AGENTS.md + MEMORY.md + KNOWLEDGE.md
    #    文件改了，这次调用立即生效
    # 3. DynamicToolsHook：读 tools.json，重新初始化 MCP 连接
    # 4. DynamicSkillHook：读 skills/*.md，更新技能列表
    # 5. DynamicSubagentsHook：读 subagents/*.md，注册子 Agent
    # ───────────────────────────────────────────────────────────────────

    for iter in range(max_iters):
        # CompactionHook：消息超阈值时自动压缩，关键事实写入 MEMORY.md
        response = llm.call(memory.get_all())   # Reason

        if not response.has_tool_call():
            break

        tool_result = toolkit.execute(response.tool_call)   # Act
        # ToolResultEvictionHook：超大结果落盘，上下文留占位符

        memory.add(tool_result)

    # ── 调用结束后 ─────────────────────────────────────────────────────
    # 1. SessionPersistenceHook：完整状态写回工作空间
    # 2. MemoryFlushHook：本次对话追加写入 sessions/ 永久日志
    # 3. MemoryMaintenanceHook：定期从 sessions/ 提炼事实，更新 MEMORY.md
    # ───────────────────────────────────────────────────────────────────

    return response
```

---

## v1 和 Harness 的差异对比

|  | v1 ReAct | Harness |
|--|--------|-------------|
| Agent 存在形式 | 每次请求临时组装，请求后销毁 | 持续住在工作空间，跨请求存活 |
| 配置载体 | 数据库表（人格/工具/MCP 分散存放）| 工作空间统一文件（一目录看全 Agent）|
| 工具动态性 | MCP + DB 配置，Agent 是只读消费者 | tools.json 在工作空间，Agent 可写 |
| 长期记忆 | 外部向量数据库（Memos / Mem0 等）| 工作空间 MEMORY.md，LLM 自己维护 |
| 会话恢复 | 靠向量检索（精度有限）| 精确序列化 + 反序列化 |
| 上下文管理 | 打进去的补丁 | 内置 CompactionHook |
| 子 Agent | 工厂里预先注册，改了要重启 | subagents/*.md 动态读取，加文件即可 |
| Agent 能否成长 | 不能，经验不沉淀 | 能，skills/ 自动增长，下次调用即可用 |
| 管理后台角色 | Agent 的组装工厂 | 工作空间的可视化编辑器 |

---

## 为什么文件比数据库更适合做 Agent 的配置

这个问题我想了很久。

v1 用数据库表来描述"Agent 是什么"——你要问清楚一个 Agent 的全貌，需要跑好几张表。Harness 用工作空间里的文件来描述——一个目录里，你能看到这个 Agent 的一切。

文件有几个特性，数据库没有：

LLM 能直接读写 Markdown，所以 `AGENTS.md` 不只是配置，它就是 Agent 的自我认知文本；工作空间是普通目录，可以用 Git 管理，技能演进有历史可查；最重要的是，Agent 可以修改自己的工作空间——成功的经验写入 `skills/`，学到的事实更新 `MEMORY.md`。

这是 v1 做不到的。在 v1 里，Agent 是一个消费者，配置系统是另一个主体。在 Harness 里，两者是同一个东西。

---

## 用哪种取决于你的问题

```
三个判断：

1. 任务需要跨越多次会话、持续数天吗？
   否 → v1 够用
   是 → Harness 的会话精确恢复不可少

2. 想在不改代码、不重启的前提下动态调整 Agent 的能力？
   否 → v1 + MCP 已经解决了工具层面的动态性
   是 → Harness 的 tools.json / subagents/ 才能做到

3. 想让 Agent 从每次运行中积累经验并提升能力？
   否 → v1 够用
   是 → Harness 的 skills/ 自演化机制才能实现
```

我自己的系统，这三个问题都是"是"，所以重构是值得的。

---

## 最后

从"每次请求临时组装一个 Agent"，到"Agent 有一个持久的工作空间，每次醒来读一读自己的家，然后去工作，结束后把状态写回家里"。

这个变化不大，但想法是不一样的：Agent 从一次性工具变成了有状态的居民。
