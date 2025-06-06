from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import time
import uuid
import logging
from api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    TokenInfo,
    MemoryResponse
)
from api.middleware import optional_token_auth, required_token_auth, simple_token_auth
from services.llm_proxy import llm_proxy_service
from services.memory_service import memory_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    token_info: TokenInfo = Depends(optional_token_auth)
):
    """
    OpenAI 兼容的聊天完成 API
    """
    if not token_info:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        logger.info(f"Processing chat completion request for user: {request.user_id}")
        
        # 使用记忆增强消息
        enhanced_messages = await memory_service.enhance_messages_with_memory(
            request.messages,
            request.user_id,
            request.enable_memory
        )
        
        # 更新请求中的消息
        enhanced_request = request.copy()
        enhanced_request.messages = enhanced_messages
        
        # 处理流式和非流式请求
        if request.stream:
            # 流式响应
            return StreamingResponse(
                _stream_chat_completion(enhanced_request, token_info, request.user_id, request.enable_memory),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        else:
            # 非流式响应
            response = await llm_proxy_service.chat_completion(enhanced_request, token_info)
            
            # 保存对话记忆
            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                await memory_service.save_conversation_memory(
                    request.messages,
                    response_content,
                    request.user_id,
                    request.enable_memory
                )
            
            return response
    
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_completion(
    request: ChatCompletionRequest, 
    token_info: TokenInfo,
    user_id: str,
    enable_memory: bool
):
    """内部流式聊天完成处理"""
    
    collected_content = ""
    
    try:
        async for chunk in llm_proxy_service.chat_completion_stream(request, token_info):
            yield chunk
            
            # 收集内容用于保存记忆
            if chunk.startswith("data: ") and not chunk.strip().endswith("[DONE]"):
                try:
                    import json
                    data = json.loads(chunk[6:])
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            collected_content += delta["content"]
                except:
                    pass
        
        # 流式完成后保存记忆
        if collected_content and enable_memory:
            await memory_service.save_conversation_memory(
                request.messages,
                collected_content,
                user_id,
                enable_memory
            )
    
    except Exception as e:
        logger.error(f"Stream completion error: {e}")
        error_chunk = f"data: {{'error': {{'message': '{str(e)}'}}}}\n\n"
        yield error_chunk


@router.get("/v1/models")
async def list_models(token_info: TokenInfo = Depends(optional_token_auth)):
    """
    列出可用模型（兼容 OpenAI API）
    """
    if not token_info:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "object": "list",
        "data": [
            {
                "id": token_info.model_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "mem0-chatapi"
            }
        ]
    }


# 记忆管理 API
@router.post("/v1/memory/save", response_model=MemoryResponse)
async def save_memory(
    content: str,
    user_id: str = "default",
    env_token: str = Depends(simple_token_auth)
):
    """保存记忆"""
    try:
        result = await memory_service.save_user_memory(content, user_id)
        return MemoryResponse(
            success=result.get("success", False),
            message="Memory saved successfully" if result.get("success") else "Failed to save memory",
            data=result
        )
    except Exception as e:
        logger.error(f"Save memory error: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error saving memory: {str(e)}"
        )


@router.get("/v1/memory/search", response_model=MemoryResponse)
async def search_memories(
    query: str,
    user_id: str = "default",
    limit: int = 5,
    env_token: str = Depends(simple_token_auth)
):
    """搜索记忆"""
    try:
        memories = await memory_service.search_user_memories(query, user_id, limit)
        return MemoryResponse(
            success=True,
            message=f"Found {len(memories)} memories",
            data=memories
        )
    except Exception as e:
        logger.error(f"Search memories error: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error searching memories: {str(e)}"
        )


@router.get("/v1/memory/list", response_model=MemoryResponse)
async def list_memories(
    user_id: str = "default",
    env_token: str = Depends(simple_token_auth)
):
    """获取所有记忆"""
    try:
        memories = await memory_service.get_user_memories(user_id)
        return MemoryResponse(
            success=True,
            message=f"Retrieved {len(memories)} memories",
            data=memories
        )
    except Exception as e:
        logger.error(f"List memories error: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error retrieving memories: {str(e)}"
        )


@router.delete("/v1/memory/clear", response_model=MemoryResponse)
async def clear_memories(
    user_id: str = "default",
    env_token: str = Depends(simple_token_auth)
):
    """清空所有记忆"""
    try:
        result = await memory_service.delete_all_user_memories(user_id)
        return MemoryResponse(
            success=result.get("success", False),
            message="All memories cleared successfully" if result.get("success") else "Failed to clear memories",
            data=result
        )
    except Exception as e:
        logger.error(f"Clear memories error: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error clearing memories: {str(e)}"
        )
