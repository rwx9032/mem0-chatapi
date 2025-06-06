#!/usr/bin/env python3
"""
Mem0 Chat API 服务启动器
同时启动主服务和管理后台
"""

import asyncio
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import uvicorn

from src.main import app as main_app
from src.admin_server import create_admin_app
from src.config.settings import settings


async def run_main_server():
    """运行主服务器"""
    config = uvicorn.Config(
        main_app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    print(f"🚀 主服务启动在: http://{settings.host}:{settings.port}")
    await server.serve()


async def run_admin_server():
    """运行管理后台服务器"""
    admin_app = create_admin_app()
    
    config = uvicorn.Config(
        admin_app,
        host=settings.admin_host,
        port=settings.admin_port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    print(f"🎛️ 管理后台启动在: http://{settings.admin_host}:{settings.admin_port}")
    print(f"🔑 管理员密钥: {settings.admin_secret_key}")
    await server.serve()


async def main():
    """主函数 - 同时运行两个服务"""
    print("=" * 60)
    print("🎯 Mem0 Chat API 多用户记忆隔离服务")
    print("=" * 60)
    
    # 创建任务
    main_task = asyncio.create_task(run_main_server())
    admin_task = asyncio.create_task(run_admin_server())
    
    # 等待任一任务完成
    try:
        await asyncio.gather(main_task, admin_task)
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭服务...")
        main_task.cancel()
        admin_task.cancel()
        
        # 等待任务清理
        await asyncio.gather(main_task, admin_task, return_exceptions=True)
        print("✅ 服务已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
