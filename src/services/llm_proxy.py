import httpx
from typing import Dict, Any, List, AsyncGenerator
import json
import logging
from src.api.models import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatMessage,
    TokenInfo
)


logger = logging.getLogger(__name__)


class LLMProxyService:
    """LLM 代理服务"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat_completion(
        self, 
        request: ChatCompletionRequest, 
        token_info: TokenInfo
    ) -> ChatCompletionResponse:
        """
        调用上游 LLM API 进行聊天完成
        
        Args:
            request: 聊天完成请求
            token_info: Token 信息
            
        Returns:
            聊天完成响应
        """
        try:
            # 构建上游请求
            upstream_request = self._build_upstream_request(request, token_info)
            
            # 发送请求到上游 API
            url = f"{token_info.base_url.rstrip('/')}/chat/completions"
            
            logger.info(f"Sending request to upstream API: {url}")
            
            response = await self.client.post(
                url,
                json=upstream_request,
                headers={
                    "Authorization": f"Bearer {token_info.actual_token}",
                    "Content-Type": "application/json"
                }
            )
            
            response.raise_for_status()
            
            # 解析响应
            response_data = response.json()
            
            # 转换为标准格式
            return ChatCompletionResponse(**response_data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Upstream API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Upstream API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"LLM proxy error: {e}")
            raise Exception(f"LLM proxy error: {str(e)}")
    
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest, 
        token_info: TokenInfo
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天完成
        
        Args:
            request: 聊天完成请求
            token_info: Token 信息
            
        Yields:
            流式响应数据
        """
        try:
            # 构建上游请求
            upstream_request = self._build_upstream_request(request, token_info)
            upstream_request["stream"] = True
            
            # 发送流式请求
            url = f"{token_info.base_url.rstrip('/')}/chat/completions"
            
            logger.info(f"Sending stream request to upstream API: {url}")
            
            async with self.client.stream(
                "POST",
                url,
                json=upstream_request,
                headers={
                    "Authorization": f"Bearer {token_info.actual_token}",
                    "Content-Type": "application/json"
                }
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        if data == "[DONE]":
                            break
                        try:
                            # 验证是否为有效的 JSON
                            json.loads(data)
                            yield f"data: {data}\n\n"
                        except json.JSONDecodeError:
                            continue
                
                yield "data: [DONE]\n\n"
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Upstream API stream error: {e.response.status_code}")
            error_data = {
                "error": {
                    "message": f"Upstream API error: {e.response.status_code}",
                    "type": "upstream_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        except Exception as e:
            logger.error(f"LLM proxy stream error: {e}")
            error_data = {
                "error": {
                    "message": f"Proxy error: {str(e)}",
                    "type": "proxy_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    def _build_upstream_request(self, request: ChatCompletionRequest, token_info: TokenInfo) -> Dict[str, Any]:
        """构建上游 API 请求"""
        
        # 基础请求数据
        upstream_request = {
            "model": token_info.model_name,  # 使用 Token 中的模型名
            "messages": [msg.model_dump() for msg in request.messages],
        }
        
        # 根据 API 提供商决定支持的参数
        is_gemini_api = "generativelanguage.googleapis.com" in token_info.base_url
        
        # 添加可选参数
        if request.temperature is not None:
            upstream_request["temperature"] = request.temperature
        if request.max_tokens is not None:
            upstream_request["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            upstream_request["top_p"] = request.top_p
        if request.stop is not None:
            upstream_request["stop"] = request.stop
        if request.stream is not None:
            upstream_request["stream"] = request.stream
            
        # OpenAI 特有的参数，Gemini 不支持
        if not is_gemini_api:
            if request.frequency_penalty is not None:
                upstream_request["frequency_penalty"] = request.frequency_penalty
            if request.presence_penalty is not None:
                upstream_request["presence_penalty"] = request.presence_penalty
        
        return upstream_request
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 全局 LLM 代理服务实例
llm_proxy_service = LLMProxyService()
