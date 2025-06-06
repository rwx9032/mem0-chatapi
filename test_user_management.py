#!/usr/bin/env python3
"""
用户管理功能测试脚本
测试管理API的用户创建、删除、token验证等功能
"""

import requests
import json
import os
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8051"
ADMIN_URL = "http://localhost:8061"
ADMIN_TOKEN = os.getenv("ADMIN_SECRET_KEY", "super-secret-admin-key")

def test_admin_auth():
    """测试管理员认证"""
    print("🔐 测试管理员认证...")
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.get(f"{ADMIN_URL}/admin/stats", headers=headers)
    
    if response.status_code == 200:
        print("✅ 管理员认证成功")
        print(f"📊 系统统计: {response.json()}")
        return True
    else:
        print(f"❌ 管理员认证失败: {response.status_code}")
        return False

def test_create_user():
    """测试创建用户"""
    print("\n👤 测试创建用户...")
    
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    user_data = {
        "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
        "user_token": f"test_token_{datetime.now().strftime('%H%M%S')}"
    }
    
    response = requests.post(f"{ADMIN_URL}/admin/users", headers=headers, json=user_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 用户创建成功")
        print(f"📝 用户信息: {result}")
        return result["user"]["user_id"], result["user"]["user_token"]
    else:
        print(f"❌ 用户创建失败: {response.status_code} - {response.text}")
        return None, None

def test_get_users():
    """测试获取用户列表"""
    print("\n📋 测试获取用户列表...")
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.get(f"{ADMIN_URL}/admin/users", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        print("✅ 获取用户列表成功")
        print(f"👥 用户数量: {len(users)}")
        return users
    else:
        print(f"❌ 获取用户列表失败: {response.status_code}")
        return []

def test_user_token_auth(user_token):
    """测试用户token认证"""
    print(f"\n🔑 测试用户token认证: {user_token[:20]}...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/v1/memory/list", headers=headers)
    
    if response.status_code == 200:
        print("✅ 用户token认证成功")
        return True
    else:
        print(f"❌ 用户token认证失败: {response.status_code}")
        return False

def test_memory_operations(user_token, user_id):
    """测试记忆操作"""
    print(f"\n🧠 测试记忆操作 (用户: {user_id})...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 添加记忆
    memory_data = {
        "content": f"测试记忆内容 - {datetime.now()}"
    }
    
    response = requests.post(f"{BASE_URL}/v1/memory/save", headers=headers, json=memory_data)
    
    if response.status_code == 200:
        print("✅ 添加记忆成功")
        memory_result = response.json()
        print(f"记忆保存结果: {memory_result}")
        
        # 获取记忆列表
        response = requests.get(f"{BASE_URL}/v1/memory/list", headers=headers)
        if response.status_code == 200:
            result = response.json()
            memories = result.get("data", [])
            print(f"📝 用户记忆数量: {len(memories)}")
            print(f"记忆内容: {memories}")
            return True
        else:
            print(f"❌ 获取记忆失败: {response.status_code}")
            return False
    else:
        print(f"❌ 添加记忆失败: {response.status_code} - {response.text}")
        return False

def test_find_user_by_token(user_token):
    """测试根据token查找用户"""
    print(f"\n🔍 测试根据token查找用户...")
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.get(f"{ADMIN_URL}/admin/users/by-token/{user_token}", headers=headers)
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ 根据token查找用户成功")
        print(f"👤 用户信息: {user_info}")
        return True
    else:
        print(f"❌ 根据token查找用户失败: {response.status_code}")
        return False

def test_delete_user(user_id):
    """测试删除用户"""
    print(f"\n🗑️ 测试删除用户: {user_id}...")
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.delete(f"{ADMIN_URL}/admin/users/{user_id}", headers=headers)
    
    if response.status_code == 200:
        print("✅ 删除用户成功")
        return True
    else:
        print(f"❌ 删除用户失败: {response.status_code}")
        return False

def main():
    """主测试流程"""
    print("🚀 开始用户管理功能测试\n")
    
    # 1. 测试管理员认证
    if not test_admin_auth():
        return
    
    # 2. 获取初始用户列表
    initial_users = test_get_users()
    
    # 3. 创建新用户
    user_id, user_token = test_create_user()
    if not user_id:
        return
    
    # 4. 测试用户token认证
    if not test_user_token_auth(user_token):
        return
    
    # 5. 测试记忆操作
    if not test_memory_operations(user_token, user_id):
        return
    
    # 6. 根据token查找用户
    if not test_find_user_by_token(user_token):
        return
    
    # 7. 获取更新后的用户列表
    updated_users = test_get_users()
    if len(updated_users) > len(initial_users):
        print("✅ 用户列表已更新")
    
    # 8. 删除测试用户
    if test_delete_user(user_id):
        # 验证删除后token失效
        print("\n🔒 验证删除后token失效...")
        if not test_user_token_auth(user_token):
            print("✅ 删除用户后token已失效")
    
    print("\n🎉 所有测试完成！")

if __name__ == "__main__":
    main()
