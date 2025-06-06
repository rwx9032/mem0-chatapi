# Mem0 Chat API

将Mem0集成在Chat API中，允许在没有MCP的情况下使用Mem0的LLM功能。

## 环境变量配置

### 安全设置

为了保护您的API密钥和其他敏感信息，本项目使用环境变量进行配置。请按照以下步骤设置：

1. **复制环境变量示例文件**：
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**，将占位符替换为实际值：
   ```bash
   # LLM 服务提供商配置
   LLM_PROVIDER=gemini
   LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   LLM_MODEL=gemini-2.0-flash-exp
   LLM_API_KEY=你的实际Google_Gemini_API密钥
   EMBEDDING_MODEL=text-embedding-004
   
   # 认证配置
   ADMIN_SECRET_KEY=你的管理员密钥
   ```

3. **重要安全提醒**：
   - ✅ `.env` 文件已添加到 `.gitignore`，不会被提交到版本控制
   - ❌ **绝不要**将实际的API密钥硬编码到代码中
   - ❌ **绝不要**将 `.env` 文件提交到版本控制系统

### 必需的环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | Google Gemini API密钥 | `AIzaSy...` |
| `LLM_BASE_URL` | LLM服务基础URL | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `LLM_MODEL` | 使用的模型名称 | `gemini-2.0-flash-exp` |
| `ADMIN_SECRET_KEY` | 管理员认证密钥 | `your-secret-key` |

## 测试

运行测试前，确保已正确配置环境变量：

```bash
# 验证环境变量
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('LLM_API_KEY configured:', bool(os.getenv('LLM_API_KEY')))"

# 运行测试
python tests/test_openai_real.py
```