"""
管理后台独立服务器
运行在单独的端口，提供管理界面
"""

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.admin import router as admin_router
from src.config.settings import settings
from src.services.database_service import db_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用生命周期"""
    # 初始化数据库
    await db_service.initialize()
    yield

def create_admin_app() -> FastAPI:
    """创建管理后台应用"""
    app = FastAPI(
        title="Mem0 Chat API 管理后台",
        description="多用户记忆隔离 Chat API 中转服务管理界面",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(admin_router)
    
    return app

async def run_admin_server():
    """运行管理后台服务器"""
    app = create_admin_app()
    
    config = uvicorn.Config(
        app,
        host=settings.admin_host,
        port=settings.admin_port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    print(f"🚀 管理后台启动在: http://{settings.admin_host}:{settings.admin_port}")
    print(f"🔑 管理员密钥: {settings.admin_secret_key}")
    
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_admin_server())
