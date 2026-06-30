+++
title = "我成了 AI 循环里的一环——Loop Engineering 到底是什么"
date = 2026-07-01T02:17:00+08:00
draft = false
slug = "loop-engineering"
tags = ["AI", "Agent", "Loop Engineering", "Claude Code", "工程化"]
series = ["Java 老兵转型 AI"]
summary = "从一次线上故障排查，理解正在改变 AI 协作方式的 Loop Engineering：不再手动提示 AI，而是设计让 AI 自己提示自己的系统。"
+++

某天早上，线上 agent 总超时，业务那边一直在反馈。

查了生产日志，是记忆模块 memos 挂了。这种事之前碰到过，重启就好。于是我登上服务器：

```bash
docker restart memos-product-api
docker logs -f --tail=200 memos-product-api
```

日志启到一半，停了。

agent 那边仍然 `connect refused`，curl 了一下 `Connection reset by peer`。我把日志扔给 Codex 求助。

它给了我几千字——十万种可能性。头昏眼花，看不下去。

我说：一条条来，不要猜测，给我指令，我来执行，你来验证。

于是就成了这样：

> Codex：执行 `docker ps | grep -i product`，结果发我
>
> 我：贴结果
>
> Codex：进程还在，但健康检查失败。执行 `docker inspect xxx --format '{{json .State.Health}}'`
>
> 我：贴结果
>
> Codex：再执行这个……

如此反复，大概十几轮之后——

> Codex：执行 `docker ps -a | grep -i milvus`

我刚想贴结果，定睛一看。

向量库怎么停了？

```
memos-milvus    Exited (255) 2 days ago
```

把 milvus 重启，等服务稳了，验证注册召回正常。历时 15 分钟，搞定。

处理完我狠狠回味了一下。

坏了。我成了循环里的一环。

---

## 我到底在干什么

那个场景里，我的角色很清楚：给 AI 提供指令触发，提供执行环境，提供验证结果，决定什么时候结束。

AI 出主意，我跑腿，我看结果，我判断"成了没有"。

你以为在用 AI，其实在充当 AI 的工具调用接口。

这不是一个舒服的发现。但我觉得很多人都在这个循环里，只是没意识到。

---

## 两句话点醒我

Peter Steinberger（OpenClaw 作者）前段时间发了条推：

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents."

Boris Cherny，Claude Code 的负责人，也说：

> "I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops."

Addy Osmani 把这个叫做 Loop Engineering，定义很干净：

> Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead.

换句话说：你从手动开枪的人，变成设计自动武器的人。

听起来很酷。但我一开始是怀疑的——这不就是套了个壳的定时任务吗？折腾了一圈，就是个 cron job？

不完全是。区别在哪里，慢慢说。

---

## 用我那次故障来想象一下

回头看那次 memos 排查，如果有个设计好的 loop，它应该是这样跑的：

定时任务每几分钟检查一次各服务健康状态 → 发现 agent 注册失败 → 定位到 memos 连接问题 → 自动跑 docker inspect、docker ps、curl 等诊断指令 → 检查结果 → 没找到原因就换方向继续排查 → 找到了就自动重启，再验证一遍

全程我不用在电脑前，不用一步步贴结果。

我唯一要做的：定义什么叫"成功"。

这是 loop 和手动提示最本质的区别。工作单元从"一条 prompt"变成了"一个目标"。

---

## Loop 需要哪些东西

Osmani 的原文把 loop 拆成五个构件，加上一个记忆层。我挨个说一下，结合自己的理解。

**Automations — 心跳**

没有自动触发，loop 就不是 loop，只是"你手动跑了一次"。

给 agent 一个触发条件——定时、事件、webhook——让它自己醒来找活干，把结果送到你的 inbox。不是你去问它，是它来找你。

Claude Code 里有 `/loop`（周期执行）、`/goal`（跑到条件满足才停）、hooks、scheduled tasks，这些都是这个层面的东西。

**Worktrees — 隔离并行**

跑多个 agent 的时候，文件冲突几乎是必然的。两个 agent 写同一个文件，和两个工程师没沟通直接 commit 同一行没区别。

git worktree 给每个 agent 一个独立的工作目录，分支隔离，互不干扰。Claude Code 里用 `--worktree` 或者 `isolation: worktree` 参数，做完自动清理。

**Skills — 把知识写出来**

每次新会话，agent 从零开始。它不知道你的项目约定，不知道哪些坑踩过，不知道"我们不这么做是有原因的"。

Skills 就是把这些写在外部，agent 每次启动时读取。格式很简单，一个文件夹加一个 SKILL.md。

我自己感受最深的是这个：没有 Skills，loop 每轮都在重新推断你的整个项目。有了 Skills，它才能积累。

**Connectors — 接入真实世界**

只能看文件系统的 loop 是孤岛。Connectors（基于 MCP 协议）让 agent 读 issue tracker、查数据库、调 staging API、发 Slack 消息。

一个只会说"这是修复方案"的 agent，和一个直接开 PR、关联 ticket、CI 绿了自动 ping 频道的 loop，差距就在这里。

**Sub-agents — 写的和审的不能是同一个**

这是我觉得最关键的一点。

模型给自己的作业打分，永远是满分。你让它自己验证自己，它永远觉得没问题。

独立的 sub-agent，带着不同指令，甚至不同模型，来做检查——这样才能抓住第一个 agent 说服自己的那些错误。

Claude Code 的 `/goal` 本质上也是这个思路：一个独立的小模型来判断"完成了没有"，而不是做完事的那个 agent 自己说"我完成了"。

**+1 Memory — 外部记忆**

这个听起来简单，但没有它 loop 就是散的。

模型跑完一轮就忘了。你需要一个外部状态文件，markdown 也好，Linear 也好，记录什么做了、什么失败了、下次从哪里继续。

agent 会遗忘，repo 不会。

---

## 什么任务适合用 Loop

说了这么多，loop 不是万能的。我用自己的标准过了一遍，什么情况下值得设计 loop：

需要定期重复跑的。服务健康检查、CI 失败汇总、每日 issue triage——有节奏的活，不是一次性的活。

有客观完成标准的。"服务正常运行"可以被验证。"写一篇好文章"不行。没有客观 break 条件，loop 会一直跑直到把账户烧空，这不是玩笑。

AI 能自己把事办完的。如果 loop 每跑几步就要停下来等你回答，和手动提示没什么区别，反而多了一层复杂度。

错误有恢复路径的。自动运行意味着你不在现场，任务本身要允许失败和重试，"错一次就不可逆"的操作别放进 loop。

---

## 成本这件事不能绕过去

我永远忘不了跑了 6 个子 agent，干了十分钟，烧了 50 块钱的经历。那之后我对 loop 的态度谨慎了很多。

Loop 的 token 消耗不是线性的。每一轮在上一轮的 context 上堆叠，再乘以 sub-agent 数量。跑偏的 loop 不是慢慢烧钱，是利滚利。

Osmani 自己也说 still skeptical，这不是客气话。

设计 loop 之前要问自己几个问题：每一轮循环是不是真的在向目标前进，不能 loop 10 次有 9 次在兜圈子。break 条件是不是足够清晰，模糊的 break 条件约等于没有。有没有最大轮次的硬限制，即使 break 条件没触发，也要有个"最多跑 N 轮"的兜底。

---

## Loop 不是让你消失

最后，Osmani 原文有一段我反复看了几遍：

> "Two people can build the exact same loop and get completely opposite results. One uses it to move faster on work they understand deeply. The other uses it to avoid understanding the work at all. The loop doesn't know the difference. You do."

两个人用完全相同的 loop，结果可以截然相反。一个用它在深度理解的基础上提速，另一个用它逃避理解。

Loop 分不清楚，你自己分得清楚。

这比提示词工程难，因为杠杆点换了。以前写好一条 prompt 就够，现在你要对整个系统的行为负责，要对它跑偏的时候负责，要对它做了你没想到的决定负责。

回到那次故障。如果有个设计好的巡检 loop，向量库停掉的当天就应该被发现，自动排查，自动重启，给我推一条通知：milvus 挂了 2 天，已重启，服务恢复正常。

我确认那条通知就够了。

那才是我该站的位置。定义"成功"是什么，而不是亲手把每一步执行出来。

构建循环，但要以工程师的姿态去构建它。不是按下"开始"按钮的那个人，是设计这个按钮该在什么时候触发的那个人。
