from typing import Tuple
from fastapi import HTTPException
import re


class TokenParser:
    """解析自定义格式的 Token"""
    
    @staticmethod
    def parse_token(token: str) -> Tuple[str, str, str, str]:
        """
        解析 Token 格式: 支持两种格式
        1. 新格式（推荐）: envtoken|||baseurl|||modelname|||token  
        2. 旧格式: envtoken-baseurl-modelname-token
        
        Args:
            token: 格式为上述两种之一的字符串
            
        Returns:
            Tuple[env_token, base_url, model_name, actual_token]
            
        Raises:
            HTTPException: 如果 Token 格式不正确
        """
        if not token:
            raise HTTPException(status_code=401, detail="Token is required")
        
        # 首先尝试新格式（|||分隔符）
        if '|||' in token:
            parts = token.split('|||')
            if len(parts) == 4:
                env_token, base_url, model_name, actual_token = parts
                
                # 验证 base_url 是否为有效的 URL
                if base_url.startswith(('http://', 'https://')):
                    return env_token, base_url, model_name, actual_token
                else:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid base URL format in token"
                    )
            else:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid new token format. Expected: envtoken|||baseurl|||modelname|||token"
                )
        
        # 回退到旧格式（-分隔符）- 为了向后兼容性
        # 使用正则表达式解析，支持 URL 中的特殊字符
        pattern = r'^([^-]+)-(https?://[^-]+)-(.+)-(.+)$'
        match = re.match(pattern, token)
        
        if not match:
            # 尝试更宽松的解析，假设最后两个破折号分隔模型名和token
            parts = token.split('-')
            if len(parts) < 4:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid token format. Expected: envtoken|||baseurl|||modelname|||token or envtoken-baseurl-modelname-token"
                )
            
            # 重新组合，假设 baseurl 可能包含破折号
            env_token = parts[0]
            actual_token = parts[-1]
            model_name = parts[-2]
            base_url = '-'.join(parts[1:-2])
            
            # 验证 base_url 是否为有效的 URL
            if not base_url.startswith(('http://', 'https://')):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid base URL format in token"
                )
        else:
            env_token, base_url, model_name, actual_token = match.groups()
        
        return env_token, base_url, model_name, actual_token
    
    @staticmethod
    def validate_env_token(env_token: str, expected_env_token: str) -> bool:
        """
        验证环境 Token
        
        Args:
            env_token: 从请求 Token 中解析出的环境 Token
            expected_env_token: 配置中设置的期望环境 Token
            
        Returns:
            bool: 验证是否通过
        """
        if not expected_env_token:
            # 如果没有设置期望的环境 Token，则跳过验证
            return True
        
        return env_token == expected_env_token


# 示例用法
if __name__ == "__main__":
    # 测试解析新格式
    test_token_new = "user_id|||https://api.example.com|||model-name|||api-key-here"
    # 测试解析旧格式（向后兼容）
    test_token_old = "env-token-https://api.example.com-model-name-api-key"
    
    parser = TokenParser()
    
    print("测试新格式:")
    try:
        env_token, base_url, model_name, actual_token = parser.parse_token(test_token_new)
        print(f"Environment Token: {env_token}")
        print(f"Base URL: {base_url}")
        print(f"Model Name: {model_name}")
        print(f"Actual Token: {actual_token}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n测试旧格式:")
    try:
        env_token, base_url, model_name, actual_token = parser.parse_token(test_token_old)
        print(f"Environment Token: {env_token}")
        print(f"Base URL: {base_url}")
        print(f"Model Name: {model_name}")
        print(f"Actual Token: {actual_token}")
    except Exception as e:
        print(f"Error: {e}")