from typing import List, Dict, Any, Optional
import json
import logging
import os
from src.memory.client import mem0_client
from src.config.settings import settings


logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self):
        # 确保API密钥正确设置
        self._ensure_api_keys()
        self.client = mem0_client.get_client()
    
    def _ensure_api_keys(self):
        """确保API密钥环境变量正确设置"""
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
        
        # 禁用 PostHog 遥测
        os.environ["POSTHOG_DISABLED"] = "true"
        
        api_key = os.getenv('LLM_API_KEY')
        if api_key and settings.llm_provider.lower() in ["gemini", "google"]:
            # 根据Mem0文档：LLM用GEMINI_API_KEY，Embedding用GOOGLE_API_KEY
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
    
    async def save_memory(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        保存记忆
        
        Args:
            text: 要保存的文本内容
            user_id: 用户ID
            
        Returns:
            保存结果
        """
        try:
            messages = [{"role": "user", "content": text}]
            result = self.client.add(messages, user_id=user_id)
            logger.info(f"Successfully saved memory for user {user_id}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_memories(self, query: str, user_id: str = "default", limit: int = 5) -> List[str]:
        """
        搜索相关记忆
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            limit: 返回结果数量限制
            
        Returns:
            相关记忆列表
        """
        try:
            memories = self.client.search(query, user_id=user_id, limit=limit)
            
            # 处理返回格式
            if isinstance(memories, dict) and "results" in memories:
                return [memory["memory"] for memory in memories["results"]]
            elif isinstance(memories, list):
                return memories
            else:
                logger.warning(f"Unexpected memory format: {type(memories)}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def delete_all_memories(self, user_id: str = "default") -> Dict[str, Any]:
        """
        删除用户的所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            删除结果
        """
        try:
            result = self.client.delete_all(user_id=user_id)
            logger.info(f"Successfully deleted all memories for user {user_id}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error deleting all memories: {e}")
            return {"success": False, "error": str(e)}

    async def get_all_memories(self, user_id: str = "default") -> List[str]:
        """
        获取所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            所有记忆列表
        """
        try:
            logger.info(f"Calling Mem0 client.get_all with user_id: {user_id}")
            memories = self.client.get_all(user_id=user_id)
            logger.info(f"Mem0 client returned: {type(memories)}, content: {memories}")
            
            # 处理返回格式
            if isinstance(memories, dict) and "results" in memories:
                result = [memory["memory"] for memory in memories["results"]]
                logger.info(f"Extracted {len(result)} memories from dict format")
                return result
            elif isinstance(memories, list):
                logger.info(f"Got {len(memories)} memories in list format")
                return memories
            else:
                logger.warning(f"Unexpected memory format: {type(memories)}, content: {memories}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving all memories for user {user_id}: {e}")
            return []
    
    async def get_all_memories_with_ids(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """
        获取所有记忆（包含ID信息）
        
        Args:
            user_id: 用户ID
            
        Returns:
            所有记忆列表，包含ID和内容
        """
        try:
            logger.info(f"Calling Mem0 client.get_all with user_id: {user_id}")
            memories = self.client.get_all(user_id=user_id)
            logger.info(f"Mem0 client returned: {type(memories)}, content: {memories}")
            
            # 处理返回格式
            if isinstance(memories, dict) and "results" in memories:
                result = []
                for memory in memories["results"]:
                    result.append({
                        "id": memory.get("id"),
                        "content": memory.get("memory", ""),
                        "user_id": user_id
                    })
                logger.info(f"Extracted {len(result)} memories with IDs from dict format")
                return result
            elif isinstance(memories, list):
                # 如果是列表格式，尝试提取ID和内容
                result = []
                for i, memory in enumerate(memories):
                    if isinstance(memory, dict):
                        result.append({
                            "id": memory.get("id", f"mem_{i}"),
                            "content": memory.get("memory", memory.get("content", str(memory))),
                            "user_id": user_id
                        })
                    else:
                        result.append({
                            "id": f"mem_{i}",
                            "content": str(memory),
                            "user_id": user_id
                        })
                logger.info(f"Got {len(result)} memories with generated IDs in list format")
                return result
            else:
                logger.warning(f"Unexpected memory format: {type(memories)}, content: {memories}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving all memories with IDs for user {user_id}: {e}")
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
            result = self.client.delete(memory_id=memory_id)
            logger.info(f"Successfully deleted memory {memory_id} for user {user_id}")
            return {"success": True, "result": result, "memory_id": memory_id}
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return {"success": False, "error": str(e), "memory_id": memory_id}

    async def enhance_context_with_memories(
        self, 
        messages: List[Dict[str, str]], 
        user_id: str = "default"
    ) -> List[Dict[str, str]]:
        """
        使用记忆增强对话上下文
        
        Args:
            messages: 原始对话消息
            user_id: 用户ID
            
        Returns:
            增强后的对话消息
        """
        if not messages:
            return messages
        
        # 分析对话上下文 - 考虑多轮对话
        user_messages = []
        conversation_context = []
        
        for message in messages:
            if message.get("role") == "user":
                user_messages.append(message.get("content", ""))
                conversation_context.append(f"用户: {message.get('content', '')}")
            elif message.get("role") == "assistant":
                conversation_context.append(f"助手: {message.get('content', '')}")
        
        if not user_messages:
            return messages
        
        # 构建搜索查询 - 结合最新消息和对话主题
        latest_message = user_messages[-1]
        
        # 如果是多轮对话，结合上下文进行搜索
        search_query = latest_message
        if len(user_messages) > 1:
            # 使用最近的几条消息作为上下文
            recent_context = " ".join(user_messages[-3:])  # 最近3条用户消息
            search_query = f"{recent_context} {latest_message}"
        
        # 搜索相关记忆
        relevant_memories = await self.search_memories(search_query, user_id, limit=5)
        
        if not relevant_memories:
            return messages
        
        # 构建记忆上下文 - 更智能的格式化
        memory_context = "基于你的历史信息:\n" + "\n".join([f"• {memory}" for memory in relevant_memories])
        
        # 找到合适的位置插入记忆上下文
        enhanced_messages = []
        memory_inserted = False
        
        # 策略：在最后一个系统消息后，或者在第一条用户消息前插入记忆
        for i, message in enumerate(messages):
            enhanced_messages.append(message)
            
            # 在最后一个系统消息后插入记忆
            if (message.get("role") == "system" and 
                not memory_inserted and 
                (i == len(messages) - 1 or messages[i + 1].get("role") != "system")):
                enhanced_messages.append({
                    "role": "system",
                    "content": memory_context
                })
                memory_inserted = True
        
        # 如果没有系统消息，在第一条用户消息前插入记忆系统消息
        if not memory_inserted:
            # 找到第一条用户消息的位置
            for i, message in enumerate(enhanced_messages):
                if message.get("role") == "user":
                    enhanced_messages.insert(i, {
                        "role": "system", 
                        "content": memory_context
                    })
                    break
            else:
                # 如果没有用户消息，在开头添加
                enhanced_messages.insert(0, {
                    "role": "system", 
                    "content": memory_context
                })
        
        return enhanced_messages
    
    async def save_conversation(
        self, 
        messages: List[Dict[str, str]], 
        response: str, 
        user_id: str = "default"
    ) -> None:
        """
        保存对话到记忆中
        
        Args:
            messages: 对话消息
            response: AI 响应
            user_id: 用户ID
        """
        try:
            # 分析对话内容
            user_messages = []
            assistant_messages = []
            
            for msg in messages:
                if msg.get("role") == "user":
                    user_messages.append(msg["content"])
                elif msg.get("role") == "assistant":
                    assistant_messages.append(msg["content"])
            
            if not user_messages:
                return
            
            # 决定保存策略
            if len(user_messages) == 1:
                # 单轮对话 - 保存简单的问答对
                conversation_summary = f"用户问: {user_messages[0]}\nAI答: {response}"
                await self.save_memory(conversation_summary, user_id)
            else:
                # 多轮对话 - 保存更丰富的上下文
                latest_user_msg = user_messages[-1]
                
                # 构建对话上下文摘要
                if len(user_messages) > 1:
                    context_summary = f"在讨论 {user_messages[0]} 的基础上，用户进一步询问: {latest_user_msg}"
                else:
                    context_summary = f"用户询问: {latest_user_msg}"
                
                conversation_summary = f"{context_summary}\nAI回复: {response}"
                await self.save_memory(conversation_summary, user_id)
                
                # 如果是重要的多轮对话，还可以保存整个对话的摘要
                if len(user_messages) >= 3:
                    dialogue_summary = f"用户与AI进行了关于 {user_messages[0]} 的深入讨论，涉及了 {len(user_messages)} 个相关问题"
                    await self.save_memory(dialogue_summary, user_id)
                
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")


# 全局记忆管理器实例
memory_manager = MemoryManager()
