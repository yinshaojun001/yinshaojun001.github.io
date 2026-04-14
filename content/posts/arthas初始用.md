+++
title = "Arthas初始用"
date = 2025-07-07T17:56:54+08:00
draft = false
slug = "arthas初始用"
tags = []
series = []
summary = ""
+++

在服务器中使用

## 一行命令快速启动[#](#一行命令快速启动)

```
curl -O https://arthas.aliyun.com/arthas-boot.jar && java -jar arthas-boot.jar
```

使用 arthas 查看是否存在某个类:
sc -d 全限定类名
sc -d com.xxx.demo.service.UserService
这条命令的含义是：查找当前 JVM 中是否加载了指定类，并打印该类的详细信息（-d 代表 detail）。

- sc: search class，查询类加载器中加载的类。
- -d: 输出详细信息（如类加载器、代码来源 JAR 路径等）。

```
[arthas@16]$ sc -d com.iac.cpp.config.flow.deploy.DemandManageDeployService

 class-info        com.iac.cpp.config.flow.deploy.DemandManageDeployService

 code-source       file:/home/admin/release/new/iac-executable.jar!/BOOT-INF/lib/iac-cpp-config-1.0-SNAPSHOT.jar!/

 name              com.iac.cpp.config.flow.deploy.DemandManageDeployService

 isInterface       false

 isAnnotation      false

 isEnum            false

 isAnonymousClass  false

 isArray           false

 isLocalClass      false

 isMemberClass     false

 isPrimitive       false

 isSynthetic       false

 simple-name       DemandManageDeployService

 modifier          public

 annotation        org.springframework.stereotype.Service

 interfaces

 super-class       +-com.trustlife.common.config.deploy.BaseConfDeployService

                     +-java.lang.Object

 class-loader      +-org.springframework.boot.loader.LaunchedURLClassLoader@6b884d57

                     +-sun.misc.Launcher$AppClassLoader@70dea4e

                       +-sun.misc.Launcher$ExtClassLoader@78411116

 classLoaderHash   6b884d57

  

Affect(row-cnt:1) cost in 334 ms.
```

这句 Arthas 命令：

```
sc -d com.iac.cpp.config.flow.deploy.DemandManageDeployService
```

的作用是：查找当前 JVM 中是否加载了指定类，并打印该类的详细信息（-d 代表 detail）。

## ✅ 解析结果详解：[#](#-解析结果详解)

```
[arthas@16]$ sc -d com.iac.cpp.config.flow.deploy.DemandManageDeployService
```

你执行了查询这个类是否被加载。

### ✅ 找到了目标类：[#](#-找到了目标类)

```
class-info        com.iac.cpp.config.flow.deploy.DemandManageDeployService
```

说明类已经被加载进 JVM。

### ✅ 类的来源：[#](#-类的来源)

```
code-source       file:/home/admin/release/new/iac-executable.jar!/BOOT-INF/lib/iac-cpp-config-1.0-SNAPSHOT.jar!/
```

这个类是从 iac-executable.jar 包中的 iac-cpp-config-1.0-SNAPSHOT.jar 这个内嵌 JAR 里加载出来的。

这常见于 Spring Boot fat jar（可执行 JAR） 打包方式。

### ✅ 类的结构信息：[#](#-类的结构信息)

```
name              com.iac.cpp.config.flow.deploy.DemandManageDeployService
isInterface       false
isAnnotation      false
isEnum            false
isAnonymousClass  false
isArray           false
isLocalClass      false
isMemberClass     false
isPrimitive       false
isSynthetic       false
```

这些表示它是一个正常的 Java 类，不是接口、注解、枚举或匿名类。

### ✅ 类修饰信息：[#](#-类修饰信息)

```
simple-name       DemandManageDeployService
modifier          public
```

这是一个 public 修饰的类。

### ✅ 注解信息：[#](#-注解信息)

```
annotation        org.springframework.stereotype.Service
```

它被 @Service 注解，说明这是一个 Spring 容器中的服务类。

### ✅ 实现结构（继承链）：[#](#-实现结构继承链)

```
super-class       +-com.trustlife.common.config.deploy.BaseConfDeployService
                     +-java.lang.Object
```

说明它是继承自一个自定义父类 BaseConfDeployService。

### ✅ 类加载器信息：[#](#-类加载器信息)

```
class-loader      +-org.springframework.boot.loader.LaunchedURLClassLoader@6b884d57
                     +-sun.misc.Launcher$AppClassLoader@70dea4e
                       +-sun.misc.Launcher$ExtClassLoader@78411116
classLoaderHash   6b884d57
```

说明这个类是被 Spring Boot 特有的类加载器加载的，即 LaunchedURLClassLoader，并且类加载器 hash 是 6b884d57。

这个信息对于你在 Arthas 中执行如 jad、watch、monitor、tt 命令非常重要，因为有些命令需要你提供 –classLoaderHash 来锁定类加载器。

### ✅ 结尾提示：[#](#-结尾提示)

```
Affect(row-cnt:1) cost in 334 ms.
```

表示这个命令查到了 1 个类，耗时 334 毫秒。

## ✅ 后续你可以干嘛？[#](#-后续你可以干嘛)

你现在知道类已加载，可以做这些操作：

目标
命令

查看源码
jad com.iac.cpp.config.flow.deploy.DemandManageDeployService

查看某方法调用参数
watch com.iac.cpp.config.flow.deploy.DemandManageDeployService 方法名 ‘{params, returnObj}’

跟踪方法执行路径
trace com.iac.cpp.config.flow.deploy.DemandManageDeployService 方法名

查看方法执行时间
monitor com.iac.cpp.config.flow.deploy.DemandManageDeployService 方法名

执行 OGNL
ognl ‘@com.iac.cpp.config.flow.deploy.DemandManageDeployService@yourStaticMethod()’（如果是静态方法）
