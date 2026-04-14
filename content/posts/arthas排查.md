+++
title = "Arthas 实战教程：排查 Java 代码执行缓慢问题"
date = 2025-07-25T17:34:25+08:00
draft = false
slug = "arthas排查"
tags = ["Java", "JVM", "排障", "性能优化"]
series = []
summary = "🎯 排查目标 定位 Java 应用中 执行缓慢的代码段，找出方法耗时最长的地方，帮助性能优化。 🛠️ 常用命令对比 命令 作用 使用场景 trace 追踪方法内部每一步执行耗时 定位慢步骤、方法耗时分布 watch 观察…"
+++

## 🎯 排查目标

定位 Java 应用中 执行缓慢的代码段，找出方法耗时最长的地方，帮助性能优化。

## 🛠️ 常用命令对比

命令
作用
使用场景

trace
追踪方法内部每一步执行耗时
定位慢步骤、方法耗时分布

watch
观察方法入参、返回值、执行耗时
查看调用情况及结果

monitor
统计方法的 QPS、平均耗时、失败率
观察方法整体性能

tt
方法调用记录快照，可回放
精确分析慢调用参数与路径

profiler
CPU 级别采样，适合查找热点（更底层）
大范围性能瓶颈分析（非单方法）

## 🔍 排查流程示例

### Step 1️⃣：用 

### monitor

### 看哪个方法慢

```
monitor -c 5 com.example.service.OrderService placeOrder
```

查看最近 5 次调用统计，包含平均耗时（avg-rt）。

### Step 2️⃣：用 

### trace

### 看慢在哪一步

```
trace com.example.service.OrderService placeOrder
```

输出样例：

```
`---[10530ms] OrderService.placeOrder()
    +---[80% 8424ms] PaymentService.charge()
    +---[15% 1575ms] InventoryService.check()
```

🔎 定位 PaymentService.charge() 最慢

### Step 3️⃣：深入 

### trace

### 子方法

```
trace com.example.payment.PaymentService charge
```

继续分析 charge() 方法中，是否数据库、远程调用、计算等耗时。

### Step 4️⃣：用 

### watch

### 看方法入参 + 耗时

```
watch com.example.payment.PaymentService charge '{params, returnObj, cost}' -x 3
```

输出：

```
params[0]: Order{id=123}
returnObj: Result{success=true}
cost: 8423ms
```

📌 可以结合参数判断哪些订单耗时长。

### Step 5️⃣：只分析慢请求（可选）

```
trace com.example.payment.PaymentService charge '#cost > 1000'
```

仅显示耗时超过 1 秒的调用。

### Step 6️⃣：使用 

### tt

### 回放某次慢调用

```
tt -t com.example.payment.PaymentService charge
tt -l
tt -i 1000
tt -w 1000
```

可以查看参数、返回值、调用堆栈，非常适合深入分析。

## 📌 实战技巧总结

场景
工具 / 命令

某个页面或接口响应慢
trace 顶层方法

细查哪个内部方法最耗时
trace 继续深入子方法

看参数和返回值 + 耗时
watch

大量数据时，平均耗时长
monitor

多次慢调用，精确重放分析
tt

不确定代码在哪执行
jad + search-class + sc

## ✅ 附加命令小抄

```
# 查找类
sc -d *OrderService

# 反编译类
jad com.example.service.OrderService

# 查看所有加载类
sc -d

# 查看方法耗时排序
profiler start
profiler stop
```

## 🧠 优化建议方向

- 是否有慢 SQL：可结合日志、SQL 分析工具查看
- 是否重复远程调用：加缓存、聚合请求
- 是否线程池/并行未生效：检查线程模型
- 是否 GC 频繁：结合 jvm 查看内存情况

## 🏁 小结

工具组合
用途

monitor + trace
找慢方法 + 慢步骤

trace + watch
找慢步骤 + 看入参结果

trace + tt
找调用链 + 精准回放
