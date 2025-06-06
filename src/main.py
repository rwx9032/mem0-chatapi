from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import asyncio
import uvicorn
from contextlib import asynccontextmanager

# 导入配置和工具
from config.settings import settings
from utils.helpers import setup_logging, get_current_timestamp

# 导入 API 路由
from api.chat import router as chat_router

# 导入服务
from services.llm_proxy import llm_proxy_service


# 设置日志
setup_logging("INFO" if not settings.debug else "DEBUG")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    logger.info("Starting Mem0 Chat API...")
    logger.info(f"Server configuration: {settings.host}:{settings.port}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    
    try:
        # 这里可以添加启动时的初始化逻辑
        yield
    finally:
        # 清理资源
        logger.info("Shutting down Mem0 Chat API...")
        await llm_proxy_service.close()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="OpenAI 兼容的聊天 API，集成 Mem0 记忆功能",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router, tags=["Chat API"])


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "timestamp": get_current_timestamp(),
        "version": "1.0.0",
        "service": "mem0-chatapi"
    }


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Welcome to Mem0 Chat API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 错误处理"""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": f"Path {request.url.path} not found",
                "type": "not_found_error",
                "param": None,
                "code": None
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500 错误处理"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "param": None,
                "code": None
            }
        }
    )


async def main():
    """主函数"""
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info" if not settings.debug else "debug",
        reload=settings.debug
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
