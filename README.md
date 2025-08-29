# My ReAct Agent

一个基于 ReAct（Reasoning and Acting）模式的智能编程助手，能够通过思考-行动-观察的循环来解决编程任务。

## 🚀 特性

- **ReAct 模式**：采用思考-行动-观察的循环模式，让AI能够逐步分析和解决问题
- **多种工具支持**：内置文件操作、目录结构查看、终端命令执行等工具
- **项目感知**：能够理解项目结构，在指定目录下完成任务
- **灵活的模型支持**：支持多种大语言模型（当前使用 Gemini 2.5 Pro）
- **中文友好**：完全支持中文交互和提示

## 📦 安装

### 前置要求

- Python 3.12+
- uv 包管理器

### 安装步骤

1. 克隆项目：
```bash
git clone <repository-url>
cd my-re-act
```

2. 安装依赖：
```bash
uv sync
```

3. 配置环境变量：
复制示例配置文件并编辑：
```bash
cp .env.example .env
```

然后编辑 `.env` 文件，添加你的 API 密钥：
```
OPENAI_API_KEY=your_api_key_here

# 可选：如果使用其他 API 服务
# OPENAI_BASE_URL=https://api.vveai.com/v1
```

## 🛠️ 使用方法

### 基本用法

在项目根目录运行：
```bash
uv run agent.py <工作目录>
```

例如：
```bash
# 在 snake 目录下工作
uv run agent.py snake

# 在项目根目录工作
uv run agent.py .
```

### 可用工具

Agent 内置了以下工具：

1. **read_file(file_path)** - 读取文件内容
2. **write_to_file(file_path, content)** - 写入文件
3. **run_terminal_command(command)** - 执行终端命令
4. **list_directory_structure(directory_path, max_depth)** - 查看目录结构
5. **get_project_path()** - 获取项目绝对路径

### 示例任务

```bash
# 创建一个简单的 Python 脚本
uv run agent.py .
> 请输入任务：在当前目录创建一个 hello.py 文件，输出 "Hello, World!"

# 在 snake 目录下开发游戏
uv run agent.py snake
> 请输入任务：创建一个贪吃蛇游戏
```

## 🏗️ 项目结构

```
my-re-act/
├── agent.py              # 主要的 ReAct Agent 实现
├── prompt_template.py    # 提示词模板
├── pyproject.toml        # 项目配置
├── README.md            # 项目说明
├── .gitignore           # Git 忽略文件
├── snake/               # 示例工作目录
│   └── snake_game/      # 贪吃蛇游戏示例
└── .env                 # 环境变量（需要自己创建）
```

## 🔧 核心组件

### ReActAgent 类

主要的智能体类，实现了：
- 工具管理和调用
- ReAct 循环逻辑
- 与大语言模型的交互
- 结果解析和处理

### ProjectTools 类

项目工具集合，提供：
- 文件系统操作
- 目录结构查看
- 终端命令执行
- 项目路径管理

## 🎯 工作原理

1. **接收任务**：用户输入要完成的任务
2. **思考阶段**：AI 分析任务，制定计划
3. **行动阶段**：调用相应工具执行操作
4. **观察阶段**：获取工具执行结果
5. **循环迭代**：重复思考-行动-观察，直到任务完成
6. **提供答案**：给出最终的完成结果

## 📝 配置说明

### 模型配置

在 `agent.py` 中可以修改使用的模型：
```python
agent = ReActAgent(tools=tools, model="gemini-2.5-pro", project_directory=project_dir)
```

支持的模型包括：
- `gpt-4o`
- `gemini-2.5-pro`
- 其他 OpenAI 兼容的模型

### API 配置

项目默认使用 OpenAI 官方 API，你可以通过环境变量配置：

**方式一：环境变量配置（推荐）**
```bash
# .env 文件
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 默认值，可省略

# 使用其他兼容服务
OPENAI_BASE_URL=https://api.vveai.com/v1
```

**方式二：代码中直接指定**
```python
agent = ReActAgent(
    tools=tools,
    model="gemini-2.5-pro",
    project_directory=project_dir,
    base_url="https://api.vveai.com/v1"  # 可选参数
)
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[添加你的许可证信息]

## 🙏 致谢

- 基于 ReAct 论文的思想实现
- 使用 OpenAI API 进行大语言模型交互
- 感谢所有贡献者的支持
