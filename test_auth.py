#!/usr/bin/env python3
"""
测试新的三层认证系统
验证Chat API、Memory API和Admin API的token格式
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# 测试配置
MAIN_SERVER = "http://localhost:8050"
ADMIN_SERVER = "http://localhost:8060"

# 测试token - 使用正确的分隔符
CHAT_TOKEN = "user_alice|||https://generativelanguage.googleapis.com/v1beta/openai/|||gemini-2.0-flash-exp|||REDACTED_API_KEY"
MEMORY_TOKEN = "user_alice"
ADMIN_TOKEN = "super-secret-admin-key"

async def test_chat_api():
    """测试Chat API的认证"""
    print("🔍 测试Chat API认证...")
    
    # 测试聊天请求
    test_payload = {
        "model": "gemini-2.0-flash-exp",
        "messages": [
            {"role": "user", "content": "Hello, my name is Alice. I like coffee."}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{MAIN_SERVER}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {CHAT_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=test_payload
            ) as response:
                print(f"   状态码: {response.status}")
                if response.status == 200:
                    print("   ✅ Chat API认证成功")
                    result = await response.json()
                    print(f"   响应: {result.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]}...")
                else:
                    print(f"   ❌ Chat API认证失败: {await response.text()}")
        except Exception as e:
            print(f"   ❌ Chat API连接错误: {e}")

async def test_memory_api():
    """测试Memory API的认证"""
    print("\n🧠 测试Memory API认证...")
    
    # 测试保存记忆
    async with aiohttp.ClientSession() as session:
        try:
            # 保存记忆
            async with session.post(
                f"{MAIN_SERVER}/v1/memory/save",
                headers={
                    "Authorization": f"Bearer {MEMORY_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={"content": "Alice喜欢喝咖啡，特别是美式咖啡"}
            ) as response:
                print(f"   保存记忆 - 状态码: {response.status}")
                if response.status == 200:
                    print("   ✅ Memory API保存成功")
                    result = await response.json()
                    print(f"   结果: {result}")
                else:
                    print(f"   ❌ Memory API保存失败: {await response.text()}")
            
            # 搜索记忆
            async with session.get(
                f"{MAIN_SERVER}/v1/memory/search?query=咖啡",
                headers={
                    "Authorization": f"Bearer {MEMORY_TOKEN}",
                }
            ) as response:
                print(f"   搜索记忆 - 状态码: {response.status}")
                if response.status == 200:
                    print("   ✅ Memory API搜索成功")
                    result = await response.json()
                    print(f"   结果: {result}")
                else:
                    print(f"   ❌ Memory API搜索失败: {await response.text()}")
                    
        except Exception as e:
            print(f"   ❌ Memory API连接错误: {e}")

async def test_admin_api():
    """测试Admin API的认证"""
    print("\n🎛️ 测试Admin API认证...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 测试统计信息
            async with session.get(
                f"{ADMIN_SERVER}/admin/stats",
                headers={
                    "Authorization": f"Bearer {ADMIN_TOKEN}",
                }
            ) as response:
                print(f"   获取统计 - 状态码: {response.status}")
                if response.status == 200:
                    print("   ✅ Admin API认证成功")
                    result = await response.json()
                    print(f"   统计数据: {result}")
                else:
                    print(f"   ❌ Admin API认证失败: {await response.text()}")
            
            # 测试用户列表
            async with session.get(
                f"{ADMIN_SERVER}/admin/users",
                headers={
                    "Authorization": f"Bearer {ADMIN_TOKEN}",
                }
            ) as response:
                print(f"   获取用户列表 - 状态码: {response.status}")
                if response.status == 200:
                    print("   ✅ Admin用户列表获取成功")
                    result = await response.json()
                    print(f"   用户数量: {len(result)}")
                else:
                    print(f"   ❌ Admin用户列表获取失败: {await response.text()}")
                    
        except Exception as e:
            print(f"   ❌ Admin API连接错误: {e}")

async def test_invalid_tokens():
    """测试无效token的拒绝"""
    print("\n🚫 测试无效token...")
    
    invalid_tokens = [
        ("错误的chat token", "invalid-token"),
        ("错误的memory token", "invalid_user"),
        ("错误的admin token", "wrong-admin-key")
    ]
    
    async with aiohttp.ClientSession() as session:
        for desc, token in invalid_tokens:
            try:
                async with session.get(
                    f"{MAIN_SERVER}/v1/memory/list",
                    headers={"Authorization": f"Bearer {token}"}
                ) as response:
                    if response.status == 401:
                        print(f"   ✅ {desc} 正确被拒绝 (401)")
                    else:
                        print(f"   ❌ {desc} 应该被拒绝但返回了: {response.status}")
            except Exception as e:
                print(f"   ❌ 测试 {desc} 时连接错误: {e}")

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🎯 Mem0 Chat API 三层认证系统测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"主服务: {MAIN_SERVER}")
    print(f"管理后台: {ADMIN_SERVER}")
    print()
    
    # 等待服务启动
    print("⏱️ 等待服务启动...")
    await asyncio.sleep(2)
    
    # 依次测试各个API
    await test_chat_api()
    await test_memory_api()
    await test_admin_api()
    await test_invalid_tokens()
    
    print("\n" + "=" * 60)
    print("✅ 认证系统测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
