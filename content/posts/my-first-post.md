+++
title = "深入理解 Java 虚拟机 - 学习笔记整理（基于《深入理解Java虚拟机》）--01"
date = 2025-06-24T08:58:00+08:00
draft = false
slug = "my-first-post"
tags = ["Java", "JVM", "并发", "排障", "性能优化"]
series = []
summary = "深入理解 Java 虚拟机 - 学习笔记整理（基于《深入理解Java虚拟机》） Java 的优点 1. 摆脱硬件平台束缚，一次编写，到处运行的理想（Write Once, Run Anywhere） • Java 程序编…"
+++

深入理解 Java 虚拟机 - 学习笔记整理（基于《深入理解Java虚拟机》）

Java 的优点
1.	摆脱硬件平台束缚，一次编写，到处运行的理想（Write Once, Run Anywhere）
•	Java 程序编译生成的是 .class 字节码文件，而不是直接生成机器码。
•	JVM（Java 虚拟机）在不同的硬件和操作系统平台上有不同的实现，负责将统一的字节码“翻译”为当前平台可以运行的机器指令。
🔍 为什么这是优点？别的语言有吗？哪些语言受硬件平台限制？
•	很多语言（如 C/C++）编译生成的是特定平台的机器码，换平台通常需要重新编译。
•	Java 依赖 JVM 实现了平台无关性，不需要重新编译。
•	类似的语言还有 Python（解释器）、.NET（通过 CLR）、Kotlin（编译为 JVM 字节码）等。
•	**受硬件平台限制的语言：**C、C++、Rust（默认需要重新编译才能跨平台）。
2.	相对安全的内存管理和访问机制，避免了绝大部分内存泄漏和指针越界问题
•	Java 拥有自动垃圾回收机制，开发者不需要手动释放内存。
•	不允许程序直接操作指针（如 C/C++ 中的指针运算）。
🔍 什么叫内存泄漏？
•	指程序中某些对象不再使用，却无法被 GC 回收，导致内存持续占用。
•	示例：对象被无意义地引用着，GC 无法判断可以释放。
🔍 什么是指针越界？
•	在 C/C++ 中访问数组或内存块时下标超出分配范围，可能导致读取或写入非法内存，引发崩溃或安全问题。
🔍 内存管理 vs 访问机制
•	内存管理机制：如何分配和回收内存（Java 使用堆、栈结构，GC 机制自动回收）。
•	内存访问机制：如何访问内存中数据，是否有越界检测、是否暴露底层地址（Java 通过数组越界检查、封装访问）。
3.	实现了热点代码检测和运行时编译及优化（JIT），程序性能随运行时间优化
•	JVM 运行过程中，会监控哪些代码执行频繁（热点代码）。
•	使用 JIT 编译器将热点代码从字节码编译为本地机器码，提高执行速度。
🔍 为什么这样能提高性能？
•	热点代码一旦编译为机器码，执行速度大幅提高。
•	JIT 编译还能根据运行时数据做优化（如内联、逃逸分析、去锁）。
4.	拥有完善的 API 体系与强大生态
•	Java 官方提供广泛的标准库（集合、IO、并发、网络等）。
•	社区支持丰富：Guava、Apache Commons、Spring、Hibernate 等。

Java 技术体系构成
1.	Java 程序设计语言
面向对象语言，定义了 Java 程序的语法和语义。
2.	各种硬件平台上的 Java 虚拟机实现
🔍 什么是 Java 虚拟机实现？
•	JVM 是一个在不同平台上模拟 Java 运行环境的软件。
•	例如在 Windows、macOS、Linux 上有不同的 JVM 可执行文件（如 java.exe 或 java），但都能运行相同的 .class 文件。
3.	Class 文件格式
🔍 Class 文件指什么？
•	编译后的 Java 文件（.java → .class）是标准的中间格式。
•	Class 文件包含字节码，是 JVM 可识别的代码格式。
•	JVM 不直接读取 .java 源码，而是执行 .class 字节码。
4.	Java 类库 API
•	由 Oracle/Java 官方提供的标准类库，如 java.lang.、java.util.、java.io.*。
5.	社区 Java 类库（如 Guava）
•	由 Google、Apache 等社区提供的扩展工具类库，增强标准库功能。

JDK 与 JRE 的关系

组件	含义	包含内容
JDK（Java Development Kit）	Java 开发工具包	包含 JRE + 编译器（javac）、调试工具等
JRE（Java Runtime Environment）	Java 运行时环境	包含 JVM + Java SE API 子集

🔍 JDK 是开发用的，JRE 是运行用的。

JVM 在技术体系的位置

> 历史图片占位：Pasted image 20250622142737.png
•	JDK 是运行在操作系统之上的整体工具集。
•	JVM 是 JDK 的最底层核心组件，负责 Java 字节码的执行。

Java 的分类

分类	说明
Java Card	适用于智能卡、小型嵌入式设备
Java ME (Micro Edition)	面向早期手机、嵌入式设备的 Java 平台
Java SE (Standard Edition)	标准版 Java，面向桌面应用、通用开发
Java EE（现在为 Jakarta EE）	企业级 Java，适用于 Web 应用、服务器端开发

运行在 JVM 上的其他语言

以下语言可以编译为 Java 字节码，运行于 JVM：
•	Kotlin
•	Groovy
•	JRuby
•	Clojure
•	Scala

这些语言共享 JVM 的运行时优势（如内存管理、跨平台、JIT 优化等）。

其他术语解释
•	JIT（Just-In-Time Compiler）即时编译器
•	JVM 在运行时将热点字节码编译为机器码，提高执行效率。
•	HotSpot 虚拟机
•	Oracle 官方提供的主流 JVM 实现，支持 JIT 编译、GC 优化等。
•	名字来源于它的“热点代码优化”功能。
