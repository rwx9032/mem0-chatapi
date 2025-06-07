#!/usr/bin/env python3
"""
Mem0 Chat API 服务启动器
启动集成了管理后台的主服务
"""

import asyncio
import signal
import sys
import uvicorn

from src.main import app as main_app
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


async def main():
    """主函数 - 运行集成了管理功能的主服务"""
    print("=" * 60)
    print("🎯 Mem0 Chat API 多用户记忆隔离服务")
    print("=" * 60)
    print(f"🚀 服务启动在: http://{settings.host}:{settings.port}")
    print(f"🎛️ 管理后台: http://{settings.host}:{settings.port}/admin/")
    print(f"🔑 管理员密钥: {settings.admin_secret_key}")
    print(f"📚 API文档: http://{settings.host}:{settings.port}/docs")
    
    # 只运行主服务器（已包含管理功能）
    try:
        await run_main_server()
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭服务...")
        print("✅ 服务已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
