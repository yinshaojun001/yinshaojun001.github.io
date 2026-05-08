+++
title = "AI 时代，该怎么做调研？"
date = 2026-03-16T02:39:00+08:00
draft = false
slug = "ai-era-how-to-research"
tags = ["AI", "调研", "Agent", "转型"]
series = ["Java 老兵转型 AI"]
summary = "一个写了 7 年 Java 的工程师，转型 AI Agent 的真实记录。第一个问题不是怎么学，而是信谁。"
+++

![图片](/images/wechat/ai-era-how-to-research/image_0.png)

系列：一个写了 7 年 Java 的工程师，转型 AI Agent 的真实记录 · 第①期

好久不见。好久不写公众号，不定期分享最近的 agent 学习。

![图片](/images/wechat/ai-era-how-to-research/image_1.png)

## 突如其来的一刀

我，一个写了 7 年 Java 的工程师，突然不写 Java 了。

ai 没给我这个程序员干掉，倒是给我需求干掉了，跑去做 AI Agent。

我当时的内心活动大概是这样的：

Java → AI Agent，这是要让我直接从农耕时代跨越到星际时代吗？

其实说完全没基础也不公平。从 2022 年底 ChatGPT 横空出世，我就开始用 AI 了。但说实话，我的"用 AI"基本停留在一个层面：

让 AI 帮我写代码、改 bug、查文档。

说白了，就是把它当一个不要钱的高级搜索引擎 + 代码补全。

而现在要我深入理解 Agent 框架、多模型协作、工程化落地……

差距不是一点点，是一个维度的差距。

![图片](/images/wechat/ai-era-how-to-research/image_2.png)

## 信息焦虑：AI 圈的信息到底信谁？

转型的第一个拦路虎，不是技术，而是信息。

AI 发展之快，用"每天都是新闻"来形容都嫌保守。每打开一个社交平台：

- 某某说 GPT-5.4要来了，颠覆一切，技术人真要没了
- 某某说 Claude code cli才是未来，cursor 要凉了
- 某某说 Agent 落地难，全是泡沫
- 某某说他用 openclaw 一天赚了xx

这些"某某"们有个共同特点：他们都让我十分焦虑。

问题来了：我到底该信谁？

## 一个原则救了我：Follow the builders, not influencers

关注了一位我非常欣赏的产品经理 张咋啦，他说过一句话：

> Follow the builders, not influencers.

追随真正在造东西的人，而不是营销号。

这句话太准了。

AI 圈营销号多到泛滥——各种分析报告、热点解读、"深度好文"，看完之后热血沸腾，但你什么都没学到，只是焦虑升了一个等级。

而"造东西的人"不一样。他们每一行代码、每一个开源项目，都是真实的思考结晶。跟着这些人走，才是真正在学习 AI。

那么问题就变成了——谁是 builder？

![图片](/images/wechat/ai-era-how-to-research/image_3.png)

## 我找到的第一个 Builder：Andrej Karpathy

如果你在 AI 圈稍微混过一段时间，一定听过这个名字：

Andrej Karpathy

前 OpenAI 联合创始人之一，前 Tesla AI 总监，深度学习领域的顶级研究者。但他最厉害的地方，不只是他做过什么，而是他讲东西的方式。

他能把最复杂的 AI 原理，讲得连我这个写 CRUD 的 Java 工程师都能听懂。

他的 YouTube 系列 "Neural Networks: Zero to Hero" 被无数人奉为入门圣经，B站也有搬运。如果你还没看过，停下来先去看。

关注他的 GitHub、X（推特）、YouTube，就相当于把 AI 前沿的一个极其重要的窗口打开了。

![图片](/images/wechat/ai-era-how-to-research/image_4.png)

## 下期预告

Karpathy 最近在 GitHub 开源了一个项目——autoresearch。

10 天，35,700+ stars。

这个速度，意味着整个 AI 工程师社区集体沸腾了。

它做的事情，用一句话描述：

让 AI Agent 自己循环：改代码 → 评估 → 保留（或丢弃）→ 无限迭代

当我第一次看到这个项目的时候，脑子里只有三个字：

> 我 草 啊（此处请自行替换为更文雅的感叹词）

下期，我们用 claude code 来把这个项目扒一扒。

---

*系列导航：第①期：我的第一个问题不是"怎么学"，而是"信谁" ◀ 本期*
