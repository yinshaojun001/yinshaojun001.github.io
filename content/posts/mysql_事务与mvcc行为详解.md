+++
title = "MySQL_事务与MVCC行为详解"
date = 2025-06-26T13:55:41+08:00
draft = false
slug = "mysql_事务与mvcc行为详解"
tags = ["MySQL", "并发", "排障"]
series = []
summary = "📘 MySQL 事务一致性与 MVCC 行为详解 本笔记主要围绕以下问题展开讲解： 事务 A 中执行了 SELECT * FROM table1 还未提交，事务 B 中执行了新增并提交，此时事务 A 执行 SELECT…"
+++

# 📘 MySQL 事务一致性与 MVCC 行为详解

本笔记主要围绕以下问题展开讲解：

> 事务 A 中执行了
> SELECT * FROM table1
> 还未提交，事务 B 中执行了新增并提交，此时事务 A 执行
> SELECT * FROM table1 WHERE id BETWEEN 1 AND 47 FOR UPDATE
> 会看到事务 B 插入的数据吗？

## 一、前提知识：MySQL InnoDB 的事务机制

### 1.1 默认隔离级别：REPEATABLE READ

MySQL 的 InnoDB 存储引擎默认采用 REPEATABLE READ 隔离级别，它具备以下特点：

- 同一个事务中多次读取结果一致（可重复读）
- 可通过 MVCC 保证一致性
- 防止不可重复读 ✅
- 防止幻读（配合间隙锁）✅

### 1.2 MVCC（多版本并发控制）

MVCC 是 InnoDB 在 REPEATABLE READ 和 READ COMMITTED 中实现非锁定一致性读的核心技术。

每个事务开启时会生成一个一致性视图（Read View），之后的所有查询操作都基于该视图决定哪些版本是“可见”的。

## 二、核心问题：事务间的数据可见性

### 问题描述：

```
-- 事务A
START TRANSACTION;
SELECT * FROM table1;

-- 此时创建了快照（Read View）

-- 事务B
START TRANSACTION;
INSERT INTO table1(id, name) VALUES (30, 'B');
COMMIT;

-- 事务A 再次执行：
SELECT * FROM table1 WHERE id BETWEEN 1 AND 47 FOR UPDATE;
```

### 会看到 id = 30 吗？

> ❌ 不会！

因为：

- 事务 A 在最开始执行 SELECT 时就已经创建了 Read View
- InnoDB 的 MVCC 决定了 该事务之后无论执行什么查询，都基于这份快照
- FOR UPDATE 是加锁语句，但不会刷新快照视图

## 三、锁类型补充说明

### 3.1 SELECT ... FOR UPDATE 会加什么锁？

- 加 排它锁（X锁），防止其他事务更新这些记录
- 在 REPEATABLE READ 下，还会加 间隙锁（Gap Lock） 防止插入造成幻读

但是：

> FOR UPDATE
> 只对“当前事务可见的记录”加锁，不可见的数据不会加锁、更不会返回！

## 四、总结回答模板（用于面试）

> 在事务 A 中，如果在最开始执行了普通查询，就已经创建了一致性快照（Read View）。之后无论执行多少次
> SELECT ... FOR UPDATE
> ，都不会重新生成快照。因此，即使事务 B 提交了新的 insert，事务 A 也不会看到这条新记录。
> FOR UPDATE
> 只锁定它能看到的行，新增数据对它完全不可见。

## 五、实验验证脚本

你可以开两个 MySQL 客户端窗口进行如下实验：

```
-- 窗口1：事务A
START TRANSACTION;
SELECT * FROM table1;

-- 窗口2：事务B
START TRANSACTION;
INSERT INTO table1(id, name) VALUES (30, 'new data');
COMMIT;

-- 回到窗口1
SELECT * FROM table1 WHERE id BETWEEN 1 AND 50 FOR UPDATE;
-- ✅ 看不到 id = 30，也不会加锁它
```

## 六、拓展：如何让事务看到最新数据？

1. 使用 READ COMMITTED 隔离级别

```
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```
每次 SELECT 都会创建新的快照视图，能够看到其他事务提交的数据。
2. 或者结束当前事务，重新开启新事务即可创建新快照。

## 七、推荐学习路径

主题
推荐资源

InnoDB 锁机制
《MySQL 技术内幕 InnoDB》

MVCC 原理
《深入浅出 MySQL》MVCC章节

幻读与间隙锁
极客时间《MySQL实战45讲》

SHOW ENGINE INNODB STATUS
手动观察锁情况，结合实际实验
