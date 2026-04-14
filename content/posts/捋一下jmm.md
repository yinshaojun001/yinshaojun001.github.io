+++
title = "捋一下JMM"
date = 2025-07-16T23:51:45+08:00
draft = false
slug = "捋一下jmm"
tags = []
series = []
summary = ""
+++

# Java Memory Model（JMM）与 JVM 运行时内存区域详解[#](#java-memory-modeljmm与-jvm-运行时内存区域详解)

## 一、Java Memory Model（JMM）概述[#](#一java-memory-modeljmm概述)

JMM（Java Memory Model）是 Java 虚拟机规范中定义的线程之间如何共享变量的一种抽象模型，用于屏蔽各种硬件和操作系统内存访问差异，确保多线程程序在不同平台下都能实现一致的内存语义。

- JMM 主要规定了：
- 线程之间变量可见性（什么时候一个线程对变量的修改对另一个线程可见）
- 指令重排序（允许编译器和 CPU 优化指令执行顺序，但需保证语义不变）
- 原子性、有序性、可见性三大特性
- volatile、synchronized、final 等关键字的内存语义

## 二、JVM 运行时内存结构（根据 JVM 规范）[#](#二jvm-运行时内存结构根据-jvm-规范)

JVM 根据 Java 虚拟机规范，将运行时的内存划分为如下几个区域：

### 1. 程序计数器（Program Counter Register）[#](#1-程序计数器program-counter-register)

- 描述：
- 每条线程都有一个独立的程序计数器。
- 它是线程私有的，存储当前线程执行的字节码指令地址（行号指示器）。
- 特点：
- 是唯一一个不会出现 OutOfMemoryError（OOM） 的内存区域。
- 用于线程切换后恢复执行位置，实现多线程的基础。

### 2. Java 虚拟机栈（Java Virtual Machine Stack）[#](#2-java-虚拟机栈java-virtual-machine-stack)

- 描述：
- 每个线程创建时会同时创建一个栈，是线程私有的。
- 栈帧中包含方法的局部变量表、操作数栈、动态链接和方法返回地址等。
- 特点：
- 每次方法调用时都会创建一个新的栈帧压入栈中，方法执行完毕则弹出。
- 可能抛出错误：
- StackOverflowError：栈帧过多或递归过深。
- OutOfMemoryError：栈内存大小限制导致无法创建新栈帧。

### 3. 本地方法栈（Native Method Stack）[#](#3-本地方法栈native-method-stack)

- 描述：
- 与 Java 虚拟机栈类似，但专门为本地方法服务（例如 C 语言方法）。
- 用于支持 native 方法的执行。
- 特点：
- 有些 JVM（如 HotSpot）将本地方法栈与 Java 虚拟机栈合并实现。

### 4. 堆（Heap）[#](#4-堆heap)

- 描述：
- 所有线程共享的区域，是 Java 内存中最大的一块区域。
- 用于存放对象实例和数组。
- 特点：
- GC（垃圾回收）管理的主要区域。
- 会抛出错误：
- OutOfMemoryError：内存不足无法分配对象。

### 5. 方法区（Method Area）[#](#5-方法区method-area)

- 描述：
- 所有线程共享的区域。
- 存放类的结构信息（类的元数据）、常量池、静态变量、即时编译器生成的代码等。
- Java 8 后的变化：
- 永久代（PermGen）被废弃，替换为 Metaspace（元空间）
- 元空间使用的是 本地内存（Native Memory） 而不是堆内存。
- 可能抛出错误：
- OutOfMemoryError: 元空间内存耗尽。

## 三、线程共享 vs 线程隔离的内存区域[#](#三线程共享-vs-线程隔离的内存区域)

区域
是否线程共享
是否可能 OOM
用途说明

程序计数器
否
❌ 不会 OOM
跟踪当前线程执行位置

虚拟机栈
否
✅ StackOverflow / OOM
每个方法调用的执行环境

本地方法栈
否
✅ StackOverflow / OOM
执行 native 方法

堆
✅ 是共享的
✅ OOM
所有对象实例分配区域

方法区（元空间）
✅ 是共享的
✅ OOM
类元信息、静态变量、运行时常量池等信息

## 四、JMM 与 JVM 内存结构的关系[#](#四jmm-与-jvm-内存结构的关系)

JMM 是一种抽象的内存模型，它不直接对应 JVM 的某一内存区域，而是规定了：

- 主内存（Main Memory）：JMM 中所有共享变量存储的地方（通常对应 JVM 中的堆、方法区）。
- 工作内存（Working Memory）：每个线程私有的变量副本（对应 JVM 的程序计数器、栈）。

注意：JMM 更关注“线程之间共享变量的读写规则”这一抽象行为。

## 五、JMM 关键点回顾[#](#五jmm-关键点回顾)

- 多线程共享变量的内存可见性由 JMM 控制。
- JMM 定义了 volatile、synchronized 等的行为语义。
- 指令重排序由编译器和 CPU 做出，但需在 JMM 语义下保证一致性。
- Java 提供的原子类（如 AtomicInteger）使用了底层的 CAS 指令，属于 JMM 的一种实现保障。
