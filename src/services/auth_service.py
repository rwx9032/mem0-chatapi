from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from src.config.settings import settings
from src.api.models import TokenInfo

logger = logging.getLogger(__name__)
bearer = HTTPBearer()


class AuthService:
    """统一认证服务"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def parse_chat_token(token: str) -> TokenInfo:
        """解析完整的 chat token: user_id|||baseurl|||model|||apikey"""
        try:
            # 使用 ||| 作为分隔符避免模型名和URL中的短横线冲突
            parts = token.split('|||')
            
            if len(parts) != 4:
                raise ValueError("Invalid token format. Expected: user_id|||baseurl|||model|||apikey")
            
            user_id, base_url, model_name, api_key = parts
            
            # 验证 user_id 格式
            if not user_id.startswith('user_'):
                raise ValueError("User ID must start with 'user_'")
            
            # 验证其他必要字段
            if not base_url.startswith(('http://', 'https://')):
                raise ValueError("Base URL must be a valid HTTP(S) URL")
            
            if not model_name.strip():
                raise ValueError("Model name cannot be empty")
            
            if not api_key.strip():
                raise ValueError("API key cannot be empty")
            
            return TokenInfo(
                env_token=user_id,
                base_url=base_url,
                model_name=model_name,
                actual_token=api_key
            )
            
        except Exception as e:
            logger.error(f"Chat token parsing error: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid chat token format: {str(e)}"
            )
    
    @staticmethod
    async def validate_user_token(token: str) -> str:
        """使用数据库验证用户token，返回user_id"""
        from src.services.database_service import db_service
        
        try:
            # 通过token查找用户
            user = await db_service.get_user_by_token(token)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user token"
                )
            
            return user.user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User token validation error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Token validation failed"
            )
    
    @staticmethod
    def parse_user_token(token: str) -> str:
        """解析用户 token，返回 user_id (简单验证)"""
        if not token.startswith('user_'):
            raise HTTPException(
                status_code=401,
                detail="User token must start with 'user_'"
            )
        
        # 验证 user_id 格式（可以添加更多验证规则）
        if len(token) < 6:  # user_ + 至少1个字符
            raise HTTPException(
                status_code=401,
                detail="User ID too short"
            )
        
        return token
    
    @staticmethod
    def verify_admin_token(token: str) -> bool:
        """验证管理员 token"""
        if token != settings.admin_secret_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid admin token"
            )
        return True


# 依赖注入函数
async def verify_chat_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> TokenInfo:
    """验证 Chat API token"""
    return AuthService.parse_chat_token(credentials.credentials)


async def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """验证用户 token（使用数据库）"""
    return await AuthService.validate_user_token(credentials.credentials)


async def verify_user_token_simple(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """验证用户 token（简单验证，向后兼容）"""
    return AuthService.parse_user_token(credentials.credentials)


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> bool:
    """验证管理员 token"""
    return AuthService.verify_admin_token(credentials.credentials)


# 可选认证（兼容性）
class OptionalChatAuth(HTTPBearer):
    """可选的 Chat Token 认证"""
    
    def __init__(self):
        super().__init__(auto_error=False)
    
    async def __call__(self, request) -> Optional[TokenInfo]:
        credentials = await super().__call__(request)
        if not credentials:
            return None
        
        try:
            return AuthService.parse_chat_token(credentials.credentials)
        except HTTPException:
            return None


optional_chat_auth = OptionalChatAuth()
