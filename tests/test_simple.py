#!/usr/bin/env python3
"""
简单的API功能测试
测试各个API端点的基本功能
"""

import asyncio
import aiohttp
import os
from datetime import datetime


class SimpleAPITester:
    """简单API测试器"""
    
    def __init__(self):
        self.main_server = os.getenv("TEST_MAIN_SERVER", "http://localhost:8050")
        self.admin_server = os.getenv("TEST_ADMIN_SERVER", "http://localhost:8060")
    
    async def test_health_check(self):
        """测试健康检查端点"""
        print("🔍 测试健康检查...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.main_server}/health") as response:
                    if response.status == 200:
                        print("   ✅ 主服务健康检查通过")
                        result = await response.json()
                        print(f"   状态: {result}")
                    else:
                        print(f"   ❌ 主服务健康检查失败: {response.status}")
            except Exception as e:
                print(f"   ❌ 主服务连接错误: {e}")
            
            try:
                async with session.get(f"{self.admin_server}/health") as response:
                    if response.status == 200:
                        print("   ✅ 管理服务健康检查通过")
                        result = await response.json()
                        print(f"   状态: {result}")
                    else:
                        print(f"   ❌ 管理服务健康检查失败: {response.status}")
            except Exception as e:
                print(f"   ❌ 管理服务连接错误: {e}")
    
    async def test_models_endpoint(self):
        """测试模型列表端点（需要token）"""
        print("\n📋 测试模型列表端点...")
        
        # 构建token（从环境变量）
        user_id = os.getenv("TEST_USER_ID", "user_alice")
        base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        model = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
        api_key = os.getenv("LLM_API_KEY")
        
        if not api_key:
            print("   ⚠️ 跳过 - LLM_API_KEY 未设置")
            return
        
        chat_token = f"{user_id}|||{base_url}|||{model}|||{api_key}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.main_server}/v1/models",
                    headers={"Authorization": f"Bearer {chat_token}"}
                ) as response:
                    if response.status == 200:
                        print("   ✅ 模型列表获取成功")
                        result = await response.json()
                        print(f"   可用模型: {[m['id'] for m in result.get('data', [])]}")
                    else:
                        print(f"   ❌ 模型列表获取失败: {response.status}")
            except Exception as e:
                print(f"   ❌ 模型列表请求错误: {e}")
    
    async def test_admin_dashboard(self):
        """测试管理后台页面"""
        print("\n🎛️ 测试管理后台...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.admin_server}/") as response:
                    if response.status == 200:
                        print("   ✅ 管理后台页面可访问")
                        content = await response.text()
                        if "Mem0 Chat API" in content:
                            print("   ✅ 页面内容正确")
                        else:
                            print("   ⚠️ 页面内容可能不正确")
                    else:
                        print(f"   ❌ 管理后台页面访问失败: {response.status}")
            except Exception as e:
                print(f"   ❌ 管理后台连接错误: {e}")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Mem0 Chat API 简单功能测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = SimpleAPITester()
    
    print("⏱️ 等待服务启动...")
    await asyncio.sleep(2)
    
    await tester.test_health_check()
    await tester.test_models_endpoint()
    await tester.test_admin_dashboard()
    
    print("\n" + "=" * 60)
    print("✅ 简单功能测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
