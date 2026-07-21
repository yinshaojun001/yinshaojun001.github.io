+++
title = "一文讲透 MCP：大模型如何发现并调用外部工具"
date = 2026-07-21T17:30:00+08:00
draft = false
slug = "mcp-model-context-protocol"
author = "尹绍钧"
tags = ["mcp", "agent", "function-calling", "json-rpc"]
series = ["Agent 系统学习"]
summary = "从 Host、Client、Server 到 JSON-RPC，沿着一次完整调用看懂 MCP 的工作原理、协议边界、传输方式、安全边界与落地场景。"
+++

大模型能写方案、做总结、生成代码，却无法凭空读取你电脑里的文件，也不知道公司数据库里刚产生的订单。要让它完成这些工作，应用需要给它接入外部能力，也就是我们常说的 Tool。

工具少的时候，直接使用 Function Calling 很顺手。应用把函数名称、用途和参数结构交给模型，模型根据用户问题决定要不要调用。真正执行函数的仍然是应用代码。

随着工具和 Agent 增多，问题开始从“模型会不会调用工具”转向“这些工具怎么接入、复用和治理”。MCP 正是在这个阶段发挥作用。

这篇文章从一次完整调用出发，拆开 MCP 的角色、消息、传输和执行过程。读完后，你应该能回答四个问题：

- MCP 解决了什么工程问题？
- MCP 和 Function Calling 各自负责哪一段？
- 一次工具调用在 Host、Client、Server 和模型之间怎样流转？
- 什么场景值得引入 MCP，又有哪些安全边界要提前处理？

## 一、工具多起来以后，接入成本会迅速膨胀

假设团队有客服、销售、数据分析 3 个 Agent，它们都要访问订单、用户和库存。

如果每个 Agent 都在自己的代码里维护工具定义、鉴权逻辑、请求封装和错误处理，3 个 Agent 乘以 3 组能力，最多会形成 9 份接入代码。订单接口改了字段，相关项目都要跟着修改和发布；新增一个 Agent，还得重新接一遍已有能力。

真正麻烦的地方不只在重复代码，还包括一整套长期维护工作：

- 工具的描述和参数结构散落在不同项目里，版本容易不一致；
- 每个项目各自处理凭证，密钥管理和权限回收很难统一；
- 超时、重试、日志、审计采用不同实现，出了问题很难追踪；
- Python 写的工具想给 TypeScript Agent 使用，往往还要再封装一层；
- Agent 很难动态得知某个能力已经新增、下线或发生变化。

传统软件工程处理这类问题时，通常会把共享能力放进独立服务，通过稳定接口向多个调用方开放。MCP 延续了这个思路，并把“能力如何被 AI 应用发现和调用”也纳入统一约定。

2024 年 11 月，Anthropic 发布 MCP，Model Context Protocol，中文通常译为模型上下文协议。

## 二、MCP 到底是什么

MCP 是一套开放协议，规定 AI 应用与外部能力之间如何建立连接、协商能力、发现内容、发起调用并接收结果。

协议可以理解为通信双方共同遵守的接口说明。它会明确：

- 消息采用什么结构；
- 初始化时交换哪些信息；
- 查询工具列表使用哪个方法名；
- 调用工具时参数放在哪里；
- 成功和失败怎样返回；
- 连接通过本地进程还是网络传输。

常见的“标准插座”比喻很直观：Host 支持 MCP 后，就可以连接文件系统、GitHub、数据库、浏览器等不同 Server。每个 Server 都按同一套协议描述自己的能力，Host 无需针对每一种服务重新设计通信流程。

不过，插座只是连接标准。电器能做什么、是否安全、由谁供电，仍由具体实现决定。同样，MCP 不负责让模型变聪明，也不会自动替应用做好权限控制。它解决的是连接层的标准化。

> **一句话概括**
>
> Function Calling 让模型表达“我想调用哪个函数”，MCP 让 AI 应用用统一方式发现并执行外部能力。

## 三、先认清三个核心角色

很多介绍只讲 MCP Client 和 MCP Server，容易漏掉真正组织整条链路的 Host。按照 MCP 的架构，可以把参与者分成三类。

### 3.1 Host：承载模型和用户体验的应用

Host 是用户直接使用的 AI 应用，例如桌面助手、IDE、代码 Agent 或企业内部智能助手。它通常负责：

- 管理对话和模型上下文；
- 创建并管理 MCP Client；
- 决定连接哪些 Server；
- 把可用工具交给模型；
- 执行权限确认和安全策略；
- 将调用结果重新放回模型上下文。

模型通常运行在 Host 的业务流程里。用户看到的确认弹窗、工具调用记录和错误提示，也由 Host 呈现。

### 3.2 Client：一条连接对应的协议客户端

MCP Client 是 Host 内部负责协议通信的组件。它与某个 MCP Server 建立有状态连接，发送 JSON-RPC 消息，并把响应交回 Host。

一个 Host 可以同时连接多个 Server，通常每条 Server 连接由一个 Client 维护：

```text
                           ┌─ MCP Client A ─ File Server
User ─ Host ─ Model ───────┼─ MCP Client B ─ GitHub Server
                           └─ MCP Client C ─ Database Server
```

Client 负责“怎么按 MCP 说话”，模型只需要看到整理后的工具定义和执行结果。

### 3.3 Server：提供上下文和能力

MCP Server 对外暴露一组能力，例如：

- 读取项目文件；
- 查询数据库；
- 创建 GitHub Issue；
- 获取提示词模板；
- 操作浏览器或设计工具。

Server 可以作为本地子进程运行，也可以部署成远程 HTTP 服务。它在收到请求后完成参数校验、权限检查和实际执行，再按 MCP 约定返回结果。

Server 后面还可以继续连接数据库、SaaS API 或公司内部服务：

```text
User
  │
  ▼
Host ─── LLM
  │
  ├── MCP Client ── MCP Server ── GitHub API
  ├── MCP Client ── MCP Server ── Database
  └── MCP Client ── MCP Server ── Local Files
```

这张图里，LLM 没有直接连接 Server。Host 和 Client 承担协议通信与执行编排，模型负责理解意图、选择能力和生成参数。

## 四、一次 MCP 连接是怎样建立的

理解 MCP 最有效的方式，是沿着一条消息链往下看。

假设用户在一个支持 MCP 的桌面助手里输入：“查询订单 ORD-2026-0721 的状态。”应用已经配置了订单 MCP Server。

### 第一步：Host 启动连接

如果使用 `stdio`，Host 会启动一个本地 Server 子进程；如果使用 Streamable HTTP，Host 会连接远程 MCP 地址。随后，Host 内部对应的 Client 开始初始化。

### 第二步：Client 与 Server 握手

Client 先发送 `initialize` 请求，携带自己支持的协议版本、能力和客户端信息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "<supported-version>",
    "capabilities": {},
    "clientInfo": {
      "name": "example-host",
      "version": "1.0.0"
    }
  }
}
```

Server 返回双方可以共同使用的协议版本、Server 能力和基本信息：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "<negotiated-version>",
    "capabilities": {
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "order-server",
      "version": "1.3.0"
    }
  }
}
```

Client 接受初始化结果后，再发送一条无需响应的通知：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

这一步很像两个人通话前先确认语言和可用功能。能力协商完成后，Client 才开始正常调用。

### 第三步：Client 获取工具列表

Host 需要知道订单 Server 提供哪些工具，于是通过 Client 发送 `tools/list`：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

Server 返回工具名称、自然语言描述和输入参数结构：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "query_order",
        "description": "根据订单号查询订单状态、金额和更新时间",
        "inputSchema": {
          "type": "object",
          "properties": {
            "order_id": {
              "type": "string",
              "description": "完整订单号，例如 ORD-2026-0721"
            }
          },
          "required": ["order_id"]
        }
      }
    ]
  }
}
```

这段定义非常重要。模型看不到 `query_order` 背后的 SQL 和接口代码，它只能根据名称、描述和参数结构判断何时调用。因此，含糊的工具描述会直接影响模型的选择与参数质量。

### 第四步：Host 把工具定义交给模型

Host 将 MCP 返回的工具描述转换成当前模型 API 支持的 Tool 格式，与用户问题一起发给模型。

模型读到用户问题和工具说明后，可能输出类似这样的调用意图：

```json
{
  "name": "query_order",
  "arguments": {
    "order_id": "ORD-2026-0721"
  }
}
```

这里发生的是 Function Calling。模型生成结构化的调用请求，没有执行数据库查询。

### 第五步：Host 通过 MCP 执行工具

Host 收到模型的调用意图，先按自身策略检查权限。需要用户确认时，可以先弹出确认界面。确认通过后，Client 向订单 Server 发送 `tools/call`：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_order",
    "arguments": {
      "order_id": "ORD-2026-0721"
    }
  }
}
```

Server 校验参数，调用订单服务，然后返回结果：

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "订单 ORD-2026-0721，金额 299 元，状态为已发货，更新时间 2026-07-21 10:32。"
      }
    ],
    "isError": false
  }
}
```

### 第六步：结果回到模型上下文

Host 将工具结果作为一条 Tool Result 交给模型。模型结合用户原始问题和查询结果，生成最终回答：“订单已经发货，最近更新时间为今天 10:32。”

如果任务还没完成，模型可以继续选择下一个工具。例如用户要求“查完订单后邮件通知负责人”，模型拿到订单结果后，还会生成 `send_email` 调用。Host 再执行一轮相同流程。

完整链路可以压缩成下面 8 步：

```text
1. Client ── initialize ───────────────> Server
2. Client <─ capabilities ───────────── Server
3. Client ── tools/list ──────────────> Server
4. Host   ── user message + tools ────> LLM
5. Host   <─ tool call ──────────────── LLM
6. Client ── tools/call ──────────────> Server
7. Client <─ tool result ────────────── Server
8. Host   ── tool result ─────────────> LLM ──> final answer
```

> **注意调用边界**
>
> `tools/list` 和 `tools/call` 由 Host 内的 MCP Client 发送。模型负责给出调用意图，无法亲自向 Server 发网络请求。把这两个层次分清，MCP 的运行原理就容易理解了。

## 五、MCP 和 Function Calling 是什么关系

这两个概念经常同时出现，因为它们位于同一条调用链的不同位置。

Function Calling 是模型 API 提供的结构化输出能力。应用把工具描述交给模型，模型返回要调用的工具名和参数。不同模型厂商的字段和接口可能有差异。

MCP 是 AI 应用与能力提供方之间的通信协议。它负责连接管理、能力发现和标准化调用，让 Host 可以用统一方式接入不同 Server。

| 维度 | Function Calling | MCP |
|---|---|---|
| 连接的两端 | 应用与模型 | MCP Client 与 MCP Server |
| 主要问题 | 模型如何表达调用意图 | 应用如何发现和执行外部能力 |
| 工具来源 | 由应用代码直接提供 | Client 从 Server 动态获取 |
| 执行位置 | 由应用自行决定 | 由对应 MCP Server 执行 |
| 规范来源 | 模型厂商 API | 开放的 MCP 规范 |
| 是否可以单独使用 | 可以 | 可以配合不同模型或确定性程序使用 |

在常见 Agent 中，两者会这样配合：

```text
MCP Server 提供工具
        ↓
MCP Client 获取工具定义
        ↓
Host 转换成模型支持的 Tool 格式
        ↓
模型通过 Function Calling 选择工具和参数
        ↓
Host 再通过 MCP Client 调用 Server
```

因此，MCP 没有替代 Function Calling。它补齐了工具从哪里来、怎样连接、怎样复用和怎样执行这一段工程链路。

## 六、协议底座：JSON-RPC 2.0

MCP 的消息采用 JSON-RPC 2.0。它结构简单，核心消息只有 Request、Response 和 Notification 三类。

### 6.1 Request：发起请求并等待结果

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/list",
  "params": {}
}
```

- `jsonrpc` 固定为 `2.0`；
- `id` 是请求标识，用来匹配异步返回的响应；
- `method` 表示要执行的协议方法；
- `params` 携带参数。

Client 和 Server 都可以发起 Request，具体方向由协议方法定义。

### 6.2 Response：返回成功结果或错误

成功响应：

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "tools": []
  }
}
```

失败响应：

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

响应里的 `id` 必须与请求一致。调用并发发生时，Client 依靠它把结果交给正确的请求。`result` 和 `error` 只会出现其中一个。

### 6.3 Notification：单向通知

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

Notification 没有 `id`，接收方也不用返回 Response。它适合表达“初始化已经完成”“工具列表发生变化”这类事件。

JSON-RPC 只定义消息骨架。MCP 在它上面继续规定了 `initialize`、`tools/list`、`resources/read` 等方法，以及每个方法的参数和返回结构。

## 七、Server 可以提供哪些能力

MCP 最常见的三类 Server 原语是 Tools、Resources 和 Prompts。可以把它们理解为“执行能力、上下文数据和可复用对话模板”。

### 7.1 Tools：由模型选择的可执行能力

Tool 用名称、描述和输入结构声明一个可调用操作，例如：

- 查询订单；
- 创建日程；
- 搜索代码；
- 发送消息；
- 生成图片。

Tool 既可以执行只读查询，也可以修改外部状态。是否产生副作用取决于具体工具。查询天气通常只读，发送邮件会产生真实影响。

Server 应明确描述副作用，Host 也应针对高风险操作增加确认。模型输出了调用意图，并不代表应用必须立即执行。

### 7.2 Resources：由应用读取的上下文数据

Resource 通过 URI 标识可读取内容，例如：

```json
{
  "uri": "file:///project/README.md",
  "name": "项目说明",
  "mimeType": "text/markdown"
}
```

也可以使用业务自定义 URI：

```text
db://customers/42
docs://handbook/security
git://repository/main/src/app.ts
```

Host 可以通过 `resources/list` 发现资源，再用 `resources/read` 获取内容。部分实现还支持资源模板、订阅和变更通知。

Resource 的选择通常由应用或用户控制。它很适合把文件、文档和业务记录加入模型上下文，避免把所有数据都包装成可执行函数。

### 7.3 Prompts：可发现的对话模板

Prompt 是 Server 提供的参数化消息模板。比如一个代码审查 Server 可以暴露：

```json
{
  "name": "review_code",
  "description": "按团队规范审查一段代码",
  "arguments": [
    {
      "name": "language",
      "required": true
    },
    {
      "name": "code",
      "required": true
    }
  ]
}
```

用户在 Host 中选择这个 Prompt 并填写参数后，Client 通过 `prompts/get` 取回一组消息，Host 再把它们送进对话。

三类原语可以这样区分：

| 原语 | 提供的内容 | 常见触发方 | 例子 |
|---|---|---|---|
| Tool | 可执行操作 | 模型 | 查订单、发邮件、建 Issue |
| Resource | 可读取上下文 | 应用或用户 | 文件、文档、数据库记录 |
| Prompt | 参数化消息模板 | 用户 | 代码审查、周报生成 |

> **理解三类原语的线索**
>
> “谁控制触发”是理解三类原语的好方法：Tool 通常由模型选择，Resource 通常由应用管理，Prompt 通常由用户主动选择。具体产品也可以设计自己的交互方式。

## 八、消息通过什么方式传输

MCP 把协议语义和传输方式分开。前者规定消息表达什么，后者决定消息走本地进程管道还是 HTTP 网络。

当前主要使用 `stdio` 和 Streamable HTTP。旧版 HTTP + SSE 传输主要用于兼容已有 Server。

### 8.1 stdio：适合本地 Server

在 `stdio` 模式下，Host 把 Server 作为子进程启动，通过标准输入和标准输出交换消息：

```text
Host / MCP Client
    │
    │ stdin: JSON-RPC message
    ▼
MCP Server process
    │
    │ stdout: JSON-RPC message
    ▼
Host / MCP Client
```

这种方式部署简单，Server 可以跟随 Host 一起启动和退出，适合文件系统、Git、本地设计工具等场景。

Server 的 `stdout` 专门用于协议消息。调试日志应写入 `stderr`，否则混入普通文本后，Client 可能无法正确解析 JSON-RPC。

### 8.2 Streamable HTTP：适合远程 Server

远程 Server 通常提供一个 MCP HTTP 端点，Client 通过 HTTP POST 发送 JSON-RPC 消息：

```http
POST /mcp HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

简单调用可以直接返回 JSON 响应；需要流式传递多条消息时，也可以通过 SSE 事件流返回。相比旧版的独立 SSE 端点，Streamable HTTP 把远程通信统一在 MCP 端点上，更利于网关、鉴权和基础设施接入。

它适合团队共享服务、云端 SaaS 和企业内部平台。远程部署也意味着必须认真处理身份认证、租户隔离、限流、超时和网络故障。

### 8.3 旧版 HTTP + SSE：用于兼容

早期 MCP 远程传输会先建立 SSE 长连接接收消息，再通过另一个 HTTP POST 端点发送请求。已有实现仍可能使用它，新项目一般优先采用 Streamable HTTP。

| 传输方式 | Server 形态 | 典型场景 | 需要关注 |
|---|---|---|---|
| stdio | 本地子进程 | 文件、Git、本地工具 | 进程权限、日志与协议输出分离 |
| Streamable HTTP | 独立网络服务 | 团队共享、云服务 | 鉴权、会话、限流、网络错误 |
| 旧版 HTTP + SSE | 长连接服务 | 兼容旧实现 | 连接维护、重连 |

传输方式不会改变 `tools/list` 和 `tools/call` 的含义。同一条 JSON-RPC 请求既可以走进程管道，也可以放进 HTTP 请求体。

## 九、MCP 把 M × N 变成 M + N，前提是什么

MCP 经常被概括为把 M 个应用接 N 个工具的复杂度从 M × N 降到 M + N。这个结论成立需要两个条件：

1. M 个 Host 都实现或复用兼容的 MCP Client；
2. N 组能力都通过规范一致的 MCP Server 暴露。

完成标准化后，每个 Host 只需理解 MCP，每个能力也只需实现一次 MCP 接口。订单服务更新时，团队主要维护订单 Server；新 Agent 接入时，可以直接发现已有工具。

但协议统一不会消除业务复杂度。字段兼容、权限模型、服务稳定性、工具描述质量和版本迁移依然需要工程治理。MCP 降低的是连接和集成成本。

## 十、安全边界：能连上不等于可以放心执行

MCP Server 可能获得文件、命令行、数据库和第三方账号权限。一旦它被错误配置或遭到恶意利用，影响会超出一次模型回答。

落地时至少要处理以下几层防线。

### 10.1 最小权限

只给 Server 完成任务所需的权限。只读文件场景不要开放写权限，查询数据库使用只读账号，GitHub Token 只授予必要仓库和必要 Scope。

### 10.2 用户确认

发送邮件、删除文件、创建订单、发布内容等操作会改变外部状态。Host 应在执行前展示工具名称和关键参数，让用户清楚知道将发生什么。

### 10.3 参数校验

Server 不能因为参数由模型生成就默认可信。所有输入都要做类型、长度、范围和业务权限检查；涉及文件路径、SQL、Shell 或 URL 时，还要防止路径穿越、注入和 SSRF。

### 10.4 凭证隔离

密钥放在 Server 或安全凭证系统中，不要塞进工具描述、模型上下文或调用结果。远程 Server 还要验证调用方身份，并把用户授权绑定到正确会话。

### 10.5 返回内容同样不可信

网页、文档和第三方 API 可能包含提示注入内容。Host 不应把 Server 返回的一切都当成高优先级指令。外部数据应保持数据身份，工具权限也不能因为一段返回文本而自动扩大。

### 10.6 审计与超时

记录谁在什么时间调用了哪个工具、使用了哪些关键参数、结果是否成功。每次调用都应设置超时、取消和结果大小限制，防止任务长期占用资源或把过大内容塞进上下文。

> **安全边界**
>
> MCP 统一了调用方式，没有替 Server 做身份认证、授权和业务风控。Server 作者、Host 作者和部署方都要承担对应的安全责任。

## 十一、什么时候适合引入 MCP

下面这些场景通常能从 MCP 中获得明显收益：

- 多个 Agent、IDE 或桌面应用需要共享同一组能力；
- 希望工具跨 Python、TypeScript、Java 等技术栈复用；
- 工具需要独立部署、升级和监控；
- Host 需要动态发现工具、资源或 Prompt；
- 团队准备建立统一的权限、审计和能力目录；
- 希望接入现成 MCP 生态，减少逐个 API 适配的工作。

下面这些阶段可以先保持简单：

- 只有一个应用和少量稳定工具；
- 工具逻辑与当前业务代码高度耦合；
- 团队还在验证产品价值，接口变化很快；
- 一次性脚本就能完成任务，长期复用价值有限。

可以用三个问题做判断：

1. 这项能力会被多个 Host 或项目使用吗？
2. 它需要独立的权限、审计、发布和生命周期管理吗？
3. 标准化接入带来的收益，能覆盖运行一个 Server 的成本吗？

如果答案大多为“是”，MCP 通常值得引入。

## 十二、几个常见误区

### 误区一：模型直接连接 MCP Server

网络连接由 Host 中的 MCP Client 建立。模型接收工具定义，输出调用意图，再由 Host 决定是否执行。

### 误区二：用了 MCP 就不用 Function Calling

在常见实现里，Host 仍会把 MCP Tool 转成模型 API 的工具格式，模型仍通过 Function Calling 选择工具。两者各自覆盖一段链路。

### 误区三：MCP Server 都部署在远程

很多 Server 通过 `stdio` 在本机运行，只有共享或跨网络场景才需要 Streamable HTTP。

### 误区四：Tool 都会修改外部状态

Tool 可以查询，也可以写入。是否有副作用由具体能力决定。Resource 更强调可寻址的上下文读取，Tool 更强调模型可选择的执行入口。

### 误区五：接入协议后自然获得安全能力

协议提供标准消息和生命周期，权限、授权确认、参数校验、凭证管理和审计仍需在 Host、Server 与基础设施中实现。

## 十三、最后用一张图记住 MCP

![一次 MCP 工具调用的信息流：模型负责选择，Host 负责执行，Server 负责访问真实系统](/images/wechat/mcp-model-context-protocol/mcp-call-flow.png)

MCP 的核心价值，可以归结为一句话：它给 AI 应用与外部能力之间增加了一层稳定、可发现、可复用的协议接口。

模型继续负责理解用户意图和规划下一步，Host 继续负责上下文与执行控制，Server 继续负责访问真实系统。MCP 把这些角色之间的沟通方式固定下来，让同一项能力更容易被不同 AI 应用使用。

当工具只有两三个时，这层协议可能显得多余；当 Agent、工具、团队和权限边界同时增长时，标准化连接会直接影响系统能否长期维护。

理解 MCP 的关键也落在这里：先分清模型、Host、Client 和 Server 各自在做什么，再沿着 `initialize → tools/list → Function Calling → tools/call → tool result` 走一遍，整套原理就串起来了。
