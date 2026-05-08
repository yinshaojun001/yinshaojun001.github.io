+++
title = "learn-claude-code 学习笔记"
date = 2026-03-19T01:06:00+08:00
draft = false
slug = "learn-claude-code-study-notes"
tags = ["AI", "Agent", "Claude Code", "Python", "教程"]
series = []
summary = "用一段 200 行的 Python 代码，带你彻底搞懂 Agent 到底是什么。"
+++

![图片](/images/wechat/learn-claude-code-study-notes/image_0.png)

最近看到了一个访谈，提到了一个中了大奖和被截肢的两个人，2 年以后的快乐程度是相同的，于是他谈到了 human 的一个 loop：

```python
for{
    渴望->多巴胺->满足->空虚
}
```

是不是用这种方式也能训练一个 ai 呢？

你有没有想过，AI 不只能聊天，还能帮你干活？本文用一段 200 行的 Python 代码，带你彻底搞懂 Agent 到底是什么。

最近看到很多人强推的 github 项目：learn-claude-code

https://learn.shareai.run/zh/s01/

很简单 慢慢跟着可以手搓一个 agent，主要看看工程方面有什么启发。

## 一、从"嘴炮 AI"到"干活 AI"

普通的 AI 对话是这样的：

```
你：帮我查一下这个目录有哪些文件。
AI：好的！通常你可以使用 ls 命令来查看目录中的文件……
```

然后你自己去终端敲命令。

Agent 版的对话是这样的：

```
你：帮我查一下这个目录有哪些文件。
AI：（悄悄打开终端，ls -la 跑完了）当前目录共有 12 个文件，其中……
```

一个是"嘴炮选手"，一个是"真·打工人"。

这就是 Agent（智能体）的核心价值：它不只说，它还做。

## 二、Agent 的三个核心组件

把 Agent 想象成一个新来的实习生，他需要三样东西才能开始干活：

### 1. 大脑（LLM）

大语言模型就是 Agent 的大脑，负责理解任务、制定计划、决定下一步。

```python
response = client.messages.create(
    model=MODEL,        # 选哪个大脑（Claude / GPT 等）
    system=SYSTEM,      # 给大脑的岗位职责书
    messages=messages,  # 对话历史（记忆）
    tools=TOOLS,        # 大脑能用的工具清单
    max_tokens=8000,
)
```

类比：大脑在看完"岗位职责书"和"历史任务记录"后，决定下一步要干什么。

### 2. 工具（Tools）

光有大脑不够，还得有手。工具就是 Agent 的"手"。

```python
TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]
```

这段代码定义了一个 bash 工具：AI 可以通过这个工具在电脑上执行任意 Shell 命令。

这意味着什么？AI 现在可以：
- 查看文件：`ls -la`
- 运行代码：`python3 main.py`
- 安装依赖：`pip install requests`
- 查询数据库、调用 API……

工具是 Agent 的超能力，但也是潘多拉魔盒。所以代码里加了一个简单黑名单：

```python
dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
if any(d in command for d in dangerous):
    return "Error: Dangerous command blocked"
```

### 3. 记忆（Messages）

Agent 的记忆就是一个不断增长的消息列表：

```python
history = []
history.append({"role": "user", "content": "帮我查文件"})
history.append({"role": "assistant", "content": response.content})
history.append({"role": "user", "content": tool_results})
```

注意这个骚操作：工具执行结果是以 `"role": "user"` 的形式回填给模型的！

这是 Anthropic API 的设计：工具结果统一封装成 `tool_result` 消息，塞进 `user` 角色的消息里。

类比：实习生（AI）说"我去查一下"，然后查完回来汇报给自己，再决定下一步。

## 三、Agent Loop：会转的魔法陀螺

有了这三样东西，就可以构建 Agent Loop（智能体循环）了。

```python
def agent_loop(messages: list):
    while True:  # ← 陀螺开始转
        response = client.messages.create(...)  # 问 AI 下一步
        messages.append(assistant_message)  # 记住 AI 说了啥

        if response.stop_reason != "tool_use":  # AI 说"我搞定了"
            return  # ← 陀螺停下来

        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])  # 真正执行
                results.append(tool_result)

        messages.append(tool_results)  # 把结果告诉 AI
```

这个循环的逻辑非常简单，用人话说就是：

1. 问 AI：下一步要干啥？
2. AI 说：我要用 bash 执行这个命令
3. 执行命令，把结果告诉 AI
4. 回到第 1 步，AI 再想下一步
5. 直到 AI 说：我不需要工具了，任务完成！

这就是 Agent Loop。它之所以叫"循环"，是因为它会一直转，直到任务完成。

**stop_reason 的两种状态：**
- `"tool_use"` → AI 还没完成，需要用工具，继续循环
- `"end_turn"` → AI 认为任务完成，退出循环

整个 Agent 的逻辑就靠这一个字段驱动。

## 四、一次完整的 Agent 执行流程

让我们用一个真实例子来感受一下：

你输入：帮我统计当前目录有多少个 Python 文件

**第 1 轮：**
→ 你的消息发给 AI
← AI 返回：我要执行 bash: `find . -name "*.py" | wc -l`
→ 执行命令，输出：42
→ 把"42"塞回消息列表

**第 2 轮：**
→ 消息列表（含工具结果）发给 AI
← AI 返回：当前目录共有 42 个 Python 文件。
→ stop_reason = "end_turn"，循环结束

最终输出：当前目录共有 42 个 Python 文件。

2 轮对话，1 次工具调用，搞定！

## 五、System Prompt：给实习生的"岗位说明书"

```python
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
```

注意最后一句："Act, don't explain."

这是 Agent 设计的核心思想之一：让 AI 干活，而不是解释该怎么干。

如果不加这句话，AI 会给你写一篇《如何统计 Python 文件数量》的教程。

加了这句话，AI 就乖乖地直接 `find . -name "*.py" | wc -l` 了。

**System Prompt 是 Agent 的"人设"。** 好的 System Prompt 能让 Agent：
- 知道自己在做什么（角色定位）
- 知道能用什么工具（能力边界）
- 知道以什么风格响应（行为规范）

坏的 System Prompt 会让 Agent 在你问"查文件"的时候，给你讲《Linux 文件系统原理》。

## 六、错误处理：真·打工人也会遇到烂事

代码里有完善的异常处理：

```python
except PermissionDeniedError:
    print("请求被服务端策略拦截")  # 被封了
except RateLimitError:
    print("请求频率过高，请稍后重试")  # 发太快了
except APIConnectionError:
    print("网络连接失败")  # 断网了
except APIStatusError as exc:
    print(f"服务返回错误（status={status_code}）")  # 服务器翻车
```

这些错误在真实使用中都会遇到。好的 Agent 需要能优雅地处理这些情况，而不是一个报错把整个程序崩掉。

![图片](/images/wechat/learn-claude-code-study-notes/image_1.png)

## 七、完整的数据流图

```
用户输入
↓
[消息列表 history]
↓
Claude API（LLM）
↓
stop_reason == "tool_use"? ──→ 否 → 打印结果，结束
↓ 是
执行 bash 命令
↓
结果追加到 history
↓
（回到 Claude API）
```

整个 Agent 的工作方式，就是在这个循环里不断地"想 → 做 → 反馈 → 再想"。

## 八、总结：Agent = LLM + 工具 + 循环

| 组件 | 作用 | 代码中的体现 |
|------|------|-------------|
| LLM | 大脑，负责决策 | `client.messages.create(...)` |
| 工具 | 手脚，负责执行 | `run_bash(command)` |
| 消息历史 | 记忆，负责上下文 | `messages` 列表 |
| Agent Loop | 协调者，负责驱动 | `while True` 循环 |

**Agent = LLM + Tools + Memory + Loop**

这四样东西凑在一起，就是一个最简单的 AI Agent。

## 写在最后

这段代码只有 200 行，却完整实现了一个可用的 Coding Agent。

真正的 Agent 框架（比如 LangChain、AutoGPT、Claude Code 本身）会在此基础上加入：
- 多种工具（文件读写、网络请求、代码执行……）
- 更复杂的记忆管理（向量数据库、长期记忆……）
- 多 Agent 协作（一群 AI 分工合作……）
- 更完善的错误恢复机制

但万变不离其宗——Agent Loop 的核心思想永远是这 4 样东西。

搞懂了这 200 行代码，但是其实真实的 loop 就只有 30 行，你就搞懂了 Agent 的灵魂。

剩下的，不过是"灵魂"的装修与扩建。

> 本文代码参考：learn-claude-code/agents/s01_agent_loop_annotated.py
