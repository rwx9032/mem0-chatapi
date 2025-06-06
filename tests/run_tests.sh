#!/bin/bash
# 运行所有测试的脚本

set -e

echo "🧪 Mem0 Chat API 测试套件"
echo "=========================="

# 检查当前目录
if [ ! -f ".env" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本（包含.env文件的目录）"
    exit 1
fi

# 加载环境变量
echo "📄 加载环境变量..."
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

# 检查必要的环境变量
if [ -z "$LLM_API_KEY" ]; then
    echo "❌ 错误: LLM_API_KEY 环境变量未设置"
    echo "请在 .env 文件中设置 LLM_API_KEY"
    exit 1
fi

if [ -z "$ADMIN_SECRET_KEY" ]; then
    echo "❌ 错误: ADMIN_SECRET_KEY 环境变量未设置"
    echo "请在 .env 文件中设置 ADMIN_SECRET_KEY"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo

# 检查服务是否运行
echo "🔍 检查服务状态..."
if ! curl -s http://localhost:8050/health > /dev/null; then
    echo "❌ 主服务未运行，请先启动服务："
    echo "   python start_servers.py"
    exit 1
fi

if ! curl -s http://localhost:8060/health > /dev/null; then
    echo "❌ 管理服务未运行，请先启动服务："
    echo "   python start_servers.py"
    exit 1
fi

echo "✅ 服务状态检查通过"
echo

# 运行简单测试
echo "🧪 运行简单功能测试..."
python tests/test_simple.py
echo

# 运行认证测试
echo "🔐 运行认证系统测试..."
python tests/test_auth.py
echo

echo "🎉 所有测试完成！"
