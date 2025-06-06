#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import os

MAIN_SERVER = "http://localhost:8050"
ADMIN_SERVER = "http://localhost:8060"
CHAT_TOKEN = os.getenv("TEST_CHAT_TOKEN", "user_test|||https://api.example.com|||test-model|||test-api-key")
MEMORY_TOKEN = os.getenv("TEST_MEMORY_TOKEN", "user_test")
ADMIN_TOKEN = os.getenv("TEST_ADMIN_TOKEN", "test-admin-key")

async def test_simple():
    print("🎯 Mem0 Chat API 认证系统测试")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 1. 测试Chat API
        print("🔍 测试Chat API...")
        try:
            payload = {
                "model": "gemini-2.0-flash-exp",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            async with session.post(
                f"{MAIN_SERVER}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {CHAT_TOKEN}"}
            ) as resp:
                print(f"   Chat API状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print("   ✅ Chat API成功")
                else:
                    error = await resp.text()
                    print(f"   ❌ Chat API失败: {error}")
        except Exception as e:
            print(f"   ❌ Chat API错误: {e}")
        
        # 2. 测试Memory API
        print("🧠 测试Memory API...")
        try:
            payload = {"messages": [{"role": "user", "content": "我喜欢咖啡"}]}
            async with session.post(
                f"{MAIN_SERVER}/v1/memory/save",
                json=payload,
                headers={"Authorization": f"Bearer {MEMORY_TOKEN}"}
            ) as resp:
                print(f"   Memory API状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print("   ✅ Memory API成功")
                else:
                    error = await resp.text()
                    print(f"   ❌ Memory API失败: {error}")
        except Exception as e:
            print(f"   ❌ Memory API错误: {e}")
        
        # 3. 测试Admin API
        print("🎛️ 测试Admin API...")
        try:
            async with session.get(
                f"{ADMIN_SERVER}/admin/stats",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            ) as resp:
                print(f"   Admin API状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print("   ✅ Admin API成功")
                    print(f"   统计: {result}")
                else:
                    error = await resp.text()
                    print(f"   ❌ Admin API失败: {error}")
        except Exception as e:
            print(f"   ❌ Admin API错误: {e}")
    
    print("=" * 50)
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_simple())
