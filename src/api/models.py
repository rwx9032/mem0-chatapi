from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")


class ChatCompletionRequest(BaseModel):
    """Chat Completion 请求模型"""
    model: str = Field(..., description="使用的模型名称")
    messages: List[ChatMessage] = Field(..., description="对话消息列表")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="最大token数")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="存在惩罚")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="停止序列")
    stream: Optional[bool] = Field(default=False, description="是否流式输出")
    
    # 扩展字段
    user_id: Optional[str] = Field(default="default", description="用户ID，用于记忆管理")
    enable_memory: Optional[bool] = Field(default=True, description="是否启用记忆功能")


class ChatCompletionChoice(BaseModel):
    """Chat Completion 选择项"""
    index: int = Field(..., description="选择项索引")
    message: ChatMessage = Field(..., description="返回的消息")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class ChatCompletionUsage(BaseModel):
    """Token 使用统计"""
    prompt_tokens: int = Field(..., description="提示token数")
    completion_tokens: int = Field(..., description="完成token数")
    total_tokens: int = Field(..., description="总token数")


class ChatCompletionResponse(BaseModel):
    """Chat Completion 响应模型"""
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[ChatCompletionChoice] = Field(..., description="选择项列表")
    usage: Optional[ChatCompletionUsage] = Field(default=None, description="使用统计")


class ChatCompletionStreamDelta(BaseModel):
    """流式响应增量"""
    role: Optional[str] = Field(default=None, description="角色")
    content: Optional[str] = Field(default=None, description="内容增量")


class ChatCompletionStreamChoice(BaseModel):
    """流式响应选择项"""
    index: int = Field(..., description="选择项索引")
    delta: ChatCompletionStreamDelta = Field(..., description="增量内容")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class ChatCompletionStreamResponse(BaseModel):
    """流式 Chat Completion 响应"""
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion.chunk", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[ChatCompletionStreamChoice] = Field(..., description="选择项列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: Dict[str, Any] = Field(..., description="错误信息")


class TokenInfo(BaseModel):
    """Token 信息模型"""
    env_token: str = Field(..., description="环境 Token")
    base_url: str = Field(..., description="API 基础 URL")
    model_name: str = Field(..., description="模型名称")
    actual_token: str = Field(..., description="实际 API Token")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok", description="服务状态")
    timestamp: int = Field(..., description="检查时间戳")
    version: str = Field(default="1.0.0", description="API 版本")


class MemoryResponse(BaseModel):
    """记忆操作响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(default=None, description="返回数据")
