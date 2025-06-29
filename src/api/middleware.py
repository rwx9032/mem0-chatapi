from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from src.config.token_parser import TokenParser
from src.config.settings import settings
from src.api.models import TokenInfo


logger = logging.getLogger(__name__)


class TokenAuthMiddleware:
    """Token 认证中间件"""
    
    def __init__(self):
        self.token_parser = TokenParser()
    
    async def __call__(self, request: Request, call_next):
        """中间件处理函数"""
        
        # 跳过不需要认证的路径
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        try:
            # 提取并解析 Token
            token_info = await self._extract_and_parse_token(request)
            
            # 将 Token 信息添加到请求状态中
            request.state.token_info = token_info
            
            logger.info(f"Authenticated request for user with env_token: {token_info.env_token}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail="Internal authentication error")
        
        return await call_next(request)
    
    def _should_skip_auth(self, path: str) -> bool:
        """判断是否应该跳过认证"""
        skip_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _extract_and_parse_token(self, request: Request) -> TokenInfo:
        """从请求中提取并解析 Token"""
        
        # 从 Authorization header 中提取 Token
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401, 
                detail="Authorization header is required"
            )
        
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401, 
                detail="Invalid authorization header format. Expected: Bearer <token>"
            )
        
        token = auth_header[7:]  # 移除 "Bearer " 前缀
        
        # 解析 Token
        env_token, base_url, model_name, actual_token = self.token_parser.parse_token(token)
        
        # 验证环境 Token
        if not self.token_parser.validate_env_token(env_token, settings.auth_token):
            raise HTTPException(
                status_code=401,
                detail="Invalid environment token"
            )
        
        return TokenInfo(
            env_token=env_token,
            base_url=base_url,
            model_name=model_name,
            actual_token=actual_token
        )


class OptionalTokenAuth(HTTPBearer):
    """可选的 Token 认证（用于 FastAPI 依赖注入）"""
    
    def __init__(self):
        super().__init__(auto_error=False)
        self.token_parser = TokenParser()
    
    async def __call__(self, request: Request) -> Optional[TokenInfo]:
        """提取并解析 Token"""
        
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            return None
        
        try:
            # 解析 Token
            env_token, base_url, model_name, actual_token = self.token_parser.parse_token(credentials.credentials)
            
            # 验证环境 Token
            if not self.token_parser.validate_env_token(env_token, settings.auth_token):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid environment token"
                )
            
            return TokenInfo(
                env_token=env_token,
                base_url=base_url,
                model_name=model_name,
                actual_token=actual_token
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token parsing error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token format"
            )


class RequiredTokenAuth(HTTPBearer):
    """强制的 Token 认证（用于 FastAPI 依赖注入）"""
    
    def __init__(self):
        super().__init__(auto_error=True)
        self.token_parser = TokenParser()
    
    async def __call__(self, request: Request) -> TokenInfo:
        """提取并解析 Token（必须存在）"""
        
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        try:
            # 解析 Token
            user_token, base_url, model_name, actual_token = self.token_parser.parse_token(credentials.credentials)
            
            # 验证用户token是否存在于数据库中
            from src.services.database_service import db_service
            user = await db_service.get_user_by_token(user_token)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user token"
                )
            
            return TokenInfo(
                env_token=user_token,  # 这里是数据库中的用户token
                base_url=base_url,
                model_name=model_name,
                actual_token=actual_token
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token parsing error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token format"
            )


class SimpleTokenAuth(HTTPBearer):
    """简单的 envtoken 认证（仅用于记忆管理 API）"""
    
    def __init__(self):
        super().__init__(auto_error=True)
        self.token_parser = TokenParser()
    
    async def __call__(self, request: Request) -> str:
        """仅验证 envtoken，返回 envtoken"""
        
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        token = credentials.credentials
        
        try:
            # 首先尝试直接验证是否为有效的 envtoken
            if self.token_parser.validate_env_token(token, settings.auth_token):
                return token
            
            # 如果不是简单的 envtoken，尝试解析完整格式并提取 envtoken
            try:
                env_token, _, _, _ = self.token_parser.parse_token(token)
                
                # 验证环境 Token
                if self.token_parser.validate_env_token(env_token, settings.auth_token):
                    return env_token
                else:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid environment token"
                    )
            except:
                # 解析失败，说明既不是简单的 envtoken，也不是完整格式
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token format"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token format"
            )


# 全局认证实例
optional_token_auth = OptionalTokenAuth()
required_token_auth = RequiredTokenAuth()
simple_token_auth = SimpleTokenAuth()
