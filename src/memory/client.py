from mem0 import Memory
import os
from typing import Optional
from config.settings import settings


class Mem0Client:
    """Mem0 客户端封装"""
    
    def __init__(self):
        self._client: Optional[Memory] = None
    
    def get_client(self) -> Memory:
        """获取或创建 Mem0 客户端"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self) -> Memory:
        """创建 Mem0 客户端"""
        config = self._build_config()
        return Memory.from_config(config)
    
    def _build_config(self) -> dict:
        """构建 Mem0 配置"""
        config = {}
        
        # 配置 LLM
        llm_config = self._get_llm_config()
        if llm_config:
            config["llm"] = llm_config
        
        # 配置嵌入模型
        embedder_config = self._get_embedder_config()
        if embedder_config:
            config["embedder"] = embedder_config
        
        # 配置向量存储（暂时使用内存存储，避免数据库依赖）
        config["vector_store"] = {
            "provider": "chroma",
            "config": {
                "collection_name": "mem0_memories",
                "path": "./chroma_db"
            }
        }
        
        return config
    
    def _get_llm_config(self) -> Optional[dict]:
        """获取 LLM 配置"""
        provider = settings.llm_provider.lower()
        
        if provider in ["openai", "openrouter"]:
            config = {
                "provider": "openai",
                "config": {
                    "model": settings.llm_model,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }
            }
            
            # 设置 API 密钥
            if settings.llm_api_key:
                if provider == "openrouter":
                    os.environ["OPENROUTER_API_KEY"] = settings.llm_api_key
                else:
                    os.environ["OPENAI_API_KEY"] = settings.llm_api_key
            
            # 设置自定义基础 URL
            if settings.llm_base_url:
                config["config"]["openai_base_url"] = settings.llm_base_url
            
            return config
        
        elif provider == "gemini":
            config = {
                "provider": "gemini",
                "config": {
                    "model": settings.llm_model,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }
            }
            
            # 设置 Gemini API 密钥
            if settings.llm_api_key:
                os.environ["GEMINI_API_KEY"] = settings.llm_api_key
            
            return config
        
        elif provider == "google":
            config = {
                "provider": "google",
                "config": {
                    "model": settings.llm_model,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }
            }
            
            if settings.llm_api_key:
                os.environ["GOOGLE_API_KEY"] = settings.llm_api_key
            
            return config
        
        elif provider == "ollama":
            config = {
                "provider": "ollama",
                "config": {
                    "model": settings.llm_model,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }
            }
            
            if settings.llm_base_url:
                config["config"]["ollama_base_url"] = settings.llm_base_url
            
            return config
        
        return None
    
    def _get_embedder_config(self) -> Optional[dict]:
        """获取嵌入模型配置"""
        provider = settings.llm_provider.lower()
        
        if provider == "openai":
            config = {
                "provider": "openai",
                "config": {
                    "model": settings.embedding_model,
                    "embedding_dims": 1536
                }
            }
            
            if settings.llm_base_url:
                config["config"]["openai_base_url"] = settings.llm_base_url
            
            if settings.llm_api_key:
                os.environ["OPENAI_API_KEY"] = settings.llm_api_key
            
            return config
        
        elif provider == "gemini":
            config = {
                "provider": "gemini",
                "config": {
                    "model": settings.embedding_model,
                    "embedding_dims": 768
                }
            }
            
            if settings.llm_api_key:
                os.environ["GEMINI_API_KEY"] = settings.llm_api_key
            
            return config
        
        elif provider == "google":
            config = {
                "provider": "google",
                "config": {
                    "model": settings.embedding_model,
                    "embedding_dims": 768
                }
            }
            
            if settings.llm_api_key:
                os.environ["GOOGLE_API_KEY"] = settings.llm_api_key
            
            return config
        
        elif provider == "ollama":
            config = {
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text",
                    "embedding_dims": 768
                }
            }
            
            if settings.llm_base_url:
                config["config"]["ollama_base_url"] = settings.llm_base_url
            
            return config
        
        return None


# 全局 Mem0 客户端实例
mem0_client = Mem0Client()
