from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
from src.api.models import MemoryResponse, SaveMemoryRequest
from src.services.auth_service import verify_user_token
from src.services.memory_service import memory_service
from src.services.database_service import db_service
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/memory", tags=["Memory Management"])


@router.post("/save", response_model=MemoryResponse)
async def save_memory(
    request: SaveMemoryRequest,
    user_id: str = Depends(verify_user_token)
):
    """保存记忆
    
    Args:
        request: 保存记忆的请求体
        user_id: 从 token 自动提取的用户ID
    
    Returns:
        MemoryResponse: 保存结果
    """
    try:
        logger.info(f"Saving memory for user: {user_id}")
        
        # 生成记忆ID
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        # 同时保存到Mem0和数据库
        mem0_result = await memory_service.save_user_memory(request.content, user_id)
        db_result = await db_service.save_memory(
            user_id=user_id,
            memory_id=memory_id,
            content=request.content,
            metadata={"source": "chat_api", "mem0_result": mem0_result}
        )
        
        # 更新用户活动
        await db_service.update_user_activity(user_id)
        
        return MemoryResponse(
            success=mem0_result.get("success", False),
            message="Memory saved successfully" if mem0_result.get("success") else "Failed to save memory",
            data={
                "memory_id": memory_id,
                "mem0_result": mem0_result,
                "db_saved": True
            }
        )
    except Exception as e:
        logger.error(f"Save memory error for user {user_id}: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error saving memory: {str(e)}"
        )


@router.get("/search", response_model=MemoryResponse)
async def search_memories(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(5, ge=1, le=50, description="返回结果数量限制"),
    user_id: str = Depends(verify_user_token)
):
    """搜索记忆
    
    Args:
        query: 搜索查询字符串
        limit: 返回结果数量限制 (1-50)
        user_id: 从 token 自动提取的用户ID
    
    Returns:
        MemoryResponse: 搜索结果
    """
    try:
        logger.info(f"Searching memories for user: {user_id}, query: {query}")
        memories = await memory_service.search_user_memories(query, user_id, limit)
        return MemoryResponse(
            success=True,
            message=f"Found {len(memories)} memories",
            data=memories
        )
    except Exception as e:
        logger.error(f"Search memories error for user {user_id}: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error searching memories: {str(e)}"
        )


@router.get("/list", response_model=MemoryResponse)
async def list_memories(
    user_id: str = Depends(verify_user_token)
):
    """获取用户的所有记忆
    
    Args:
        user_id: 从 token 自动提取的用户ID
    
    Returns:
        MemoryResponse: 记忆列表
    """
    try:
        logger.info(f"Listing memories for user: {user_id}")
        memories = await memory_service.get_user_memories(user_id)
        return MemoryResponse(
            success=True,
            message=f"Retrieved {len(memories)} memories",
            data=memories
        )
    except Exception as e:
        logger.error(f"List memories error for user {user_id}: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error retrieving memories: {str(e)}"
        )


@router.delete("/clear", response_model=MemoryResponse)
async def clear_memories(
    user_id: str = Depends(verify_user_token)
):
    """清空用户的所有记忆
    
    Args:
        user_id: 从 token 自动提取的用户ID
    
    Returns:
        MemoryResponse: 清空结果
    """
    try:
        logger.info(f"Clearing all memories for user: {user_id}")
        result = await memory_service.delete_all_user_memories(user_id)
        return MemoryResponse(
            success=result.get("success", False),
            message="All memories cleared successfully" if result.get("success") else "Failed to clear memories",
            data=result
        )
    except Exception as e:
        logger.error(f"Clear memories error for user {user_id}: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error clearing memories: {str(e)}"
        )


@router.get("/stats", response_model=MemoryResponse)
async def get_memory_stats(
    user_id: str = Depends(verify_user_token)
):
    """获取用户记忆统计信息
    
    Args:
        user_id: 从 token 自动提取的用户ID
    
    Returns:
        MemoryResponse: 统计信息
    """
    try:
        logger.info(f"Getting memory stats for user: {user_id}")
        memories = await memory_service.get_user_memories(user_id)
        
        stats = {
            "total_memories": len(memories),
            "user_id": user_id,
            "last_updated": None  # 可以从记忆中获取最新时间
        }
        
        return MemoryResponse(
            success=True,
            message="Memory statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Get memory stats error for user {user_id}: {e}")
        return MemoryResponse(
            success=False,
            message=f"Error retrieving memory statistics: {str(e)}"
        )
