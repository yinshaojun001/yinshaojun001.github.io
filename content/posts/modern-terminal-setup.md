+++
title = "不用iTerm2 + oh-my-zsh + tmux：如何快速搭起一套现代终端"
date = 2026-04-14T02:37:00+08:00
draft = false
slug = "modern-terminal-setup"
tags = ["终端", "Ghostty", "开发工具", "效率", "CLI"]
series = []
summary = "从 iTerm2 + oh-my-zsh + tmux 迁移到 Ghostty，重新梳理终端工作流。"
+++

![图片](/images/wechat/modern-terminal-setup/image_0.jpg)

最近 cli 很火，本来打算分享这些年总结的终端工具，但是看到了 claude code 团队分享的终端 Ghostty，尝试了一下真的爱上了。

所以从 iTerm2 + oh-my-zsh + tmux 迁移到 Ghostty 之后，我重新梳理了一遍自己的终端工作流。这篇文章会讲清楚：为什么值得换、换完有哪些实际好处，以及新手如何快速搭起一套好用的现代终端环境。

## 前言：我为什么决定离开 iTerm2 + oh-my-zsh + tmux

我曾经长期使用 iTerm2 + oh-my-zsh + tmux 这套经典组合。它成熟、稳定、功能强，也支撑过我很长一段时间的开发工作。

但随着终端使用越来越高频，我越来越明显地感觉到：这套方案虽然强大，却也越来越像一套"拼装系统"。

终端模拟器是一层，shell 是一层，tmux 又是一层。很多体验不是"天然顺手"，而是"多层叠加之后勉强够用"。tmux 的指令总是记不住，配置还要写进 `~/tmux/config` 里。

后来我换到了 Ghostty。真正打动我的，不是"它很新"，而是它在几个最核心的地方做得更好：

- 性能
- 原生分屏
- 体验一致性

不过这篇文章不会花太多篇幅反复比较两套方案。更重要的是：如果你想快速搭起一套好用的终端环境，应该先装什么、怎么装、装完怎么顺手用起来。

## 先给结论：如果你只想快速上手，先装这 5 个

如果你不想先看长篇背景，可以直接从这里开始：

1. **Ghostty**：终端本体，负责性能和原生分屏
2. **zsh + oh-my-zsh**：更友好的 shell 交互基础
3. **fzf**：让"找命令、找文件、找目录"变成搜索
4. **ripgrep（rg）**：让"搜代码、搜配置、搜日志"变快很多
5. **lazygit / yazi / lsd**：分别解决 Git、文件浏览、目录展示问题

最小安装顺序可以直接照着来：

```bash
brew install --cask ghostty
brew install fzf ripgrep lazygit yazi lsd
```

然后再补：

- oh-my-zsh
- zsh-autosuggestions
- zsh-syntax-highlighting
- Nerd Font（如果你需要图标显示更完整）

如果你今天只想先跟着用起来 3 个东西，可以按这个顺序来：

1. Ghostty
2. fzf
3. rg

因为这三个最容易立刻改变你的使用习惯。

## 接下来直接开始：按这个顺序安装，最省事

### 第一步：先把终端本体换掉

```bash
brew install --cask ghostty
```

### 第二步：安装最核心的效率工具

```bash
brew install fzf ripgrep lazygit yazi lsd
```

- **fzf** = 终端里的"搜索框 + 下拉选择菜单"
- **ripgrep（rg）** = 更快、更智能的 grep

它本质就是一个文本搜索工具，但：
- 比 grep 快很多（通常 10x+）
- 默认递归搜索（不用你写 `-r`）
- 自动忽略 .gitignore
- 支持现代正则（更好用）

- **lazygit**：Git 的终端图形界面（TUI）客户端，让你不用记一堆 git 命令，用键盘就能操作
- **yazi**：终端里的高性能文件管理器，类似 Finder / Explorer，但在终端里，而且更强

### 第三步：给 zsh 补上两个高收益插件

如果你已经在用 oh-my-zsh：

```bash
git clone https://github.com/zsh-users/zsh-autosuggestions \
  ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
  ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

然后在 `~/.zshrc` 里启用：

```bash
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
```

### 第四步：把最常用的别名和函数放进去

```bash
alias lg="lazygit"
alias ls="lsd"
alias ll="lsd -l"
alias la="lsd -la"

source <(fzf --zsh)

function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
  yazi "$@" --cwd-file="$tmp"
  if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
    builtin cd -- "$cwd"
  fi
  rm -f -- "$tmp"
}
```

到这里，其实已经是一套非常能打的终端环境了。

## 为什么我最后选了 Ghostty

这里只说结论，不展开长对比：

- **更快**：窗口、滚动、分屏都更跟手
- **更省事**：本地开发时很多分屏需求不必再完全依赖 tmux
- **更统一**：终端行为和快捷键更自然

如果你主要关心的是"终端本身要顺手"，Ghostty 很值得直接试。

## 我现在实际在用的核心组合

为了方便你照着装，我先把本机这套组合直接列出来：

- **Ghostty**：终端本体
- **zsh + oh-my-zsh**：shell 基础
- **powerlevel10k**：prompt 主题
- **zsh-autosuggestions**：命令自动建议
- **zsh-syntax-highlighting**：命令高亮
- **fzf**：模糊搜索
- **ripgrep（rg）**：全文检索
- **lazygit**：Git 可视化操作
- **yazi**：终端文件管理
- **lsd**：更易读的目录展示

你可以把它简单理解成两层：

- **终端 / shell 层**：Ghostty、zsh、oh-my-zsh、powerlevel10k、自动建议、高亮
- **效率工具层**：fzf、rg、lazygit、yazi、lsd

![图片](/images/wechat/modern-terminal-setup/image_1.png)

## 一、先把终端本体换掉：Ghostty 为什么值得上手

### 安装 Ghostty

```bash
brew install --cask ghostty
```

安装完成后，直接打开即可。

如果你以前用的是 iTerm2，最直接的感受通常不是"功能多了多少"，而是：

- 启动更干脆
- 交互更轻
- 分屏更自然

### 一份适合新手起步的 Ghostty 最小配置

```bash
# ~/.config/ghostty/config

font-family = JetBrainsMono Nerd Font
font-size = 14

# 先选一个耐看的暗色主题
theme = catppuccin-mocha

# 轻微透明，保留层次感
background-opacity = 0.95

# 光标更利落一点
cursor-style = bar

# macOS 下保留窗口装饰
window-decoration = true

# 给原生分屏配上顺手的快捷键
keybind = cmd+d=new_split:right
keybind = cmd+shift+d=new_split:down
```

如果你还没装字体，可以先装：

```bash
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono-nerd-font
```

![图片](/images/wechat/modern-terminal-setup/image_2.png)

## 二、真正把效率拉开的，不是配置文件，而是这几个 CLI 工具

![图片](/images/wechat/modern-terminal-setup/image_3.png)

### fzf：先从这个开始，收益最大

如果只想先装一个终端效率工具，我大概率会先放 fzf。

它解决什么问题？在传统终端里，很多事情都依赖"记住"。而 fzf 的思路是：你不用完全记住，只要能大概想起来，然后搜索。

可以先从这 3 个快捷键开始：

| 快捷键 | 作用 |
|--------|------|
| Ctrl + R | 模糊搜索历史命令 |
| Ctrl + T | 模糊搜索文件并插入命令行 |
| Alt + C | 模糊搜索目录并快速进入 |

如果先只试一个，我会更推荐 Ctrl + R。它会直接改变你使用终端的方式。

![图片](/images/wechat/modern-terminal-setup/image_4.png)

### ripgrep（rg）：代码、配置、日志搜索神器

```bash
# 搜函数或关键字
rg "useEffect"

# 搜报错信息
rg "connection refused"

# 只搜某种文件
rg "TODO" --type ts

# 搜配置项
rg "PORT="
```

![图片](/images/wechat/modern-terminal-setup/image_5.png)

### lazygit：让 Git 的高频操作更可视化

```bash
brew install lazygit
alias lg="lazygit"
```

新手先从这几个动作开始就够了：

| 按键 | 作用 |
|------|------|
| space | 暂存 / 取消暂存 |
| c | 提交 |
| p | push |
| b | 查看 / 切换分支 |
| d | 查看 diff |
| ? | 查看帮助 |

![图片](/images/wechat/modern-terminal-setup/image_6.png)

### yazi：终端里的文件管理器

```bash
brew install yazi
```

在 `~/.zshrc` 里加入 `y()` 函数（见上文），以后运行 `y` 就能进入 yazi，退出后 shell 会自动切到你最后浏览的目录。

![图片](/images/wechat/modern-terminal-setup/image_7.png)

### lsd：让目录展示更可读

```bash
brew install lsd
alias ls="lsd"
alias ll="lsd -l"
alias la="lsd -la"
alias lt="lsd --tree"
```

![图片](/images/wechat/modern-terminal-setup/image_8.png)

## 四、安装完成后，先按这份清单检查一遍

1. 确认 Ghostty 已经能正常打开
2. 确认 zsh 插件已经生效（`source ~/.zshrc`）
3. 确认 fzf shell integration 已经接管常用搜索动作
4. 确认 ripgrep（rg）能正常搜索
5. 确认 lazygit 能正常启动
6. 确认 yazi 和 `y()` 函数已经打通
7. 确认 lsd 别名是否已经生效
8. 最后做一次"最小工作流联调"

![图片](/images/wechat/modern-terminal-setup/image_9.png)

## 五、一套真实的日常工作流

### 场景 1：进入项目并开始开发

- 打开 Ghostty
- 开一个分屏跑服务
- 另一个分屏执行命令
- 需要找目录时，用 `y` 或 `Alt + C`
- 需要找历史命令时，用 `Ctrl + R`

### 场景 2：排查问题

```
rg "error keyword"
```

然后用 rg 搜代码、配置、日志，用 Ctrl + R 找之前跑过的相关命令，用 lg 看最近改动和 diff。

### 场景 3：整理目录和文件

用 lsd 快速看目录结构，用 y 进入 yazi 浏览文件，浏览结束后自动回到目标目录，继续执行命令。

## 速查表

### 安装速查

```bash
brew install --cask ghostty
brew install fzf ripgrep lazygit yazi lsd
```

### .zshrc 里可以先放进去的内容

```bash
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
source <(fzf --zsh)

alias lg="lazygit"
alias ls="lsd"
alias ll="lsd -l"
alias la="lsd -la"
```

### 每天可以顺手这样用的 5 个动作

1. 用 Ghostty 分屏把服务、命令、日志分开
2. 用 Ctrl + R 找历史命令
3. 用 rg 搜代码、配置和报错
4. 用 lg 处理 Git 高频操作
5. 用 y 或 Alt + C 快速跳目录

![图片](/images/wechat/modern-terminal-setup/image_10.png)

## 结语

我这次迁移最大的感受，不是"终端变酷了"，而是：

- 更少折腾底层组合
- 更少在多个层之间切换心智
- 更快进入真正的工作状态

终端最好的状态，不是让你时刻意识到它的存在，而是它已经顺手到可以退到背景里。

如果你也在考虑从 iTerm2 + oh-my-zsh + tmux 迁移，我会建议你认真试试 Ghostty。它不一定会取代你过去所有的习惯，但很可能会让你的终端重新回到一个更轻、更快、更统一的状态。
