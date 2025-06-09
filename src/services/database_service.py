"""
数据库服务
管理用户和记忆数据的持久化存储
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import aiosqlite
import random
import string

from src.config.settings import settings

settings = settings


@dataclass
class UserData:
    """用户数据类"""
    user_id: str
    username: str
    user_token: str
    memory_count: int = 0
    first_seen: Optional[str] = None
    last_activity: Optional[str] = None
    total_requests: int = 0
    # LLM配置信息
    llm_base_url: Optional[str] = None
    llm_model_name: Optional[str] = None
    llm_api_key: Optional[str] = None


@dataclass 
class MemoryData:
    """记忆数据类"""
    id: str
    user_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self):
        self.db_path = settings.db_url.replace("sqlite:///", "")
        self._initialized = False
    
    def _generate_token(self) -> str:
        """生成16字符的token，以'Mem'开头，后跟13个随机字符"""
        chars = string.ascii_letters + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(13))
        return f"Mem{random_part}"
    
    async def initialize(self):
        """初始化数据库"""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            # 创建用户表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    user_token TEXT UNIQUE NOT NULL,
                    memory_count INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_activity TEXT,
                    total_requests INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # 创建记忆表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # 创建索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories (user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories (created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users (last_activity)")
            
            await db.commit()
        
        self._initialized = True
    
    async def ensure_user_exists(self, user_id: str, username: str = None, user_token: str = None) -> UserData:
        """确保用户存在，如果不存在则创建"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # 检查用户是否存在
            async with db.execute("SELECT user_id, username, user_token, memory_count, first_seen, last_activity, total_requests FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                return UserData(
                    user_id=row[0],
                    username=row[1],
                    user_token=row[2],
                    memory_count=row[3],
                    first_seen=row[4],
                    last_activity=row[5],
                    total_requests=row[6]
                )
            else:
                # 创建新用户 - 只有在显式提供username和token时才创建
                if username and user_token:
                    now = datetime.now().isoformat()
                    await db.execute("""
                        INSERT INTO users (user_id, username, user_token, first_seen, last_activity)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, username, user_token, now, now))
                    await db.commit()
                    
                    return UserData(
                        user_id=user_id,
                        username=username,
                        user_token=user_token,
                        memory_count=0,
                        first_seen=now,
                        last_activity=now,
                        total_requests=0
                    )
                else:
                    raise ValueError(f"User {user_id} not found and username/token not provided")
    
    async def update_user_activity(self, user_id: str):
        """更新用户活动时间"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().isoformat()
            await db.execute("""
                UPDATE users 
                SET last_activity = ?, total_requests = total_requests + 1
                WHERE user_id = ?
            """, (now, user_id))
            await db.commit()
    
    async def save_memory(self, user_id: str, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> MemoryData:
        """保存记忆"""
        await self.initialize()
        await self.ensure_user_exists(user_id)
        
        if metadata is None:
            metadata = {}
        
        now = datetime.now().isoformat()
        memory_data = MemoryData(
            id=memory_id,
            user_id=user_id,
            content=content,
            metadata=metadata,
            created_at=now
        )
        
        async with aiosqlite.connect(self.db_path) as db:
            # 保存记忆
            await db.execute("""
                INSERT OR REPLACE INTO memories (id, user_id, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (memory_id, user_id, content, json.dumps(metadata), now))
            
            # 更新用户记忆计数
            await db.execute("""
                UPDATE users 
                SET memory_count = (
                    SELECT COUNT(*) FROM memories WHERE user_id = ?
                )
                WHERE user_id = ?
            """, (user_id, user_id))
            
            await db.commit()
        
        return memory_data
    
    async def get_user_memories(self, user_id: str, limit: int = 100, offset: int = 0) -> List[MemoryData]:
        """获取用户记忆"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()
        
        memories = []
        for row in rows:
            memories.append(MemoryData(
                id=row[0],
                user_id=row[1],
                content=row[2],
                metadata=json.loads(row[3]) if row[3] else {},
                created_at=row[4],
                updated_at=row[5]
            ))
        
        return memories
    
    async def delete_memory(self, memory_id: str, user_id: str = None) -> bool:
        """删除记忆"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            if user_id:
                # 只允许删除指定用户的记忆
                cursor = await db.execute("""
                    DELETE FROM memories 
                    WHERE id = ? AND user_id = ?
                """, (memory_id, user_id))
            else:
                # 管理员可以删除任何记忆
                cursor = await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            deleted = cursor.rowcount > 0
            
            if deleted and user_id:
                # 更新用户记忆计数
                await db.execute("""
                    UPDATE users 
                    SET memory_count = (
                        SELECT COUNT(*) FROM memories WHERE user_id = ?
                    )
                    WHERE user_id = ?
                """, (user_id, user_id))
            
            await db.commit()
        
        return deleted
    
    async def clear_user_memories(self, user_id: str) -> int:
        """清空用户所有记忆"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            
            # 更新用户记忆计数
            await db.execute("UPDATE users SET memory_count = 0 WHERE user_id = ?", (user_id,))
            await db.commit()
        
        return deleted_count
    
    async def get_all_users(self) -> List[UserData]:
        """获取所有用户"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, username, user_token, memory_count, first_seen, last_activity, total_requests
                FROM users
                ORDER BY last_activity DESC
            """) as cursor:
                rows = await cursor.fetchall()
        
        users = []
        for row in rows:
            users.append(UserData(
                user_id=row[0],
                username=row[1],
                user_token=row[2],
                memory_count=row[3],
                first_seen=row[4],
                last_activity=row[5],
                total_requests=row[6]
            ))
        
        return users
    
    async def get_all_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryData]:
        """获取所有记忆（管理员功能）"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, user_id, content, metadata, created_at, updated_at
                FROM memories 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
        
        memories = []
        for row in rows:
            memories.append(MemoryData(
                id=row[0],
                user_id=row[1],
                content=row[2],
                metadata=json.loads(row[3]) if row[3] else {},
                created_at=row[4],
                updated_at=row[5]
            ))
        
        return memories
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # 总用户数
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]
            
            # 总记忆数
            async with db.execute("SELECT COUNT(*) FROM memories") as cursor:
                total_memories = (await cursor.fetchone())[0]
            
            # 今日活跃用户（简化：最近活动的用户）
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE date(last_activity) = date('now')
            """) as cursor:
                active_users_today = (await cursor.fetchone())[0]
            
            # 总请求数
            async with db.execute("SELECT SUM(total_requests) FROM users") as cursor:
                total_requests = (await cursor.fetchone())[0] or 0
            
            # 平均每用户记忆数
            avg_memories_per_user = total_memories / max(total_users, 1)
        
        return {
            "total_users": total_users,
            "total_memories": total_memories,
            "active_users_today": active_users_today,
            "total_chat_requests": total_requests,
            "total_memory_operations": total_memories,  # 简化统计
            "avg_memories_per_user": round(avg_memories_per_user, 1),
            "system_uptime_hours": 24  # 简化：固定值
        }
    
    async def clear_all_data(self) -> Dict[str, int]:
        """清空所有数据（危险操作）"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # 获取删除前的计数
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                deleted_users = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM memories") as cursor:
                deleted_memories = (await cursor.fetchone())[0]
            
            # 删除所有数据
            await db.execute("DELETE FROM memories")
            await db.execute("DELETE FROM users")
            await db.commit()
        
        return {
            "deleted_users": deleted_users,
            "deleted_memories": deleted_memories
        }
    
    async def export_all_data(self) -> Dict[str, Any]:
        """导出所有数据"""
        users = await self.get_all_users()
        memories = await self.get_all_memories(limit=10000)  # 大数量限制
        
        return {
            "export_time": datetime.now().isoformat(),
            "version": "1.0",
            "total_users": len(users),
            "total_memories": len(memories),
            "users": [
                {
                    "user_id": user.user_id,
                    "memory_count": user.memory_count,
                    "first_seen": user.first_seen,
                    "last_activity": user.last_activity,
                    "total_requests": user.total_requests
                }
                for user in users
            ],
            "memories": [
                {
                    "id": memory.id,
                    "user_id": memory.user_id,
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at
                }
                for memory in memories
            ]
        }
    
    async def get_user_by_token(self, user_token: str) -> Optional[UserData]:
        """通过token获取用户信息"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, username, user_token, memory_count, first_seen, last_activity, total_requests 
                FROM users WHERE user_token = ?
            """, (user_token,)) as cursor:
                row = await cursor.fetchone()
            
            if row:
                return UserData(
                    user_id=row[0],
                    username=row[1],
                    user_token=row[2],
                    memory_count=row[3],
                    first_seen=row[4],
                    last_activity=row[5],
                    total_requests=row[6]
                )
            return None
    
    async def create_user(self, username: str, user_token: str = None) -> UserData:
        """创建新用户"""
        await self.initialize()
        
        # 如果没有提供token或token为空，自动生成一个
        if not user_token or user_token.strip() == "":
            user_token = self._generate_token()
            # 确保生成的token是唯一的
            async with aiosqlite.connect(self.db_path) as db:
                while True:
                    async with db.execute("SELECT user_id FROM users WHERE user_token = ?", (user_token,)) as cursor:
                        if not await cursor.fetchone():
                            break
                    user_token = self._generate_token()
        
        # 生成user_id
        user_id = f"user_{username}"
        
        async with aiosqlite.connect(self.db_path) as db:
            # 检查用户名是否已存在
            async with db.execute("SELECT user_id FROM users WHERE username = ?", (username,)) as cursor:
                if await cursor.fetchone():
                    raise ValueError(f"Username '{username}' already exists")
            
            # 检查token是否已存在（如果是用户提供的token）
            if user_token:
                async with db.execute("SELECT user_id FROM users WHERE user_token = ?", (user_token,)) as cursor:
                    if await cursor.fetchone():
                        raise ValueError(f"Token already exists")
            
            # 创建用户
            now = datetime.now().isoformat()
            await db.execute("""
                INSERT INTO users (user_id, username, user_token, first_seen, last_activity)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, user_token, now, now))
            await db.commit()
            
            return UserData(
                user_id=user_id,
                username=username,
                user_token=user_token,
                memory_count=0,
                first_seen=now,
                last_activity=now,
                total_requests=0
            )
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户及其所有记忆"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # 检查用户是否存在
            async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
                if not await cursor.fetchone():
                    return False
            
            # 删除用户的所有记忆
            await db.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            
            # 删除用户
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            await db.commit()
            return True
    
    async def update_user_token(self, user_id: str, new_token: str) -> bool:
        """更新用户token"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # 检查新token是否已被使用
            async with db.execute("SELECT user_id FROM users WHERE user_token = ? AND user_id != ?", (new_token, user_id)) as cursor:
                if await cursor.fetchone():
                    raise ValueError("Token already exists")
            
            # 更新token
            result = await db.execute("UPDATE users SET user_token = ? WHERE user_id = ?", (new_token, user_id))
            await db.commit()
            
            return result.rowcount > 0

    async def update_user_memory_count(self, user_id: str, memory_count: int) -> bool:
        """更新用户记忆计数"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute(
                "UPDATE users SET memory_count = ? WHERE user_id = ?", 
                (memory_count, user_id)
            )
            await db.commit()
            
            return result.rowcount > 0


# 创建全局数据库服务实例
db_service = DatabaseService()
