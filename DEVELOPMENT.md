# Mem0 Chat API 开发指南

## 快速开始

### 1. 环境设置
```bash
# 运行环境设置脚本
./setup_env.sh

# 或者手动设置
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
```

### 3. 运行服务

#### 开发模式
```bash
./run_dev.sh
```

#### 生产模式
```bash
./run_prod.sh
```

## 项目结构

```
src/
├── main.py              # FastAPI 应用入口
├── config/
│   ├── settings.py      # 配置管理
│   └── token_parser.py  # Token 解析逻辑
├── memory/
│   ├── client.py        # Mem0 客户端
│   └── manager.py       # 记忆管理业务逻辑
├── api/
│   ├── models.py        # 数据模型
│   ├── chat.py          # Chat API 端点
│   └── middleware.py    # 认证中间件
├── services/
│   ├── llm_proxy.py     # LLM 代理服务
│   └── memory_service.py # 记忆服务封装
└── utils/
    └── helpers.py       # 通用工具函数
```

## Token 格式

Token 支持两种格式：

### 完整格式（包含模型名）
`envtoken|||baseurl|||modelname|||token`

示例: `IamSettedInEnvFile|||https://example.com|||gemini-2.0-flash|||sk-1145141919810`

解析后:
- env token: `IamSettedInEnvFile`
- base url: `https://example.com`
- model name: `gemini-2.0-flash`
- actual token: `sk-1145141919810`

### 简化格式（模型名可选）
`envtoken|||baseurl|||token`

示例: `IamSettedInEnvFile|||https://example.com|||sk-1145141919810`

解析后:
- env token: `IamSettedInEnvFile`
- base url: `https://example.com`
- model name: 使用请求中的 `model` 参数
- actual token: `sk-1145141919810`

**注意**: 当使用简化格式时，必须在请求体中指定 `model` 参数。

## API 端点

### Chat Completions
```
POST /v1/chat/completions
```

兼容 OpenAI Chat API 格式，支持记忆增强的对话。

## 开发工具

- 虚拟环境: `venv`
- Web 框架: `FastAPI`
- 记忆管理: `Mem0`
- HTTP 客户端: `httpx`
- 向量数据库: `Supabase/PostgreSQL`
