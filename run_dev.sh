#!/bin/bash

# 开发环境启动脚本
source venv/bin/activate

# 设置开发环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 启动开发服务器
echo "启动开发服务器..."
python src/main.py
