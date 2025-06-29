#!/usr/bin/env python3
"""
使用真正的OpenAI库测试Mem0 Chat API
测试多轮对话记忆和流式输出功能
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from openai import OpenAI
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Mem0ChatTester:
    """使用OpenAI库测试Mem0 Chat API"""
    
    def __init__(self, base_url: str = "http://localhost:8050", user_token: str = "test_token_123"):
        """
        初始化测试器
        
        Args:
            base_url: Mem0 Chat API服务器地址
            user_token: 用户token（将与环境变量中的LLM配置组合）
        """
        # 从环境变量读取LLM配置
        llm_base_url = os.getenv('LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')
        llm_model = os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')
        llm_api_key = os.getenv('LLM_API_KEY')
        
        if not llm_api_key:
            raise ValueError("LLM_API_KEY environment variable is required")
        
        # 构建完整的API key: user_token|||base_url|||model|||api_key
        api_key = f"{user_token}|||{llm_base_url}|||{llm_model}|||{llm_api_key}"
        
        self.client = OpenAI(
            base_url=f"{base_url}/v1",
            api_key=api_key
        )
        self.api_key = api_key
    
    def print_section(self, title: str):
        """打印测试节标题"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def test_basic_chat_with_memory(self):
        """测试基本对话和记忆功能"""
        self.print_section("基本对话和记忆测试")
        
        try:
            print("💬 发送消息: 我是王小明，25岁，在北京工作，是一名Python开发工程师，喜欢机器学习。")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "我是王小明，25岁，在北京工作，是一名Python开发工程师，喜欢机器学习。"}
                ],
                temperature=0.7,
                extra_body={"enable_memory": True}
            )
            
            print(f"🤖 AI回复: {response.choices[0].message.content}")
            print(f"📊 使用模型: {response.model}")
            print(f"🔢 使用tokens: {response.usage.total_tokens if response.usage else 'N/A'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 基本对话测试失败: {e}")
            return False
    
    def test_memory_recall(self):
        """测试记忆回忆功能"""
        self.print_section("记忆回忆测试")
        
        try:
            # 等待一下确保记忆已保存
            time.sleep(2)
            
            print("💬 发送消息: 我的名字是什么？我的职业是什么？")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "我的名字是什么？我的职业是什么？"}
                ],
                temperature=0.7,
                extra_body={"enable_memory": True}
            )
            
            reply = response.choices[0].message.content
            print(f"🤖 AI回复: {reply}")
            
            # 检查是否包含用户信息
            if "王小明" in reply and ("Python" in reply or "开发" in reply):
                print("✅ 记忆回忆成功！AI正确记住了用户信息")
            else:
                print("⚠️  记忆回忆可能有问题，AI没有提到用户的具体信息")
            
            return True
            
        except Exception as e:
            print(f"❌ 记忆回忆测试失败: {e}")
            return False
    
    def test_multi_turn_conversation(self):
        """测试多轮对话记忆"""
        self.print_section("多轮对话记忆测试")
        
        conversation_history = []
        turns = [
            "我最近想学习深度学习，有什么推荐吗？",
            "我比较倾向于使用PyTorch框架，你觉得怎么样？",
            "能推荐一些适合初学者的项目吗？",
            "我之前做过图像分类项目，想尝试更复杂的任务。"
        ]
        
        try:
            for i, user_message in enumerate(turns, 1):
                print(f"\n💬 第{i}轮 - 用户: {user_message}")
                
                # 添加用户消息到历史
                conversation_history.append({"role": "user", "content": user_message})
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=conversation_history,
                    temperature=0.7,
                    extra_body={"enable_memory": True}
                )
                
                ai_reply = response.choices[0].message.content
                print(f"🤖 第{i}轮 - AI回复: {ai_reply}")
                
                # 添加AI回复到历史
                conversation_history.append({"role": "assistant", "content": ai_reply})
                
                # 短暂延迟
                time.sleep(1)
            
            print("✅ 多轮对话测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 多轮对话测试失败: {e}")
            return False
    
    def test_streaming_output(self):
        """测试流式输出功能"""
        self.print_section("流式输出测试")
        
        try:
            print("💬 发送消息: 请给我详细介绍一下机器学习的发展历程，包括重要的里程碑。")
            print("🌊 开始流式输出:")
            print("-" * 40)
            
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "请给我详细介绍一下机器学习的发展历程，包括重要的里程碑。"}
                ],
                temperature=0.7,
                stream=True,
                extra_body={"enable_memory": True}
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n" + "-" * 40)
            print("✅ 流式输出测试完成")
            print(f"📝 总字符数: {len(full_response)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 流式输出测试失败: {e}")
            return False
    
    def test_memory_with_streaming(self):
        """测试记忆功能配合流式输出"""
        self.print_section("记忆+流式输出组合测试")
        
        try:
            # 等待确保之前的记忆已保存
            time.sleep(2)
            
            print("💬 发送消息: 基于我的背景和兴趣，推荐一个详细的学习计划。")
            print("🌊 开始流式输出:")
            print("-" * 40)
            
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "基于我的背景和兴趣，推荐一个详细的学习计划。"}
                ],
                temperature=0.7,
                stream=True,
                extra_body={"enable_memory": True}
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n" + "-" * 40)
            
            # 检查是否使用了记忆信息
            if any(keyword in full_response for keyword in ["王小明", "Python", "北京", "机器学习", "开发"]):
                print("✅ AI成功结合记忆信息生成个性化回复！")
            else:
                print("⚠️  AI可能没有充分利用记忆信息")
            
            return True
            
        except Exception as e:
            print(f"❌ 记忆+流式输出测试失败: {e}")
            return False
    
    def test_without_memory(self):
        """测试禁用记忆功能"""
        self.print_section("禁用记忆功能测试")
        
        try:
            print("💬 发送消息: 我的名字是什么？（记忆功能已禁用）")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "我的名字是什么？"}
                ],
                temperature=0.7,
                extra_body={"enable_memory": False}
            )
            
            reply = response.choices[0].message.content
            print(f"🤖 AI回复: {reply}")
            
            # 应该不知道用户信息
            if "不知道" in reply or "没有" in reply or "无法" in reply:
                print("✅ 禁用记忆功能正常工作")
            else:
                print("⚠️  禁用记忆功能可能有问题")
            
            return True
            
        except Exception as e:
            print(f"❌ 禁用记忆测试失败: {e}")
            return False
    
    def test_complex_scenario(self):
        """测试复杂场景：多轮对话+记忆+流式输出"""
        self.print_section("复杂场景测试")
        
        try:
            scenarios = [
                {
                    "message": "我想开始一个新的深度学习项目，你有什么建议吗？",
                    "stream": False,
                    "description": "项目咨询（非流式）"
                },
                {
                    "message": "请详细解释一下卷积神经网络的工作原理。",
                    "stream": True,
                    "description": "技术解释（流式）"
                },
                {
                    "message": "考虑到我的背景，这个项目适合我吗？",
                    "stream": False,
                    "description": "个性化建议（非流式）"
                }
            ]
            
            conversation_history = []
            
            for i, scenario in enumerate(scenarios, 1):
                print(f"\n💬 第{i}轮 - {scenario['description']}")
                print(f"消息: {scenario['message']}")
                
                conversation_history.append({"role": "user", "content": scenario['message']})
                
                if scenario['stream']:
                    print("🌊 流式输出:")
                    print("-" * 30)
                    
                    stream = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=conversation_history,
                        temperature=0.7,
                        stream=True,
                        extra_body={"enable_memory": True}
                    )
                    
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            print(content, end="", flush=True)
                            full_response += content
                    
                    print("\n" + "-" * 30)
                    conversation_history.append({"role": "assistant", "content": full_response})
                    
                else:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=conversation_history,
                        temperature=0.7,
                        extra_body={"enable_memory": True}
                    )
                    
                    ai_reply = response.choices[0].message.content
                    print(f"🤖 AI回复: {ai_reply}")
                    conversation_history.append({"role": "assistant", "content": ai_reply})
                
                time.sleep(1)
            
            print("✅ 复杂场景测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 复杂场景测试失败: {e}")
            return False


def main():
    """主测试函数"""
    print("🚀 启动OpenAI库集成测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 配置
    BASE_URL = "http://localhost:8050"
    USER_TOKEN = "test_token_123"  # 只需要用户token，LLM配置从环境变量读取
    
    print(f"🌐 服务器地址: {BASE_URL}")
    print(f"🔑 用户Token: {USER_TOKEN}")
    print(f"🤖 LLM模型: {os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')}")
    print(f"🌍 LLM服务: {os.getenv('LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/')}")
    
    tester = Mem0ChatTester(BASE_URL, USER_TOKEN)
    
    # 测试结果统计
    test_results = {}
    
    try:
        # 运行所有测试
        test_results["基本对话和记忆"] = tester.test_basic_chat_with_memory()
        time.sleep(1)
        
        test_results["记忆回忆"] = tester.test_memory_recall()
        time.sleep(1)
        
        test_results["多轮对话记忆"] = tester.test_multi_turn_conversation()
        time.sleep(1)
        
        test_results["流式输出"] = tester.test_streaming_output()
        time.sleep(1)
        
        test_results["记忆+流式输出"] = tester.test_memory_with_streaming()
        time.sleep(1)
        
        test_results["禁用记忆"] = tester.test_without_memory()
        time.sleep(1)
        
        test_results["复杂场景"] = tester.test_complex_scenario()
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    
    # 输出测试结果汇总
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！Mem0 Chat API工作正常")
    else:
        print("⚠️  部分测试失败，请检查服务器状态和配置")
    
    print(f"\n✅ 测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 测试程序退出")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        sys.exit(1)
