from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用程序配置设置"""
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8050
    
    # LLM 提供商配置
    llm_provider: str = "openai"  # openai, openrouter, ollama
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    
    # 数据库配置
    database_url: Optional[str] = None
    db_type: str = "sqlite"
    db_url: str = "sqlite:///./memories.db"
    
    # 认证配置
    admin_secret_key: str = "change-this-admin-secret-key"
    
    # 管理后台配置
    admin_host: str = "0.0.0.0"
    admin_port: int = 8080
    
    # 应用配置
    app_name: str = "Mem0 Chat API"
    debug: bool = False
    
    # Mem0 配置
    mem0_config_type: str = "chroma"
    chroma_path: str = "./chroma_db"
    
    # 日志配置
    log_level: str = "INFO"
    
    # 其他配置
    timeout: int = 30
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局设置实例
settings = Settings()