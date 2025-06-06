import logging
import time
import uuid
from typing import Any, Dict, Optional
from datetime import datetime


def setup_logging(level: str = "INFO") -> None:
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def generate_request_id() -> str:
    """生成请求ID"""
    return f"chatcmpl-{uuid.uuid4().hex[:29]}"


def get_current_timestamp() -> int:
    """获取当前时间戳"""
    return int(time.time())


def format_error_response(error_message: str, error_type: str = "invalid_request_error") -> Dict[str, Any]:
    """格式化错误响应"""
    return {
        "error": {
            "message": error_message,
            "type": error_type,
            "param": None,
            "code": None
        }
    }


def validate_messages(messages: list) -> bool:
    """验证消息格式"""
    if not messages:
        return False
    
    for message in messages:
        if not isinstance(message, dict):
            return False
        if "role" not in message or "content" not in message:
            return False
        if message["role"] not in ["system", "user", "assistant"]:
            return False
    
    return True


def sanitize_user_id(user_id: str) -> str:
    """清理用户ID"""
    if not user_id or not isinstance(user_id, str):
        return "default"
    
    # 移除特殊字符，只保留字母数字和下划线
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    
    # 确保不为空
    return sanitized if sanitized else "default"


def calculate_token_usage(text: str) -> int:
    """简单的 token 计算（粗略估算）"""
    # 这是一个简化的计算，实际应该使用具体的 tokenizer
    return len(text.split()) + len(text) // 4


class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logging.info(f"Performance: {self.name} took {duration:.3f} seconds")
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全的 JSON 解析"""
    try:
        import json
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 1000) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_user_message_content(messages: list) -> str:
    """提取最后一条用户消息内容"""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return message.get("content", "")
    return ""


def build_memory_context(memories: list, max_memories: int = 5) -> str:
    """构建记忆上下文"""
    if not memories:
        return ""
    
    limited_memories = memories[:max_memories]
    context_lines = ["相关记忆:"]
    
    for i, memory in enumerate(limited_memories, 1):
        context_lines.append(f"{i}. {memory}")
    
    return "\n".join(context_lines)


def is_valid_url(url: str) -> bool:
    """验证 URL 格式"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def format_datetime(timestamp: Optional[float] = None) -> str:
    """格式化日期时间"""
    if timestamp is None:
        timestamp = time.time()
    
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # 清理过期的请求记录
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.window_seconds
        ]
        
        # 检查是否超过限制
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[identifier].append(current_time)
        return True
