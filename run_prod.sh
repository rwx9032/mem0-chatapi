#!/bin/bash

# 生产环境启动脚本
source venv/bin/activate

# 设置生产环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 使用 uvicorn 启动生产服务器
echo "启动生产服务器..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8050} --workers 1
