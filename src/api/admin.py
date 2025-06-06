"""
管理员API端点
提供用户管理、记忆统计、系统监控等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from src.services.auth_service import verify_admin_token
from src.services.database_service import db_service
from src.services.memory_service import memory_service
from src.config.settings import settings
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

# 添加用户管理相关的数据模型
class CreateUserRequest(BaseModel):
    username: str
    user_token: str

class UpdateUserTokenRequest(BaseModel):
    new_token: str

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """管理员控制台首页"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mem0 Chat API 管理控制台</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
            }
            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .header h1 {
                color: #2c3e50;
                margin-bottom: 0.5rem;
                font-size: 2.5rem;
            }
            .header p {
                color: #7f8c8d;
                font-size: 1.1rem;
            }
            .card {
                background: rgba(255, 255, 255, 0.95);
                padding: 1.5rem;
                border-radius: 15px;
                margin-bottom: 1.5rem;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
            }
            .stat-card {
                text-align: center;
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                color: white;
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 32px rgba(116, 185, 255, 0.3);
            }
            .stat-number {
                font-size: 3rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .stat-label {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            .action-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin-top: 2rem;
            }
            .action-btn {
                display: block;
                padding: 1rem;
                background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                text-align: center;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
            }
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 184, 148, 0.4);
            }
            .danger-btn {
                background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
                box-shadow: 0 4px 15px rgba(225, 112, 85, 0.3);
            }
            .warning-btn {
                background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
                box-shadow: 0 4px 15px rgba(253, 203, 110, 0.3);
            }
            .login-form {
                max-width: 400px;
                margin: 0 auto;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .form-group {
                margin-bottom: 1rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #2c3e50;
            }
            .form-group input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.3s;
            }
            .form-group input:focus {
                outline: none;
                border-color: #74b9ff;
            }
            .btn-primary {
                width: 100%;
                padding: 0.75rem;
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
            }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- 登录表单 -->
            <div id="loginForm" class="login-form">
                <h2 style="text-align: center; margin-bottom: 2rem; color: #2c3e50;">管理员登录</h2>
                <div class="form-group">
                    <label for="adminKey">管理员密钥</label>
                    <input type="password" id="adminKey" placeholder="请输入管理员密钥">
                </div>
                <button class="btn-primary" onclick="login()">登录</button>
            </div>

            <!-- 管理界面 -->
            <div id="adminPanel" class="hidden">
                <div class="header">
                    <h1>🎛️ Mem0 Chat API 管理控制台</h1>
                    <p>多用户记忆隔离 Chat API 中转服务管理界面</p>
                </div>

                <!-- 统计卡片 -->
                <div class="grid">
                    <div class="stat-card">
                        <div class="stat-number" id="totalUsers">-</div>
                        <div class="stat-label">总用户数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalMemories">-</div>
                        <div class="stat-label">总记忆条目</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="todayRequests">-</div>
                        <div class="stat-label">今日请求</div>
                    </div>
                </div>

                <!-- 功能区域 -->
                <div class="card">
                    <h2 style="margin-bottom: 1rem;">🔧 管理功能</h2>
                    <div class="action-grid">
                        <a href="#" class="action-btn" onclick="loadUsers()">👥 用户管理</a>
                        <a href="#" class="action-btn" onclick="loadMemories()">🧠 记忆管理</a>
                        <a href="#" class="action-btn" onclick="loadStats()">📊 系统统计</a>
                        <a href="#" class="action-btn warning-btn" onclick="exportData()">📤 导出数据</a>
                        <a href="#" class="action-btn danger-btn" onclick="clearAllData()">🗑️ 清空数据</a>
                        <a href="#" class="action-btn" onclick="logout()">🚪 退出登录</a>
                    </div>
                </div>

                <!-- 数据显示区域 -->
                <div class="card">
                    <h2 style="margin-bottom: 1rem;">📋 数据详情</h2>
                    <div id="dataContent">
                        <p style="color: #7f8c8d; text-align: center; padding: 2rem;">选择上方功能查看详细数据</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let adminToken = null;

            function login() {
                const key = document.getElementById('adminKey').value;
                if (!key) {
                    alert('请输入管理员密钥');
                    return;
                }
                
                adminToken = key;
                document.getElementById('loginForm').classList.add('hidden');
                document.getElementById('adminPanel').classList.remove('hidden');
                loadDashboard();
            }

            function logout() {
                adminToken = null;
                document.getElementById('loginForm').classList.remove('hidden');
                document.getElementById('adminPanel').classList.add('hidden');
                document.getElementById('adminKey').value = '';
            }

            async function apiCall(endpoint, method = 'GET') {
                const response = await fetch(endpoint, {
                    method,
                    headers: {
                        'Authorization': `Bearer ${adminToken}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        alert('认证失败，请重新登录');
                        logout();
                        return null;
                    }
                    throw new Error(`API调用失败: ${response.status}`);
                }
                
                return await response.json();
            }

            async function loadDashboard() {
                try {
                    const stats = await apiCall('/admin/stats');
                    if (stats) {
                        document.getElementById('totalUsers').textContent = stats.total_users || 0;
                        document.getElementById('totalMemories').textContent = stats.total_memories || 0;
                        document.getElementById('todayRequests').textContent = stats.today_requests || 0;
                    }
                } catch (error) {
                    console.error('加载统计数据失败:', error);
                }
            }

            async function loadUsers() {
                try {
                    const users = await apiCall('/admin/users');
                    if (users) {
                        let html = '<h3>👥 用户管理</h3>';
                        
                        // 添加用户表单
                        html += `<div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                            <h4>➕ 创建新用户</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 1rem; align-items: end;">
                                <div>
                                    <label>用户名:</label>
                                    <input type="text" id="newUsername" placeholder="输入用户名" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                                </div>
                                <div>
                                    <label>用户Token:</label>
                                    <input type="text" id="newUserToken" placeholder="输入用户token" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                                </div>
                                <button onclick="createUser()" style="background: #00b894; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; cursor: pointer;">创建用户</button>
                            </div>
                        </div>`;
                        
                        // 用户列表表格
                        html += '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse;">';
                        html += '<tr style="background: #f8f9fa;"><th style="padding: 1rem; border: 1px solid #ddd;">用户ID</th><th style="padding: 1rem; border: 1px solid #ddd;">用户名</th><th style="padding: 1rem; border: 1px solid #ddd;">Token</th><th style="padding: 1rem; border: 1px solid #ddd;">记忆数量</th><th style="padding: 1rem; border: 1px solid #ddd;">最后活动</th><th style="padding: 1rem; border: 1px solid #ddd;">操作</th></tr>';
                        
                        users.forEach(user => {
                            html += `<tr>
                                <td style="padding: 1rem; border: 1px solid #ddd;">${user.user_id}</td>
                                <td style="padding: 1rem; border: 1px solid #ddd;">${user.username || 'N/A'}</td>
                                <td style="padding: 1rem; border: 1px solid #ddd;">
                                    <code style="background: #e9ecef; padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.8rem;">
                                        ${user.user_token ? user.user_token.substring(0, 20) + '...' : 'N/A'}
                                    </code>
                                </td>
                                <td style="padding: 1rem; border: 1px solid #ddd;">${user.memory_count}</td>
                                <td style="padding: 1rem; border: 1px solid #ddd;">${user.last_activity || 'N/A'}</td>
                                <td style="padding: 1rem; border: 1px solid #ddd;">
                                    <button onclick="clearUserMemories('${user.user_id}')" style="background: #fdcb6e; color: white; border: none; padding: 0.3rem 0.6rem; border-radius: 4px; cursor: pointer; margin-right: 0.5rem; font-size: 0.8rem;">清空记忆</button>
                                    <button onclick="deleteUser('${user.user_id}')" style="background: #e74c3c; color: white; border: none; padding: 0.3rem 0.6rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">删除用户</button>
                                </td>
                            </tr>`;
                        });
                        
                        html += '</table></div>';
                        document.getElementById('dataContent').innerHTML = html;
                    }
                } catch (error) {
                    console.error('加载用户列表失败:', error);
                    document.getElementById('dataContent').innerHTML = '<p style="color: #e74c3c;">加载用户列表失败</p>';
                }
            }
            
            async function createUser() {
                const username = document.getElementById('newUsername').value.trim();
                const userToken = document.getElementById('newUserToken').value.trim();
                
                if (!username || !userToken) {
                    alert('请输入用户名和token');
                    return;
                }
                
                try {
                    const response = await fetch('/admin/users', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${adminToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            username: username,
                            user_token: userToken
                        })
                    });
                    
                    if (response.ok) {
                        alert('用户创建成功');
                        document.getElementById('newUsername').value = '';
                        document.getElementById('newUserToken').value = '';
                        loadUsers();
                    } else {
                        const error = await response.json();
                        alert('创建失败: ' + error.detail);
                    }
                } catch (error) {
                    alert('创建失败: ' + error.message);
                }
            }
            
            async function deleteUser(userId) {
                if (confirm(`⚠️ 确定要删除用户 ${userId} 吗？这将同时删除该用户的所有记忆数据！此操作不可恢复！`)) {
                    try {
                        await apiCall(`/admin/users/${userId}`, 'DELETE');
                        alert('用户已删除');
                        loadUsers();
                    } catch (error) {
                        alert('删除失败: ' + error.message);
                    }
                }
            }

            async function loadMemories() {
                try {
                    const memories = await apiCall('/admin/memories');
                    if (memories) {
                        let html = '<h3>🧠 记忆管理</h3><div style="max-height: 500px; overflow-y: auto;">';
                        
                        memories.forEach(memory => {
                            html += `<div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #74b9ff;">
                                <div style="font-weight: bold; color: #2c3e50;">用户: ${memory.user_id}</div>
                                <div style="margin: 0.5rem 0; color: #555;">${memory.content}</div>
                                <div style="font-size: 0.9rem; color: #7f8c8d;">创建时间: ${memory.created_at}</div>
                                <button onclick="deleteMemory('${memory.id}')" style="background: #e74c3c; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer; margin-top: 0.5rem; font-size: 0.8rem;">删除</button>
                            </div>`;
                        });
                        
                        html += '</div>';
                        document.getElementById('dataContent').innerHTML = html;
                    }
                } catch (error) {
                    console.error('加载记忆列表失败:', error);
                    document.getElementById('dataContent').innerHTML = '<p style="color: #e74c3c;">加载记忆列表失败</p>';
                }
            }

            async function loadStats() {
                try {
                    const stats = await apiCall('/admin/detailed-stats');
                    if (stats) {
                        let html = '<h3>📊 系统统计</h3>';
                        html += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">`;
                        
                        for (const [key, value] of Object.entries(stats)) {
                            html += `<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-size: 2rem; font-weight: bold; color: #2c3e50;">${value}</div>
                                <div style="color: #7f8c8d;">${key.replace(/_/g, ' ').toUpperCase()}</div>
                            </div>`;
                        }
                        
                        html += '</div>';
                        document.getElementById('dataContent').innerHTML = html;
                    }
                } catch (error) {
                    console.error('加载统计数据失败:', error);
                    document.getElementById('dataContent').innerHTML = '<p style="color: #e74c3c;">加载统计数据失败</p>';
                }
            }

            async function clearUserMemories(userId) {
                if (confirm(`确定要清空用户 ${userId} 的所有记忆吗？此操作不可恢复！`)) {
                    try {
                        await apiCall(`/admin/users/${userId}/memories`, 'DELETE');
                        alert('用户记忆已清空');
                        loadUsers();
                    } catch (error) {
                        alert('清空失败: ' + error.message);
                    }
                }
            }

            async function deleteMemory(memoryId) {
                if (confirm('确定要删除这条记忆吗？此操作不可恢复！')) {
                    try {
                        await apiCall(`/admin/memories/${memoryId}`, 'DELETE');
                        alert('记忆已删除');
                        loadMemories();
                    } catch (error) {
                        alert('删除失败: ' + error.message);
                    }
                }
            }

            async function clearAllData() {
                if (confirm('⚠️ 警告：确定要清空所有数据吗？这将删除所有用户的记忆数据，此操作不可恢复！\\n\\n请输入 "CONFIRM" 确认')) {
                    const confirmation = prompt('请输入 "CONFIRM" 来确认删除所有数据:');
                    if (confirmation === 'CONFIRM') {
                        try {
                            await apiCall('/admin/clear-all', 'DELETE');
                            alert('所有数据已清空');
                            loadDashboard();
                        } catch (error) {
                            alert('清空失败: ' + error.message);
                        }
                    }
                }
            }

            async function exportData() {
                try {
                    const response = await fetch('/admin/export', {
                        headers: {
                            'Authorization': `Bearer ${adminToken}`
                        }
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `mem0_export_${new Date().toISOString().split('T')[0]}.json`;
                        a.click();
                        window.URL.revokeObjectURL(url);
                    } else {
                        alert('导出失败');
                    }
                } catch (error) {
                    alert('导出失败: ' + error.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/stats")
async def get_basic_stats(admin_token: str = Depends(verify_admin_token)):
    """获取基础统计信息"""
    try:
        stats = await db_service.get_stats()
        return {
            "total_users": stats["total_users"],
            "total_memories": stats["total_memories"],
            "today_requests": stats["active_users_today"] * 10  # 估算今日请求
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/detailed-stats")
async def get_detailed_stats(admin_token: str = Depends(verify_admin_token)):
    """获取详细统计信息"""
    try:
        stats = await db_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取详细统计信息失败: {str(e)}")

@router.get("/users")
async def list_users(admin_token: str = Depends(verify_admin_token)):
    """获取用户列表"""
    try:
        users = await db_service.get_all_users()
        return [
            {
                "user_id": user.user_id,
                "memory_count": user.memory_count,
                "last_activity": user.last_activity
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

@router.get("/memories")
async def list_all_memories(
    admin_token: str = Depends(verify_admin_token),
    limit: int = Query(50, description="返回记忆数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """获取所有记忆列表"""
    try:
        memories = await db_service.get_all_memories(limit=limit, offset=offset)
        return [
            {
                "id": memory.id,
                "user_id": memory.user_id,
                "content": memory.content,
                "created_at": memory.created_at
            }
            for memory in memories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆列表失败: {str(e)}")

@router.delete("/users/{user_id}/memories")
async def clear_user_memories(
    user_id: str,
    admin_token: str = Depends(verify_admin_token)
):
    """清空指定用户的所有记忆"""
    try:
        deleted_count = await db_service.clear_user_memories(user_id)
        return {"message": f"用户 {user_id} 的 {deleted_count} 条记忆已清空", "user_id": user_id, "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空用户记忆失败: {str(e)}")

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    admin_token: str = Depends(verify_admin_token)
):
    """删除指定记忆"""
    try:
        deleted = await db_service.delete_memory(memory_id)
        if deleted:
            return {"message": "记忆已删除", "memory_id": memory_id}
        else:
            raise HTTPException(status_code=404, detail="记忆不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记忆失败: {str(e)}")

@router.delete("/clear-all")
async def clear_all_data(admin_token: str = Depends(verify_admin_token)):
    """清空所有数据（危险操作）"""
    try:
        result = await db_service.clear_all_data()
        return {
            "message": "所有数据已清空", 
            "timestamp": datetime.now().isoformat(),
            "deleted_users": result["deleted_users"],
            "deleted_memories": result["deleted_memories"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空所有数据失败: {str(e)}")

@router.get("/export")
async def export_data(admin_token: str = Depends(verify_admin_token)):
    """导出所有数据"""
    try:
        export_data = await db_service.export_all_data()
        
        from fastapi.responses import Response
        import json
        
        return Response(
            content=json.dumps(export_data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=mem0_export.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")

@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    admin_token: str = Depends(verify_admin_token)
):
    """创建新用户"""
    try:
        user = await db_service.create_user(request.username, request.user_token)
        return {
            "message": "用户创建成功",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "user_token": user.user_token,
                "created_at": user.first_seen
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_token: str = Depends(verify_admin_token)
):
    """删除用户及其所有记忆"""
    try:
        deleted = await db_service.delete_user(user_id)
        if deleted:
            return {
                "message": "用户已删除",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

@router.put("/users/{user_id}/token")
async def update_user_token(
    user_id: str,
    request: UpdateUserTokenRequest,
    admin_token: str = Depends(verify_admin_token)
):
    """更新用户token"""
    try:
        updated = await db_service.update_user_token(user_id, request.new_token)
        if updated:
            return {
                "message": "用户token已更新",
                "user_id": user_id,
                "new_token": request.new_token,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新token失败: {str(e)}")

@router.get("/users/by-token/{user_token}")
async def get_user_by_token(
    user_token: str,
    admin_token: str = Depends(verify_admin_token)
):
    """根据token查找用户"""
    try:
        user = await db_service.get_user_by_token(user_token)
        if user:
            return {
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "user_token": user.user_token,
                    "memory_count": user.memory_count,
                    "first_seen": user.first_seen,
                    "last_activity": user.last_activity,
                    "total_requests": user.total_requests
                }
            }
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找用户失败: {str(e)}")
