#!/usr/bin/env python3
"""
测试三层认证系统 - 从环境变量读取配置
验证Chat API、Memory API和Admin API的token格式
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Optional


class TestConfig:
    """测试配置，从环境变量读取"""
    
    def __init__(self):
        # 服务器配置
        self.main_server = os.getenv("TEST_MAIN_SERVER", "http://localhost:8050")
        self.admin_server = os.getenv("TEST_ADMIN_SERVER", "http://localhost:8060")
        
        # Token配置 - 必须从环境变量获取
        self.chat_token = self._get_chat_token()
        self.memory_token = os.getenv("TEST_MEMORY_TOKEN", "user_alice")
        self.admin_token = os.getenv("TEST_ADMIN_TOKEN", "super-secret-admin-key")
        
        # 测试配置
        self.test_user_id = os.getenv("TEST_USER_ID", "user_alice")
        self.test_model = os.getenv("TEST_MODEL", "gemini-2.0-flash-exp")
    
    def _get_chat_token(self) -> str:
        """构建Chat token从环境变量"""
        # 从.env文件读取基础配置
        user_id = os.getenv("TEST_USER_ID", "user_alice")
        base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        model = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
        api_key = os.getenv("LLM_API_KEY")
        
        if not api_key:
            raise ValueError("LLM_API_KEY 必须在环境变量中设置")
        
        # 使用新的分隔符格式
        return f"{user_id}|||{base_url}|||{model}|||{api_key}"
    
    def validate(self):
        """验证配置完整性"""
        required_vars = [
            ("LLM_API_KEY", os.getenv("LLM_API_KEY")),
            ("ADMIN_SECRET_KEY", os.getenv("ADMIN_SECRET_KEY"))
        ]
        
        for var_name, var_value in required_vars:
            if not var_value:
                raise ValueError(f"环境变量 {var_name} 未设置")


class AuthenticationTester:
    """认证系统测试器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
    
    async def test_chat_api(self) -> bool:
        """测试Chat API的认证"""
        print("🔍 测试Chat API认证...")
        
        test_payload = {
            "model": self.config.test_model,
            "messages": [
                {"role": "user", "content": "Hello, my name is Alice. I like coffee."}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.config.main_server}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.chat_token}",
                        "Content-Type": "application/json"
                    },
                    json=test_payload
                ) as response:
                    print(f"   状态码: {response.status}")
                    if response.status == 200:
                        print("   ✅ Chat API认证成功")
                        result = await response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"   响应: {content[:100]}...")
                        return True
                    else:
                        print(f"   ❌ Chat API认证失败: {await response.text()}")
                        return False
            except Exception as e:
                print(f"   ❌ Chat API连接错误: {e}")
                return False
    
    async def test_memory_api(self) -> bool:
        """测试Memory API的认证"""
        print("\n🧠 测试Memory API认证...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 保存记忆
                async with session.post(
                    f"{self.config.main_server}/v1/memory/save",
                    headers={
                        "Authorization": f"Bearer {self.config.memory_token}",
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
                        return False
                
                # 搜索记忆
                async with session.get(
                    f"{self.config.main_server}/v1/memory/search?query=咖啡",
                    headers={
                        "Authorization": f"Bearer {self.config.memory_token}",
                    }
                ) as response:
                    print(f"   搜索记忆 - 状态码: {response.status}")
                    if response.status == 200:
                        print("   ✅ Memory API搜索成功")
                        result = await response.json()
                        print(f"   结果: {result}")
                        return True
                    else:
                        print(f"   ❌ Memory API搜索失败: {await response.text()}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ Memory API连接错误: {e}")
                return False
    
    async def test_admin_api(self) -> bool:
        """测试Admin API的认证"""
        print("\n🎛️ 测试Admin API认证...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 测试统计信息
                async with session.get(
                    f"{self.config.admin_server}/admin/stats",
                    headers={
                        "Authorization": f"Bearer {self.config.admin_token}",
                    }
                ) as response:
                    print(f"   获取统计 - 状态码: {response.status}")
                    if response.status == 200:
                        print("   ✅ Admin API认证成功")
                        result = await response.json()
                        print(f"   统计数据: {result}")
                    else:
                        print(f"   ❌ Admin API认证失败: {await response.text()}")
                        return False
                
                # 测试用户列表
                async with session.get(
                    f"{self.config.admin_server}/admin/users",
                    headers={
                        "Authorization": f"Bearer {self.config.admin_token}",
                    }
                ) as response:
                    print(f"   获取用户列表 - 状态码: {response.status}")
                    if response.status == 200:
                        print("   ✅ Admin用户列表获取成功")
                        result = await response.json()
                        print(f"   用户数量: {len(result)}")
                        return True
                    else:
                        print(f"   ❌ Admin用户列表获取失败: {await response.text()}")
                        return False
                        
            except Exception as e:
                print(f"   ❌ Admin API连接错误: {e}")
                return False
    
    async def test_invalid_tokens(self) -> bool:
        """测试无效token的拒绝"""
        print("\n🚫 测试无效token...")
        
        invalid_tokens = [
            ("错误的chat token", "invalid-token"),
            ("错误的memory token", "invalid_user"),
            ("错误的admin token", "wrong-admin-key")
        ]
        
        async with aiohttp.ClientSession() as session:
            all_rejected = True
            for desc, token in invalid_tokens:
                try:
                    async with session.get(
                        f"{self.config.main_server}/v1/memory/list",
                        headers={"Authorization": f"Bearer {token}"}
                    ) as response:
                        if response.status == 401:
                            print(f"   ✅ {desc} 正确被拒绝 (401)")
                        else:
                            print(f"   ❌ {desc} 应该被拒绝但返回了: {response.status}")
                            all_rejected = False
                except Exception as e:
                    print(f"   ❌ 测试 {desc} 时连接错误: {e}")
                    all_rejected = False
            
            return all_rejected


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🎯 Mem0 Chat API 三层认证系统测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 初始化配置
        config = TestConfig()
        config.validate()
        
        print(f"主服务: {config.main_server}")
        print(f"管理后台: {config.admin_server}")
        print(f"测试用户: {config.test_user_id}")
        print(f"测试模型: {config.test_model}")
        print()
        
        # 等待服务启动
        print("⏱️ 等待服务启动...")
        await asyncio.sleep(2)
        
        # 初始化测试器
        tester = AuthenticationTester(config)
        
        # 依次测试各个API
        results = []
        results.append(await tester.test_chat_api())
        results.append(await tester.test_memory_api())
        results.append(await tester.test_admin_api())
        results.append(await tester.test_invalid_tokens())
        
        # 总结结果
        print("\n" + "=" * 60)
        if all(results):
            print("✅ 所有认证测试通过！")
        else:
            print("❌ 部分认证测试失败！")
            failed_tests = []
            test_names = ["Chat API", "Memory API", "Admin API", "Invalid Tokens"]
            for i, result in enumerate(results):
                if not result:
                    failed_tests.append(test_names[i])
            print(f"失败的测试: {', '.join(failed_tests)}")
        print("=" * 60)
        
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("请确保以下环境变量已设置:")
        print("  - LLM_API_KEY: LLM服务的API密钥")
        print("  - ADMIN_SECRET_KEY: 管理员密钥")
        print("建议运行: source .env 或 export $(cat .env | xargs)")
    except Exception as e:
        print(f"❌ 测试执行错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
