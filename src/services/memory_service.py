from typing import List, Dict, Any
import logging
from src.memory.manager import memory_manager
from src.api.models import ChatMessage


logger = logging.getLogger(__name__)


class MemoryService:
    """记忆服务封装"""
    
    def __init__(self):
        self.memory_manager = memory_manager
    
    async def enhance_messages_with_memory(
        self, 
        messages: List[ChatMessage], 
        user_id: str = "default",
        enable_memory: bool = True
    ) -> List[ChatMessage]:
        """
        使用记忆增强消息
        
        Args:
            messages: 原始消息列表
            user_id: 用户ID
            enable_memory: 是否启用记忆功能
            
        Returns:
            增强后的消息列表
        """
        if not enable_memory:
            return messages
        
        try:
            # 转换为字典格式
            message_dicts = [msg.model_dump() for msg in messages]
            
            # 使用记忆管理器增强上下文
            enhanced_message_dicts = await self.memory_manager.enhance_context_with_memories(
                message_dicts, user_id
            )
            
            # 转换回 ChatMessage 对象
            enhanced_messages = [ChatMessage(**msg) for msg in enhanced_message_dicts]
            
            logger.info(f"Enhanced {len(messages)} messages with memory for user {user_id}")
            return enhanced_messages
            
        except Exception as e:
            logger.error(f"Error enhancing messages with memory: {e}")
            # 如果记忆增强失败，返回原始消息
            return messages
    
    async def save_conversation_memory(
        self, 
        messages: List[ChatMessage], 
        response_content: str, 
        user_id: str = "default",
        enable_memory: bool = True
    ) -> None:
        """
        保存对话记忆
        
        Args:
            messages: 对话消息
            response_content: AI 响应内容
            user_id: 用户ID
            enable_memory: 是否启用记忆功能
        """
        if not enable_memory:
            return
        
        try:
            # 转换为字典格式
            message_dicts = [msg.model_dump() for msg in messages]
            
            # 保存对话到Mem0
            await self.memory_manager.save_conversation(
                message_dicts, response_content, user_id
            )
            
            # 同时保存到SQLite数据库
            # 导入数据库服务
            from src.services.database_service import db_service
            import uuid
            
            # 构建对话摘要作为记忆内容
            user_messages = [msg for msg in messages if msg.role == "user"]
            if user_messages:
                latest_user_msg = user_messages[-1].content
                if len(user_messages) == 1:
                    conversation_summary = f"用户问: {latest_user_msg}\nAI答: {response_content}"
                else:
                    conversation_summary = f"在多轮对话中，用户询问: {latest_user_msg}\nAI回复: {response_content}"
                
                # 生成记忆ID并保存到数据库
                memory_id = f"conv_{uuid.uuid4().hex[:12]}"
                await db_service.save_memory(
                    user_id=user_id,
                    memory_id=memory_id,
                    content=conversation_summary,
                    metadata={"source": "conversation", "type": "auto_save"}
                )
                
                # 更新用户活动
                await db_service.update_user_activity(user_id)
            
            logger.info(f"Saved conversation memory to both Mem0 and database for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation memory: {e}")
    
    async def search_user_memories(
        self, 
        query: str, 
        user_id: str = "default", 
        limit: int = 5
    ) -> List[str]:
        """
        搜索用户记忆
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        try:
            memories = await self.memory_manager.search_memories(query, user_id, limit)
            logger.info(f"Found {len(memories)} memories for query: {query}")
            return memories
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def save_user_memory(
        self, 
        content: str, 
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        保存用户记忆
        
        Args:
            content: 记忆内容
            user_id: 用户ID
            
        Returns:
            保存结果
        """
        try:
            result = await self.memory_manager.save_memory(content, user_id)
            logger.info(f"Saved memory for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_memories(self, user_id: str = "default") -> List[str]:
        """
        获取用户所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户记忆列表
        """
        try:
            memories = await self.memory_manager.get_all_memories(user_id)
            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def delete_all_user_memories(self, user_id: str = "default") -> Dict[str, Any]:
        """
        删除用户所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            result = await self.memory_manager.delete_all_memories(user_id)
            logger.info(f"Deleted all memories for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting all memories: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_memories_with_ids(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """
        获取用户记忆（包含ID信息）
        
        Args:
            user_id: 用户ID
            
        Returns:
            记忆列表，包含ID和内容
        """
        try:
            memories = await self.memory_manager.get_all_memories_with_ids(user_id)
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories with IDs: {e}")
            return []

    async def delete_memory_by_id(self, memory_id: str, user_id: str = "default") -> Dict[str, Any]:
        """
        删除特定记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            result = await self.memory_manager.delete_memory_by_id(memory_id, user_id)
            logger.info(f"Deleted memory {memory_id} for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return {"success": False, "error": str(e)}


# 全局记忆服务实例
memory_service = MemoryService()
